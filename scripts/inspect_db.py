#!/usr/bin/env python
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
"""
Simple database inspection script
"""
import sqlite3
import sys

db_path = "data/app.db"

try:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    print("=" * 60)
    print("Database Inspection")
    print("=" * 60)
    
    # List all documents
    print("\n📚 DOCUMENTOS:")
    cur.execute("SELECT id, tipo, titulo, numero FROM documentos")
    for row in cur.fetchall():
        print(f"  {row[0]}. [{row[1]}] {row[2]} (nº {row[3]})")
    
    # Count chunks per document
    print("\n📄 CHUNKS POR DOCUMENTO:")
    cur.execute("""
        SELECT d.titulo, d.tipo, COUNT(c.id) as num_chunks
        FROM documentos d
        LEFT JOIN chunks c ON d.id = c.documento_id
        GROUP BY d.id
        ORDER BY d.tipo, d.titulo
    """)
    for row in cur.fetchall():
        print(f"  {row[0][:50]:50s} [{row[1]:10s}] {row[2]:4d} chunks")
    
    # Show sample chunks from pauta
    print("\n📋 SAMPLE CHUNKS DA PAUTA:")
    cur.execute("""
        SELECT c.conteudo, c.posicao
        FROM chunks c
        JOIN documentos d ON c.documento_id = d.id
        WHERE d.tipo = 'pauta'
        ORDER BY c.posicao
        LIMIT 3
    """)
    for i, row in enumerate(cur.fetchall(), 1):
        print(f"\n  Chunk {i} (posição {row[1]}):")
        print(f"  {row[0][:300]}...")
    
    conn.close()
    print("\n" + "=" * 60)
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
