# 🏗️ ARQUITETURA AZURE FUNCTIONS - PromoAgente

## 📚 O QUE É AZURE FUNCTIONS?

Azure Functions é um serviço de **computação serverless** que permite executar código sob demanda sem precisar gerenciar infraestrutura.

### 🎯 Conceitos Fundamentais:

1. **Function App** = Container de múltiplas Functions
   - `promoagente-func` (nosso Function App)
   
2. **Function** = Função individual com trigger específico
   - Cada function é uma pasta na raiz do projeto
   - Tem seu próprio `__init__.py` e `function.json`

3. **Trigger** = Evento que inicia a function
   - HTTP Trigger (nosso caso)
   - Timer, Queue, Blob, etc.

---

## 🤔 UMA FUNCTION OU VÁRIAS?

### **OPÇÃO A: UMA ÚNICA FUNCTION (Monolítica)**

```
/ChatFunction/
  __init__.py  ← Contém TUDO (orchestrator + agents)
  function.json
```

**Vantagens:**
- ✅ Mais simples de deployar
- ✅ Compartilha memória entre agentes
- ✅ Menos cold starts

**Desvantagens:**
- ❌ Difícil escalar componentes individualmente
- ❌ Se um agente falha, todos param
- ❌ Dificulta debug e logs específicos
- ❌ Não aproveita arquitetura serverless

---

### **OPÇÃO B: MULTIPLE FUNCTIONS (Microservices)** ⭐ **RECOMENDADO**

```
/OrchestratorFunction/    ← Coordena tudo
  __init__.py
  function.json

/ExtractorFunction/       ← Extrai dados
  __init__.py
  function.json

/ValidatorFunction/       ← Valida promoção
  __init__.py
  function.json

/SumarizerFunction/       ← Cria resumo
  __init__.py
  function.json
```

**Vantagens:**
- ✅ **Escalabilidade independente**: Extractor pode ter mais instâncias que Validator
- ✅ **Isolamento**: Falha em um não afeta outros
- ✅ **Logs específicos**: Cada agent tem seus logs
- ✅ **Deploy independente**: Atualiza só o que mudou
- ✅ **Custos otimizados**: Paga só pelo que usa
- ✅ **Timeout individual**: Extractor pode ter 5min, Validator 2min

**Desvantagens:**
- ❌ Mais complexo de implementar
- ❌ Pouco mais cold starts (mas gerenciável)

---

## ✅ NOSSA ESCOLHA: MICROSERVICES

Vamos usar **OPÇÃO B** porque:

1. **Extractor é pesado** (processa prompts grandes)
2. **Validator e Sumarizer são leves** (chamadas rápidas)
3. **Orchestrator coordena** tudo de forma assíncrona
4. Permite **escalar só o que precisa**

---

## 🗂️ ESTRUTURA ATUAL DO PROJETO

```
PromoAgenteAzure/
│
├── ChatFunction/              ← ❌ Antiga (chat direto)
├── StatusFunction/            ← ✅ Status da aplicação
├── ExtractorFunction/         ← ⚠️ Precisa atualizar
├── ValidatorFunction/         ← ⚠️ Precisa atualizar
├── SumarizerFunction/         ← ⚠️ Precisa atualizar
│
├── OrchestratorFunction/      ← ❌ FALTA CRIAR
│
├── prompts/                   ← ✅ Prompts existem
│   ├── persona.md
│   ├── extraction.md
│   ├── validation.md
│   └── summarization.md
│
├── shared/                    ← ✅ Código compartilhado
│   ├── adapters/
│   │   ├── cosmos_adapter.py
│   │   └── blob_adapter.py
│   └── utils/                 ← ❌ CRIAR para carregar prompts
│
└── src/                       ← Código local (não usado no Azure)
```

---

## 🔄 FLUXO DE EXECUÇÃO

### **Como as Functions se comunicam:**

```
Frontend
   ↓ POST /api/orchestrator
OrchestratorFunction
   ├─→ POST /api/extract       (ExtractorFunction)
   ├─→ POST /api/validate      (ValidatorFunction)
   └─→ POST /api/summarize     (SumarizerFunction)
   ↓ Salva no Cosmos DB
   ↓ Retorna para Frontend
```

### **Fluxo Detalhado:**

1. **Frontend** envia mensagem para `/api/orchestrator`
2. **OrchestratorFunction**:
   - Carrega estado do Cosmos DB
   - Decide qual agente chamar
3. **ExtractorFunction**:
   - Carrega `extraction.md`
   - Processa com OpenAI
   - Retorna dados estruturados
4. **ValidatorFunction**:
   - Carrega `validation.md`
   - Valida dados
   - Retorna OK/Erros
