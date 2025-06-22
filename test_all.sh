#!/bin/bash
# test_all.sh
# Created: 2025-06-22
# Comprehensive test script for all MCP Development Toolkit programs

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Utility functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"
    
    ((TOTAL_TESTS++))
    log_info "Testing $test_name..."
    
    # Run command with timeout
    if timeout 5s bash -c "$test_command" 2>/dev/null | grep -q "$expected_pattern"; then
        log_success "$test_name"
        return 0
    else
        log_error "$test_name"
        return 1
    fi
}

run_test_with_output() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"
    
    ((TOTAL_TESTS++))
    log_info "Testing $test_name..."
    
    # Run command and capture output
    local output
    if output=$(timeout 5s bash -c "$test_command" 2>&1); then
        if echo "$output" | grep -q "$expected_pattern"; then
            log_success "$test_name"
            return 0
        else
            log_error "$test_name - Expected: $expected_pattern"
            echo "  Actual output: $output"
            return 1
        fi
    else
        log_error "$test_name - Command failed or timed out"
        return 1
    fi
}

start_background_server() {
    local server_command="$1"
    local server_name="$2"
    local port="$3"
    
    log_info "Starting $server_name..."
    $server_command &
    local server_pid=$!
    
    # Wait for server to start
    sleep 2
    
    # Check if server is running
    if lsof -i :$port >/dev/null 2>&1; then
        log_success "$server_name started on port $port"
        echo $server_pid
    else
        log_error "$server_name failed to start"
        return 1
    fi
}

stop_background_server() {
    local server_pid="$1"
    local server_name="$2"
    
    if kill $server_pid 2>/dev/null; then
        log_info "$server_name stopped"
    else
        log_warning "Could not stop $server_name (PID: $server_pid)"
    fi
}

