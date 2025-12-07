# Como Adicionar Documentos PDF

## ✅ Sim! Você pode adicionar PDFs

O sistema já está configurado para processar arquivos PDF automaticamente.

## 📁 Onde colocar os PDFs

Coloque seus arquivos PDF nas pastas apropriadas:

```
secs_chatbot/data/documentos/
├── regimentos/          ← PDFs de regimentos aqui
├── atas/               ← PDFs de atas aqui
├── resolucoes/         ← PDFs de resoluções aqui
└── pautas/             ← PDFs de pautas aqui
```

## 🚀 Como processar

### Método 1: Usando run.sh (Recomendado)

```bash
# 1. Verificar PDFs disponíveis
./run.sh verify-pdfs

# 2. Processar e vetorizar
./run.sh vectorize
```

### Método 2: Script Python direto

```bash
python scripts/ingest_documents.py
```

O script irá:
1. ✅ Detectar automaticamente os PDFs
2. ✅ Extrair o texto de cada página
3. ✅ Criar chunks semânticos
4. ✅ Gerar embeddings
5. ✅ Armazenar no banco de dados

## 📝 Formatos Suportados

- ✅ `.pdf` - Arquivos PDF
- ✅ `.md` - Markdown
- ✅ `.txt` - Texto puro

## 💡 Dicas

### Organização por Tipo
O sistema detecta automaticamente o tipo do documento pela pasta:
- `regimentos/` → tipo: "regimento"
- `atas/` → tipo: "ata"
- `resolucoes/` → tipo: "resolucao"
- `pautas/` → tipo: "pauta"

### Metadados Extraídos
O sistema tenta extrair automaticamente:
- Número do documento (ex: "024/2024")
- Data
- Conselho (CONSUNI, CEPE, etc.)
- Título

### Exemplo de Uso Completo

```bash
# 1. Adicionar PDFs
cp ~/Downloads/regimento_consuni.pdf data/documentos/regimentos/
cp ~/Downloads/ata_*.pdf data/documentos/atas/
cp ~/Downloads/resolucao_*.pdf data/documentos/resolucoes/

# 2. Verificar novos PDFs
./run.sh verify-pdfs
# Saída: mostrará quantos PDFs novos foram encontrados

# 3. Processar
./run.sh vectorize
# Confirme quando solicitado

# 4. Verificar processamento
./run.sh stats
```

## 🔍 Verificar Documentos Processados

### Método 1: Usando run.sh (Mais Simples)

```bash
./run.sh stats
```

Mostrará:
- 👥 Número de usuários
- 📄 Total de documentos processados
- 📦 Total de chunks
- ⚡ Entradas em cache
- 📊 Total de interações

### Método 2: Python (Detalhado)

```python
from src.services.vector_store import get_vector_store

store = get_vector_store()
stats = store.get_stats()
print(stats)
```

## ⚠️ Importante

- **Duplicatas**: O sistema detecta duplicatas pelo hash SHA256 e não reprocessa
- **Qualidade do PDF**: PDFs escaneados (imagens) não funcionarão bem - use PDFs com texto selecionável
- **Tamanho**: Não há limite de tamanho, mas PDFs muito grandes serão divididos em muitos chunks

## 🎯 Próximos Passos

Após adicionar seus PDFs reais:
1. Execute a ingestão
2. Teste o chatbot com perguntas sobre os documentos
3. O sistema usará RAG para responder com base nos PDFs
