# shorttest.py
# Created: 2025-06-22

import asyncio
import sys
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def minimal_test():
    """Minimal test to see exactly what's happening"""
    
    print("🔌 Connecting...")
    
    try:
        # Connect
        streams_context = streamablehttp_client(url="http://localhost:8080/mcp", headers={})
        read_stream, write_stream, _ = await streams_context.__aenter__()
        
        session_context = ClientSession(read_stream, write_stream)
        session = await session_context.__aenter__()
        
        # Initialize
        print("🔄 Initializing...")
        init_result = await session.initialize()
        print(f"✅ Server: {init_result.serverInfo.name}")
        
        # List tools with detailed output
        print("\n🔍 Listing tools...")
        
        # Capture any print statements
        import io
        from contextlib import redirect_stdout, redirect_stderr
        
        f_out = io.StringIO()
        f_err = io.StringIO()
        
        with redirect_stdout(f_out), redirect_stderr(f_err):
            tools_response = await session.list_tools()
        
        # Show any captured output
        stdout_content = f_out.getvalue()
        stderr_content = f_err.getvalue()
        
        if stdout_content:
            print(f"📝 Captured stdout: {repr(stdout_content)}")
        if stderr_content:
            print(f"📝 Captured stderr: {repr(stderr_content)}")
        
        # Show the actual response
        print(f"📋 Response type: {type(tools_response)}")
        print(f"📋 Response: {tools_response}")
        
        if hasattr(tools_response, 'tools'):
            tools = tools_response.tools
            print(f"🔧 Tools count: {len(tools)}")
            
            for i, tool in enumerate(tools):
                print(f"\nTool {i+1}:")
                print(f"  Name: {tool.name}")
                print(f"  Description: {tool.description}")
                print(f"  Schema: {getattr(tool, 'inputSchema', 'No schema')}")
        else:
            print("❌ No tools attribute found")
            print(f"📋 Available attributes: {dir(tools_response)}")
        
        # Test direct tool call
        print("\n🧪 Testing direct tool call...")
        try:
            result = await session.call_tool("remote_address_lookup", {"zip_code": "10001"})
            print(f"✅ Tool call succeeded!")
            print(f"📋 Result type: {type(result)}")
            print(f"📋 Result: {result}")
            
            if hasattr(result, 'content'):
                print(f"📋 Content: {result.content}")
                if isinstance(result.content, list):
                    for item in result.content:
                        print(f"  Item: {item}")
                        if hasattr(item, 'text'):
                            print(f"  Text: {item.text}")
        except Exception as e:
            print(f"❌ Tool call failed: {e}")
        
        # Cleanup
        await session_context.__aexit__(None, None, None)
        await streams_context.__aexit__(None, None, None)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(minimal_test())
