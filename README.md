# MCP Development Toolkit

This directory contains a comprehensive collection of **working** Model Context Protocol (MCP) implementations in Go and Python, featuring servers, clients, proxies, and testing utilities for both stdio and HTTP transports. All programs in this directory have been tested and verified to work correctly.

**Status: 100% Working Programs** ✅

## Go Programs (7/7 Working)

### **Name:** helloserver.go
**Type:** Go MCP Server (stdio) ✅  
**Description:** Basic MCP server using stdio transport that registers "hello" tool, prompt test, and resource endpoints for testing MCP functionality. Fixed deadlock issue for clean operation.  
**How To Use:** 
```bash
go run helloserver.go
# Or use compiled binary:
./helloserver
# Test with: echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | go run helloserver.go
```

### **Name:** proxy.go
**Type:** Go HTTP Proxy Server (Fully Functional) ✅  
**Description:** Fully functional MCP stdio ↔ HTTP bridge that works like 'supergateway'. Forwards JSON-RPC messages from stdin to HTTP MCP servers, with comprehensive logging. Successfully tested with remoteserver.go for initialize, tool calls, and bidirectional communication.  
**How To Use:** 
```bash
go build proxy.go
./proxy http://localhost:8080/mcp
# Replaces: npx -y supergateway --streamableHttp
# Test with: echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | ./proxy http://localhost:8080/mcp
```

### **Name:** proxy1.go
**Type:** Go HTTP Proxy Server (Simple) ✅  
**Description:** Simplified version of the MCP proxy that forwards JSON-RPC messages between stdin/stdout and a remote HTTP MCP server. Tested and working.  
**How To Use:** 
```bash
go run proxy1.go <target-url>
# Test with: echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | go run proxy1.go http://localhost:8080/mcp
```

### **Name:** remoteserver.go
**Type:** Go MCP HTTP Server (Fully Tested) ✅  
**Description:** Remote MCP server with HTTP transport on port 8080/mcp that provides "remote_address_lookup" and "time" tools. Successfully tested with proxy.go for full MCP protocol compatibility including initialize handshake and tool execution.  
**How To Use:** 
```bash
go run remoteserver.go
# Server runs on http://localhost:8080/mcp
# Test with: echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"time","arguments":{"format":"2006-01-02 15:04:05"}},"id":1}' | ./proxy http://localhost:8080/mcp
```

### **Name:** helloclienttest.go
**Type:** Go MCP Client ✅  
**Description:** HTTP client that connects to an MCP server to test tool listing and calling the "time" tool with different format parameters. Fully functional and tested.  
**How To Use:** 
```bash
# Start a server first (hellotest.go), then:
go run helloclienttest.go
# Expected output: Tool discovery and successful time tool calls
```

### **Name:** hellotest.go
**Type:** Go MCP HTTP Server (Fixed Logging) ✅  
**Description:** Simple HTTP MCP server on port 8080 that provides a "time" tool for returning formatted current time. Fixed logging inconsistency - now correctly shows port 8080.  
**How To Use:** 
```bash
go run hellotest.go
# Server runs on http://localhost:8080/mcp (log message now correct)
# Test with: echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | ./proxy http://localhost:8080/mcp
```

### **Name:** servermain.go
**Type:** Go MCP Server (stdio) ✅  
**Description:** Basic stdio MCP server that implements a "zipcode" tool for returning fake addresses based on zip code input. Fixed deadlock issue for clean operation.  
**How To Use:** 
```bash
go run servermain.go
# Communicates via stdin/stdout
# Test with: echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | go run servermain.go
```

## Python Programs (3/3 Working)

### **Name:** main.py
**Type:** Python Entry Point ✅  
**Description:** Simple Python script that prints a hello message for the mcph-dev-to-eminetto project. Basic functionality verified.  
**How To Use:** 
```bash
python3 main.py
# Expected output: Hello from mcph-dev-to-eminetto!
```

### **Name:** anthroptestmcp.py
**Type:** Python Anthropic MCP Client (Fixed) ✅  
**Description:** Tests Anthropic API connectivity with proper syntax. Fixed API compatibility issues - now works with current Anthropic Python library.  
**How To Use:** 
```bash
python3 anthroptestmcp.py
# Requires Anthropic API key in environment
# Expected output: Claude response confirming API connectivity
```

### **Name:** direct.py
**Type:** Python MCP Health Check (Fully Functional) ✅  
**Description:** Health check script that tests connectivity to a remote MCP server by making HTTP requests to both base URL and MCP endpoint. Works perfectly with Go HTTP servers.  
**How To Use:** 
```bash
python3 direct.py
# Tests http://localhost:8080 and /mcp endpoint
# Expected output: ✅ Base URL accessible, ✅ MCP endpoint accessible, server info
```

## JavaScript Programs (1/1 Working)

### **Name:** npxtest/test-mcp.js
**Type:** Node.js MCP Test Client ✅  
**Description:** Node.js script that tests MCP server endpoints by sending JSON-RPC requests including initialize, list tools, and tool calls.  
**How To Use:** 
```bash
cd npxtest
node test-mcp.js
```

## Quick Start Examples

### 1. Test stdio MCP server:
```bash
go run helloserver.go
# In another terminal: echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | go run helloserver.go
```

### 2. Test HTTP MCP server with proxy:
```bash
# Terminal 1: Start HTTP server
go run remoteserver.go

# Terminal 2: Test with proxy
echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"time","arguments":{"format":"2006-01-02 15:04:05"}},"id":1}' | ./proxy http://localhost:8080/mcp
```

### 3. Python health check:
```bash
# Start a Go server first, then:
python3 direct.py
```

### 4. Full client-server test:
```bash
# Terminal 1: Start server
go run hellotest.go

# Terminal 2: Run client
go run helloclienttest.go
```


These programs expect streaming HTTP MCP servers but work with request/response HTTP servers.

## Dependencies

**Go:** Requires `github.com/metoro-io/mcp-golang` SDK  
```bash
go mod tidy  # Install Go dependencies
```

**Python:** Install required packages using requirements.txt  
```bash
pip3 install -r requirements.txt
```
Required packages:
- `anthropic==0.49.0` - Anthropic Claude API client
- `mcp==1.9.4` - Model Context Protocol library
- `python-dotenv==1.1.0` - Environment variable loading
- `requests==2.32.3` - HTTP requests library
- `certifi==2025.1.31` - Certificate validation
- `urllib3==2.4.0` - HTTP client library

## Architecture

This toolkit demonstrates various MCP transport patterns:
- **stdio transport:** Direct process communication (helloserver.go, servermain.go)
- **HTTP transport:** Web-based MCP servers (hellotest.go, remoteserver.go)  
- **Proxy patterns:** Protocol bridges for transport conversion (proxy.go, proxy1.go)
- **Client libraries:** Both Go and Python implementations
- **Health checking:** HTTP connectivity testing (direct.py)

The `proxy.go` serves as a key component, enabling stdio-based MCP clients to communicate with HTTP-based MCP servers seamlessly.

## Testing Status

All programs in this directory have been tested and verified:
- **Go Programs:** 100% working (7/7)
- **Python Programs:** 100% working (3/3)  
- **JavaScript Programs:** 100% working (1/1)
- **Overall Success Rate:** 100% (11/11 programs work correctly)

Each program includes example usage and expected output for easy verification.
