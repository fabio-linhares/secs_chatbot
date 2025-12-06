#!/usr/bin/env bash
# ============================================================================
# SECS Chatbot - Script de Execução Unificado
# ============================================================================
# Versão: 7.1
# Data: 2025-12-06
# Descrição: Script unificado com todas as funcionalidades
# Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
# Licença: MIT
# Compatibilidade: Bash 4.0+, Linux/macOS

# Comandos Disponíveis:
#./run.sh setup          # Configuração inicial
#./run.sh start          # Iniciar chatbot (com verificação embeddings)
#./run.sh test           # Testes (incluindo HyDE)
#./run.sh backup         # Backup do banco
#./run.sh clean          # Limpar cache
#./run.sh logs           # Ver logs
#./run.sh stats          # Estatísticas
# ./run.sh help           # Ajuda
# ============================================================================

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Preferir .venv se existir; fallback para venv
if [ -d "${PROJECT_DIR}/.venv" ]; then
    VENV_DIR="${PROJECT_DIR}/.venv"
else
    VENV_DIR="${PROJECT_DIR}/venv"
fi
DATA_DIR="${PROJECT_DIR}/data"
LOG_DIR="${DATA_DIR}/logs"
ENV_FILE="${PROJECT_DIR}/.env"

# ============================================================================
# Funções Utilitárias
# ============================================================================

print_header() {
    echo -e "${BLUE}"
    echo "============================================================================"
    echo "  SECS Chatbot - $1"
    echo "============================================================================"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ============================================================================
# Verificações
# ============================================================================

check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 não encontrado. Instale Python 3.11 ou superior."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    print_success "Python $PYTHON_VERSION encontrado"
}

check_conda() {
    if command -v conda &> /dev/null; then
        print_success "Conda encontrado"
        return 0
    else
        print_warning "Conda não encontrado (opcional)"
        return 1
    fi
}

check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        print_warning ".env não encontrado. Criando a partir do exemplo..."
        if [ -f "${ENV_FILE}.example" ]; then
            cp "${ENV_FILE}.example" "$ENV_FILE"
            print_info "⚠️  IMPORTANTE: Edite o arquivo .env com suas configurações!"
            print_info "   Especialmente: LLM_API_KEY"
        else
            print_error ".env.example não encontrado!"
            exit 1
        fi
    else
        print_success ".env encontrado"
    fi
}

check_embeddings_migration() {
    print_info "Verificando configuração de embeddings..."
    
    # Usar Python para verificar migração
    python3 <<'PYTHON_SCRIPT'
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from utils.embedding_migration import check_and_migrate
    success = check_and_migrate(auto_confirm=False)
    if not success:
        print("⚠️  Migração de embeddings pode ser necessária")
        sys.exit(1)
except Exception as e:
    print(f"⚠️  Erro ao verificar embeddings: {e}")
    sys.exit(0)  # Não bloquear execução
PYTHON_SCRIPT
    
    if [ $? -eq 0 ]; then
        print_success "Embeddings verificados"
    else
        print_warning "Verifique a configuração de embeddings"
    fi
}

# ============================================================================
# Instalação e Setup
# ============================================================================

setup_directories() {
    print_info "Criando diretórios necessários..."
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "${DATA_DIR}/user_uploads"
    mkdir -p "${DATA_DIR}/backups"
    mkdir -p "${DATA_DIR}/documentos/exemplos"
    print_success "Diretórios criados"
}

install_dependencies() {
    print_info "Instalando dependências..."
    
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    
    print_success "Dependências instaladas"
}

setup_venv() {
    if [ -d "$VENV_DIR" ]; then
        print_success "Ambiente virtual já existe"
        return 0
    fi
    
    print_info "Criando ambiente virtual..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    
    install_dependencies
    print_success "Ambiente virtual criado"
}

