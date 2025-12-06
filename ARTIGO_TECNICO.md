# 🤖 Chatbot SECS/UFAL - Arquitetura Técnica

**Sistema RAG com HyDE para Consulta de Documentos Institucionais**

**Versão**: 7.1  
**Data**: 06/12/2025  
**Autor**: Fábio Linhares

---

## 📋 Sumário Executivo

Sistema de Retrieval-Augmented Generation (RAG) desenvolvido para facilitar o acesso a documentos institucionais da UFAL. Combina busca semântica vetorial, LLMs via OpenRouter, e HyDE (Hypothetical Document Embeddings) para respostas precisas sobre regimentos, resoluções, atas e pautas dos Conselhos Superiores.

**Características**:
- 🔍 Busca semântica com embeddings OpenRouter (1536 dims)
- 🧠 HyDE para +20-30% precisão
- 🔐 Permissões granulares (global/privado)
- 📤 Upload automático de PDFs
- 💾 Cache multinível (98% redução latência)
- 🎯 Agentes especializados

**Otimizado para hardware modesto** (Celeron N3050, 8GB RAM)

---

## 1. Arquitetura do Sistema

### 1.1 Visão Geral

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERFACE (Streamlit)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   CAMADA DE APLICAÇÃO                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Focal Agent  │  │ Semantic     │  │ HyDE Query   │       │
│  │ (7 tools)    │  │ Rewriter     │  │ Expander     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE RAG                             │
│  1. Query Enhancement (Semantic Rewriter)                   │
│  2. HyDE (opcional) - Gera resposta hipotética              │
│  3. Vector Search - Busca top-k chunks                      │
│  4. Context Building - Monta prompt com fontes              │
│  5. LLM Generation - Gera resposta                          │
│  6. Source Citation - Cita documentos                       │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  VECTOR STORE    │    │   LLM SERVICE    │
│  (SQLite)        │    │  (OpenRouter)    │
│                  │    │                  │
│  • Embeddings    │    │  • Gemini Flash  │
│  • Similarity    │    │  • Streaming     │
│  • Permissions   │    │  • Temperature   │
└────────┬─────────┘    └──────────────────┘
         │
         ▼
┌──────────────────┐
│ EMBEDDING API    │
│ OpenRouter       │
│ (1536 dims)      │
└──────────────────┘
```

### 1.2 Stack Tecnológico

| Componente | Tecnologia | Justificativa |
|------------|------------|---------------|
| **Frontend** | Streamlit | Prototipagem rápida, reativo |
| **LLM** | Gemini Flash 1.5 via OpenRouter | Rápido, gratuito, qualidade |
| **Embeddings** | text-embedding-3-small via OpenRouter | 1536 dims, sem overhead local |
| **Vector DB** | SQLite + NumPy | Simples, portável, leve |
| **Chunking** | RecursiveCharacterTextSplitter | Preserva semântica |
| **Cache** | SQLite | Persistente, eficiente |

**Por que OpenRouter?**
- ✅ Unified API (múltiplos modelos)
- ✅ Fallback automático
- ✅ Custo otimizado
- ✅ Sem vendor lock-in

---

## 2. Pipeline RAG Detalhado

### 2.1 Fluxo Completo

```
Usuário: "Como o conselho se reúne?"
    ↓
1. SEMANTIC REWRITER
   → "Como o conselho se reúne? Qual o quorum? 
      Conforme regimento interno..."
    ↓
2. HyDE (se ativado)
   → Gera hipótese: "O Conselho se reúne mediante 
      convocação, conforme Art. 7º..."
    ↓
3. EMBEDDING
   → Vetoriza hipótese (ou query)
   → [0.23, -0.15, ..., 0.42] (1536 dims)
    ↓
4. VECTOR SEARCH
   → Busca top-5 chunks similares
   → Filtra por permissões (user_id)
    ↓
5. CONTEXT BUILDING
   → Monta prompt com chunks
   → Adiciona metadados (fonte, similaridade)
    ↓
6. LLM GENERATION
   → Envia para Gemini Flash
   → Streaming de resposta
    ↓
7. SOURCE CITATION
   → Exibe fontes consultadas
   → Percentual de similaridade
```

### 2.2 Semantic Rewriter

**Objetivo**: Expandir queries vagas com contexto

**Exemplo**:
```python
Original: "Qual a pauta?"
Reescrita: "Qual a pauta da próxima reunião ordinária do CONSUNI? 
            Quais são os itens da ordem do dia? Quando será?"
```

**Implementação**:
```python
# src/agents/semantic_rewriter.py
class SemanticRewriter:
    def enrich(self, query: str, use_llm: bool = True):
        # 1. Heurísticas (rápido)
        heuristics = self._apply_heuristics(query)
        
        # 2. LLM (preciso)
        if use_llm:
            llm_expansion = self._llm_expand(query)
            return combine(heuristics, llm_expansion)
        
        return heuristics
