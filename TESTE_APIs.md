# 🧪 GUIA DE TESTES - APIs do PromoAgente

## 🎯 URLs Base

**Backend Azure:**
```
https://promoagente-func.azurewebsites.net
```

**Frontend Azure:**
```
https://blue-forest-012694f0f-preview.eastus2.3.azurestaticapps.net
```

---

## 📡 APIs Disponíveis

### **1. POST /api/chat**
**Função:** Chat com IA para criar promoções

**Teste com cURL:**
```bash
curl -X POST https://promoagente-func.azurewebsites.net/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Olá, quero criar uma promoção\"}"
```

**Teste com PowerShell:**
```powershell
$body = @{
    message = "Olá, quero criar uma promoção"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://promoagente-func.azurewebsites.net/api/chat" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

**Resposta esperada:**
```json
{
  "response": "Olá! Fico feliz em ajudá-lo...",
  "session_id": "session_1699999999.999",
  "timestamp": "2025-11-06T...",
  "status": "success"
}
```

---

### **2. POST /api/extract**
**Função:** Extrai informações de texto

**Teste com cURL:**
```bash
curl -X POST https://promoagente-func.azurewebsites.net/api/extract \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"Promoção válida de 01/12 a 31/12. Compre 10 caixas e ganhe 10% de desconto.\"}"
```

**Resposta esperada:**
```json
{
  "extracted_data": {
    "titulo": "...",
    "periodo": "01/12 a 31/12",
    "mecanica": "volume",
    ...
  }
}
```

---

### **3. POST /api/validate**
**Função:** Valida dados de promoção

**Teste com cURL:**
```bash
curl -X POST https://promoagente-func.azurewebsites.net/api/validate \
  -H "Content-Type: application/json" \
  -d "{\"promo_data\":{\"titulo\":\"Teste\",\"mecanica\":\"progressiva\"}}"
```

---

### **4. POST /api/summarize**
**Função:** Gera resumo da promoção

**Teste com cURL:**
```bash
curl -X POST https://promoagente-func.azurewebsites.net/api/summarize \
  -H "Content-Type: application/json" \
  -d "{\"promo_data\":{\"titulo\":\"Teste\"},\"type\":\"summary\"}"
```

---

## 🐍 Script Python de Teste

**Use o script já criado:**
```bash
python test_endpoints.py
```

**Ou crie um teste personalizado:**
```python
import requests
import json

BASE_URL = "https://promoagente-func.azurewebsites.net"

