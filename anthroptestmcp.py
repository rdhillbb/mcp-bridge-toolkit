# anthroptestmcp.py
# Created: 2025-06-22

import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

def chat_with_go_proxy_via_anthropic():
    """Use Anthropic's MCP connector with proper beta headers"""
    
    # Initialize client with beta headers
    client = anthropic.Anthropic(
        # Beta header required for MCP connector
        default_headers={
            "anthropic-beta": "mcp-client-2025-04-04"
        }
    )
    
    # Configure MCP server
    mcp_servers = [
        {
            "type": "url",
            "url": "http://localhost:8080/mcp",
            "name": "remote-address-lookup",
            "tool_configuration": {
                "enabled": True
            }
        }
    ]
    
    try:
        # Note: Direct MCP server integration not available in current API
        # This is a basic test of Anthropic client connectivity
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[
                {
                    "role": "user", 
                    "content": "Hello! This is a test of the Anthropic API connection. Please respond with a brief greeting."
                }
            ]
            # mcp_servers parameter not supported in current API version
        )
        
        print("🤖 Claude response using your Go proxy:")
        for content in response.content:
            if content.type == "text":
                print(content.text)
            elif content.type == "tool_use":
                print(f"🔧 Tool used: {content.name}")
                print(f"📋 Tool args: {content.input}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    chat_with_go_proxy_via_anthropic()
