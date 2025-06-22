# antropicmcpremote.py
# Created: 2025-06-22

import asyncio
import argparse
from typing import Optional, List, Dict, Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class WorkingRemoteMCPClient:
    """Working MCP Client for remote address lookup server"""

    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.anthropic = Anthropic()
        self.server_info = None
        self.available_tools = []

    async def connect_to_server(self, server_url: str):
        """Connect to remote MCP server and initialize"""
        print(f"🔌 Connecting to remote server at {server_url}")
        
        try:
            self._streams_context = streamablehttp_client(url=server_url, headers={})
            read_stream, write_stream, _ = await self._streams_context.__aenter__()

            self._session_context = ClientSession(read_stream, write_stream)
            self.session = await self._session_context.__aenter__()

            # Initialize the session
            init_result = await self.session.initialize()
            self.server_info = init_result
            
            print("✅ Connected and initialized successfully")
            print(f"📋 Server: {init_result.serverInfo.name} v{init_result.serverInfo.version}")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    async def discover_tools(self) -> List[Any]:
        """Discover available tools from the server"""
        if not self.session:
            print("❌ Not connected to server")
            return []
        
        try:
            print("\n🔍 Discovering available tools...")
            response = await self.session.list_tools()
            self.available_tools = response.tools
            
            if not self.available_tools:
                print("❌ No tools available")
                return []
            
            print(f"🔧 Found {len(self.available_tools)} tools:")
            for i, tool in enumerate(self.available_tools, 1):
                print(f"  {i}. {tool.name}")
                print(f"     Description: {tool.description}")
                
                # Show input schema
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    schema = tool.inputSchema
                    if 'properties' in schema:
                        params = list(schema['properties'].keys())
                        print(f"     Parameters: {params}")
                        
                        # Show required parameters
                        if 'required' in schema:
                            print(f"     Required: {schema['required']}")
                print()
            
            return self.available_tools
            
        except Exception as e:
            print(f"❌ Error discovering tools: {e}")
            return []

    async def test_address_lookup(self, zip_code: str = "10001"):
        """Test the remote_address_lookup tool directly"""
        if not self.session:
            print("❌ Not connected to server")
            return None
        
        try:
            print(f"🧪 Testing remote_address_lookup with zip code {zip_code}")
            
            # Use the correct tool name from curl test: remote_address_lookup
            result = await self.session.call_tool("remote_address_lookup", {"zip_code": zip_code})
            
            # Extract content from result
            content = ""
            if hasattr(result, 'content'):
                if isinstance(result.content, list):
                    for item in result.content:
                        if hasattr(item, 'text'):
                            content += item.text
                        else:
                            content += str(item)
                else:
                    content = str(result.content)
            else:
                content = str(result)
            
            print(f"✅ Address lookup result: {content}")
            return content
                
        except Exception as e:
            print(f"❌ Address lookup test failed: {e}")
            return None

    async def run_sample_tests(self):
        """Run sample address lookups"""
        print("\n🧪 Running sample address lookups...")
        
        test_zip_codes = ["10001", "90210", "94102", "60601"]
        
        for zip_code in test_zip_codes:
            result = await self.test_address_lookup(zip_code)
            if result:
                print(f"  📍 {zip_code}: {result}")
            await asyncio.sleep(0.5)  # Be nice to the server

    async def chat_with_claude(self, user_message: str) -> str:
        """Use Claude to interact with the remote address lookup tool"""
        if not self.session or not self.available_tools:
            return "❌ Not connected or no tools available"
        
        try:
            # Prepare tools for Claude
            claude_tools = []
            for tool in self.available_tools:
                claude_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                })
            
            # Start conversation
            messages = [{"role": "user", "content": user_message}]
            
            print(f"🤖 Claude is thinking...")
            
            # Call Claude
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=messages,
                tools=claude_tools,
            )

            # Handle tool use
            iteration = 0
            max_iterations = 5
            
            while response.stop_reason == "tool_use" and iteration < max_iterations:
                iteration += 1
                print(f"🔄 Tool use iteration {iteration}")
                
                # Add Claude's response to conversation
                messages.append({
                    "role": "assistant",
                    "content": response.content,
                })

                # Process each tool use
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_args = content_block.input
                        tool_id = content_block.id

                        print(f"🔧 Claude calling: {tool_name}")
                        print(f"📝 Arguments: {tool_args}")

                        try:
                            # Call the remote tool
                            tool_result = await self.session.call_tool(tool_name, tool_args)
                            
                            # Extract result content
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
                            
                            print(f"✅ Result: {result_content}")
                            
                            # Add tool result to conversation
                            messages.append({
                                "role": "user",
                                "content": [{
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": result_content,
                                }]
                            })
                            
                        except Exception as e:
                            error_msg = f"Error calling {tool_name}: {str(e)}"
                            print(f"❌ {error_msg}")
                            
                            # Add error to conversation
                            messages.append({
                                "role": "user",
                                "content": [{
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": error_msg,
                                    "is_error": True,
                                }]
                            })

                # Continue conversation with Claude
                response = self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1500,
                    messages=messages,
                    tools=claude_tools,
                )

            # Extract final text response
            final_response = ""
            for content_block in response.content:
                if content_block.type == "text":
                    final_response += content_block.text

            return final_response

        except Exception as e:
            return f"❌ Error in Claude conversation: {str(e)}"

    async def interactive_chat(self):
        """Run interactive chat session"""
        print("\n💬 Interactive Chat Mode")
        print("Ask Claude to look up addresses by zip code!")
        print("Type 'quit' to exit\n")

        sample_queries = [
            "What tools do you have available?",
            "Look up the address for zip code 10001",
            "Can you find addresses for zip codes 90210 and 94102?",
            "What's the address for Beverly Hills zip code 90210?",
            "Look up multiple zip codes: 10001, 60601, and 30301"
        ]
        
        print("💡 Sample queries you can try:")
        for i, query in enumerate(sample_queries, 1):
            print(f"  {i}. {query}")
        print()

        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                response = await self.chat_with_claude(user_input)
                print(f"🤖 Claude: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}\n")

    async def cleanup(self):
        """Clean up connections"""
        try:
            if hasattr(self, "_session_context"):
                await self._session_context.__aexit__(None, None, None)
            if hasattr(self, "_streams_context"):
                await self._streams_context.__aexit__(None, None, None)
            print("🧹 Connections cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

async def main():
    parser = argparse.ArgumentParser(description="Working Remote Address Lookup MCP Client")
    parser.add_argument(
        "--server-url",
        default="http://localhost:8080/mcp",
        help="Remote MCP server URL"
    )
    parser.add_argument(
        "--quick-test",
        help="Run a single quick test query"
    )
    
    args = parser.parse_args()

    client = WorkingRemoteMCPClient()
    
    try:
        print("🚀 Starting Remote Address Lookup Client")
        print("="*50)
        
        # Connect to server
        if not await client.connect_to_server(args.server_url):
            return
        
        # Discover tools
        tools = await client.discover_tools()
        if not tools:
            print("❌ No tools found, cannot proceed")
            return
        
        # Run sample tests
        await client.run_sample_tests()
        
        if args.quick_test:
            # Quick test mode
            print(f"\n⚡ Quick test: {args.quick_test}")
            result = await client.chat_with_claude(args.quick_test)
            print(f"🤖 Claude: {result}")
        else:
            # Interactive mode
            await client.interactive_chat()
        
        print("\n✅ Session completed successfully")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
