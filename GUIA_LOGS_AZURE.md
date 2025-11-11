# 🔍 GUIA COMPLETO: COMO VER LOGS DO AZURE

## 🎯 OBJETIVO
Descobrir por que a ExportFunction está retornando erro 500

---

## 📋 OPÇÃO 1: PORTAL AZURE (MAIS FÁCIL)

### **Passo 1: Acesse o Portal**
```
https://portal.azure.com
```

### **Passo 2: Encontre sua Function App**
1. No topo, clique na **barra de busca**
2. Digite: `promoagente-func`
3. Clique em **promoagente-func** (tipo: Function App)

### **Passo 3: Abra Log Stream**
1. No menu lateral esquerdo, procure por:
   - **"Monitoring"** ou **"Monitoramento"**
   - Clique em **"Log stream"** ou **"Fluxo de log"**

2. Você verá algo assim:
```
2025-11-11T10:22:13 [Information] Host started
2025-11-11T10:22:15 [Information] Functions host started
```

### **Passo 4: Teste a função**
1. **Abra o frontend** em outra aba:
   ```
   https://blue-forest-012694f0f-preview.eastus2.3.azurestaticapps.net
   ```

2. **Complete uma promoção** até ficar "ready"

3. **Digite no chat:** `gerar excel`

4. **Volte para a aba dos logs** - você verá algo como:

#### **Se openpyxl não carregou:**
```
2025-11-11T10:23:00 [Error] ❌ openpyxl não disponível: No module named 'openpyxl'
```

#### **Se teve erro ao gerar:**
```
2025-11-11T10:23:01 [Information] 📊 ExportFunction: Gerando exportação
2025-11-11T10:23:01 [Information] 📝 Gerando arquivo Excel para: combo_always
2025-11-11T10:23:02 [Error] ❌ Erro ao gerar Excel: 'str' object has no attribute 'replace'
Traceback (most recent call last):
  File "/home/site/wwwroot/ExportFunction/__init__.py", line 65, in main
    ...
```

#### **Se converteu para base64:**
```
2025-11-11T10:23:01 [Information] 📊 ExportFunction: Gerando exportação
2025-11-11T10:23:01 [Information] ✅ openpyxl carregado com sucesso
2025-11-11T10:23:01 [Information] 📝 Gerando arquivo Excel para: combo_always
2025-11-11T10:23:02 [Information] ✅ Excel gerado em memória
2025-11-11T10:23:02 [Information] 📦 Tamanho do Excel: 8567 bytes
2025-11-11T10:23:02 [Information] 📦 Base64 gerado: 11423 caracteres
```

---

## 📋 OPÇÃO 2: VIA CLI (MAIS TÉCNICO)

### **Abra PowerShell e execute:**
```bash
# Faz login no Azure
az login

# Lista logs em tempo real
func azure functionapp logstream promoagente-func
```

### **Ou para ver logs específicos:**
```bash
az monitor activity-log list \
  --resource-group geravi-ia \
  --query "[?contains(resourceId, 'promoagente-func')]" \
  --max-events 50
```

---

## 📋 OPÇÃO 3: APPLICATION INSIGHTS (MAIS DETALHADO)

### **Se configurado:**
1. Portal Azure → `promoagente-func`
2. Menu lateral → **"Application Insights"**
3. Clique em **"View Application Insights data"**
4. Menu **"Logs"** ou **"Transaction search"**
5. Filtre por:
   - **Operation name:** `ExportFunction`
   - **Time range:** Last 30 minutes

---

## 🎯 O QUE PROCURAR NOS LOGS

### **1. Erro de Import**
```
❌ Procure por:
"openpyxl não disponível"
"No module named 'openpyxl'"
"ImportError"
```

**Se encontrar:** openpyxl não instalou corretamente

---

### **2. Erro ao Gerar Excel**
```
❌ Procure por:
"❌ Erro ao gerar Excel"
"Traceback"
"KeyError"
"AttributeError"
```

**Se encontrar:** Problema com os dados da promoção

---

### **3. Erro de Base64**
```
❌ Procure por:
"❌ Erro ao converter para base64"
"UnicodeDecodeError"
```

**Se encontrar:** Problema na conversão