# Teste /api/chat
response = requests.post(
    f"{BASE_URL}/api/chat",
    json={"message": "Quero criar uma promoção de desconto"}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

---

## 🌐 Teste no Navegador

### **Opção 1 - Console do Navegador:**

1. Abra o frontend:
   ```
   https://blue-forest-012694f0f-preview.eastus2.3.azurestaticapps.net
   ```

2. Pressione **F12** (Dev Tools)

3. Vá em **Console**

4. Digite e execute:
   ```javascript
   fetch('https://promoagente-func.azurewebsites.net/api/chat', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({message: 'Olá'})
   })
   .then(r => r.json())
   .then(data => console.log(data))
   ```

### **Opção 2 - Ferramenta Postman:**

1. Baixe: https://www.postman.com/downloads/

2. Crie uma nova Request:
   - Method: **POST**
   - URL: `https://promoagente-func.azurewebsites.net/api/chat`
   - Headers:
     ```
     Content-Type: application/json
     ```
   - Body (raw, JSON):
     ```json
     {
       "message": "Quero criar uma promoção"
     }
     ```

3. Clique **Send**

---

## 🔍 Ver Erros Detalhados

### **1. No Terminal (cURL com verbose):**
```bash
curl -v -X POST https://promoagente-func.azurewebsites.net/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"teste\"}"
```

### **2. No Browser DevTools:**
1. F12 → Network tab
2. Acesse o frontend
3. Digite algo no chat
4. Veja a requisição no Network
5. Clique nela para ver detalhes

### **3. Logs do Azure (Real-time):**
```bash
func azure functionapp logstream promoagente-func
```

Ou no Portal:
```
Portal Azure → promoagente-func → Monitor → Log stream
```

---

## ⚠️ Erros Comuns e Soluções

### **Erro 401 - Unauthorized**
```
Problema: OpenAI API Key inválida
Solução: Configurar no Portal Azure

Portal → geravi-ia → promoagente-func → Configuration
Adicionar: OPENAI_API_KEY = 932843a5e242442a98f4a26fc634f218
Salvar
```

### **Erro 500 - Internal Server Error**
```
Problema: Erro no código ou configuração
Solução: Ver logs
```bash
func azure functionapp logstream promoagente-func
```

### **Erro 404 - Not Found**
```
Problema: Endpoint não existe ou não foi deployado
Solução: Verificar se Functions foram deployadas
```bash
az functionapp function list \
  --name promoagente-func \
  --resource-group geravi-ia
```

### **CORS Error (no browser)**
```
Problema: Frontend não autorizado
Solução: Adicionar URL do frontend no CORS
```bash
az functionapp cors add \
  --name promoagente-func \
  --resource-group geravi-ia \
  --allowed-origins "https://blue-forest-012694f0f-preview.eastus2.3.azurestaticapps.net"
```

---

## ✅ Checklist de Teste

### **Backend:**
- [ ] /api/chat responde (mesmo que com erro de key)
- [ ] /api/extract responde
- [ ] /api/validate responde
- [ ] /api/summarize responde
- [ ] Status code é 200, 401 ou 500 (não 404)

### **Frontend:**
- [ ] Página carrega
- [ ] Sem erros de CORS no console
- [ ] Input de mensagem funciona
- [ ] Botão envia funciona
- [ ] Mostra resposta (pode ser erro por enquanto)

---

## 🎯 Teste Rápido - 30 segundos

**Windows PowerShell:**
```powershell
# Teste simples
Invoke-WebRequest -Uri "https://promoagente-func.azurewebsites.net/api/chat" `
  -Method Post `
  -Body '{"message":"teste"}' `
  -ContentType "application/json"
```

**Linux/Mac:**
```bash
curl -X POST https://promoagente-func.azurewebsites.net/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"teste"}'
```

**Python (se requests instalado):**
```python
import requests
r = requests.post('https://promoagente-func.azurewebsites.net/api/chat', 
                  json={'message':'teste'})
print(f"{r.status_code}: {r.text}")
```

---

## 📊 Status Esperado

**ANTES de configurar OpenAI Key:**
```
Chat: 500 (erro OpenAI key) ✅ Código funciona!
Extract: 401 (falta key) ✅ Endpoint responde!
Validate: 401 (falta key) ✅ Endpoint responde!
Summarize: 401 (falta key) ✅ Endpoint responde!
```

**DEPOIS de configurar OpenAI Key:**
```
Chat: 200 ✅ Funcionando!
Extract: 200 ✅ Funcionando!
Validate: 200 ✅ Funcionando!
Summarize: 200 ✅ Funcionando!
```

---

## 🔑 Lembre-se

**OpenAI Key para configurar no Portal:**
```
932843a5e242442a98f4a26fc634f218
```

**Portal Azure:**
```
https://portal.azure.com
→ geravi-ia
→ promoagente-func
→ Configuration
→ Application settings
→ + New application setting
→ Name: OPENAI_API_KEY
→ Value: 932843a5e242442a98f4a26fc634f218
→ OK
→ Save (no topo)
```

---

## 💡 Dica Pro

**Teste mais rápido:**
```bash
# Salve isso em test_quick.bat
@echo off
curl -X POST https://promoagente-func.azurewebsites.net/api/chat -H "Content-Type: application/json" -d "{\"message\":\"teste\"}"
pause
```

**Execute:**
```bash
test_quick.bat
```

---

**Última atualização:** 06/11/2025 19:12  
**Próximo passo:** Configure OpenAI Key no Portal e todos os testes passarão! ✅