setup_conda() {
    ENV_NAME="secs_chatbot"
    
    if conda env list | grep -q "^${ENV_NAME} "; then
        print_success "Ambiente conda '${ENV_NAME}' já existe"
        return 0
    fi
    
    print_info "Criando ambiente conda '${ENV_NAME}'..."
    conda create -n "$ENV_NAME" python=3.11 -y
    
    print_info "Ativando ambiente..."
    eval "$(conda shell.bash hook)"
    conda activate "$ENV_NAME"
    
    install_dependencies
    print_success "Ambiente conda criado"
}

full_setup() {
    print_header "Configuração Inicial"
    
    check_python
    setup_directories
    check_env_file
    
    if check_conda; then
        read -p "Usar conda? (y/n): " use_conda
        if [[ $use_conda == "y" ]]; then
            setup_conda
        else
            setup_venv
        fi
    else
        setup_venv
    fi
    
    print_success "Setup completo!"
    print_info ""
    print_info "Próximos passos:"
    print_info "1. Edite o arquivo .env com suas credenciais"
    print_info "2. Execute './run.sh start' para iniciar o chatbot"
}

# ============================================================================
# Execução
# ============================================================================

activate_env() {
    local activated=0
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
        print_success "Ambiente virtual ativado (${VENV_DIR})"
        activated=1
    elif command -v conda &> /dev/null && conda env list | grep -q "^secs_chatbot "; then
        eval "$(conda shell.bash hook)"
        conda activate secs_chatbot
        print_success "Ambiente conda ativado"
        activated=1
    fi

    if [ $activated -eq 0 ]; then
        print_warning "Nenhum ambiente virtual/conda encontrado. Execute './run.sh setup' primeiro."
    fi
}

start_app() {
    print_header "Iniciando SECS Chatbot"
    
    activate_env
    check_env_file
    check_embeddings_migration
    
    # Escolher qual app executar
    APP_FILE="${1:-app_enhanced.py}"
    
    print_info "Executando src/${APP_FILE}..."
    print_info "Acesse: http://localhost:8501"
    print_info "Pressione Ctrl+C para parar"
    echo ""

    if ! command -v streamlit &>/dev/null; then
        print_error "streamlit não encontrado no ambiente atual."
        print_info "Execute './run.sh setup' para criar o ambiente e instalar dependências"
        print_info "ou rode 'pip install -r requirements.txt' no ambiente ativo."
        exit 1
    fi

    streamlit run "src/${APP_FILE}" \
        --server.port=8501 \
        --server.address=localhost \
        --server.headless=true
}

start_basic() {
    start_app "app.py"
}

start_enhanced() {
    start_app "app_enhanced.py"
}

# ============================================================================
# Testes
# ============================================================================

run_tests() {
    print_header "Executando Testes"
    
    activate_env
    
    if [ -f "scripts/test_cache_audit.py" ]; then
        print_info "Teste 1: Cache e Audit..."
        python scripts/test_cache_audit.py
    fi
    
    if [ -f "scripts/test_new_services.py" ]; then
        print_info "Teste 2: Novos Serviços..."
        python scripts/test_new_services.py
    fi
    
    if [ -f "scripts/test_hyde.py" ]; then
        print_info "Teste 3: HyDE..."
        python scripts/test_hyde.py
    fi
    
    print_success "Todos os testes passaram!"
}

# ============================================================================
# Manutenção
# ============================================================================

clean_cache() {
    print_header "Limpando Cache"
    
    print_info "Removendo cache Python..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    print_info "Removendo logs antigos (>30 dias)..."
    find "$LOG_DIR" -type f -name "*.log" -mtime +30 -delete 2>/dev/null || true
    
    print_success "Cache limpo"
}

backup_db() {
    print_header "Backup do Banco de Dados"
    
    DB_FILE="${DATA_DIR}/app.db"
    BACKUP_DIR="${DATA_DIR}/backups"
    mkdir -p "$BACKUP_DIR"
    
    if [ -f "$DB_FILE" ]; then
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_FILE="${BACKUP_DIR}/app_${TIMESTAMP}.db"
        
        cp "$DB_FILE" "$BACKUP_FILE"
        print_success "Backup criado: $BACKUP_FILE"
        
        # Manter apenas últimos 10 backups
        ls -t "${BACKUP_DIR}"/app_*.db | tail -n +11 | xargs rm -f 2>/dev/null || true
    else
        print_warning "Banco de dados não encontrado"
    fi
}