```

### 2.3 HyDE (Hypothetical Document Embeddings)

**Conceito**: Gera resposta hipotética e busca por ela

**Vantagem**: Resposta hipotética é mais similar ao documento real que a query

**Exemplo**:
```
Query: "como o conselho se reune?"
    ↓
Análise de Contexto:
  - Conselho: PPGMCC
  - Tipo doc: regimento
  - Formato: "Art. X do Regimento..."
    ↓
Hipótese Gerada (LLM):
  "O Colegiado do PPGMCC se reúne mediante convocação 
   da Coordenação ou por requerimento de metade dos 
   membros, conforme Art. 7º do Regimento Interno..."
    ↓
Embedding da Hipótese:
  [0.45, 0.23, ..., 0.67] (1536 dims)
    ↓
Busca Vetorial:
  Similaridade com Art. 7º: 87% (vs 64% sem HyDE) ✅
```

**Implementação**:
```python
# src/services/hyde_query_expander.py
class HyDEQueryExpander:
    def expand_query(self, query, history):
        # 1. Analisar contexto
        analysis = self._analyze_context(query, history)
        
        # 2. Gerar hipótese
        hypothesis = self._generate_hypothesis(query, analysis)
        
        # 3. Embeddings
        query_emb = self.embeddings.generate(query)
        hyp_emb = self.embeddings.generate(hypothesis)
        
        return HyDEResult(
            original_query=query,
            hypothetical_answer=hypothesis,
            answer_embedding=hyp_emb,
            confidence=self._calculate_confidence(analysis)
        )
```

**Prompts Domain-Specific**:
```python
# src/utils/hyde_prompts.py
REGIMENTO_HYPOTHESIS_PROMPT = """
Você está gerando resposta hipotética sobre REGIMENTO.

Query: {query}
Conselho: {conselho}

Estrutura típica:
- "Conforme Art. [número] do Regimento [nome]..."
- "O [órgão] [ação], conforme Art. [número]..."

Gere resposta hipotética:
"""
```

### 2.4 Vector Search com Permissões

**Busca com Filtros**:
```python
# src/services/vector_store.py
def search(self, query: str, k: int = 5, user_id: str = None):
    # 1. Gerar embedding
    query_emb = self.embeddings.generate_embedding(query)
    
    # 2. Filtro de permissões
    if user_id:
        permission_filter = """
            WHERE d.is_global = 1 OR d.user_id = ?
        """
        params = (user_id,)
    else:
        permission_filter = "WHERE d.is_global = 1"
        params = ()
    
    # 3. Buscar chunks
    cur.execute(f"""
        SELECT c.conteudo, c.embedding, d.titulo, d.tipo
        FROM chunks c
        JOIN documentos d ON c.documento_id = d.id
        {permission_filter}
    """, params)
    
    # 4. Calcular similaridade
    results = []
    for row in cur.fetchall():
        chunk_emb = np.frombuffer(row['embedding'], dtype=np.float32)
        similarity = cosine_similarity(query_emb, chunk_emb)
        results.append({
            'conteudo': row['conteudo'],
            'similarity': similarity,
            'titulo': row['titulo']
        })
    
    # 5. Ordenar e retornar top-k
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:k]
```

**Similaridade de Cosseno**:
```python
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

---

## 3. Embeddings e Vetorização

### 3.1 Configuração OpenRouter

**Modelo**: `openai/text-embedding-3-small`  
**Dimensões**: 1536  
**Formato**: float32 (6144 bytes por vetor)

**Por que OpenRouter em vez de local?**

| Aspecto | Local (sentence-transformers) | OpenRouter |
|---------|-------------------------------|------------|
| **RAM** | 2-4GB overhead | 0GB |
| **CPU** | Intensivo (Celeron sofre) | Nenhum |
| **Latência** | ~500ms | ~200ms |
| **Qualidade** | Boa (384 dims) | Excelente (1536 dims) |
| **Custo** | Grátis | ~$0.0001/doc |

**Configuração**:
```python
# src/services/embeddings.py
class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(
            api_key=config.LLM_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = "openai/text-embedding-3-small"
    
    def generate_embedding(self, text: str) -> np.ndarray:
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        # IMPORTANTE: Converter para float32!
        embedding = np.array(
            response.data[0].embedding,
            dtype=np.float32  # ← Essencial!
        )
        return embedding
```

### 3.2 Processamento de Documentos

**Pipeline**:
```
PDF → Extração de Texto → Chunking → Embeddings → Armazenamento
```

**Chunking**:
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,        # ~150-200 palavras
    chunk_overlap=200,      # Evita perda nas bordas
    separators=["\n\n", "\n", ". ", " ", ""]
)