5. **SumarizerFunction**:
   - Carrega `summarization.md`
   - Cria resumo
   - Retorna texto formatado
6. **OrchestratorFunction**:
   - Salva tudo no Cosmos DB
   - Retorna resposta final

---

## 📁 COMO INTEGRAR OS PROMPTS

### **Criar Utilitário Compartilhado:**

```python
# shared/utils/prompt_loader.py
import os
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"

def load_prompt(prompt_name: str) -> str:
    """Carrega um prompt .md"""
    prompt_path = PROMPTS_DIR / f"{prompt_name}.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt não encontrado: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_extraction_prompt() -> str:
    return load_prompt("extraction")

def get_validation_prompt() -> str:
    return load_prompt("validation")

def get_summarization_prompt() -> str:
    return load_prompt("summarization")

def get_persona_prompt() -> str:
    return load_prompt("persona")
```

### **Usar nas Functions:**

```python
# ExtractorFunction/__init__.py
import azure.functions as func
from shared.utils.prompt_loader import get_extraction_prompt
from openai import OpenAI

async def main(req: func.HttpRequest) -> func.HttpResponse:
    # Carrega prompt
    extraction_prompt = get_extraction_prompt()
    
    # Usa com OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": extraction_prompt},
            {"role": "user", "content": user_message}
        ]
    )
    
    return func.HttpResponse(response.choices[0].message.content)
```

---

## 📦 O QUE SERÁ DEPLOYADO

Cada function vai para o Azure com:

1. **Código Python** (`__init__.py`)
2. **Configuração** (`function.json`)
3. **Dependências** (compartilhadas via `requirements.txt`)
4. **Prompts** (pasta `/prompts` inteira)
5. **Utilitários** (pasta `/shared`)

### **Deploy é único:**
```bash
# Deploy de TODAS as functions de uma vez
func azure functionapp publish promoagente-func
```

Azure detecta TODAS as pastas na raiz com `function.json` e deploya automaticamente!

---

## 🎯 PLANO DE AÇÃO

### **FASE 1: Estrutura**
- [x] Requirements.txt atualizado com python-dateutil
- [ ] Criar `shared/utils/prompt_loader.py`
- [ ] Criar `OrchestratorFunction/` na raiz
- [ ] Atualizar `ExtractorFunction/`
- [ ] Atualizar `ValidatorFunction/`
- [ ] Atualizar `SumarizerFunction/`

### **FASE 2: Código**
- [ ] Implementar OrchestratorFunction com lógica completa
- [ ] Integrar prompts em cada agent function
- [ ] Implementar comunicação entre functions
- [ ] Adicionar tratamento de erros

### **FASE 3: Testes Locais**
- [ ] Testar cada function individualmente
- [ ] Testar fluxo completo orquestrado
- [ ] Validar carregamento de prompts

### **FASE 4: Deploy**
- [ ] Configurar OpenAI Key no Azure Portal
- [ ] Deploy único de todas as functions
- [ ] Testar no Azure
- [ ] Atualizar frontend para usar novo endpoint

---

## 💰 CUSTOS ESTIMADOS

### **Com Microservices:**
- OrchestratorFunction: ~1000 execuções/mês = $0.20
- ExtractorFunction: ~1000 execuções/mês = $0.40 (mais pesado)
- ValidatorFunction: ~800 execuções/mês = $0.16
- SumarizerFunction: ~800 execuções/mês = $0.16

**Total Functions: ~$0.92/mês** (quase grátis!)

Custo real vem de:
- OpenAI API: $10-30/mês
- Cosmos DB: $25-40/mês
- Storage: $1-2/mês

---

## 🔧 CONFIGURAÇÃO NECESSÁRIA

### **No Azure Portal:**

1. **Function App → Configuration → Application Settings:**
   ```
   OPENAI_API_KEY = sua-chave-aqui
   COSMOS_CONNECTION_STRING = ...
   BLOB_CONNECTION_STRING = ...
   ```

2. **Function App → CORS:**
   - Adicionar URL do frontend

3. **Cosmos DB:**
   - Database: `promoagente`
   - Containers:
     - `promo_states`
     - `promo_history`
     - `sessions`

---

## 📊 MONITORAMENTO

Cada function gera logs separados em **Application Insights**:

```
OrchestratorFunction → logs próprios
ExtractorFunction → logs próprios
ValidatorFunction → logs próprios
SumarizerFunction → logs próprios
```

Facilita debug e análise de performance!

---

## 🚀 PRÓXIMO PASSO

Vamos implementar:
1. `shared/utils/prompt_loader.py`
2. `OrchestratorFunction/` completa
3. Atualizar agents functions

**Pronto para começar?**