---

### **4. Timeout**
```
❌ Procure por:
"Function timeout"
"Execution timeout"
"Request timeout"
```

**Se encontrar:** Function demorou muito

---

### **5. Memória**
```
❌ Procure por:
"Out of memory"
"MemoryError"
```

**Se encontrar:** Excel muito grande

---

## 📸 EXEMPLO DE LOGS NORMAIS (SEM ERRO)

```
2025-11-11T10:23:00.123 [Information] 🎯 OrchestratorFunction: Processando requisição
2025-11-11T10:23:00.234 [Information] 💬 Mensagem recebida: gerar excel
2025-11-11T10:23:00.345 [Information] 📊 Comando detectado: gerar excel
2025-11-11T10:23:00.456 [Information] 📊 ExportFunction: Gerando exportação
2025-11-11T10:23:00.567 [Information] ✅ openpyxl carregado com sucesso
2025-11-11T10:23:00.678 [Information] 📝 Gerando arquivo Excel para: combo_always
2025-11-11T10:23:00.789 [Information] ✅ Excel gerado em memória
2025-11-11T10:23:00.890 [Information] 📦 Tamanho do Excel: 8567 bytes
2025-11-11T10:23:00.991 [Information] 📦 Base64 gerado: 11423 caracteres
2025-11-11T10:23:01.102 [Information] ✅ Exportação concluída: combo_always_20251111_102301.xlsx
2025-11-11T10:23:01.213 [Information] ✅ Processamento concluído: ready
```

---

## 🚨 ERROS COMUNS E SOLUÇÕES

### **ERRO 1: openpyxl não instalou**
```
❌ Log: "No module named 'openpyxl'"
```

**Causa:** requirements-azure.txt não foi lido

**Solução:**
1. Verifique se `openpyxl==3.1.2` está em `requirements-azure.txt`
2. Faça novo deploy: `func azure functionapp publish promoagente-func --python`

---

### **ERRO 2: Dados inválidos**
```
❌ Log: "KeyError: 'titulo'"
```

**Causa:** Promoção sem campo obrigatório

**Solução:** Complete todos os 9 campos antes de "gerar excel"

---

### **ERRO 3: Timeout**
```
❌ Log: "Function timeout (Timeout value: 00:05:00)"
```

**Causa:** Function demorou > 5 minutos

**Solução:** Aumente timeout em `host.json`

---

### **ERRO 4: Async incompatível**
```
❌ Log: "cannot be called from a running event loop"
```

**Causa:** Azure Functions não suporta `async def main`

**Solução:** Mudar para `def main` (síncrono)

---

## 📝 CHECKLIST DE VERIFICAÇÃO

Após ver os logs, verifique:

- [ ] openpyxl foi instalado? (Procure "✅ openpyxl carregado")
- [ ] Excel foi gerado? (Procure "✅ Excel gerado em memória")
- [ ] Base64 foi criado? (Procure "📦 Base64 gerado")
- [ ] Qual o tamanho? (Procure "📦 Tamanho do Excel")
- [ ] Tem erro de traceback? (Procure "Traceback")
- [ ] Tem timeout? (Procure "timeout")

---

## 🎯 PRÓXIMO PASSO

**Me envie:**
1. ✅ Trechos dos logs com erro (copie e cole)
2. ✅ Ou screenshot da tela de logs
3. ✅ Ou apenas descreva o que viu

**E eu:**
1. ✅ Analiso o erro
2. ✅ Faço a correção
3. ✅ 19º deploy
4. ✅ Excel funcionando!

---

## 💡 DICA RÁPIDA

**Teste mais rápido:**
```bash
# No PowerShell:
func azure functionapp logstream promoagente-func

# Em outra aba:
# Teste "gerar excel" no frontend

# Veja logs em tempo real!
```

---

## ✅ SUCESSO SE VER

```
✅ openpyxl carregado com sucesso
✅ Excel gerado em memória
📦 Tamanho do Excel: 8567 bytes
📦 Base64 gerado: 11423 caracteres
✅ Exportação concluída
```

**Se viu isso tudo, o erro está no frontend, não no backend!**

---

**Qualquer dúvida, me avise!** 🚀
