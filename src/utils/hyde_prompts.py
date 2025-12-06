#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - HyDE Prompts
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Domain-specific prompts for Hypothetical Document Embeddings
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""


# Prompt para análise de contexto
CONTEXT_ANALYSIS_PROMPT = """
Você é um especialista em Conselhos Superiores da UFAL (SECS).

Analise a seguinte pergunta e identifique:
1. Qual conselho está sendo referenciado (CONSUNI, CEPE, etc.)
2. Que tipo de documento contém a resposta (Regimento, Ata, Pauta, Resolução)
3. Qual o formato esperado da resposta

Pergunta: {query}

Histórico da conversa:
{history}

Responda em JSON:
{{
    "conselho": "nome do conselho ou 'indefinido'",
    "tipo_documento": "regimento|ata|pauta|resolucao|indefinido",
    "topico": "descrição breve do tópico",
    "formato_esperado": "como a resposta deve ser estruturada"
}}
"""

# Prompt principal para geração de hipótese
HYPOTHESIS_GENERATION_PROMPT = """
Você é um assistente especializado em documentos dos Conselhos Superiores da UFAL (SECS).

CONTEXTO DO DOMÍNIO:
- Documentos disponíveis: Regimentos, Atas, Pautas, Resoluções
- Conselhos: CONSUNI, CEPE, e outros
- Estrutura típica: Artigos, Parágrafos (§), Incisos, Alíneas
- Linguagem: Formal, técnica, jurídica

ANÁLISE DA PERGUNTA:
Pergunta do usuário: {query}
Conselho identificado: {conselho}
Tipo de documento: {tipo_documento}
Tópico: {topico}

HISTÓRICO DA CONVERSA:
{history}

TAREFA:
Gere uma resposta HIPOTÉTICA e REALISTA que provavelmente existe nos documentos.

A resposta deve:
1. Usar linguagem formal típica de documentos oficiais
2. Incluir referências específicas (ex: "Art. 7º", "§1º", "Inciso II")
3. Ser detalhada e precisa
4. Seguir a estrutura típica desse tipo de documento
5. Mencionar o documento fonte (ex: "conforme Regimento do PPGMCC")

IMPORTANTE: 
- NÃO invente informações
- Baseie-se em padrões típicos desses documentos
- Use terminologia técnica apropriada
- Seja específico sobre artigos e parágrafos

Resposta hipotética:
"""

# Prompt para regimentos especificamente
REGIMENTO_HYPOTHESIS_PROMPT = """
Você está gerando uma resposta hipotética sobre um REGIMENTO.

Pergunta: {query}
Regimento: {conselho}

Estrutura típica de resposta sobre regimentos:
- "Conforme o Art. [número] do Regimento [nome]..."
- "O [órgão/conselho] [ação], conforme estabelecido no Art. [número]..."
- "De acordo com o §[número] do Art. [número]..."

Gere uma resposta hipotética seguindo esse padrão:
"""

# Prompt para atas
ATA_HYPOTHESIS_PROMPT = """
Você está gerando uma resposta hipotética sobre uma ATA.

Pergunta: {query}
Contexto: Ata de reunião do {conselho}

Estrutura típica de resposta sobre atas:
- "Na reunião de [data], foi deliberado..."
- "Conforme Ata da [tipo] Reunião [número], realizada em [data]..."
- "Os participantes presentes foram..."
- "Foi aprovado por [quorum]..."

Gere uma resposta hipotética seguindo esse padrão:
"""

# Prompt para pautas
PAUTA_HYPOTHESIS_PROMPT = """
Você está gerando uma resposta hipotética sobre uma PAUTA.

Pergunta: {query}
Contexto: Pauta de reunião do {conselho}

Estrutura típica de resposta sobre pautas:
- "A próxima reunião está agendada para [data], às [hora]..."
- "Conforme Pauta da [tipo] Reunião, os itens a serem discutidos são..."
- "Item [número]: [descrição]..."

Gere uma resposta hipotética seguindo esse padrão:
"""

# Prompt para resoluções
RESOLUCAO_HYPOTHESIS_PROMPT = """
Você está gerando uma resposta hipotética sobre uma RESOLUÇÃO.

Pergunta: {query}
Contexto: Resolução do {conselho}

Estrutura típica de resposta sobre resoluções:
- "A Resolução {conselho} nº [número]/[ano] estabelece..."
- "Conforme Art. [número] da Resolução..."
- "Fica aprovado/estabelecido..."

Gere uma resposta hipotética seguindo esse padrão:
"""

# Mapeamento de prompts por tipo de documento
DOCUMENT_TYPE_PROMPTS = {
    'regimento': REGIMENTO_HYPOTHESIS_PROMPT,
    'ata': ATA_HYPOTHESIS_PROMPT,
    'pauta': PAUTA_HYPOTHESIS_PROMPT,
    'resolucao': RESOLUCAO_HYPOTHESIS_PROMPT,
}