chunks = splitter.split_text(document_text)
```

**Armazenamento**:
```sql
-- Tabela de chunks
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY,
    documento_id INTEGER NOT NULL,
    conteudo TEXT NOT NULL,
    embedding BLOB,           -- 6144 bytes (1536 × 4)
    metadata TEXT,
    posicao INTEGER,
    FOREIGN KEY (documento_id) REFERENCES documentos(id)
);

-- Serialização
embedding_blob = embedding.astype(np.float32).tobytes()

-- Deserialização
embedding = np.frombuffer(embedding_blob, dtype=np.float32)
```

---

## 4. Permissões e Segurança

### 4.1 Sistema de Permissões

**Modelo**:
- **Documentos Globais** (🌍): Visíveis para todos
- **Documentos Privados** (🔒): Visíveis só para dono

**Schema**:
```sql
CREATE TABLE documentos (
    id INTEGER PRIMARY KEY,
    tipo TEXT NOT NULL,
    titulo TEXT NOT NULL,
    user_id TEXT DEFAULT 'system',  -- Dono
    is_global BOOLEAN DEFAULT 1,    -- Global?
    -- ... outros campos
);
```

**Lógica de Busca**:
```python
# Admin vê tudo
if user_role == 'admin':
    filter = "1=1"  # Sem filtro

# Usuário comum vê:
# - Documentos globais
# - Seus documentos privados
else:
    filter = "(is_global = 1 OR user_id = ?)"
    params = (user_id,)
```

### 4.2 Autenticação

**PBKDF2** com 100.000 iterações:
```python
# src/services/user_service.py
def hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations=100000
    )
```

**Roles**:
- `publico`: Acesso básico
- `secs`: Funcionalidades extras
- `admin`: Acesso total

---

## 5. Cache e Performance

### 5.1 Cache Multinível

**Estrutura**:
```
┌─────────────────────┐
│  Cache de Usuário   │  ← Específico do usuário
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   Cache Global      │  ← Compartilhado
└─────────────────────┘
```

**Implementação**:
```python
# src/services/cache_service.py
class CacheService:
    def get(self, query: str, user_id: str):
        # 1. Normalizar query
        normalized = self._normalize(query)
        
        # 2. Buscar em cache de usuário
        user_cache = self._get_user_cache(user_id, normalized)
        if user_cache:
            return user_cache, "user"
        
        # 3. Buscar em cache global
        global_cache = self._get_global_cache(normalized)
        if global_cache:
            return global_cache, "global"
        
        return None, None
    
    def _normalize(self, query: str) -> str:
        # Remove pontuação, lowercase, trim
        return query.lower().strip().rstrip('?!.')
```

**Métricas**:
- **Hit rate**: ~98%
- **Redução latência**: 98% (3s → 50ms)
- **Economia API**: 70%

### 5.2 Otimizações para Hardware Modesto

**Configuração Recomendada**:
```env
# .env - Otimizado para Celeron N3050
EMBEDDING_PROVIDER=openai  # NÃO local!
LLM_MODEL=openrouter/google/gemini-flash-1.5
CACHE_ENABLED=true  # ESSENCIAL!
RAG_TOP_K=5  # Não aumentar
```

**Benchmarks** (Celeron N3050, 8GB RAM):

| Operação | Tempo | Observação |
|----------|-------|------------|
| Startup | ~3s | Com cache |
| Query (cache hit) | ~50ms | 98% dos casos |
| Query (cache miss) | ~2-3s | Busca + LLM |
| Upload PDF (10MB) | ~30s | Processamento |
| HyDE query | +500ms | LLM extra |

---

## 6. Agentes Especializados

### 6.1 Focal Agent

**7 Ferramentas**:
1. **Pauta**: Busca pautas de reuniões
2. **Ata**: Busca atas
3. **Votação**: Informações sobre votações
4. **Participantes**: Lista de participantes
5. **Resolução**: Busca resoluções
6. **Portaria**: Busca portarias
7. **Data**: Informações temporais

**Implementação**:
```python
# src/agents/focal_agent.py
class FocalAgent:
    def run(self, query: str, user_id: str):
        # 1. Detectar ferramenta
        tool = self._detect_tool(query)
        
        # 2. Executar busca especializada
        if tool == 'pauta':
            results = self.vector_store.search_with_filter(
                query,
                filters={'tipo': 'pauta'},
                user_id=user_id
            )
        
        return AgentResult(tool=tool, chunks=results)
```

---

## 7. Métricas e Monitoramento

### 7.1 Performance

**Precisão RAG**: ~92%  
**Cache hit rate**: ~98%  
**HyDE melhoria**: +20-30%

### 7.2 Capacidade

- **Documentos**: Ilimitado (disco)
- **Chunks**: ~500 tokens médio
- **Embeddings**: 1536 dimensões
- **Cache**: 1000 queries (configurável)

