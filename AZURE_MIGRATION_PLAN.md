# 🚀 Plano Completo de Migração para Azure

## 📊 Arquitetura Azure Completa

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                            │
│            Azure Static Web App / App Service                │
│                  (React TypeScript)                          │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   API GATEWAY LAYER                          │
│            Azure API Management (Opcional)                   │
│               + Application Gateway                          │
└────────────────────┬────────────────────────────────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
     ▼               ▼               ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│Extract  │    │Validate │    │Summarize│
│Function │    │Function │    │ Function│
│         │    │         │    │         │
└────┬────┘    └────┬────┘    └────┬────┘
     │              │              │
     └──────────────┼──────────────┘
                    │
     ┌──────────────┼──────────────┐
     ▼              ▼              ▼
┌─────────┐   ┌──────────┐   ┌──────────┐
│ OpenAI  │   │ Cosmos   │   │  Blob    │
│ GPT-4o  │   │    DB    │   │ Storage  │
└─────────┘   └──────────┘   └──────────┘
                    │              │
                    │              │
              ┌─────┴──────┐  ┌───┴───┐
              │            │  │       │
              ▼            ▼  ▼       ▼
         Sessions    Promotions   Excel
         Messages    States       Files
```

---

## 🎯 Componentes da Arquitetura

### 1. **Frontend - Azure Static Web App**
- React + TypeScript (já existente em `/frontend`)
- Deploy automático via GitHub Actions
- CDN global integrado
- Custom domain + SSL grátis
- **Custo**: ~$0-9/mês

### 2. **Backend - Azure Functions** ✅ JÁ CRIADO
- ExtractorFunction
- ValidatorFunction
- SumarizerFunction
- **Plus**: ChatFunction (orquestrador)
- **Custo**: ~$0-20/mês (Consumption Plan)

### 3. **Database - Azure Cosmos DB**
**Substituir**: SQLite → Cosmos DB (API SQL/NoSQL)
- **Containers**:
  - `sessions` - Sessões de usuário
  - `messages` - Histórico de conversas
  - `promotions` - Promoções finalizadas
  - `promo_states` - Estados temporários
- **Custo**: ~$25-50/mês (Serverless/Autoscale)

### 4. **Storage - Azure Blob Storage**
**Substituir**: Arquivos locais → Blob Storage
- **Containers**:
  - `excel-exports` - Arquivos Excel gerados
  - `email-templates` - Templates HTML
  - `logs` - Logs do sistema
- **Custo**: ~$1-5/mês

### 5. **Secrets - Azure Key Vault**
- OPENAI_API_KEY
- COSMOS_DB_CONNECTION_STRING
- BLOB_STORAGE_CONNECTION_STRING
- **Custo**: ~$0.03/mês

### 6. **Monitoring - Application Insights**
- Logs centralizados
- Métricas de performance
- Alertas automáticos
- **Custo**: ~$2-10/mês

---

## 📦 Migração de Componentes

### BANCO DE DADOS: SQLite → Cosmos DB

#### Estrutura Atual (SQLite)
```sql
-- Tabela sessions
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT,
    last_activity TEXT
);

-- Tabela messages
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    user_message TEXT,
    ai_response TEXT,
    timestamp TEXT
);

-- Tabela promo_states
CREATE TABLE promo_states (
    session_id TEXT PRIMARY KEY,
    promo_id TEXT,
    state_data TEXT,
    status TEXT,
    created_at TEXT,
    updated_at TEXT
);

