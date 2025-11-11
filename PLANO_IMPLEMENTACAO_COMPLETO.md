# 🚀 PLANO DE IMPLEMENTAÇÃO COMPLETO - Azure Functions

## ✅ **O QUE JÁ FOI FEITO**

### **Frontend:**
- ✅ StatusBar atualizado (Azure OpenAI + Cosmos DB)
- ✅ Tipos TypeScript ajustados
- ✅ Build e deploy no Azure Static Web App

### **Backend:**
- ✅ ChatFunction básica funcionando
- ✅ Azure OpenAI Service integrado
- ✅ Prompt persona.md carregado
- ✅ 4 Functions criadas (Chat, Extract, Validate, Summarize)

### **Infraestrutura:**
- ✅ Cosmos DB provisionado
- ✅ Blob Storage provisionado
- ✅ Adapters criados (cosmos_adapter.py, blob_adapter.py)

---

## 🎯 **O QUE FALTA IMPLEMENTAR**

### **1. StatusFunction** ⏱️ 30 min
Criar `/api/status` para retornar saúde do sistema

**Arquivos:**
- `StatusFunction/__init__.py`
- `StatusFunction/function.json`

**Retorna:**
```json
{
  "system_ready": true,
  "openai": true,
  "openai_model": "gpt-4o-mini",
  "cosmos_db": true,
  "blob_storage": true,
  "messages_stored": 0,
  "promotions_count": 0,
  "environment": "azure"
}
```

---

### **2. ChatFunction com Cosmos DB** ⏱️ 2-3h

**Adicionar:**
- Salvar mensagens no Cosmos DB
- Carregar histórico da conversa
- Manter contexto entre mensagens
- Detectar quando promoção está completa

**Mudanças:**
```python
# Inicializar Cosmos
from shared.adapters.cosmos_adapter import CosmosAdapter
cosmos = CosmosAdapter()

# Carregar histórico
history = await cosmos.get_conversation_history(session_id)

# Montar contexto completo para OpenAI
messages = [system_prompt] + history + [user_message]

# Salvar mensagens
await cosmos.save_message(session_id, user_message)
await cosmos.save_message(session_id, ai_response)

# Detectar promoção completa
if "✅ Dados registrados" in response:
    await cosmos.save_promotion(session_id, extracted_data)
```

---

### **3. ExportFunction** ⏱️ 2-3h

Criar `/api/export` para gerar Excel

**Arquivos:**
- `ExportFunction/__init__.py`
- `ExportFunction/function.json`
- Copiar `src/services/excel_service.py` para `shared/services/`

**Fluxo:**
1. Recebe `session_id`
2. Busca promoções no Cosmos DB
3. Gera arquivo Excel
4. Salva no Blob Storage
5. Retorna URL para download

**Código:**
```python
# Buscar promoções
promotions = await cosmos.get_promotions(session_id)

# Gerar Excel
from shared.services.excel_service import generate_excel
excel_file = generate_excel(promotions)

# Upload para Blob
from shared.adapters.blob_adapter import BlobAdapter
blob = BlobAdapter()
file_url = await blob.upload(excel_file, f"{session_id}.xlsx")

return {"file_url": file_url}
```

---

### **4. Adapters - Implementar Métodos** ⏱️ 1-2h

**cosmos_adapter.py precisa:**
```python
async def save_message(session_id, message)
async def get_conversation_history(session_id)
async def save_promotion(session_id, promo_data)
async def get_promotions(session_id)
async def get_promo_state(session_id)
async def save_promo_state(session_id, state)
```

**blob_adapter.py precisa:**
```python
async def upload(file_data, filename)
async def get_url(filename)
async def delete(filename)
```

---

### **5. Frontend - Ajustes Finais** ⏱️ 1h

**Adicionar:**
- Botão "Gerar Excel" quando promoção finalizada
- Download automático do Excel
- Melhorar formatação de mensagens
- Adicionar ícones

---

## 📋 **ORDEM DE IMPLEMENTAÇÃO**

### **Fase 1: Infraestrutura** (2h)
1. ✅ Ajustar frontend (FEITO)
2. ⏳ Criar StatusFunction
3. ⏳ Implementar métodos nos Adapters
4. ⏳ Testar conexões (Cosmos DB + Blob)

