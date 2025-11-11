# 🔧 Instalação do Azure CLI e Validação

## 📦 Opção 1: Instalar Azure CLI (Recomendado)

### Windows - MSI Installer

**Método mais fácil:**
1. Baixe o instalador MSI: https://aka.ms/installazurecliwindows
2. Execute o instalador
3. Reinicie o terminal/PowerShell
4. Verifique: `az --version`

### Windows - Chocolatey

```bash
choco install azure-cli -y
```

### Windows - Winget

```bash
winget install -e --id Microsoft.AzureCLI
```

---

## ✅ Após Instalação - Login

```bash
# Login no Azure
az login

# Verificar conta atual
az account show

# Listar subscriptions
az account list --output table

# Selecionar subscription específica
az account set --subscription "Nome-ou-ID-da-Subscription"
```

---

## 🔍 Opção 2: Validação Manual (Sem Azure CLI)

Se não puder instalar o Azure CLI agora, você pode validar manualmente:

### 1. Portal Azure (portal.azure.com)

**Passos:**
1. Acesse https://portal.azure.com
2. Login com suas credenciais
3. No menu lateral, clique em "Resource groups"
4. Encontre seu Resource Group de IA
5. Clique nele para ver os recursos disponíveis

**Anote:**
- Nome do Resource Group
- Recursos disponíveis (OpenAI, Storage, Cosmos DB, etc.)
- Localização (Brazil South, East US, etc.)

---

### 2. Configurar local.settings.json Manualmente

Com as informações do Portal, configure seu `local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    
    "OPENAI_API_KEY": "sua-chave-openai-aqui",
    "OPENAI_MODEL": "gpt-4o-mini",
    
    "COSMOS_DB_ENDPOINT": "https://SEU-COSMOS-ACCOUNT.documents.azure.com:443/",
    "COSMOS_DB_KEY": "sua-cosmos-primary-key-aqui",
    
    "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;AccountName=SEU-STORAGE;AccountKey=SUA-KEY;EndpointSuffix=core.windows.net",
    
    "ENVIRONMENT": "development",
    "DEBUG": "True"
  }
}
```

---

## 📋 Como Obter as Credenciais no Portal Azure

### OpenAI API Key

**Se usando Azure OpenAI:**
1. Portal Azure > Resource Groups > Seu RG
2. Clique no recurso "Azure OpenAI"
3. Menu lateral: Keys and Endpoint
4. Copie "KEY 1" e "Endpoint"

**Se usando OpenAI direto:**
- Use sua chave da OpenAI: https://platform.openai.com/api-keys

---

### Cosmos DB Connection

1. Portal Azure > Resource Groups > Seu RG
2. Clique no recurso "Cosmos DB"
3. Menu lateral: Keys
4. Copie:
   - URI (endpoint)
   - PRIMARY KEY (key)

---

### Storage Account Connection

1. Portal Azure > Resource Groups > Seu RG
2. Clique no recurso "Storage account"
3. Menu lateral: Access keys
4. Em "key1", clique em "Show" e copie "Connection string"

---

## 🧪 Testar Conexões

### Teste 1: OpenAI Connection

Crie arquivo `test_openai_connection.py`:

```python
import os
from openai import OpenAI

# Configure
os.environ["OPENAI_API_KEY"] = "sua-chave-aqui"

# Teste
client = OpenAI()

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}],
        max_tokens=10
    )
    print("✅ OpenAI conectado com sucesso!")
    print(f"Resposta: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Erro: {e}")
```

Execute: `python test_openai_connection.py`

---

### Teste 2: Cosmos DB Connection

Crie arquivo `test_cosmos_connection.py`:

```python
import os
from azure.cosmos import CosmosClient

# Configure
endpoint = "https://SEU-COSMOS.documents.azure.com:443/"
key = "sua-key-aqui"

try:
    client = CosmosClient(endpoint, key)
    # Lista databases
    databases = list(client.list_databases())
    print(f"✅ Cosmos DB conectado com sucesso!")
    print(f"Databases encontrados: {len(databases)}")
    for db in databases:
        print(f"  - {db['id']}")
except Exception as e:
    print(f"❌ Erro: {e}")
```

Execute: `python test_cosmos_connection.py`

---

### Teste 3: Blob Storage Connection

Crie arquivo `test_blob_connection.py`:

```python
import os
from azure.storage.blob import BlobServiceClient

# Configure
connection_string = "sua-connection-string-aqui"

try:
    blob_service = BlobServiceClient.from_connection_string(connection_string)
    # Lista containers
    containers = list(blob_service.list_containers())
    print(f"✅ Blob Storage conectado com sucesso!")
    print(f"Containers encontrados: {len(containers)}")
    for container in containers:
        print(f"  - {container['name']}")
except Exception as e:
    print(f"❌ Erro: {e}")
```

Execute: `python test_blob_connection.py`

---

## 🎯 Checklist de Validação

- [ ] Azure CLI instalado (ou validação manual feita)
- [ ] Login no Azure realizado (az login)
- [ ] Resource Group de IA localizado
- [ ] OpenAI API Key configurada
- [ ] Cosmos DB credentials obtidas (se disponível)
- [ ] Storage Account credentials obtidas (se disponível)
- [ ] local.settings.json configurado
- [ ] Testes de conexão executados com sucesso

---

## 📝 Informações para Preencher

Preencha com suas informações:

```
RESOURCE GROUP: ____________________________________
LOCATION: ___________________________________________

OPENAI:
- Service Name: _____________________________________
- Endpoint: _________________________________________
- Key: ______________________________________________

COSMOS DB (se disponível):
- Account Name: _____________________________________
- Endpoint: _________________________________________
- Primary Key: ______________________________________

STORAGE ACCOUNT (se disponível):
- Account Name: _____________________________________
- Connection String: ________________________________

FUNCTION APP (se já criado):
- App Name: _________________________________________
- URL: ______________________________________________
```

---

## 🚀 Próximo Passo

Depois de validar as conexões:

1. ✅ Se TUDO funcionou: Execute `func start` para testar localmente
2. ⏳ Se falta provisionar recursos: Siga o `AZURE_MIGRATION_PLAN.md`
3. 📚 Consulte `QUICK_START.md` para guia completo

---

**Precisa de ajuda?**
- Documentação Azure CLI: https://docs.microsoft.com/cli/azure/
- Tutorial Azure Functions: https://docs.microsoft.com/azure/azure-functions/
- Suporte Azure: https://portal.azure.com > Help + support