# Main test execution
main() {
    echo "============================================="
    echo "   MCP Development Toolkit - Full Test Suite"
    echo "============================================="
    echo
    
    # Check prerequisites
    log_info "Checking prerequisites..."
    
    if ! command -v go >/dev/null 2>&1; then
        log_error "Go is not installed"
        exit 1
    fi
    
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python3 is not installed"
        exit 1
    fi
    
    if ! command -v proxy >/dev/null 2>&1; then
        log_error "proxy binary not found in PATH"
        exit 1
    fi
    
    # Check Python requirements
    if [ -f "requirements.txt" ]; then
        log_info "Checking Python requirements..."
        if ! python3 -c "import anthropic, mcp, dotenv, requests" 2>/dev/null; then
            log_warning "Some Python packages missing. Installing requirements..."
            if pip3 install -r requirements.txt; then
                log_success "Python requirements installed"
            else
                log_error "Failed to install Python requirements"
                exit 1
            fi
        else
            log_success "Python requirements satisfied"
        fi
    fi
    
    log_success "Prerequisites check"
    echo
    
    # Test 1: Simple Python programs
    echo "=== Testing Python Programs ==="
    
    run_test_with_output "main.py" "python3 main.py" "Hello from mcph-dev-to-eminetto"
    
    run_test_with_output "anthroptestmcp.py" "python3 anthroptestmcp.py" "I'm Claude"
    
    echo
    
    # Test 2: Build all Go programs
    echo "=== Building Go Programs ==="
    
    for go_file in *.go; do
        if [ -f "$go_file" ]; then
            program_name="${go_file%.go}"
            log_info "Building $go_file..."
            if go build "$go_file" 2>/dev/null; then
                log_success "Built $program_name"
                ((TOTAL_TESTS++))
                ((PASSED_TESTS++))
            else
                log_error "Failed to build $go_file"
                ((TOTAL_TESTS++))
                ((FAILED_TESTS++))
            fi
        fi
    done
    echo
    
    # Test 3: stdio MCP servers
    echo "=== Testing stdio MCP Servers ==="
    
    run_test "helloserver.go (initialize)" \
        "echo '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{},\"id\":1}' | ./helloserver" \
        "serverInfo"
    
    run_test "servermain.go (initialize)" \
        "echo '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{},\"id\":1}' | ./servermain" \
        "serverInfo"
    
    echo
    
    # Test 4: HTTP MCP servers with proxy
    echo "=== Testing HTTP MCP Servers ==="
    
    # Test hellotest.go
    log_info "Testing hellotest.go HTTP server..."
    if hellotest_pid=$(start_background_server "./hellotest" "hellotest HTTP server" "8080"); then
        
        run_test "hellotest.go (initialize via proxy)" \
            "echo '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{},\"id\":1}' | proxy http://localhost:8080/mcp" \
            "serverInfo"
        
        run_test "hellotest.go (tools/list via proxy)" \
            "echo '{\"jsonrpc\":\"2.0\",\"method\":\"tools/list\",\"params\":{},\"id\":2}' | proxy http://localhost:8080/mcp" \
            "tools"
        
        run_test "hellotest.go (time tool via proxy)" \
            "echo '{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"time\",\"arguments\":{\"format\":\"2006-01-02\"}},\"id\":3}' | proxy http://localhost:8080/mcp" \
            "2025-06-22"
        
        stop_background_server $hellotest_pid "hellotest"
        sleep 1
    fi
    
    # Test remoteserver.go
    log_info "Testing remoteserver.go HTTP server..."
    if remoteserver_pid=$(start_background_server "./remoteserver" "remoteserver HTTP server" "8080"); then
        
        run_test "remoteserver.go (initialize via proxy)" \
            "echo '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{},\"id\":1}' | proxy http://localhost:8080/mcp" \
            "remote-address-lookup-server"
        
        run_test "remoteserver.go (tools/list via proxy)" \
            "echo '{\"jsonrpc\":\"2.0\",\"method\":\"tools/list\",\"params\":{},\"id\":2}' | proxy http://localhost:8080/mcp" \
            "remote_address_lookup"
        
        run_test "remoteserver.go (address lookup via proxy)" \
            "echo '{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"remote_address_lookup\",\"arguments\":{\"zip_code\":\"12345\"}},\"id\":3}' | proxy http://localhost:8080/mcp" \
            "Bartonsville Road"
        
        run_test "remoteserver.go (time tool via proxy)" \
            "echo '{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"time\",\"arguments\":{\"format\":\"2006-01-02\"}},\"id\":4}' | proxy http://localhost:8080/mcp" \
            "2025-06-22"
        
        stop_background_server $remoteserver_pid "remoteserver"
        sleep 1
    fi
    
    echo
    
    # Test 5: Proxy programs
    echo "=== Testing Proxy Programs ==="
    
    # Test with a simple HTTP server for proxy testing
    if hellotest_pid=$(start_background_server "./hellotest" "hellotest for proxy testing" "8080"); then
        
        run_test "proxy.go (via binary)" \
            "echo '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{},\"id\":1}' | proxy http://localhost:8080/mcp" \
            "serverInfo"
        
        run_test "proxy1.go (simple proxy)" \
            "echo '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{},\"id\":1}' | go run proxy1.go http://localhost:8080/mcp" \
            "serverInfo"
        
        stop_background_server $hellotest_pid "hellotest"
        sleep 1
    fi
    
    echo
    
    # Test 6: MCP Client
    echo "=== Testing MCP Client ==="
    
    if hellotest_pid=$(start_background_server "./hellotest" "hellotest for client testing" "8080"); then
        
        run_test_with_output "helloclienttest.go (full client test)" \
            "./helloclienttest" \
            "Available Tools"
        
        stop_background_server $hellotest_pid "hellotest"
        sleep 1
    fi
    
    echo
    
    # Test 7: Python health check with running server
    echo "=== Testing Python Health Check ==="
    
    if hellotest_pid=$(start_background_server "./hellotest" "hellotest for health check" "8080"); then
        
        run_test_with_output "direct.py (health check)" \
            "python3 direct.py" \
            "MCP endpoint accessible"
        
        stop_background_server $hellotest_pid "hellotest"
    fi
    
    echo
    
    # Test 8: JavaScript/Node.js programs
    echo "=== Testing JavaScript Programs ==="
    
    if [ -d "npxtest" ] && [ -f "npxtest/test-mcp.js" ]; then
        if hellotest_pid=$(start_background_server "./hellotest" "hellotest for JS testing" "8080"); then
            
            run_test_with_output "test-mcp.js (Node.js client)" \
                "cd npxtest && node test-mcp.js" \
                "response"
            
            stop_background_server $hellotest_pid "hellotest"
        fi
    else
        log_warning "JavaScript test files not found in npxtest/"
    fi
    
    echo
    
    # Clean up any remaining processes
    log_info "Cleaning up..."
    pkill -f "hellotest" 2>/dev/null || true
    pkill -f "remoteserver" 2>/dev/null || true
    pkill -f "helloserver" 2>/dev/null || true
    pkill -f "servermain" 2>/dev/null || true
    
    # Final results
    echo "============================================="
    echo "              TEST RESULTS"
    echo "============================================="
    echo -e "Total Tests:  ${BLUE}$TOTAL_TESTS${NC}"
    echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "\n${GREEN}🎉 ALL TESTS PASSED! 🎉${NC}"
        echo -e "${GREEN}MCP Development Toolkit is 100% functional!${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ Some tests failed${NC}"
        echo -e "Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
        exit 1
    fi
}

# Run main function
main "$@"