-- Tabela promotions
CREATE TABLE promotions (
    id INTEGER PRIMARY KEY,
    promo_id TEXT UNIQUE,
    titulo TEXT,
    mecanica TEXT,
    ... (15+ campos)
);
```

#### Nova Estrutura (Cosmos DB)

**Container: sessions**
```json
{
  "id": "session_20251106_123456",
  "partitionKey": "session",
  "created_at": "2025-11-06T12:34:56Z",
  "last_activity": "2025-11-06T12:45:00Z",
  "user_agent": "Mozilla/5.0...",
  "ttl": 86400
}
```

**Container: messages**
```json
{
  "id": "msg_uuid",
  "partitionKey": "session_20251106_123456",
  "session_id": "session_20251106_123456",
  "user_message": "Quero criar uma promoção...",
  "ai_response": "Ótimo! Me conte mais sobre...",
  "timestamp": "2025-11-06T12:35:00Z",
  "ttl": 2592000
}
```

**Container: promo_states** (estados temporários)
```json
{
  "id": "session_20251106_123456",
  "partitionKey": "active",
  "promo_id": "promo_20251106_123456",
  "status": "collecting",
  "completion": 45,
  "data": {
    "titulo": "Compre Mais Ganhe Mais",
    "mecanica": "progressiva",
    "descricao": "...",
    "segmentacao": "...",
    ...
  },
  "created_at": "2025-11-06T12:34:56Z",
  "updated_at": "2025-11-06T12:40:00Z",
  "ttl": 604800
}
```

**Container: promotions** (finalizadas)
```json
{
  "id": "promo_20251106_123456",
  "partitionKey": "2025-11",
  "session_id": "session_20251106_123456",
  "titulo": "Compre Mais Ganhe Mais",
  "mecanica": "progressiva",
  "descricao": "A cada 10 caixas...",
  "segmentacao": "Pequenos varejistas",
  "periodo_inicio": "2025-12-01",
  "periodo_fim": "2025-12-31",
  "condicoes": "Válido para compras...",
  "recompensas": "5% a 10% de desconto",
  "produtos": ["Refrigerantes", "Sucos"],
  "categorias": ["Bebidas"],
  "volume_minimo": "10 caixas",
  "desconto_percentual": "5%;10%",
  "status": "completed",
  "excel_blob_url": "https://.../excel-exports/promo_123.xlsx",
  "created_at": "2025-11-06T12:34:56Z",
  "sent_at": "2025-11-06T13:00:00Z"
}
```

---

### STORAGE: Arquivos Locais → Blob Storage

#### Atual (Local)
```
exports/
├── promocao_compre_mais_20251106_123456.xlsx
├── promocao_lista_20251106_140000.xlsx
└── ...
```

#### Novo (Azure Blob)
```
Container: excel-exports/
├── 2025/11/06/promo_20251106_123456.xlsx
├── 2025/11/06/promo_20251106_140000.xlsx
└── ...

Container: email-templates/
├── default_template.html
├── vip_template.html
└── ...
```

---

## 🔧 Implementação - Passo a Passo

### FASE 1: Criar Recursos Azure (Azure CLI)

```bash
# Variáveis
RESOURCE_GROUP="PromoAgenteRG"
LOCATION="brazilsouth"
FUNCTION_APP="promoagente-functions"
STORAGE_ACCOUNT="promoagentestorage"
COSMOSDB_ACCOUNT="promoagente-cosmos"
KEYVAULT_NAME="promoagente-vault"
STATIC_WEB_APP="promoagente-frontend"

# 1. Resource Group
az group create --name $RESOURCE_GROUP --location $LOCATION

# 2. Storage Account (para Functions + Blobs)
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# 3. Cosmos DB (Serverless)
az cosmosdb create \
  --name $COSMOSDB_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --locations regionName=$LOCATION \
  --capabilities EnableServerless

# Criar database
az cosmosdb sql database create \
  --account-name $COSMOSDB_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --name PromoAgente

# Criar containers
az cosmosdb sql container create \
  --account-name $COSMOSDB_ACCOUNT \
  --database-name PromoAgente \
  --name sessions \
  --partition-key-path "/partitionKey" \
  --resource-group $RESOURCE_GROUP

az cosmosdb sql container create \
  --account-name $COSMOSDB_ACCOUNT \
  --database-name PromoAgente \
  --name messages \
  --partition-key-path "/session_id" \
  --resource-group $RESOURCE_GROUP

