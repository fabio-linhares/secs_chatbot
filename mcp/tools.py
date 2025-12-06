# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
"""
MCP Tools - Tools available through the MCP server
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any, Optional
from src.services.vector_store import get_vector_store
import sqlite3
from src.config import config

class SECSTools:
    """Tools for SECS document access via MCP"""
    
    def __init__(self):
        self.vector_store = get_vector_store()
        self.db_path = config.DB_PATH
    
    def search_documents(
        self,
        query: str,
        document_type: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Search for documents using semantic search.
        
        Args:
            query: Search query
            document_type: Filter by type (ata, pauta, resolucao, regimento)
            limit: Maximum number of results
            
        Returns:
            Dictionary with search results
        """
        try:
            if document_type:
                results = self.vector_store.search_with_filter(
                    query,
                    {'tipo': document_type},
                    k=limit
                )
            else:
                results = self.vector_store.search(query, k=limit)
            
            return {
                'success': True,
                'query': query,
                'num_results': len(results),
                'results': [
                    {
                        'titulo': r['titulo'],
                        'tipo': r['tipo'],
                        'numero': r.get('numero'),
                        'data': r.get('data'),
                        'conteudo': r['conteudo'][:500],
                        'similarity': r['similarity']
                    }
                    for r in results
                ]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_ata(self, numero: str = None) -> Dict[str, Any]:
        """
        Get specific ata or list all atas.
        
        Args:
            numero: Ata number (e.g., "01/2024", "02/2024")
            
        Returns:
            Ata content or list of atas
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                
                if numero:
                    # Get specific ata
                    cur.execute("""
                        SELECT titulo, tipo, numero, data, hash
                        FROM documentos
                        WHERE tipo = 'ata' AND (titulo LIKE ? OR numero LIKE ?)
                    """, (f'%{numero}%', f'%{numero}%'))
                    
                    row = cur.fetchone()
                    if not row:
                        return {
                            'success': False,
                            'error': f'Ata {numero} não encontrada'
                        }
                    
                    # Get chunks
                    cur.execute("""
                        SELECT conteudo, posicao
                        FROM chunks
                        WHERE documento_id = (
                            SELECT id FROM documentos WHERE hash = ?
                        )
                        ORDER BY posicao
                    """, (row[4],))
                    
                    chunks = cur.fetchall()
                    content = '\n\n'.join([c[0] for c in chunks])
                    
                    return {
                        'success': True,
                        'titulo': row[0],
                        'tipo': row[1],
                        'numero': row[2],
                        'data': row[3],
                        'conteudo': content
                    }
                else:
                    # List all atas
                    cur.execute("""
                        SELECT titulo, numero, data
                        FROM documentos
                        WHERE tipo = 'ata'
                        ORDER BY data DESC
                    """)
                    
                    atas = cur.fetchall()
                    return {
                        'success': True,
                        'num_atas': len(atas),
                        'atas': [
                            {
                                'titulo': a[0],
                                'numero': a[1],
                                'data': a[2]
                            }
                            for a in atas
                        ]
                    }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_resolucao(self, numero: str = None) -> Dict[str, Any]:
        """
        Get specific resolução or list all resoluções.
        
        Args:
            numero: Resolução number (e.g., "024/2024")
            
        Returns:
            Resolução content or list
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                
                if numero:
                    # Get specific resolução
                    cur.execute("""
                        SELECT titulo, tipo, numero, data, hash
                        FROM documentos
                        WHERE tipo = 'resolucao' AND (titulo LIKE ? OR numero LIKE ?)
                    """, (f'%{numero}%', f'%{numero}%'))
                    
                    row = cur.fetchone()
                    if not row:
                        return {
                            'success': False,
                            'error': f'Resolução {numero} não encontrada'
                        }
                    
                    # Get chunks
                    cur.execute("""
                        SELECT conteudo, posicao
                        FROM chunks
                        WHERE documento_id = (
                            SELECT id FROM documentos WHERE hash = ?
                        )
                        ORDER BY posicao
                    """, (row[4],))
                    
                    chunks = cur.fetchall()
                    content = '\n\n'.join([c[0] for c in chunks])
                    
                    return {
                        'success': True,
                        'titulo': row[0],
                        'tipo': row[1],
                        'numero': row[2],
                        'data': row[3],
                        'conteudo': content
                    }
                else:
                    # List all resoluções
                    cur.execute("""
                        SELECT titulo, numero, data
                        FROM documentos
                        WHERE tipo = 'resolucao'
                        ORDER BY numero DESC
                    """)
                    
                    resolucoes = cur.fetchall()
                    return {
                        'success': True,
                        'num_resolucoes': len(resolucoes),
                        'resolucoes': [
                            {
                                'titulo': r[0],
                                'numero': r[1],
                                'data': r[2]
                            }
                            for r in resolucoes
                        ]
                    }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_pautas(self) -> Dict[str, Any]:
        """
        List all available pautas.
        
        Returns:
            List of pautas
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                
                cur.execute("""
                    SELECT titulo, numero, data
                    FROM documentos
                    WHERE tipo = 'pauta'
                    ORDER BY data DESC
                """)
                
                pautas = cur.fetchall()
                return {
                    'success': True,
                    'num_pautas': len(pautas),
                    'pautas': [
                        {
                            'titulo': p[0],
                            'numero': p[1],
                            'data': p[2]
                        }
                        for p in pautas
                    ]
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Statistics about documents and chunks
        """
        try:
            stats = self.vector_store.get_stats()
            return {
                'success': True,
                **stats
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
