# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
"""
MCP Client - Client for testing the MCP server
"""
import json
import subprocess
import sys

class MCPClient:
    """Simple MCP client for testing"""
    
    def __init__(self, server_command: str):
        self.process = subprocess.Popen(
            server_command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    
    def send_request(self, method: str, params: dict = None) -> dict:
        """Send request to MCP server"""
        request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': method,
            'params': params or {}
        }
        
        request_json = json.dumps(request) + '\n'
        self.process.stdin.write(request_json)
        self.process.stdin.flush()
        
        response_line = self.process.stdout.readline()
        return json.loads(response_line)
    
    def close(self):
        """Close the client"""
        self.process.terminate()
        self.process.wait()

def test_mcp_server():
    """Test the MCP server"""
    print("=" * 60)
    print("Testing SECS MCP Server")
    print("=" * 60)
    
    # Start server
    client = MCPClient("python mcp/server.py")
    
    try:
        # Test 1: List tools
        print("\n1. Listing tools...")
        response = client.send_request('tools/list')
        print(f"Found {len(response.get('tools', []))} tools")
        for tool in response.get('tools', []):
            print(f"  - {tool['name']}: {tool['description']}")
        
        # Test 2: Get stats
        print("\n2. Getting stats...")
        response = client.send_request('tools/call', {
            'name': 'get_stats',
            'arguments': {}
        })
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # Test 3: Search documents
        print("\n3. Searching documents...")
        response = client.send_request('tools/call', {
            'name': 'search_documents',
            'arguments': {
                'query': 'pauta reunião',
                'limit': 3
            }
        })
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # Test 4: List resources
        print("\n4. Listing resources...")
        response = client.send_request('resources/list')
        print(f"Found {len(response.get('resources', []))} resources")
        for resource in response.get('resources', []):
            print(f"  - {resource['uri']}: {resource['name']}")
        
        # Test 5: Read resource
        print("\n5. Reading resource (stats)...")
        response = client.send_request('resources/read', {
            'uri': 'secs://stats'
        })
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)
        
    finally:
        client.close()

if __name__ == '__main__':
    test_mcp_server()
