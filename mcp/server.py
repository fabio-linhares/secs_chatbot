# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
"""
MCP Server - Model Context Protocol server for SECS documents
"""
import json
import sys
from typing import Any, Dict
from mcp.tools import SECSTools

class MCPServer:
    """
    MCP Server for SECS document access.
    
    Provides tools and resources for accessing SECS documents
    through the Model Context Protocol.
    """
    
    def __init__(self):
        self.tools = SECSTools()
        self.version = "1.0.0"
        self.name = "secs-mcp-server"
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MCP request.
        
        Args:
            request: MCP request dictionary
            
        Returns:
            MCP response dictionary
        """
        method = request.get('method')
        params = request.get('params', {})
        
        if method == 'tools/list':
            return self._list_tools()
        elif method == 'tools/call':
            return self._call_tool(params)
        elif method == 'resources/list':
            return self._list_resources()
        elif method == 'resources/read':
            return self._read_resource(params)
        else:
            return {
                'error': {
                    'code': -32601,
                    'message': f'Method not found: {method}'
                }
            }
    
    def _list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        return {
            'tools': [
                {
                    'name': 'search_documents',
                    'description': 'Search for documents using semantic search',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'query': {
                                'type': 'string',
                                'description': 'Search query'
                            },
                            'document_type': {
                                'type': 'string',
                                'enum': ['ata', 'pauta', 'resolucao', 'regimento'],
                                'description': 'Filter by document type'
                            },
                            'limit': {
                                'type': 'integer',
                                'default': 5,
                                'description': 'Maximum number of results'
                            }
                        },
                        'required': ['query']
                    }
                },
                {
                    'name': 'get_ata',
                    'description': 'Get specific ata or list all atas',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'numero': {
                                'type': 'string',
                                'description': 'Ata number (e.g., "01/2024")'
                            }
                        }
                    }
                },
                {
                    'name': 'get_resolucao',
                    'description': 'Get specific resolução or list all resoluções',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'numero': {
                                'type': 'string',
                                'description': 'Resolução number (e.g., "024/2024")'
                            }
                        }
                    }
                },
                {
                    'name': 'list_pautas',
                    'description': 'List all available pautas',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {}
                    }
                },
                {
                    'name': 'get_stats',
                    'description': 'Get database statistics',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {}
                    }
                }
            ]
        }
    
    def _call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool"""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        try:
            if tool_name == 'search_documents':
                result = self.tools.search_documents(**arguments)
            elif tool_name == 'get_ata':
                result = self.tools.get_ata(**arguments)
            elif tool_name == 'get_resolucao':
                result = self.tools.get_resolucao(**arguments)
            elif tool_name == 'list_pautas':
                result = self.tools.list_pautas()
            elif tool_name == 'get_stats':
                result = self.tools.get_stats()
            else:
                return {
                    'error': {
                        'code': -32602,
                        'message': f'Unknown tool: {tool_name}'
                    }
                }
            
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': json.dumps(result, indent=2, ensure_ascii=False)
                    }
                ]
            }
        except Exception as e:
            return {
                'error': {
                    'code': -32603,
                    'message': f'Tool execution error: {str(e)}'
                }
            }
    
    def _list_resources(self) -> Dict[str, Any]:
        """List available resources"""
        return {
            'resources': [
                {
                    'uri': 'secs://atas',
                    'name': 'Atas do CONSUNI',
                    'description': 'Atas de reuniões do Conselho Universitário',
                    'mimeType': 'application/json'
                },
                {
                    'uri': 'secs://resolucoes',
                    'name': 'Resoluções do CONSUNI',
                    'description': 'Resoluções aprovadas pelo Conselho',
                    'mimeType': 'application/json'
                },
                {
                    'uri': 'secs://pautas',
                    'name': 'Pautas de Reuniões',
                    'description': 'Pautas de reuniões do CONSUNI',
                    'mimeType': 'application/json'
                },
                {
                    'uri': 'secs://stats',
                    'name': 'Estatísticas',
                    'description': 'Estatísticas da base de documentos',
                    'mimeType': 'application/json'
                }
            ]
        }
    
    def _read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a resource"""
        uri = params.get('uri')
        
        try:
            if uri == 'secs://atas':
                result = self.tools.get_ata()
            elif uri == 'secs://resolucoes':
                result = self.tools.get_resolucao()
            elif uri == 'secs://pautas':
                result = self.tools.list_pautas()
            elif uri == 'secs://stats':
                result = self.tools.get_stats()
            else:
                return {
                    'error': {
                        'code': -32602,
                        'message': f'Unknown resource: {uri}'
                    }
                }
            
            return {
                'contents': [
                    {
                        'uri': uri,
                        'mimeType': 'application/json',
                        'text': json.dumps(result, indent=2, ensure_ascii=False)
                    }
                ]
            }
        except Exception as e:
            return {
                'error': {
                    'code': -32603,
                    'message': f'Resource read error: {str(e)}'
                }
            }
    
    def run(self):
        """Run the MCP server (stdio mode)"""
        print(f"Starting {self.name} v{self.version}", file=sys.stderr)
        
        for line in sys.stdin:
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
            except json.JSONDecodeError as e:
                error_response = {
                    'error': {
                        'code': -32700,
                        'message': f'Parse error: {str(e)}'
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
            except Exception as e:
                error_response = {
                    'error': {
                        'code': -32603,
                        'message': f'Internal error: {str(e)}'
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()

if __name__ == '__main__':
    server = MCPServer()
    server.run()
