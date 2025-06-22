# Test Script Documentation

## Overview
`test_all.sh` is a comprehensive test script that validates all programs in the MCP Development Toolkit.

## Setup Completed
✅ **proxy binary moved to ~/bin/** - The proxy can now be used from any directory

## What the Test Script Does

### 1. **Prerequisites Check**
- Verifies Go is installed
- Verifies Python3 is installed  
- Verifies proxy binary is accessible from PATH

### 2. **Python Programs Testing**
- **main.py**: Tests basic hello message output
- **anthroptestmcp.py**: Tests Anthropic API connectivity
- **direct.py**: Tests HTTP health checking (with running server)

### 3. **Go Program Building**
- Builds all .go files to verify they compile correctly
- Reports build success/failure for each program

### 4. **stdio MCP Servers Testing**
- **helloserver.go**: Tests initialize request/response
- **servermain.go**: Tests initialize request/response

### 5. **HTTP MCP Servers Testing**
- **hellotest.go**: 
  - Tests initialize via proxy
  - Tests tools/list via proxy
  - Tests time tool call via proxy
- **remoteserver.go**:
  - Tests initialize via proxy
  - Tests tools/list via proxy
  - Tests remote_address_lookup tool via proxy
  - Tests time tool via proxy

### 6. **Proxy Programs Testing**
- **proxy** (binary): Tests stdio ↔ HTTP bridging
- **proxy1.go**: Tests simple proxy functionality

### 7. **MCP Client Testing**
- **helloclienttest.go**: Tests full client functionality with tool discovery

### 8. **JavaScript Programs Testing**
- **npxtest/test-mcp.js**: Tests Node.js MCP client (if available)

## Usage

```bash
# Run all tests
./test_all.sh

# The script will show:
# - Colorized output (PASS/FAIL/INFO/WARN)
# - Progress for each test
# - Final summary with success rate
```

## Test Results Format

```
[INFO] Testing program_name...
[PASS] program_name
[FAIL] program_name

===========================================
              TEST RESULTS
===========================================
Total Tests:  25
Passed:       25  
Failed:       0

🎉 ALL TESTS PASSED! 🎉
MCP Development Toolkit is 100% functional!
```

## Key Features

### **Smart Server Management**
- Automatically starts/stops HTTP servers as needed
- Waits for servers to be ready before testing
- Cleans up background processes on completion

### **Comprehensive Testing**
- Tests all transport types (stdio, HTTP)
- Tests all program types (servers, clients, proxies)
- Tests actual MCP protocol messages
- Validates expected responses

### **Error Handling** 
- 5-second timeouts prevent hanging
- Graceful failure handling
- Detailed error reporting
- Clean process cleanup

### **Cross-Language Support**
- Tests Go programs
- Tests Python programs  
- Tests JavaScript programs (if available)

## Expected Test Count
- **~25+ individual tests** covering all programs and functionality
- **100% pass rate expected** for all working programs

## Troubleshooting

### If Tests Fail:
1. **Check Prerequisites**: Ensure Go, Python3, and proxy are installed
2. **Python Dependencies**: Install with `pip3 install -r requirements.txt`
3. **Port Conflicts**: Kill any processes using port 8080
4. **Permissions**: Ensure test_all.sh is executable (`chmod +x test_all.sh`)
5. **Go Dependencies**: Run `go mod tidy` to install Go packages

### Manual Test Commands:
```bash
# Test proxy directly
echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | proxy http://httpbin.org/post

# Test Go server
go run hellotest.go &
echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | proxy http://localhost:8080/mcp
```

## Benefits

1. **Quality Assurance**: Validates all programs work correctly
2. **Regression Testing**: Catches issues after code changes  
3. **Documentation**: Serves as executable documentation
4. **CI/CD Ready**: Can be integrated into automated pipelines
5. **Cross-Platform**: Works on any Unix-like system with bash

This comprehensive test suite ensures the MCP Development Toolkit maintains 100% functionality across all its components.