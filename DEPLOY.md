# Guia de Deploy para Azure

Este guia descreve como fazer o deploy do Agente de Promoções para o Azure.

## Pré-requisitos

1. **Azure CLI** instalado e configurado
2. **Azure Functions Core Tools** instalado
3. **Conta Azure** ativa
4. **Python 3.9+** instalado

## Passo 1: Criar Resource Group

```bash
az group create \
  --name rg-promocoes \
  --location brazilsouth
```

## Passo 2: Criar Storage Account

```bash
az storage account create \
  --name stpromocoesapp \
  --resource-group rg-promocoes \
  --location brazilsouth \
  --sku Standard_LRS
```

## Passo 3: Criar Cosmos DB Account

```bash
# Criar conta do Cosmos DB
az cosmosdb create \
  --name cosmos-promocoes \
  --resource-group rg-promocoes \
  --default-consistency-level Session \
  --locations regionName=brazilsouth failoverPriority=0

# Criar database
az cosmosdb sql database create \
  --account-name cosmos-promocoes \
  --resource-group rg-promocoes \
  --name PromocoesDB

# Criar container
az cosmosdb sql container create \
  --account-name cosmos-promocoes \
  --database-name PromocoesDB \
  --resource-group rg-promocoes \
  --name Promocoes \
  --partition-key-path "/id"
```

## Passo 4: Obter Connection String do Cosmos DB

```bash
az cosmosdb keys list \
  --name cosmos-promocoes \
  --resource-group rg-promocoes \
  --type connection-strings \
  --query "connectionStrings[0].connectionString" \
  --output tsv
```

Guarde essa connection string, você vai precisar dela!

## Passo 5: Criar Function App

```bash
az functionapp create \
  --resource-group rg-promocoes \
  --consumption-plan-location brazilsouth \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4 \
  --name func-promocoes-app \
  --storage-account stpromocoesapp \
  --os-type Linux
```

## Passo 6: Configurar Variáveis de Ambiente

```bash
# Substitua <CONNECTION_STRING> pela connection string obtida no Passo 4
az functionapp config appsettings set \
  --name func-promocoes-app \
  --resource-group rg-promocoes \
  --settings \
    "COSMOS_DB_CONNECTION_STRING=<CONNECTION_STRING>" \
    "COSMOS_DB_DATABASE_NAME=PromocoesDB" \
    "COSMOS_DB_CONTAINER_NAME=Promocoes"
```

## Passo 7: Deploy da Aplicação

```bash
# No diretório raiz do projeto
func azure functionapp publish func-promocoes-app
```

## Passo 8: Obter a Function Key

```bash
az functionapp function keys list \
  --resource-group rg-promocoes \
  --name func-promocoes-app \
  --function-name PromocaoFunction
```

## Passo 9: Testar a API

```bash
# Substitua pelos valores corretos
FUNCTION_URL="https://func-promocoes-app.azurewebsites.net"
FUNCTION_KEY="sua-function-key-aqui"

# Testar criação de promoção
curl -X POST "$FUNCTION_URL/api/promocoes" \
  -H "Content-Type: application/json" \
  -H "x-functions-key: $FUNCTION_KEY" \
  -d '{
    "nome": "Teste Deploy",
    "descricao": "Testando deploy no Azure",
    "valor_original": 100.00,
    "valor_promocional": 70.00,
    "data_inicio": "2024-11-01T00:00:00Z",
    "data_fim": "2024-12-31T23:59:59Z"
  }'

# Listar promoções
curl -X GET "$FUNCTION_URL/api/promocoes" \
  -H "x-functions-key: $FUNCTION_KEY"
```

## Passo 10: Monitoramento

### Ver logs em tempo real

```bash
func azure functionapp logstream func-promocoes-app
```

### Application Insights (Opcional mas recomendado)

```bash
# Criar Application Insights
az monitor app-insights component create \
  --app ai-promocoes \
  --resource-group rg-promocoes \
  --location brazilsouth

# Obter Instrumentation Key
AI_KEY=$(az monitor app-insights component show \
  --app ai-promocoes \
  --resource-group rg-promocoes \
  --query instrumentationKey \
  --output tsv)

# Configurar na Function App
az functionapp config appsettings set \
  --name func-promocoes-app \
  --resource-group rg-promocoes \
  --settings "APPINSIGHTS_INSTRUMENTATIONKEY=$AI_KEY"
```

## Comandos Úteis

### Ver status dos recursos

```bash
az functionapp list \
  --resource-group rg-promocoes \
  --output table
```

### Reiniciar a Function App

```bash
az functionapp restart \
  --name func-promocoes-app \
  --resource-group rg-promocoes
```

### Ver logs recentes

```bash
az monitor activity-log list \
  --resource-group rg-promocoes \
  --offset 1h
```

## Limpeza de Recursos

Para remover todos os recursos criados:

```bash
az group delete \
  --name rg-promocoes \
  --yes \
  --no-wait
```

## Troubleshooting

### A função não inicia

1. Verifique os logs: `func azure functionapp logstream func-promocoes-app`
2. Verifique as configurações: `az functionapp config appsettings list --name func-promocoes-app --resource-group rg-promocoes`
3. Verifique se o runtime Python está correto: `az functionapp show --name func-promocoes-app --resource-group rg-promocoes --query "siteConfig.linuxFxVersion"`

### Erro de conexão com Cosmos DB

1. Verifique se a connection string está correta
2. Verifique se o firewall do Cosmos DB permite conexões do Azure
3. Teste a conexão com: `az cosmosdb show --name cosmos-promocoes --resource-group rg-promocoes`

### Erro 500 na API

1. Verifique os logs da aplicação
2. Verifique se todas as dependências estão instaladas
3. Teste localmente antes de fazer deploy

## Custos Estimados

- **Function App (Consumption Plan)**: ~R$ 0,00 (primeiro 1M de execuções grátis)
- **Cosmos DB**: ~R$ 25,00/mês (400 RU/s)
- **Storage Account**: ~R$ 1,00/mês
- **Application Insights**: Grátis até 5GB/mês

Total estimado: ~R$ 26,00/mês para uso moderado
