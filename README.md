# Agente de Cadastro de Promoções - Azure

Este projeto implementa um agente inteligente para cadastro e gerenciamento de promoções na nuvem Azure, utilizando Azure Functions e Cosmos DB.

## 📋 Descrição

O Agente de Promoções é uma solução serverless que permite:
- Criar, ler, atualizar e deletar promoções
- Validação automática de dados
- Cálculo automático de percentual de desconto
- Persistência em Azure Cosmos DB
- API REST completa

## 🏗️ Arquitetura

### Componentes Principais

1. **Azure Functions**: Hospeda a API REST serverless
2. **Cosmos DB**: Banco de dados NoSQL para armazenamento de promoções
3. **Pydantic**: Validação e modelagem de dados
4. **Python 3.9+**: Runtime da aplicação

### Estrutura do Projeto

```
PromoAgenteAzure/
├── PromocaoFunction/         # Azure Function HTTP trigger
│   ├── __init__.py           # Handler da função
│   └── function.json         # Configuração do binding
├── models.py                 # Modelo de dados Promocao
├── database_service.py       # Serviço de acesso ao Cosmos DB
├── tests/                    # Testes unitários
├── requirements.txt          # Dependências Python
├── host.json                 # Configuração do host Azure Functions
└── local.settings.json       # Configurações locais (não commitar)
```

## 🚀 Como Usar

### Pré-requisitos

- Python 3.9 ou superior
- Azure Functions Core Tools
- Conta Azure com Cosmos DB configurado

### Instalação Local

1. Clone o repositório:
```bash
git clone https://github.com/ElaineMBarros/PromoAgenteAzure.git
cd PromoAgenteAzure
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente em `local.settings.json`:
```json
{
  "Values": {
    "COSMOS_DB_CONNECTION_STRING": "sua-connection-string",
    "COSMOS_DB_DATABASE_NAME": "PromocoesDB",
    "COSMOS_DB_CONTAINER_NAME": "Promocoes"
  }
}
```

4. Execute localmente:
```bash
func start
```

### Deploy para Azure

1. Crie uma Function App no Azure:
```bash
az functionapp create --resource-group <resource-group> \
  --consumption-plan-location <location> \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4 \
  --name <app-name> \
  --storage-account <storage-account>
```

2. Configure as variáveis de ambiente:
```bash
az functionapp config appsettings set --name <app-name> \
  --resource-group <resource-group> \
  --settings "COSMOS_DB_CONNECTION_STRING=<connection-string>"
```

3. Deploy:
```bash
func azure functionapp publish <app-name>
```

## 📚 API Reference

### Endpoints

#### Listar Promoções
```
GET /api/promocoes
GET /api/promocoes?ativas=true
```

**Resposta:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "nome": "Black Friday - Produto X",
    "descricao": "Desconto especial",
    "valor_original": 100.00,
    "valor_promocional": 70.00,
    "percentual_desconto": 30.0,
    "data_inicio": "2024-11-01T00:00:00",
    "data_fim": "2024-11-30T23:59:59",
    "ativa": true,
    "categoria": "Eletrônicos"
  }
]
```

#### Obter Promoção Específica
```
GET /api/promocoes/{id}
```

#### Criar Nova Promoção
```
POST /api/promocoes
Content-Type: application/json

{
  "nome": "Black Friday - Produto X",
  "descricao": "Desconto especial de Black Friday",
  "valor_original": 100.00,
  "valor_promocional": 70.00,
  "data_inicio": "2024-11-01T00:00:00",
  "data_fim": "2024-11-30T23:59:59",
  "categoria": "Eletrônicos"
}
```

#### Atualizar Promoção
```
PUT /api/promocoes/{id}
Content-Type: application/json

{
  "nome": "Black Friday - Produto X (Atualizado)",
  "descricao": "Nova descrição",
  "valor_original": 100.00,
  "valor_promocional": 60.00,
  "data_inicio": "2024-11-01T00:00:00",
  "data_fim": "2024-11-30T23:59:59"
}
```

#### Deletar Promoção
```
DELETE /api/promocoes/{id}
```

## 🧪 Testes

Execute os testes unitários:
```bash
python -m pytest tests/
```

Com cobertura:
```bash
python -m pytest tests/ --cov=. --cov-report=html
```

## 📊 Modelo de Dados

### Promoção

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| id | string (UUID) | Sim (auto) | Identificador único |
| nome | string | Sim | Nome da promoção |
| descricao | string | Sim | Descrição detalhada |
| valor_original | float | Sim | Valor original (> 0) |
| valor_promocional | float | Sim | Valor promocional (> 0 e < original) |
| percentual_desconto | float | Não (auto) | Percentual calculado automaticamente |
| data_inicio | datetime | Sim | Data de início |
| data_fim | datetime | Sim | Data de término (> início) |
| ativa | boolean | Não | Status (default: true) |
| categoria | string | Não | Categoria da promoção |
| criado_em | datetime | Sim (auto) | Timestamp de criação |
| atualizado_em | datetime | Sim (auto) | Timestamp de atualização |

### Validações Automáticas

- ✅ Valor promocional deve ser menor que valor original
- ✅ Data fim deve ser posterior à data início
- ✅ Percentual de desconto calculado automaticamente
- ✅ IDs únicos gerados automaticamente (UUID)

## 🔒 Segurança

- Autenticação via Function Key
- Validação de dados com Pydantic
- Conexão segura com Cosmos DB
- Variáveis de ambiente para secrets

## 🛠️ Tecnologias

- **Python 3.9+**
- **Azure Functions** - Serverless compute
- **Azure Cosmos DB** - NoSQL database
- **Pydantic** - Data validation
- **Azure Functions Core Tools** - Local development

## 📝 Licença

Este projeto está sob licença MIT.

## 👥 Contribuindo

Contribuições são bem-vindas! Por favor:
1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📧 Contato

Elaine M Barros - [@ElaineMBarros](https://github.com/ElaineMBarros)

Link do Projeto: [https://github.com/ElaineMBarros/PromoAgenteAzure](https://github.com/ElaineMBarros/PromoAgenteAzure)
