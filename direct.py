# direct.py
# Created: 2025-06-22

import requests
import json

def test_remote_server_health():
    """Test if remote MCP server is accessible"""
    
    base_url = "http://localhost:8080"
    mcp_url = "http://localhost:8080/mcp"
    
    print("🔍 Testing remote MCP server connectivity...")
    
    # Test base URL
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✅ Base URL accessible: {response.status_code}")
    except Exception as e:
        print(f"❌ Base URL failed: {e}")
    
    # Test MCP endpoint with initialize
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    
    try:
        response = requests.post(
            mcp_url,
            json=mcp_request,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"✅ MCP endpoint accessible: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"📋 Server info: {json.dumps(result, indent=2)}")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ MCP endpoint failed: {e}")

if __name__ == "__main__":
    test_remote_server_health()
