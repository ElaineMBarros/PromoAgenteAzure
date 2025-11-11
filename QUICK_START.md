# ⚡ Quick Start - PromoAgente Azure Functions

## 🚀 Início Rápido em 5 Minutos

### 1️⃣ Criar Ambiente Python 3.11

```bash
# Execute o script automatizado
setup_python311.bat

# OU manualmente:
conda create -n promoagente-azure python=3.11 -y
conda activate promoagente-azure
pip install -r requirements-azure.txt
```

### 2️⃣ Configurar Variáveis de Ambiente

Edite `local.settings.json` e adicione sua chave OpenAI:

```json
{
  "Values": {
    "OPENAI_API_KEY": "sua-chave-aqui"
  }
}
```

### 3️⃣ Instalar Azure Functions Core Tools

```bash
# Via npm (recomendado)
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# OU via Chocolatey (Windows)
choco install azure-functions-core-tools-4 -y
```

### 4️⃣ Iniciar Functions Localmente

```bash
# Ativar ambiente
conda activate promoagente-azure

# Iniciar
func start
```

Suas functions estarão disponíveis em:
- **Extractor**: http://localhost:7071/api/extract
- **Validator**: http://localhost:7071/api/validate
- **Summarizer**: http://localhost:7071/api/summarize

---

## 📝 Testando as Functions

### ExtractorFunction - Extração de Dados

```bash
curl -X POST http://localhost:7071/api/extract \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Quero criar uma promoção progressiva de refrigerantes. Título: Compre Mais Ganhe Mais. A cada 10 caixas, 5% de desconto. A partir de 20 caixas, 10% de desconto. Período de 01/12/2025 a 31/12/2025. Para pequenos e médios varejistas."
  }'
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "titulo": "Compre Mais Ganhe Mais",
    "mecanica": "progressiva",
    "descricao": "A cada 10 caixas, 5% de desconto. A partir de 20 caixas, 10% de desconto",
    "segmentacao": "Pequenos e médios varejistas",
    "periodo_inicio": "01/12/2025",
    "periodo_fim": "31/12/2025",
    ...
  },
  "is_multiple": false
}
```

### ValidatorFunction - Validação

```bash
curl -X POST http://localhost:7071/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "promo_data": {
      "titulo": "Compre Mais Ganhe Mais",
      "mecanica": "progressiva",
      "descricao": "A cada 10 caixas, 5% de desconto",
      "segmentacao": "Pequenos e médios varejistas",
      "periodo_inicio": "01/12/2025",
      "periodo_fim": "31/12/2025",
      "condicoes": "Válido para compras acima de 10 caixas",
      "recompensas": "Desconto progressivo de 5% a 10%"
    }
  }'
```

**Resposta:**
```json
{
  "success": true,
  "is_valid": true,
  "status": "APROVADO",
  "feedback": "✅ Promoção aprovada! Todos os campos obrigatórios preenchidos...",
  "issues": [],
  "suggestions": []
}
```

### SumarizerFunction - Resumo/Email

**Criar Resumo:**
```bash
curl -X POST http://localhost:7071/api/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "promo_data": {...},
    "type": "summary"
  }'
```

**Criar Email HTML:**
```bash
curl -X POST http://localhost:7071/api/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "promo_data": {...},
    "type": "email"
  }'
```

---

## 🏗️ Arquitetura Serverless

```
┌─────────────────────────────────────┐
│         Cliente Frontend            │
│        (React/Mobile/Web)           │
└────────────┬────────────────────────┘
             │ HTTP Requests
             ▼
┌─────────────────────────────────────┐
│      Azure Function App             │
│    (Consumption/Premium Plan)       │
└─────────────────────────────────────┘
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
┌────────┐ ┌────────┐ ┌────────┐
│Extract │ │Validate│ │Summariz│
│Function│ │Function│ │Function│
└────────┘ └────────┘ └────────┘
    │        │        │
    └────────┼────────┘
             ▼
    ┌──────────────────┐
    │  OpenAI GPT-4o   │
    └──────────────────┘
```

---

## 🔧 Estrutura do Projeto

```
PromoAgenteAzure/
├── functions/                    # Azure Functions
│   ├── ExtractorFunction/       
│   │   ├── __init__.py          # Lógica de extração
│   │   └── function.json        # Configuração
│   ├── ValidatorFunction/
│   │   ├── __init__.py          # Lógica de validação
│   │   └── function.json
│   └── SumarizerFunction/
│       ├── __init__.py          # Lógica de resumo/email
│       └── function.json
├── host.json                    # Config do Function App
├── local.settings.json          # Configurações locais
├── requirements-azure.txt       # Dependências Python
├── .funcignore                  # Arquivos ignorados
└── setup_python311.bat          # Script de instalação
```

---

## 🚀 Deploy para Azure

### Opção 1: Via Azure CLI

```bash
# Login
az login

# Deploy
func azure functionapp publish promoagente-functions
```

### Opção 2: Via VS Code

1. Instalar extensão **Azure Functions**
2. Clicar com botão direito na pasta `functions`
3. Selecionar **Deploy to Function App**

### Opção 3: CI/CD com GitHub Actions

```yaml
# .github/workflows/azure-functions.yml
name: Deploy Azure Functions

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python 3.11
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    - name: Install dependencies
      run: pip install -r requirements-azure.txt
    - name: Deploy to Azure Functions
      uses: Azure/functions-action@v1
      with:
        app-name: promoagente-functions
        package: .
        publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
```

---

## 💡 Vantagens da Arquitetura Serverless

✅ **Escalabilidade Automática**
- Cada function escala independentemente
- Suporta milhares de requisições simultâneas

✅ **Custo Reduzido**
- Paga apenas pelo uso (execuções + tempo)
- Primeiro 1 milhão de execuções grátis

✅ **Manutenção Simplificada**
- Agents isolados
- Deploy independente
- Rollback fácil

✅ **Performance**
- Cold start < 2s com Python 3.11
- Execução paralela
- Caching automático

✅ **Integração Azure**
- Application Insights (monitoramento)
- Key Vault (secrets)
- Storage (persistência)
- Cosmos DB (database)

---

## 🔍 Monitoramento

### Application Insights

```bash
# Ver logs em tempo real
func azure functionapp logstream promoagente-functions

# Ou no Azure Portal:
# Function App > Monitor > Live Metrics
```

### Métricas Importantes
- Execuções por minuto
- Duração média
- Erros/Exceções
- Consumo de memória

---

## 🐛 Troubleshooting

### Erro: "OPENAI_API_KEY não encontrada"
- Verifique `local.settings.json`
- No Azure: configure em Application Settings

### Erro: "Module not found"
- Execute: `pip install -r requirements-azure.txt`
- Verifique se está no ambiente correto: `conda activate promoagente-azure`

### Erro: "func: command not found"
- Instale Azure Functions Core Tools
- Reinicie o terminal

---

## 📚 Próximos Passos

1. ✅ Configure CI/CD com GitHub Actions
2. ✅ Adicione autenticação JWT/OAuth
3. ✅ Implemente cache com Redis
4. ✅ Configure alertas no Application Insights
5. ✅ Crie testes automatizados

---

## 📞 Suporte

- **Documentação Completa**: `AZURE_FUNCTIONS_SETUP.md`
- **Azure Functions Docs**: https://docs.microsoft.com/azure/azure-functions/
- **Python 3.11 Support**: https://docs.microsoft.com/azure/azure-functions/supported-languages

---

**Desenvolvido por**: Elaine Barros  
**Projeto**: PromoAgente Azure Functions  
**Versão**: 3.0.0 Serverless
