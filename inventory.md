# File Inventory

## Go Files

**Name:** go.mod  
**Type:** Go Module Configuration  
**Description:** Defines the Go module for a Model Context Protocol (MCP) server with dependencies for mcp-golang SDK and related libraries.

**Name:** helloserver.go  
**Type:** Go MCP Server (stdio)  
**Description:** Basic MCP server using stdio transport that registers "hello" tool, prompt test, and resource endpoints for testing MCP functionality.

**Name:** proxy.go  
**Type:** Go HTTP Proxy Server (Fixed)  
**Description:** Fully functional MCP stdio ↔ HTTP bridge that works like 'supergateway'. Forwards JSON-RPC messages from stdin to HTTP MCP servers, with comprehensive logging. Successfully tested with remoteserver.go for initialize, tool calls, and bidirectional communication.

**Name:** proxy1.go  
**Type:** Go HTTP Proxy Server (Simple)  
**Description:** Simplified version of the MCP proxy that forwards JSON-RPC messages between stdin/stdout and a remote HTTP MCP server.

**Name:** remoteserver.go  
**Type:** Go MCP HTTP Server (Tested)  
**Description:** Remote MCP server with HTTP transport on port 8080/mcp that provides "remote_address_lookup" and "time" tools. Successfully tested with proxy.go for full MCP protocol compatibility including initialize handshake and tool execution.

**Name:** helloclienttest.go  
**Type:** Go MCP Client  
**Description:** HTTP client that connects to an MCP server to test tool listing and calling the "time" tool with different format parameters.

**Name:** hellotest.go  
**Type:** Go MCP HTTP Server (Test)  
**Description:** Simple HTTP MCP server on port 8080 that provides a "time" tool for returning formatted current time.

**Name:** servermain.go  
**Type:** Go MCP Server (stdio)  
**Description:** Basic stdio MCP server that implements a "zipcode" tool for returning fake addresses based on zip code input.

## Python Files

**Name:** main.py  
**Type:** Python Entry Point  
**Description:** Simple Python script that prints a hello message for the mcph-dev-to-eminetto project.

**Name:** anthroptestmcp.py  
**Type:** Python Anthropic MCP Client  
**Description:** Tests Anthropic's MCP connector by configuring remote MCP servers and making requests to Claude with MCP tool access.

**Name:** direct.py  
**Type:** Python MCP Health Check  
**Description:** Health check script that tests connectivity to a remote MCP server by making HTTP requests to both base URL and MCP endpoint.

**Name:** antroptest2.py  
**Type:** Python Async MCP Client  
**Description:** Full-featured async MCP client that connects directly to remote servers, lists tools, and integrates with Claude for interactive chat sessions.

**Name:** antropicmcpremote.py  
**Type:** Python Advanced MCP Client  
**Description:** Comprehensive async MCP client with tool discovery, direct tool testing, Claude integration, and interactive chat capabilities.

**Name:** shorttest.py  
**Type:** Python Minimal MCP Test  
**Description:** Minimal test script for debugging MCP connections, tool listing, and direct tool calls with detailed output capture.

## JavaScript Files

**Name:** npxtest/test-mcp.js  
**Type:** Node.js MCP Test Client  
**Description:** Node.js script that tests MCP server endpoints by sending JSON-RPC requests including initialize, list tools, and tool calls.

## Configuration Files

**Name:** pyproject.toml  
**Type:** Python Project Configuration  
**Description:** Python project metadata file defining project name, version, and Python version requirements.

**Name:** test_request.json  
**Type:** JSON Test Data  
**Description:** Simple JSON-RPC request payload for testing the tools/list method.

## Documentation Files

**Name:** README.md  
**Type:** Documentation  
**Description:** Empty documentation file for the project.

**Name:** .gitignore  
**Type:** Git Configuration  
**Description:** Git ignore patterns file.

**Name:** .python-version  
**Type:** Python Version File  
**Description:** Specifies the Python version for the project.

## Compiled Binaries

**Name:** helloclienttest  
**Type:** Compiled Go Binary  
**Description:** Compiled executable of helloclienttest.go

**Name:** helloserver  
**Type:** Compiled Go Binary  
**Description:** Compiled executable of helloserver.go

**Name:** hellotest  
**Type:** Compiled Go Binary  
**Description:** Compiled executable of hellotest.go

**Name:** proxy  
**Type:** Compiled Go Binary (Working)  
**Description:** Compiled executable of proxy.go - fully functional MCP stdio/HTTP bridge. Usage: `./proxy <target-url>` - replaces `npx -y supergateway --streamableHttp` functionality.

**Name:** remoteserver  
**Type:** Compiled Go Binary (Tested)  
**Description:** Compiled executable of remoteserver.go - HTTP MCP server verified working with proxy.go for complete MCP communication testing.

**Name:** servermain  
**Type:** Compiled Go Binary  
**Description:** Compiled executable of servermain.go

## Other Files

**Name:** go.sum  
**Type:** Go Dependencies Checksum  
**Description:** Go module dependency checksums for ensuring integrity of downloaded modules.

**Name:** remoteserver.go.org  
**Type:** Backup/Original File  
**Description:** Original or backup version of remoteserver.go file.