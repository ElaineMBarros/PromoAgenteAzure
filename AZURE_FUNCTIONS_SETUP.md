# 🚀 Setup Python 3.11 e Migração para Azure Functions

## 📋 Guia Completo para Preparação do Ambiente

---

## 🐍 PASSO 1: Criar Ambiente Python 3.11 com Conda

### Criar novo ambiente
```bash
# Criar ambiente com Python 3.11
conda create -n promoagente-azure python=3.11 -y

# Ativar o ambiente
conda activate promoagente-azure

# Verificar versão
python --version
# Deve mostrar: Python 3.11.x
```

### Instalar dependências do projeto
```bash
# Atualizar pip
pip install --upgrade pip

# Instalar dependências
pip install -r requirements.txt

# Instalar Azure Functions Core Tools (via pip)
pip install azure-functions azure-functions-core-tools
```

---

## ☁️ PASSO 2: Instalar Azure Functions Core Tools

### Windows (usando Chocolatey)
```bash
# Se não tem Chocolatey, instale primeiro:
# https://chocolatey.org/install

choco install azure-functions-core-tools-4 -y
```

### Ou usar npm
```bash
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

### Verificar instalação
```bash
func --version
# Deve mostrar: 4.x.x
```

---

## 📦 PASSO 3: Atualizar Dependências para Azure Functions

### requirements.txt atualizado
Já preparado para Azure Functions Python 3.11:
```
# Azure Functions
azure-functions>=1.18.0

# Core AI Framework
agno==2.1.9
openai==1.40.0

# Web Framework (para desenvolvimento local)
fastapi==0.110.0
uvicorn==0.24.0

# Utilities
python-dotenv==1.0.0
aiosqlite==0.19.0
sqlalchemy==2.0.23
httpx<0.28

# Templates and Forms
jinja2==3.1.2
python-multipart==0.0.6

# Excel Generation
openpyxl==3.1.2

# Azure Storage (opcional, para persistência)
azure-storage-blob>=12.19.0
```

---

## 🏗️ PASSO 4: Estrutura de Azure Functions Serverless

### Arquitetura proposta:

```
PromoAgenteAzure/
├── functions/                          # Azure Functions
│   ├── ExtractorFunction/             # Function para extração
│   │   ├── __init__.py
│   │   └── function.json
│   ├── ValidatorFunction/             # Function para validação
│   │   ├── __init__.py
│   │   └── function.json
│   ├── SumarizerFunction/             # Function para resumos
│   │   ├── __init__.py
│   │   └── function.json
│   └── OrchestratorFunction/          # Function orquestradora
│       ├── __init__.py
│       └── function.json
├── shared/                            # Código compartilhado
│   ├── models/
│   │   └── promo_state.py
│   ├── utils/
│   │   └── helpers.py
│   └── config/
│       └── settings.py
├── host.json                          # Configuração do Function App
├── local.settings.json                # Configurações locais
├── requirements.txt                   # Dependências
└── .funcignore                       # Arquivos ignorados no deploy
```

---

## 📝 PASSO 5: Criar Configuração do Azure Functions

Vou criar os arquivos necessários automaticamente.

---

## 🔐 PASSO 6: Configurar Variáveis de Ambiente

### local.settings.json (desenvolvimento local)
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "OPENAI_API_KEY": "sua-chave-aqui",
    "OPENAI_MODEL": "gpt-4o-mini",
    "ENVIRONMENT": "development"
  }
}
```

### No Azure Portal (produção)
- Configuration > Application settings
- Adicionar as mesmas variáveis

---

## 🧪 PASSO 7: Testar Localmente

### Iniciar Azure Functions localmente
```bash
# Ativar ambiente conda
conda activate promoagente-azure

# Navegar para pasta do projeto
cd PromoAgenteAzure

# Iniciar Functions runtime
func start
```

### Testar endpoints
```bash
# Extractor Function
curl -X POST http://localhost:7071/api/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "Quero criar uma promoção progressiva"}'

# Validator Function
curl -X POST http://localhost:7071/api/validate \
  -H "Content-Type: application/json" \
  -d '{"promo_data": {...}}'
```

---

## 🚀 PASSO 8: Deploy para Azure

### Usando Azure CLI
```bash
# Login no Azure
az login

# Criar Resource Group
az group create --name PromoAgenteRG --location brazilsouth

# Criar Storage Account
az storage account create \
  --name promoagentestorage \
  --resource-group PromoAgenteRG \
  --location brazilsouth

# Criar Function App
az functionapp create \
  --name promoagente-functions \
  --resource-group PromoAgenteRG \
  --consumption-plan-location brazilsouth \
  --runtime python \
  --runtime-version 3.11 \
  --storage-account promoagentestorage \
  --os-type Linux

# Deploy
func azure functionapp publish promoagente-functions
```

---

## 💡 VANTAGENS da Arquitetura Serverless

✅ **Escalabilidade Automática**
- Cada função escala independentemente
- Paga apenas pelo uso

✅ **Manutenção Simplificada**
- Agents isolados
- Fácil debug e atualização

✅ **Performance**
- Execução paralela
- Cold start otimizado no Python 3.11

✅ **Custo-Efetivo**
- Modelo de consumo
- Ideal para workloads variáveis

---

## 🔄 MIGRAÇÃO dos Agents para Functions

### ExtractorFunction
```python
import azure.functions as func
from src.agents.extractor import ExtractorAgent

async def main(req: func.HttpRequest) -> func.HttpResponse:
    # Lógica da função
    text = req.get_json().get('text')
    result = await extractor.extract(text)
    return func.HttpResponse(json.dumps(result), mimetype="application/json")
```

### OrchestratorFunction (Durable Functions)
- Usa Durable Functions para orquestração
- Mantém estado entre chamadas
- Coordena chamadas aos outros agents

---

## 📊 Monitoramento

### Application Insights
- Logs automáticos
- Métricas de performance
- Alertas personalizados

### Configurar no Azure
```bash
az monitor app-insights component create \
  --app promoagente-insights \
  --location brazilsouth \
  --resource-group PromoAgenteRG
```

---

## 🎯 PRÓXIMOS PASSOS

1. ✅ Criar ambiente Python 3.11
2. ✅ Instalar Azure Functions Core Tools
3. ⏳ Criar estrutura de Functions
4. ⏳ Migrar agents para Functions
5. ⏳ Testar localmente
6. ⏳ Deploy para Azure
7. ⏳ Configurar CI/CD

---

## 📚 Referências

- [Azure Functions Python Developer Guide](https://docs.microsoft.com/azure/azure-functions/functions-reference-python)
- [Azure Functions Python 3.11 Support](https://docs.microsoft.com/azure/azure-functions/supported-languages)
- [Durable Functions](https://docs.microsoft.com/azure/azure-functions/durable/)

---

**Desenvolvido por**: Elaine Barros
**Projeto**: PromoAgente Azure Functions Migration
**Data**: Novembro 2025