### **Fase 2: Persistência** (3h)
1. ⏳ ChatFunction com Cosmos DB
2. ⏳ Salvar mensagens
3. ⏳ Carregar histórico
4. ⏳ Manter contexto
5. ⏳ Testar conversas longas

### **Fase 3: Export** (3h)
1. ⏳ Criar ExportFunction
2. ⏳ Integrar excel_service
3. ⏳ Upload para Blob Storage
4. ⏳ Retornar URL
5. ⏳ Testar download

### **Fase 4: Integration** (2h)
1. ⏳ Frontend chama /api/export
2. ⏳ Botão download Excel
3. ⏳ Melhorar UI
4. ⏳ Testes end-to-end

**TOTAL ESTIMADO: 10-12 horas**

---

## 🔧 **COMEÇANDO AGORA**

### **Passo 1: Criar StatusFunction**

```bash
# Criar pasta
mkdir StatusFunction

# Arquivos necessários
StatusFunction/__init__.py
StatusFunction/function.json
```

**Código StatusFunction/__init__.py:**
```python
import azure.functions as func
import json
import os

async def main(req: func.HttpRequest) -> func.HttpResponse:
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }
    
    if req.method == 'OPTIONS':
        return func.HttpResponse("", status_code=200, headers=headers)
    
    # Verificar serviços
    openai_ok = bool(os.environ.get("AZURE_OPENAI_API_KEY"))
    cosmos_ok = bool(os.environ.get("COSMOS_ENDPOINT"))
    blob_ok = bool(os.environ.get("AZURE_STORAGE_CONNECTION_STRING"))
    
    status = {
        "system_ready": openai_ok and cosmos_ok,
        "openai": openai_ok,
        "openai_model": "gpt-4o-mini",
        "cosmos_db": cosmos_ok,
        "blob_storage": blob_ok,
        "messages_stored": 0,
        "promotions_count": 0,
        "environment": "azure"
    }
    
    return func.HttpResponse(
        json.dumps(status),
        status_code=200,
        headers=headers
    )
```

**function.json:**
```json
{
  "scriptFile": "__init__.py",
  "bindings": [
    {
      "authLevel": "anonymous",
      "type": "httpTrigger",
      "direction": "in",
      "name": "req",
      "methods": ["get", "options"],
      "route": "status"
    },
    {
      "type": "http",
      "direction": "out",
      "name": "$return"
    }
  ]
}
```

---

## 📦 **ARQUIVOS QUE VOU CRIAR/MODIFICAR**

### **Novos:**
```
StatusFunction/
  __init__.py
  function.json

ExportFunction/
  __init__.py
  function.json

shared/services/
  excel_service.py
```

### **Modificar:**
```
ChatFunction/__init__.py          (adicionar Cosmos DB)
shared/adapters/cosmos_adapter.py (implementar métodos)
shared/adapters/blob_adapter.py   (implementar métodos)
frontend/ (build e redeploy)
```

---

## 🎯 **PRIORIDADES**

### **Alta (Essencial):**
1. StatusFunction
2. ChatFunction com Cosmos DB
3. Salvar/Carregar histórico

### **Média (Importante):**
4. ExportFunction
5. Adapters completos
6. Frontend melhorias

### **Baixa (Nice to have):**
7. Ícones frontend
8. Animações
9. Melhorias UX

---

## ✅ **CRITÉRIOS DE SUCESSO**

**A aplicação estará completa quando:**

- [ ] `/api/status` retorna info correta
- [ ] Chat salva mensagens no Cosmos DB
- [ ] Chat mantém histórico da conversa
- [ ] Chat extrai dados das promoções
- [ ] `/api/export` gera Excel
- [ ] Excel é salvo no Blob Storage
- [ ] Frontend baixa o Excel
- [ ] Tudo funciona end-to-end

---

## 🚀 **PRÓXIMA AÇÃO**

**Posso começar agora criando:**

1. **StatusFunction** (30 min)
2. **Implementar cosmos_adapter** (1h)
3. **Atualizar ChatFunction** (2h)
4. **Criar ExportFunction** (2h)
5. **Testar tudo** (1h)

**Total: ~6-7 horas de trabalho**

**Quer que eu comece?** 

Posso fazer em etapas, testando cada uma antes de continuar.

---

**Última atualização:** 06/11/2025 19:42  
**Status:** Pronto para começar implementação  
**Próximo:** Criar StatusFunction
