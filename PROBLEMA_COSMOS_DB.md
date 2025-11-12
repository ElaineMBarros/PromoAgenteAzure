# ⚠️ PROBLEMA: Promoções Não Estão Sendo Salvas

## 🔍 **DIAGNÓSTICO:**

Implementação está correta, mas promoções não são salvas no Cosmos DB.

---

## 🎯 **CAUSA PROVÁVEL:**

### **Variáveis de ambiente faltando no Azure Functions:**

```bash
COSMOS_DB_ENDPOINT=xxxxx
COSMOS_DB_KEY=xxxxx
```

O código verifica se essas variáveis existem:

```python
# cosmos_adapter.py linha 18
self.endpoint = os.environ.get("COSMOS_DB_ENDPOINT")
self.key = os.environ.get("COSMOS_DB_KEY")

if not self.endpoint or not self.key:
    logger.warning("⚠️ Cosmos DB credentials não configuradas")
    self.client = None  # ← FICA DESABILITADO
```

**Resultado:** `cosmos_adapter.client = None` → não salva

---

## ✅ **SOLUÇÃO (AMANHÃ):**

### **1. Configurar variáveis no Azure Functions:**

```bash
# Portal Azure ou CLI:
az functionapp config appsettings set \
  --name promoagente-func \
  --resource-group <seu-resource-group> \
  --settings \
    COSMOS_DB_ENDPOINT="https://<cosmos-account>.documents.azure.com:443/" \
    COSMOS_DB_KEY="<sua-chave-primaria>"
```

### **2. Verificar logs no Azure:**

```bash
# Ver se aparece o warning:
"⚠️ Cosmos DB credentials não configuradas"

# Ou erro de import:
"⚠️ Cosmos adapter não disponível"
```

### **3. Criar containers no Cosmos DB:**

Se não existirem, criar:
- `sessions`
- `messages`
- `promo_states`
- `promotions` ← **PRINCIPAL**

---

## 🔧 **ALTERNATIVA (SE COSMOS NÃO DISPONÍVEL):**

### **Implementar fallback local:**

Modificar OrchestratorFunction para salvar em arquivo JSON:

```python
# Se Cosmos falhar, salva localmente
if not COSMOS_ADAPTER_AVAILABLE:
    # Salva em blob storage ou arquivo local
    import json
    with open(f"promotions/{promo_id}.json", "w") as f:
        json.dump(promo_data, f)
```

---

## 📋 **CHECKLIST PARA AMANHÃ:**

- [ ] Verificar se Cosmos DB existe no Azure
- [ ] Pegar ENDPOINT e KEY do Cosmos DB
- [ ] Configurar variáveis no Azure Functions
- [ ] Verificar se containers existem
- [ ] Criar containers se necessário
- [ ] Redeploy Azure Functions (se mudou env vars)
- [ ] Testar salvamento novamente
- [ ] Verificar logs para confirmar

---

## 🎯 **ARQUIVOS RELEVANTES:**

- `shared/adapters/cosmos_adapter.py` - Implementação
- `OrchestratorFunction/__init__.py` - Linha ~425 (save_promotion)
- Azure Portal → Configuration → Application Settings

---

## 💡 **DICA:**

Se não tiver Cosmos DB provisionado:
1. Criar no Azure Portal
2. Database: `PromoAgente`
3. Containers: `promotions`, `sessions`, `messages`, `promo_states`
4. Partition key: `/partitionKey`

---

**Status:** 🔴 Implementado mas não funcionando (faltam env vars)
**Próximo:** 🟡 Configurar Cosmos DB no Azure
