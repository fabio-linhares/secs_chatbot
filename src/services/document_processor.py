#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Processamento de documentos (PDF, TXT, DOCX)
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Processamento de documentos (PDF, TXT, DOCX)
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

import os
import hashlib
from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

try:
    from pypdf import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Warning: pypdf not installed. PDF support disabled.")

@dataclass
class Document:
    """Represents a document"""
    tipo: str  # 'regimento', 'ata', 'resolucao', 'pauta'
    titulo: str
    numero: str = None
    data: str = None
    conselho: str = None
    caminho: str = None
    conteudo: str = ""
    hash_sha256: str = ""
    
@dataclass
class Chunk:
    """Represents a chunk of a document"""
    documento_id: int
    conteudo: str
    metadata: dict
    posicao: int

class DocumentProcessor:
    """Processes documents for RAG"""
    
    def __init__(self):
        self.supported_extensions = ['.md', '.txt', '.pdf']
    
    def ingest_directory(self, directory_path: str) -> List[Document]:
        """
        Ingests all documents from a directory structure.
        Expected structure:
        - regimentos/
        - atas/
        - resolucoes/
        - pautas/
        """
        documents = []
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_extensions):
                    file_path = os.path.join(root, file)
                    doc = self._process_file(file_path)
                    if doc:
                        documents.append(doc)
        
        return documents
    
    def _process_file(self, file_path: str) -> Document:
        """Process a single file"""
        try:
            # Determine document type from directory
            tipo = self._extract_tipo(file_path)
            
            # Read content based on file type
            if file_path.endswith('.pdf'):
                conteudo = self._read_pdf(file_path)
            else:
                # Read as text
                with open(file_path, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
            
            if not conteudo:
                print(f"Warning: Empty content for {file_path}")
                return None
            
            # Extract metadata from content
            metadata = self._extract_metadata(conteudo, tipo)
            
            # Calculate hash
            hash_sha256 = hashlib.sha256(conteudo.encode()).hexdigest()
            
            return Document(
                tipo=tipo,
                titulo=metadata.get('titulo', os.path.basename(file_path)),
                numero=metadata.get('numero'),
                data=metadata.get('data'),
                conselho=metadata.get('conselho'),
                caminho=file_path,
                conteudo=conteudo,
                hash_sha256=hash_sha256
            )
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None
    
    def _read_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        if not PDF_SUPPORT:
            print(f"Warning: Cannot read PDF {file_path} - pypdf not installed")
            return ""
        
        try:
            reader = PdfReader(file_path)
            text_parts = []
            
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return '\n\n'.join(text_parts)
        except Exception as e:
            print(f"Error reading PDF {file_path}: {e}")
            return ""
    
    def _extract_tipo(self, file_path: str) -> str:
        """Extract document type from file path"""
        if 'regimentos' in file_path:
            return 'regimento'
        elif 'atas' in file_path:
            return 'ata'
        elif 'resolucoes' in file_path:
            return 'resolucao'
        elif 'pautas' in file_path:
            return 'pauta'
        return 'outro'
    
    def _extract_metadata(self, conteudo: str, tipo: str) -> Dict:
        """Extract metadata from document content"""
        metadata = {}
        lines = conteudo.split('\n')
        
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            
            # Extract conselho
            if 'Conselho:' in line or 'CONSUNI' in line or 'CEPE' in line:
                if 'CONSUNI' in line:
                    metadata['conselho'] = 'CONSUNI'
                elif 'CEPE' in line:
                    metadata['conselho'] = 'CEPE'
            
            # Extract numero
            if 'Número:' in line or 'nº' in line:
                parts = line.split(':')
                if len(parts) > 1:
                    metadata['numero'] = parts[1].strip()
            
            # Extract data
            if 'Data:' in line or 'Data de Aprovação:' in line:
                parts = line.split(':')
                if len(parts) > 1:
                    metadata['data'] = parts[1].strip()
            
            # Extract titulo from first heading
            if line.startswith('#') and 'titulo' not in metadata:
                metadata['titulo'] = line.lstrip('#').strip()
        
        return metadata
    
    def chunk_document(self, doc: Document, chunk_size: int = 500, overlap: int = 100) -> List[Chunk]:
        """
        Chunk a document into smaller pieces.
        Uses semantic chunking based on markdown structure.
        """
        chunks = []
        lines = doc.conteudo.split('\n')
        
        current_chunk = []
        current_size = 0
        current_section = ""
        posicao = 0
        
        for line in lines:
            # Detect section headers
            if line.startswith('#'):
                # Save previous chunk if it exists
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    chunks.append(Chunk(
                        documento_id=0,  # Will be set when saving to DB
                        conteudo=chunk_text,
                        metadata={
                            'tipo': doc.tipo,
                            'titulo': doc.titulo,
                            'numero': doc.numero,
                            'secao': current_section,
                            'conselho': doc.conselho
                        },
                        posicao=posicao
                    ))
                    posicao += 1
                    current_chunk = []
                    current_size = 0
                
                current_section = line.lstrip('#').strip()
            
            # Add line to current chunk
            current_chunk.append(line)
            current_size += len(line)
            
            # If chunk is too large, split it
            if current_size > chunk_size and len(current_chunk) > 1:
                chunk_text = '\n'.join(current_chunk)
                chunks.append(Chunk(
                    documento_id=0,
                    conteudo=chunk_text,
                    metadata={
                        'tipo': doc.tipo,
                        'titulo': doc.titulo,
                        'numero': doc.numero,
                        'secao': current_section,
                        'conselho': doc.conselho
                    },
                    posicao=posicao
                ))
                posicao += 1
                
                # Keep overlap
                overlap_lines = current_chunk[-3:] if len(current_chunk) > 3 else current_chunk
                current_chunk = overlap_lines
                current_size = sum(len(line) for line in current_chunk)
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append(Chunk(
                documento_id=0,
                conteudo=chunk_text,
                metadata={
                    'tipo': doc.tipo,
                    'titulo': doc.titulo,
                    'numero': doc.numero,
                    'secao': current_section,
                    'conselho': doc.conselho
                },
                posicao=posicao
            ))
        
        return chunks
