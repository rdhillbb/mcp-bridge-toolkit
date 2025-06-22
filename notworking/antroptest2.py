# antroptest2.py
# Created: 2025-06-22

import asyncio
import argparse
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class RemoteMCPClient:
    """MCP Client for your remote server (bypassing Go proxy)"""

    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()

    async def connect_to_remote_server(self, server_url: str):
        """Connect directly to your remote MCP server"""
        print(f"🔌 Connecting to remote MCP server at {server_url}")
        
        self._streams_context = streamablehttp_client(
            url=server_url,
            headers={},
        )
        read_stream, write_stream, _ = await self._streams_context.__aenter__()

        self._session_context = ClientSession(read_stream, write_stream)
        self.session: ClientSession = await self._session_context.__aenter__()

        await self.session.initialize()
        print("✅ Connected to remote MCP server")

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and remote MCP tools"""
        if not self.session:
            return "❌ Not connected to remote MCP server."
        
        try:
            # Format messages for Claude
            messages = [{"role": "user", "content": query}]

            # Get available tools from remote MCP server
            response = await self.session.list_tools()
            available_tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in response.tools
            ]
            
            print("🔧 Available tools from remote server:")
            for tool in response.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Initial Claude API call
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=messages,
                tools=available_tools,
            )

            # Handle tool use (following skeleton pattern)
            while response.stop_reason == "tool_use":
                # Add assistant message with tool use
                messages.append({
                    "role": "assistant",
                    "content": response.content,
                })

                # Process each tool use
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_args = content_block.input

                        print(f"🔧 Calling remote tool: {tool_name} with args: {tool_args}")

                        try:
                            # Call the tool via remote MCP server
                            tool_result = await self.session.call_tool(tool_name, tool_args)
                            
                            # Extract the actual content from the tool result
                            result_content = ""
                            if hasattr(tool_result, 'content'):
                                if isinstance(tool_result.content, list):
                                    for content in tool_result.content:
                                        if hasattr(content, 'text'):
                                            result_content += content.text
                                        else:
                                            result_content += str(content)
                                else:
                                    result_content = str(tool_result.content)
                            else:
                                result_content = str(tool_result)
                            
                            print(f"📋 Remote tool result: {result_content}")
                            
                            # Add tool result to messages
                            messages.append({
                                "role": "user",
                                "content": [{
                                    "type": "tool_result",
                                    "tool_use_id": content_block.id,
                                    "content": result_content,
                                }]
                            })
                        except Exception as e:
                            # Add error result
                            messages.append({
                                "role": "user",
                                "content": [{
                                    "type": "tool_result",
                                    "tool_use_id": content_block.id,
                                    "content": f"Error calling remote tool: {str(e)}",
                                    "is_error": True,
                                }]
                            })

                # Continue conversation with Claude
                response = self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=messages,
                    tools=available_tools,
                )

            # Extract final response text
            result = ""
            for content_block in response.content:
                if content_block.type == "text":
                    result += content_block.text

            return result

        except Exception as e:
            return f"❌ Error processing query: {str(e)}"

    async def test_remote_tools(self):
        """Test available tools from remote server"""
        if not self.session:
            print("❌ Not connected to remote server")
            return
        
        try:
            # List available tools
            response = await self.session.list_tools()
            print(f"🔧 Available tools from remote server:")
            for tool in response.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Test a tool directly
            if response.tools:
                tool = response.tools[0]
                print(f"\n🧪 Testing tool: {tool.name}")
                
                # Example: test zipcode tool if available
                if tool.name == "zipcode":
                    result = await self.session.call_tool("zipcode", {"zip_code": "10001"})
                    print(f"📋 Tool result: {result}")
                
        except Exception as e:
            print(f"❌ Error testing remote tools: {e}")

    async def chat_loop(self):
        """Run an interactive chat loop with remote MCP server"""
        print("\n🤖 Remote MCP Client with Claude Integration")
        print("Claude will use tools from your remote MCP server.")
        print("Type 'quit' to exit.\n")

        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Process query through Claude with remote MCP tools
                response = await self.process_query(user_input)
                print(f"Claude: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}\n")

    async def cleanup(self):
        """Clean up resources and close connections"""
        try:
            if hasattr(self, "_session_context"):
                await self._session_context.__aexit__(None, None, None)
                print("🧹 Session closed")
            
            if hasattr(self, "_streams_context"):
                await self._streams_context.__aexit__(None, None, None)
                print("🧹 Streams closed")
            
        except Exception as e:
            print(f"⚠️  Cleanup warning: {str(e)}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

async def main():
    """Main function to run the remote MCP client"""
    parser = argparse.ArgumentParser(description="Remote MCP Client via Anthropic")
    parser.add_argument(
        "--server-url",
        default="http://localhost:8080/mcp",  # Your remote server
        help="Remote MCP server URL"
    )
    parser.add_argument(
        "--test-query",
        help="Single query to test (skips interactive mode)"
    )
    
    args = parser.parse_args()

    # Create and use the client
    async with RemoteMCPClient() as client:
        try:
            # Connect to remote server
            await client.connect_to_remote_server(args.server_url)
            
            # Test remote tools
            await client.test_remote_tools()
            
            if args.test_query:
                # Single query mode
                print(f"\n🔍 Testing query: {args.test_query}")
                response = await client.process_query(args.test_query)
                print(f"Claude: {response}")
            else:
                # Interactive chat mode
                await client.chat_loop()
                
        except Exception as e:
            print(f"❌ Failed to connect to remote server: {e}")
            print("\nTroubleshooting:")
            print("1. Is your remote MCP server running at localhost:8080?")
            print("2. Can you access http://localhost:8080/mcp directly?")
            print("3. Check firewall/network settings")

if __name__ == "__main__":
    asyncio.run(main())
