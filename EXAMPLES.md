# Exemplos de Uso da API

Este arquivo contém exemplos de como usar a API de promoções.

## Criar uma nova promoção

```bash
curl -X POST https://seu-app.azurewebsites.net/api/promocoes \
  -H "Content-Type: application/json" \
  -H "x-functions-key: SEU_FUNCTION_KEY" \
  -d '{
    "nome": "Black Friday - Notebook",
    "descricao": "Desconto especial de Black Friday em notebooks",
    "valor_original": 3000.00,
    "valor_promocional": 2100.00,
    "data_inicio": "2024-11-25T00:00:00Z",
    "data_fim": "2024-11-30T23:59:59Z",
    "categoria": "Eletrônicos"
  }'
```

## Listar todas as promoções

```bash
curl -X GET https://seu-app.azurewebsites.net/api/promocoes \
  -H "x-functions-key: SEU_FUNCTION_KEY"
```

## Listar apenas promoções ativas

```bash
curl -X GET "https://seu-app.azurewebsites.net/api/promocoes?ativas=true" \
  -H "x-functions-key: SEU_FUNCTION_KEY"
```

## Obter uma promoção específica

```bash
curl -X GET https://seu-app.azurewebsites.net/api/promocoes/123e4567-e89b-12d3-a456-426614174000 \
  -H "x-functions-key: SEU_FUNCTION_KEY"
```

## Atualizar uma promoção

```bash
curl -X PUT https://seu-app.azurewebsites.net/api/promocoes/123e4567-e89b-12d3-a456-426614174000 \
  -H "Content-Type: application/json" \
  -H "x-functions-key: SEU_FUNCTION_KEY" \
  -d '{
    "nome": "Black Friday - Notebook (Atualizado)",
    "descricao": "Desconto ainda maior!",
    "valor_original": 3000.00,
    "valor_promocional": 1800.00,
    "data_inicio": "2024-11-25T00:00:00Z",
    "data_fim": "2024-11-30T23:59:59Z",
    "categoria": "Eletrônicos",
    "ativa": true
  }'
```

## Deletar uma promoção

```bash
curl -X DELETE https://seu-app.azurewebsites.net/api/promocoes/123e4567-e89b-12d3-a456-426614174000 \
  -H "x-functions-key: SEU_FUNCTION_KEY"
```

## Testando localmente

Se você está executando a função localmente (com `func start`), use:

```bash
# Base URL local
BASE_URL="http://localhost:7071/api"

# Criar promoção
curl -X POST $BASE_URL/promocoes \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Promoção Teste",
    "descricao": "Descrição da promoção teste",
    "valor_original": 100.00,
    "valor_promocional": 70.00,
    "data_inicio": "2024-11-01T00:00:00",
    "data_fim": "2024-11-30T23:59:59"
  }'

# Listar promoções
curl -X GET $BASE_URL/promocoes
```

## Respostas de exemplo

### Criação bem-sucedida (201 Created)

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "nome": "Black Friday - Notebook",
  "descricao": "Desconto especial de Black Friday em notebooks",
  "valor_original": 3000.0,
  "valor_promocional": 2100.0,
  "percentual_desconto": 30.0,
  "data_inicio": "2024-11-25T00:00:00Z",
  "data_fim": "2024-11-30T23:59:59Z",
  "ativa": true,
  "categoria": "Eletrônicos",
  "criado_em": "2024-11-06T15:30:00Z",
  "atualizado_em": "2024-11-06T15:30:00Z"
}
```

### Erro de validação (400 Bad Request)

```json
{
  "erro": "Valor promocional deve ser menor que o valor original"
}
```

### Promoção não encontrada (404 Not Found)

```json
{
  "erro": "Promoção não encontrada"
}
```
