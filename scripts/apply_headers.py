#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
Script para aplicar headers padronizados a todos os arquivos do projeto.
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
"""

import os
import re
from pathlib import Path
from datetime import datetime

# Configuração
PROJECT_ROOT = Path(__file__).parent.parent
AUTHOR = "Fábio Linhares"
EMAIL = "fabio.linhares@edu.vertex.org.br"
VERSION = "7.0"
DATE = datetime.now().strftime("%Y-%m-%d")
REPO = "https://github.com/fabiolinhares/secs_chatbot"
LICENSE = "MIT"

# Mapeamento de descrições por arquivo
DESCRIPTIONS = {
    # Services
    "cache_service.py": "Serviço de cache inteligente multinível",
    "audit.py": "Serviço de auditoria e logging de interações",
    "user_service.py": "Serviço de gerenciamento de usuários",
    "user_preferences_service.py": "Serviço de preferências personalizadas do usuário",
    "user_documents_service.py": "Serviço de upload e gestão de documentos do usuário",
    "quota_service.py": "Serviço de gestão de quotas de armazenamento",
    "feature_flags_service.py": "Serviço de feature flags por role",
    "admin_service.py": "Serviço administrativo do sistema",
    "chat_service.py": "Orquestrador do pipeline de chat completo",
    "llm.py": "Serviço de integração com LLM (OpenAI/OpenRouter)",
    "embeddings.py": "Serviço de geração de embeddings",
    "vector_store.py": "Armazenamento e busca vetorial",
    "document_processor.py": "Processamento de documentos (PDF, TXT, DOCX)",
    "count_helper.py": "Extração de fatos derivados de chunks",
    "prompt_enricher.py": "Enriquecimento de prompts com contexto",
    
    # Agents
    "semantic_rewriter.py": "Agente de reescrita semântica híbrida",
    "focal_agent.py": "Agente com ferramentas focais especializadas",
    "query_enhancer.py": "Agente de melhoria de queries",
    "clarification_agent.py": "Agente de clarificação e desambiguação",
    
    # Utils
    "logger.py": "Sistema de logging estruturado",
    "error_handler.py": "Framework de tratamento de erros",
    "validation.py": "Modelos Pydantic para validação de inputs",
    "rate_limiter.py": "Controle de taxa de requisições",
    "metrics.py": "Coletor de métricas e estatísticas",
    "text_utils.py": "Utilitários para processamento de texto",
    "advanced_disambiguation.py": "Desambiguação avançada de queries",
    "conversation_controls.py": "Controles de gerenciamento de conversa",
    "prompts.py": "Templates de prompts do sistema",
    
    # Components
    "auth_panel.py": "Painel de autenticação Streamlit",
    "login.py": "Componente de login",
    
    # Apps
    "app.py": "Aplicação Streamlit básica",
    "app_enhanced.py": "Aplicação Streamlit com todas as funcionalidades",
    "config.py": "Configuração do sistema com Pydantic Settings",
}

def get_python_header(filename: str, description: str) -> str:
    """Gera header para arquivo Python"""
    return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - {description}
============================================================================
Versão: {VERSION}
Data: {DATE}
Descrição: {description}
Autoria: {AUTHOR} <{EMAIL}>
Repositório: {REPO}
Licença: {LICENSE}
Compatibilidade: Python 3.11+
============================================================================
"""
'''

def get_shell_header(filename: str, description: str) -> str:
    """Gera header para arquivo Shell"""
    return f'''#!/usr/bin/env bash
# ============================================================================
# SECS Chatbot - {description}
# ============================================================================
# Versão: {VERSION}
# Data: {DATE}
# Descrição: {description}
# Autoria: {AUTHOR} <{EMAIL}>
# Repositório: {REPO}
# Licença: {LICENSE}
# Compatibilidade: Bash 4.0+, Linux/macOS
# ============================================================================
'''

def remove_old_header(content: str, file_type: str) -> str:
    """Remove header antigo do arquivo"""
    if file_type == "python":
        # Remove shebang, encoding e docstring inicial
        content = re.sub(r'^#!/usr/bin/env python3?\n', '', content)
        content = re.sub(r'^# -\*- coding: utf-8 -\*-\n', '', content)
        content = re.sub(r'^"""[\s\S]*?"""\n+', '', content, count=1)
    elif file_type == "shell":
        # Remove shebang e comentários iniciais
        content = re.sub(r'^#!/usr/bin/env bash\n', '', content)
        lines = content.split('\n')
        while lines and (lines[0].startswith('#') or not lines[0].strip()):
            lines.pop(0)
        content = '\n'.join(lines)
    
    return content.lstrip()

def apply_header_to_file(filepath: Path):
    """Aplica header a um arquivo"""
    filename = filepath.name
    
    # Determinar tipo de arquivo
    if filename.endswith('.py'):
        file_type = "python"
    elif filename.endswith('.sh'):
        file_type = "shell"
    else:
        return  # Ignorar outros tipos
    
    # Obter descrição
    description = DESCRIPTIONS.get(filename, f"Módulo {filename}")
    
    # Ler conteúdo atual
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Erro ao ler {filepath}: {e}")
        return
    
    # Remover header antigo
    content = remove_old_header(content, file_type)
    
    # Gerar novo header
    if file_type == "python":
        header = get_python_header(filename, description)
    else:
        header = get_shell_header(filename, description)
    
    # Combinar header + conteúdo
    new_content = header + '\n' + content
    
    # Escrever arquivo
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ {filepath.relative_to(PROJECT_ROOT)}")
    except Exception as e:
        print(f"❌ Erro ao escrever {filepath}: {e}")

def main():
    """Aplica headers a todos os arquivos do projeto"""
    print("🚀 Aplicando headers padronizados...\n")
    
    # Diretórios a processar
    dirs_to_process = [
        PROJECT_ROOT / "src" / "services",
        PROJECT_ROOT / "src" / "agents",
        PROJECT_ROOT / "src" / "utils",
        PROJECT_ROOT / "src" / "components",
        PROJECT_ROOT / "src",
    ]
    
    files_processed = 0
    
    for directory in dirs_to_process:
        if not directory.exists():
            continue
        
        # Processar arquivos Python
        for filepath in directory.glob("*.py"):
            if filepath.name != "__init__.py":  # Ignorar __init__.py
                apply_header_to_file(filepath)
                files_processed += 1
    
    # Processar scripts shell
    for filepath in PROJECT_ROOT.glob("*.sh"):
        apply_header_to_file(filepath)
        files_processed += 1
    
    print(f"\n✅ {files_processed} arquivos processados!")
    print(f"📝 Headers aplicados com sucesso!")

if __name__ == "__main__":
    main()
