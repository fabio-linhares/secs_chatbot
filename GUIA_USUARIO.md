# 📖 Guia do Usuário - Chatbot SECS/UFAL

**Versão**: 7.1  
**Última atualização**: 06/12/2024

---

## 📋 Índice

1. [Primeiro Acesso](#primeiro-acesso)
2. [Interface Principal](#interface-principal)
3. [Fazendo Perguntas](#fazendo-perguntas)
4. [Upload de Documentos](#upload-de-documentos)
5. [Permissões](#permissões)
6. [HyDE (Busca Aprimorada)](#hyde-busca-aprimorada)
7. [Painel Administrativo](#painel-administrativo)
8. [Dicas e Truques](#dicas-e-truques)
9. [Troubleshooting](#troubleshooting)
10. [FAQs](#faqs)

---

## 🚀 Primeiro Acesso

### Passo 1: Iniciar a Aplicação

```bash
# Ativar ambiente
conda activate secs_chatbot

# Iniciar app
streamlit run src/app_enhanced.py
```

Aguarde ~3-15 segundos (primeira vez pode demorar mais).

### Passo 2: Acessar no Navegador

Abra: **http://localhost:8501**

### Passo 3: Primeiro Usuário (Wizard)

Na primeira vez, você verá o **Wizard de Configuração**:

1. **Criar Usuário Admin**:
   - Nome de usuário: `admin` (ou seu preferido)
   - Senha: Mínimo 8 caracteres
   - Confirmar senha

   - Obs. Caso o usuário `admin` já exista, apenas faça login com a senha `vertex`

2. **Configurar Sistema**:
   - Nome da instituição: `SECS/UFAL`
   - Descrição: (opcional)

3. **Concluir**:
   - Clique em "Finalizar Configuração"
   - Você será logado automaticamente

### Passo 4: Login Subsequente

Após configuração inicial:

1. **Sidebar** → Seção "Autenticação"
2. Digite usuário e senha
3. Clique em "Entrar"

---

## 🖥️ Interface Principal

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  SIDEBAR (Esquerda)          │  ÁREA PRINCIPAL (Direita)│
│                              │                          │
│  🏛️ SECS/UFAL                │  💬 Chat                 │
│  ─────────────────           │  ─────────────           │
│  🔐 Autenticação             │  Histórico de mensagens  │
│  👤 user: admin              │  ↓                       │
│  🎭 role: admin              │  Input de texto          │
│                              │                          │
│  📊 Última Consulta          │  📚 Fontes consultadas   │
│  Trechos RAG: 5              │  (expansível)            │
│  ⚡ Cache: user              │                          │
│                              │                          │
│  🔬 Recursos Experimentais   │  🔍 Detalhes da busca    │
│  ☑ HyDE (Busca Aprimorada)   │  (expansível)            │
│                              │                          │
│  📤 Upload de Documentos     │                          │
│  (se habilitado)             │                          │
│                              │                          │
│  ⚙️ Admin Panel              │                          │
│  (só para admin)             │                          │
└─────────────────────────────────────────────────────────┘
```

### Elementos da Sidebar

1. **Informações do Usuário**:
   - Nome de usuário logado
   - Role (publico, secs, admin)

2. **Estatísticas**:
   - Trechos RAG recuperados
   - Status do cache
   - Agente utilizado

3. **Controles**:
   - Toggle HyDE
   - Botão "Limpar Conversa"
   - Upload de documentos (se habilitado)

4. **Admin Panel** (só admin):
   - Gerenciar usuários
   - Ver auditoria
   - Configurar permissões

---

## 💬 Fazendo Perguntas

### Tipos de Perguntas Suportadas

#### 1. Sobre Pautas

```
✅ "Qual a pauta da próxima reunião?"
✅ "Mostre a pauta de abril de 2024"
✅ "Quais os itens da pauta 03/2024?"
```

**Resposta esperada**:
- Data e horário da reunião
- Local
- Ordem do dia (itens)
- Fonte citada (documento específico)

#### 2. Sobre Atas

```
✅ "Resumo da última ata"
✅ "Quem participou da reunião de março?"
✅ "O que foi aprovado na ata 02/2024?"
```

**Resposta esperada**:
- Participantes presentes
- Decisões tomadas
- Votações
- Fonte citada

#### 3. Sobre Resoluções

```
✅ "O que diz a resolução 024/2024?"
✅ "Resoluções sobre calendário acadêmico"
✅ "Última resolução aprovada"
```

#### 4. Sobre Regimentos

```
✅ "Como o conselho se reúne?"
✅ "Qual o quorum mínimo?"
✅ "O que diz o artigo 7 do regimento?"
```

**Com HyDE ativado**, perguntas sobre artigos específicos têm 85%+ de precisão!

### Exemplo Completo

**Pergunta**:
```
Qual a pauta da próxima reunião?
```

**Processamento** (visível na sidebar):
1. 🔍 Reescrita semântica ativa
2. 🤖 Agente: pauta
3. 📚 Trechos RAG: 5
4. ⚡ Cache: miss (primeira vez)

**Resposta**:
```
A próxima reunião do CONSUNI está agendada para 15 de maio de 2024, 
às 14h00, na Sala de Reuniões do CONSUNI.

Ordem do Dia:
1. Aprovação da ata da reunião anterior
2. Discussão sobre o calendário acadêmico 2024.2
3. Análise de proposta de novo curso de graduação
4. Assuntos gerais

📚 Fontes consultadas:
• Pauta da 4ª Reunião Ordinária - 2024 (87.3%)
• Ata da 3ª Reunião - 2024 (72.1%)
```

### Dicas para Melhores Respostas

✅ **Seja específico**:
- ❌ "Qual a pauta?"
- ✅ "Qual a pauta da próxima reunião do CONSUNI?"

✅ **Use palavras-chave**:
- "pauta", "ata", "resolução", "regimento"
- "CONSUNI", "CONSU", "UFAL"
- Números: "024/2024", "artigo 7"

✅ **Contexto temporal**:
- "última", "próxima", "de abril", "2024"

✅ **Ative HyDE** para perguntas sobre artigos específicos

---

## 📤 Upload de Documentos

### Passo 1: Acessar Upload

**Sidebar** → **"📤 Upload de Documentos"**

(Se não aparecer, verifique permissões com admin)

### Passo 2: Selecionar Arquivo

1. Clique em "Browse files"
2. Selecione PDF (máx 100MB por padrão)
3. Aguarde upload

### Passo 3: Configurar Documento

**Metadados**:
- **Tipo**: Pauta, Ata, Resolução, Regimento, Outro
- **Título**: Nome descritivo
- **Número**: Ex: "024/2024" (opcional)
- **Data**: Data do documento (opcional)
- **Conselho**: CONSUNI, CONSU, etc (opcional)

**Permissões** (só admin):
- ☐ Documento global (todos podem ver)
- ☑ Documento privado (só você vê)

### Passo 4: Processar

1. Clique em "Processar Documento"
2. Aguarde processamento (~30s para 10MB)
3. Veja progresso:
   - Extração de texto
   - Chunking (divisão em partes)
   - Geração de embeddings
   - Armazenamento

### Passo 5: Verificar

**Lista de Documentos** (abaixo do upload):
- ✅ Status: Processado
- 📄 Chunks: 45 (exemplo)
- 🌍 Badge: Global ou 🔒 Privado

### Exemplo Prático

**Cenário**: Upload de ata de reunião

1. **Arquivo**: `Ata_Reuniao_CONSUNI_05_2024.pdf` (2.3MB)
2. **Metadados**:
   - Tipo: Ata
   - Título: "Ata da 5ª Reunião Ordinária - 2024"
   - Número: "05/2024"
   - Data: "2024-06-15"
   - Conselho: "CONSUNI"
3. **Permissão**: ☑ Global (admin)
4. **Processar**: ~15 segundos
5. **Resultado**: 38 chunks criados

**Testar**:
```
Pergunta: "O que foi decidido na reunião de junho?"
Resposta: [Usa o documento recém-carregado]
```

### Quotas

- **Usuário comum**: 100MB / 50 documentos
- **Admin**: Ilimitado

Ver quota atual: **Sidebar** → **"📊 Quota"**

---

## 🔐 Permissões

### Tipos de Documentos

#### 1. Documentos Globais (🌍)

- **Visíveis para**: Todos os usuários
- **Quem pode criar**: Apenas admin
- **Exemplos**: Regimentos, resoluções oficiais, atas públicas

#### 2. Documentos Privados (🔒)

- **Visíveis para**: Apenas o dono
- **Quem pode criar**: Qualquer usuário
- **Exemplos**: Rascunhos, documentos pessoais

### Como Funciona

**Busca RAG**:
```
Usuário comum procura "pauta"
    ↓
Sistema busca:
  ✅ Documentos globais (todos)
  ✅ Documentos privados do usuário
  ❌ Documentos privados de outros
```

### Gerenciar Permissões (Admin)

**Admin Panel** → **"Permissões de Documentos"**

**Visualização**:
- Lista todos os documentos
- Filtros: Todos, Globais, Privados
- Por usuário

**Ações**:
1. **Toggle individual**: Clicar no badge 🌍/🔒
2. **Operações em massa**:
   - "Tornar todos globais"
   - "Tornar todos privados"

**Exemplo**:
```
Documento: "Ata Reunião 05/2024"
Dono: user123
Status atual: 🔒 Privado

Admin clica no badge → 🌍 Global
Agora todos podem ver!
```

---

## 🔬 HyDE (Busca Aprimorada)

### O Que É?

**HyDE** (Hypothetical Document Embeddings) melhora a busca gerando uma resposta hipotética e usando-a para encontrar documentos similares.

### Como Ativar

**Sidebar** → **"🔬 Recursos Experimentais"**  
☑ **HyDE (Busca Aprimorada)**

### Quando Usar?

✅ **Recomendado para**:
- Perguntas sobre artigos específicos
- Queries sobre regimentos
- Busca por informações estruturadas

❌ **Não necessário para**:
- Perguntas simples ("qual a pauta?")
- Busca por número de documento

### Exemplo Comparativo

**Pergunta**: "Como o conselho se reúne?"

**Sem HyDE**:
```
Busca: "como o conselho se reune?"
Resultado: 64% similaridade com Art. 7º
Resposta: Genérica, pode não citar artigo
```

**Com HyDE**:
```
Busca: "como o conselho se reune?"
    ↓
Hipótese gerada:
"O Conselho se reúne mediante convocação da Coordenação 
 ou por requerimento de metade dos membros, conforme 
 Art. 7º do Regimento..."
    ↓
Resultado: 87% similaridade com Art. 7º ✅
Resposta: Cita Art. 7º corretamente!
```

### Ver Hipótese Gerada

**Sidebar** → Expandir **"Ver hipótese gerada"**

Mostra:
- Análise de contexto
- Tipo de documento identificado
- Hipótese completa
- Confiança (0-100%)

### Performance

- **Melhoria**: +20-30% precisão
- **Custo**: +500ms latência (chamada LLM extra)
- **Vale a pena?**: SIM para queries complexas!

---

## ⚙️ Painel Administrativo

### Acessar

**Sidebar** → **"⚙️ Admin Panel"** (só admin)

### Funcionalidades

#### 1. Gerenciar Usuários

**Aba**: "Usuários"

**Visualizar**:
- Lista de todos os usuários
- Role de cada um
- Data de criação

**Ações**:
- Criar novo usuário
- Alterar role
- Resetar senha
- Desativar usuário

**Exemplo**:
```
Criar usuário:
1. Nome: "joao.silva"
2. Senha: "senha123"
3. Role: "secs"
4. Clicar "Criar"
```

#### 2. Auditoria

**Aba**: "Auditoria"

**Visualizar**:
- Todas as interações
- Filtros: Usuário, data, ação
- Busca por texto

**Informações**:
- Timestamp
- Usuário
- Ação (query, upload, etc)
- Detalhes (query text, documento, etc)

**Exemplo de busca**:
```
Filtro: user_id = "joao.silva"
Período: Última semana
Resultado: 47 interações
```

#### 3. Permissões de Documentos

**Aba**: "Permissões"

Veja seção [Permissões](#permissões) acima.

#### 4. Estatísticas

**Aba**: "Estatísticas"

**Métricas**:
- Total de documentos
- Documentos globais vs privados
- Total de chunks
- Armazenamento usado
- Queries por dia
- Cache hit rate

---

## 💡 Dicas e Truques

### 1. Use o Cache

O cache reduz 98% da latência!

**Como funciona**:
- Primeira pergunta: ~2-3s
- Mesma pergunta: ~50ms ✅

**Limpar cache**: Botão "Limpar Conversa"

### 2. Seja Específico

❌ "Qual a pauta?"  
✅ "Qual a pauta da próxima reunião do CONSUNI?"

### 3. Use Filtros Automáticos

O sistema detecta automaticamente:
- "pauta" → busca só em pautas
- "ata" → busca só em atas
- "resolução" → busca só em resoluções

### 4. Ative HyDE para Artigos

Para perguntas tipo "o que diz o artigo X?", ative HyDE!

### 5. Veja as Fontes

Sempre expanda **"📚 Fontes consultadas"** para ver:
- Documentos usados
- Similaridade (%)
- Verificar se resposta é confiável

### 6. Upload em Lote

Pode fazer upload de múltiplos PDFs:
1. Upload arquivo 1 → Processar
2. Upload arquivo 2 → Processar
3. Etc.

### 7. Organize por Metadados

Use metadados consistentes:
- Números: "001/2024", "002/2024"
- Datas: "2024-01-15"
- Conselhos: "CONSUNI", "CONSU"

Facilita buscas futuras!

---

## 🐛 Troubleshooting

### Problema 1: App Muito Lento

**Sintomas**:
- Demora >10s para responder
- Interface trava

**Soluções**:

1. **Verificar configuração** (.env):
```env
EMBEDDING_PROVIDER=openai  # Não "local"!
CACHE_ENABLED=true
LLM_MODEL=openrouter/google/gemini-flash-1.5
```

2. **Fechar outros apps**:
   - Navegador com muitas abas
   - Editores pesados
   - Etc.

3. **Limpar cache**:
   - Botão "Limpar Conversa"
   - Reiniciar app

### Problema 2: Erro ao Fazer Upload

**Sintomas**:
- "Erro ao processar documento"
- Upload trava

**Soluções**:

1. **Verificar tamanho**:
   - Máximo: 100MB (padrão)
   - Ver quota: Sidebar → "📊 Quota"

2. **Verificar formato**:
   - Só PDFs suportados
   - PDF deve ter texto (não só imagens)

3. **Verificar permissões**:
   - Pasta `data/documents/` deve existir
   - Permissões de escrita

### Problema 3: "Documento não encontrado"

**Sintomas**:
- Pergunta sobre documento recém-carregado
- Resposta: "Não encontrei informações"

**Soluções**:

1. **Verificar status**:
   - Lista de documentos
   - Status deve ser "✅ Processado"

2. **Aguardar processamento**:
   - Pode demorar ~30s
   - Ver barra de progresso

3. **Verificar permissões**:
   - Se documento é privado de outro usuário
   - Você não verá!

### Problema 4: HyDE Não Melhora

**Sintomas**:
- HyDE ativado mas resultados iguais

**Soluções**:

1. **Verificar tipo de pergunta**:
   - HyDE é melhor para artigos específicos
   - Não faz diferença em perguntas simples

2. **Ver hipótese gerada**:
   - Expandir "Ver hipótese"
   - Confiança deve ser >70%

3. **Limpar cache**:
   - Cache pode ter resposta antiga
   - Limpar e tentar novamente

### Problema 5: Erro de Memória

**Sintomas**:
- "MemoryError"
- App fecha sozinho

**Soluções**:

1. **Fechar outros apps**:
   ```bash
   # Ver uso de RAM
   free -h
   ```

2. **Verificar embeddings**:
   ```env
   # NUNCA use local em hardware modesto!
   EMBEDDING_PROVIDER=openai  # ← Correto
   ```

3. **Reduzir chunks**:
   ```env
   # Em config.py ou .env
   RAG_TOP_K=3  # Em vez de 5
   ```

---

## ❓ FAQs

### 1. Posso usar sem internet?

❌ Não. O sistema precisa de internet para:
- Embeddings via OpenRouter
- LLM via OpenRouter

### 2. Quanto custa usar?

**Custos** (OpenRouter):
- Embeddings: ~$0.0001 por documento
- LLM: ~$0.001 por query

**Com cache**: ~70% economia!

**Estimativa**: 1000 queries = ~$0.30

### 3. Quantos documentos posso carregar?

**Usuário comum**: 50 documentos / 100MB  
**Admin**: Ilimitado

### 4. Posso compartilhar documentos?

Sim! Admin pode tornar documento global:
- Upload → ☑ Documento global
- Ou: Admin Panel → Permissões → Toggle

### 5. Como deletar documento?

**Admin Panel** → **"Documentos"** → **"Deletar"**

(Usuários comuns não podem deletar)

### 6. HyDE sempre melhora?

Não. HyDE é melhor para:
- ✅ Artigos específicos
- ✅ Regimentos
- ✅ Informações estruturadas

Não faz diferença em:
- ❌ Perguntas simples
- ❌ Busca por número

### 7. Posso usar modelo local?

❌ Não recomendado para hardware modesto!

Celeron N3050 não tem potência para:
- Embeddings locais (2-4GB RAM)
- LLM local (impossível)

Use sempre OpenRouter.

### 8. Como melhorar precisão?

1. ✅ Ativar HyDE
2. ✅ Ser específico nas perguntas
3. ✅ Usar palavras-chave
4. ✅ Verificar fontes consultadas
5. ✅ Fazer upload de documentos relevantes

### 9. Posso integrar com outros sistemas?

Sim! Veja [MCP_SERVER.md](MCP_SERVER.md) para:
- Servidor MCP
- Integração com Claude Desktop
- API REST (futuro)

### 10. Como fazer backup?

**Backup manual**:
```bash
# Copiar banco de dados
cp data/app.db data/app.db.backup

# Copiar documentos
cp -r data/documents data/documents.backup
```

**Backup automático**: Em desenvolvimento