# MCP Server - SECS/UFAL

## 📡 O que é MCP?

**MCP (Model Context Protocol)** é um protocolo que permite que modelos de IA acessem informações externas através de ferramentas (tools) e recursos (resources).

## 🎯 Funcionalidades Implementadas

### Tools (Ferramentas)

1. **search_documents** - Busca semântica em documentos
2. **get_ata** - Obtém ata específica ou lista todas
3. **get_resolucao** - Obtém resolução específica ou lista todas
4. **list_pautas** - Lista todas as pautas disponíveis
5. **get_stats** - Estatísticas da base de documentos

### Resources (Recursos)

1. **secs://atas** - Acesso a todas as atas
2. **secs://resolucoes** - Acesso a todas as resoluções
3. **secs://pautas** - Acesso a todas as pautas
4. **secs://stats** - Estatísticas do sistema

---

## 🚀 Como Usar

### Iniciar o Servidor

```bash
cd secs_chatbot
python mcp/server.py
```

O servidor roda em modo stdio (entrada/saída padrão).

### Testar o Servidor

```bash
python mcp/client.py
```

---

## 📝 Exemplos de Uso

### 1. Listar Tools

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

**Response:**
```json
{
  "tools": [
    {
      "name": "search_documents",
      "description": "Search for documents using semantic search",
      "inputSchema": {...}
    },
    ...
  ]
}
```

### 2. Buscar Documentos

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_documents",
    "arguments": {
      "query": "pauta reunião",
      "document_type": "pauta",
      "limit": 5
    }
  }
}
```

**Response:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"success\": true, \"num_results\": 3, ...}"
    }
  ]
}
```

### 3. Obter Ata Específica

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_ata",
    "arguments": {
      "numero": "01/2024"
    }
  }
}
```

### 4. Ler Resource

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/read",
  "params": {
    "uri": "secs://stats"
  }
}
```

---

## 🔧 Arquitetura

```
mcp/
├── __init__.py       # Package init
├── server.py         # MCP Server (stdio mode)
├── tools.py          # Tools implementation
└── client.py         # Test client
```

### Fluxo de Dados

```
Client Request
    ↓
MCP Server (server.py)
    ↓
Tools (tools.py)
    ↓
Vector Store / Database
    ↓
Response
```

---

## 📊 Tools Disponíveis

### search_documents

Busca semântica em documentos.

**Parâmetros:**
- `query` (string, required): Query de busca
- `document_type` (string, optional): Filtro por tipo
- `limit` (integer, optional): Máximo de resultados (default: 5)

**Retorno:**
```json
{
  "success": true,
  "query": "pauta reunião",
  "num_results": 3,
  "results": [...]
}
```

### get_ata

Obtém ata específica ou lista todas.

**Parâmetros:**
- `numero` (string, optional): Número da ata

**Retorno (específica):**
```json
{
  "success": true,
  "titulo": "Ata da 1ª Reunião...",
  "tipo": "ata",
  "numero": "01/2024",
  "data": "2024-03-15",
  "conteudo": "..."
}
```

**Retorno (lista):**
```json
{
  "success": true,
  "num_atas": 4,
  "atas": [...]
}
```

### get_resolucao

Similar a `get_ata`, mas para resoluções.

### list_pautas

Lista todas as pautas disponíveis.

**Retorno:**
```json
{
  "success": true,
  "num_pautas": 3,
  "pautas": [...]
}
```

### get_stats

Retorna estatísticas da base.

**Retorno:**
```json
{
  "success": true,
  "num_documentos": 18,
  "num_chunks": 1109,
  "documentos_por_tipo": {...}
}
```

---

## 🧪 Testes

Execute o cliente de teste:

```bash
python mcp/client.py
```

**Saída esperada:**
```
============================================================
Testing SECS MCP Server
============================================================

1. Listing tools...
Found 5 tools
  - search_documents: Search for documents...
  - get_ata: Get specific ata...
  ...

2. Getting stats...
{
  "success": true,
  "num_documentos": 18,
  ...
}

...

All tests completed successfully!
```

---

## 🔗 Integração com LLMs

O servidor MCP pode ser usado por LLMs compatíveis com MCP para acessar documentos SECS dinamicamente.

**Exemplo de configuração (Claude Desktop):**

```json
{
  "mcpServers": {
    "secs": {
      "command": "python",
      "args": ["/path/to/secs_chatbot/mcp/server.py"]
    }
  }
}
```