az cosmosdb sql container create \
  --account-name $COSMOSDB_ACCOUNT \
  --database-name PromoAgente \
  --name promo_states \
  --partition-key-path "/partitionKey" \
  --resource-group $RESOURCE_GROUP

az cosmosdb sql container create \
  --account-name $COSMOSDB_ACCOUNT \
  --database-name PromoAgente \
  --name promotions \
  --partition-key-path "/partitionKey" \
  --resource-group $RESOURCE_GROUP

# 4. Key Vault
az keyvault create \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# 5. Function App (Consumption Plan)
az functionapp create \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.11 \
  --storage-account $STORAGE_ACCOUNT \
  --os-type Linux \
  --functions-version 4

# 6. Static Web App (Frontend)
az staticwebapp create \
  --name $STATIC_WEB_APP \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

---

### FASE 2: Criar Adapters para Cosmos DB

Vou criar arquivo: `shared/adapters/cosmos_adapter.py`

### FASE 3: Criar Adapters para Blob Storage

Vou criar arquivo: `shared/adapters/blob_adapter.py`

### FASE 4: Atualizar Functions

Adaptar ExtractorFunction, ValidatorFunction, SumarizerFunction

### FASE 5: Deploy Frontend

Configurar CI/CD para Static Web App

---

## 💰 Estimativa de Custos

| Serviço | Plano | Custo Mensal (USD) |
|---------|-------|-------------------|
| **Azure Functions** | Consumption | $0-20 |
| **Cosmos DB** | Serverless | $25-50 |
| **Blob Storage** | Standard | $1-5 |
| **Static Web App** | Standard | $9 |
| **Key Vault** | Standard | $0.03 |
| **Application Insights** | Pay-as-you-go | $2-10 |
| **TOTAL** | | **$37-94/mês** |

**Comparado com Railway/Docker**: $20-40/mês
**Vantagens**: Escalabilidade ilimitada + Infraestrutura gerenciada

---

## 📈 Benefícios da Migração

### ✅ Escalabilidade
- Auto-scaling em todos os componentes
- Suporta milhares de usuários simultâneos
- CDN global no frontend

### ✅ Confiabilidade
- SLA 99.95% (Azure Functions)
- SLA 99.99% (Cosmos DB)
- Backups automáticos
- Disaster recovery

### ✅ Performance
- Cosmos DB: < 10ms latência
- Blob Storage: Download ultra-rápido
- Functions: Execução paralela

### ✅ Segurança
- Managed Identity
- Key Vault para secrets
- HTTPS everywhere
- Network isolation

### ✅ Manutenção
- Zero administração de servidores
- Updates automáticos
- Monitoring integrado

---

## 🚀 Timeline de Implementação

### Semana 1: Preparação
- ✅ Criar recursos Azure
- ✅ Configurar Cosmos DB
- ✅ Configurar Blob Storage
- ✅ Configurar Key Vault

### Semana 2: Backend
- ⏳ Implementar adapters (Cosmos + Blob)
- ⏳ Migrar Functions existentes
- ⏳ Criar ChatFunction (orquestrador)
- ⏳ Testes locais

### Semana 3: Frontend
- ⏳ Atualizar API client
- ⏳ Configurar Static Web App
- ⏳ CI/CD GitHub Actions
- ⏳ Deploy produção

### Semana 4: Migração de Dados
- ⏳ Exportar dados SQLite
- ⏳ Importar para Cosmos DB
- ⏳ Migrar arquivos Excel para Blob
- ⏳ Validação final

---

## 📝 Próximos Arquivos a Criar

1. `shared/adapters/cosmos_adapter.py` - Adapter Cosmos DB
2. `shared/adapters/blob_adapter.py` - Adapter Blob Storage
3. `functions/ChatFunction/` - Orquestrador completo
4. `shared/models/` - Modelos de dados
5. `.github/workflows/azure-deploy.yml` - CI/CD completo

---

**Desenvolvido por**: Elaine Barros  
**Projeto**: PromoAgente Azure Migration  
**Versão**: 3.0.0 Full Azure Stack
