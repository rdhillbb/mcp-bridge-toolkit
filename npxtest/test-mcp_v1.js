#!/usr/bin/env node

const http = require('http');

const MCP_URL = 'http://localhost:8080/mcp';

function sendMCPRequest(method, params = {}, id = null) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify({
      jsonrpc: '2.0',
      method,
      ...(Object.keys(params).length > 0 && { params }),
      ...(id !== null && { id })
    });

    const options = {
      hostname: 'localhost',
      port: 8080,
      path: '/mcp',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      }
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(new Error(`Invalid JSON response: ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.setTimeout(5000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    req.write(payload);
    req.end();
  });
}

async function testMCPServer() {
  console.log('🧪 Testing MCP Server at http://localhost:8080/mcp\n');

  // Test basic endpoints first
  const basicTests = [
    {
      name: 'Initialize',
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: { name: 'test-client', version: '1.0.0' }
      },
      id: 1
    },
    {
      name: 'List Tools',
      method: 'tools/list',
      params: {},
      id: 2
    },
    {
      name: 'List Resources',
      method: 'resources/list',
      params: {},
      id: 3
    }
  ];

  // Test problematic endpoints separately
  const problematicTests = [
    {
      name: 'List Prompts',
      method: 'prompts/list',
      params: {},
      id: 4
    },
    {
      name: 'Notifications/Initialized',
      method: 'notifications/initialized',
      params: {},
      id: null // notifications don't have IDs
    }
  ];

  const tests = [...basicTests, ...problematicTests];

  for (const test of tests) {
    try {
      console.log(`📤 ${test.name}:`);
      console.log(`   Request: ${JSON.stringify({
        jsonrpc: '2.0',
        method: test.method,
        ...(Object.keys(test.params).length > 0 && { params: test.params }),
        ...(test.id !== null && { id: test.id })
      })}`);

      const start = Date.now();
      const result = await sendMCPRequest(test.method, test.params, test.id);
      const duration = Date.now() - start;

      console.log(`📥 Response (${duration}ms):`, JSON.stringify(result, null, 2));
      console.log('✅ Success\n');
    } catch (error) {
      console.log(`❌ Error: ${error.message}\n`);
    }
  }

  // Test the specific tool call based on your log
  try {
    console.log('📤 Testing remote_address_lookup tool:');
    const toolCall = {
      jsonrpc: '2.0',
      method: 'tools/call',
      params: {
        name: 'remote_address_lookup',
        arguments: { zip_code: '90210' }
      },
      id: 5
    };
    
    console.log(`   Request: ${JSON.stringify(toolCall)}`);
    const result = await sendMCPRequest('tools/call', toolCall.params, 5);
    console.log('📥 Response:', JSON.stringify(result, null, 2));
    console.log('✅ Success\n');
  } catch (error) {
    console.log(`❌ Tool call error: ${error.message}\n`);
  }
}

testMCPServer().catch(console.error);