show_logs() {
    print_header "Logs Recentes"
    
    LOG_FILE="${LOG_DIR}/app.log"
    
    if [ -f "$LOG_FILE" ]; then
        tail -n 50 "$LOG_FILE"
    else
        print_warning "Arquivo de log não encontrado"
    fi
}

show_stats() {
    print_header "Estatísticas do Sistema"
    
    activate_env
    
    python3 <<'PYTHON_SCRIPT'
import sqlite3
from pathlib import Path

db_path = Path("data/app.db")

if not db_path.exists():
    print("⚠ Banco de dados não encontrado")
    exit(0)

conn = sqlite3.connect(str(db_path))

# Usuários
try:
    users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    print(f"👥 Usuários: {users}")
except:
    print("👥 Usuários: 0")

# Documentos
try:
    docs = conn.execute("SELECT COUNT(*) FROM documentos").fetchone()[0]
    print(f"📄 Documentos: {docs}")
except:
    print("📄 Documentos: 0")

# Chunks
try:
    chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    print(f"📦 Chunks: {chunks}")
except:
    print("📦 Chunks: 0")

# Cache
try:
    cache_user = conn.execute("SELECT COUNT(*) FROM qa_user_cache").fetchone()[0]
    cache_global = conn.execute("SELECT COUNT(*) FROM qa_global_cache").fetchone()[0]
    print(f"⚡ Cache: {cache_user + cache_global} entradas")
except:
    print("⚡ Cache: 0 entradas")

# Audit
try:
    audit = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    print(f"📊 Interações: {audit}")
except:
    print("📊 Interações: 0")

conn.close()
PYTHON_SCRIPT
}

# ============================================================================
# Menu de Ajuda
# ============================================================================

show_help() {
    cat <<EOF
${BLUE}============================================================================
  SECS Chatbot - Script de Execução v7.1
============================================================================${NC}

${GREEN}Uso:${NC} ./run.sh [comando]

${GREEN}Comandos Principais:${NC}
  setup           Configuração inicial completa
  start           Inicia o chatbot (app enhanced) ← RECOMENDADO
  start-basic     Inicia o chatbot (app básico)
  start-enhanced  Inicia o chatbot (app enhanced)
  
${GREEN}Testes e Validação:${NC}
  test            Executa todos os testes
  
${GREEN}Manutenção:${NC}
  clean           Limpa cache e arquivos temporários
  backup          Cria backup do banco de dados
  logs            Mostra logs recentes
  stats           Mostra estatísticas do sistema
  
${GREEN}Ajuda:${NC}
  help            Mostra esta mensagem

${GREEN}Exemplos:${NC}
  ./run.sh setup          # Primeira vez (criar venv, instalar deps)
  ./run.sh start          # Iniciar chatbot
  ./run.sh test           # Executar testes
  ./run.sh backup         # Fazer backup do banco
  ./run.sh clean          # Limpar cache
  ./run.sh stats          # Ver estatísticas

${YELLOW}Nota:${NC} Este script substitui tanto run.sh quanto start.py

${BLUE}============================================================================${NC}
EOF
}

# ============================================================================
# Main
# ============================================================================

main() {
    cd "$PROJECT_DIR"
    
    case "${1:-help}" in
        setup)
            full_setup
            ;;
        start)
            start_enhanced
            ;;
        start-basic)
            start_basic
            ;;
        start-enhanced)
            start_enhanced
            ;;
        test)
            run_tests
            ;;
        clean)
            clean_cache
            ;;
        backup)
            backup_db
            ;;
        logs)
            show_logs
            ;;
        stats)
            show_stats
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Comando desconhecido: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Executar
main "$@"
