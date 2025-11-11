# 🧪 GUIA COMPLETO DE TESTES - Sistema PromoAgente

## 🚀 3 FORMAS DE TESTAR

---

## 1️⃣ TESTE RÁPIDO COM SCRIPT PYTHON (Mais Fácil)

### **Teste o Orchestrator completo:**
```bash
python test_orchestrator.py
```

**O que acontece:**
- Envia uma promoção de teste
- Mostra o resultado completo
- ✅ Status 200 = Funcionando!

### **Teste só o Extractor:**
```bash
python test_extractor_direct.py
```

---

## 2️⃣ TESTE COM POSTMAN OU INSOMNIA (Visual)

### **1. Abra o Postman/Insomnia**

### **2. Configure a requisição:**
```
Método: POST
URL: https://promoagente-func.azurewebsites.net/api/orchestrator
Headers:
  Content-Type: application/json
```

### **3. Body (JSON):**
```json
{
  "session_id": null,
  "message": "Promoção compre e ganhe Dove, válida de 15/01 a 28/02/2025, ganhe 1 sabonete a cada 3 comprados"
}
```

### **4. Clique em SEND**

### **5. Resultado Esperado:**
```json
{
  "success": true,
  "session_id": "xxxxx-xxxxx",
  "response": "...",
  "state": {
    "status": "needs_review",
    "data": {
      "titulo": "Promoção compre e ganhe Dove",
      "mecanica": "compre_e_ganhe",
      "periodo_inicio": "15/01/2025",
      "periodo_fim": "28/02/2025"
    }
  }
}
```

---

## 3️⃣ TESTE DIRETO NO NAVEGADOR COM FETCH (Simples)

### **1. Abra o Console do Navegador:**
- Pressione `F12`
- Vá na aba "Console"

### **2. Cole este código:**
```javascript
fetch('https://promoagente-func.azurewebsites.net/api/orchestrator', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    session_id: null,
    message: 'Promoção Nestlé de 10% OFF em chocolates, de 01/12/2024 a 31/12/2024'
  })
})
.then(r => r.json())
.then(data => {
  console.log('✅ Resultado:', data);
  if (data.success) {
    console.log('🎉 Sistema funcionando!');
    console.log('📊 Dados extraídos:', data.state.data);
  }
})
.catch(err => console.error('❌ Erro:', err));
```

### **3. Pressione Enter**

### **4. Veja o resultado no console! ✅**

---

## 📋 EXEMPLOS DE TESTES

### **Teste 1: Promoção Simples**
```json
{
  "message": "Promoção 15% OFF na Coca-Cola de 01/11/2024 a 30/11/2024"
}
```

### **Teste 2: Promoção Progressiva**
```json
{
  "message": "Promoção progressiva Unilever: compre 3 ganhe 5%, compre 5 ganhe 10%, compre 10 ganhe 15%. Válida janeiro a março de 2025"
}
```

### **Teste 3: Compre e Ganhe**
```json
{
  "message": "Compre 2 Nescafé e ganhe 1 copo. De 15/12/2024 a 15/01/2025"
}
```

### **Teste 4: Múltiplas Promoções**
```json
{
  "message": "Temos 3 promoções: Dove 10% OFF em janeiro, Lux 15% OFF em fevereiro, e Rexona 20% OFF em março"
}
```

---

## 🔍 COMO INTERPRETAR OS RESULTADOS

### **✅ Sucesso - Status 200:**
```json
{
  "success": true,
  "session_id": "abc123...",
  "response": "📝 Informações registradas!...",
  "state": {
    "status": "draft" ou "needs_review",
    "data": { ... }
  }
}
```

### **⚠️ Campos Faltantes:**
```json
{
  "success": true,
  "status": "needs_review",
  "response": "⚠️ Validação encontrou alguns problemas..."
}
```
**Isso é normal!** O sistema identificou que faltam informações.

### **❌ Erro:**
```json
{
  "success": false,
  "error": "mensagem de erro"
}
```

---

## 🧪 TESTES AVANÇADOS

### **Teste de Continuação de Sessão:**

**1. Primeira mensagem:**
```json
{
  "session_id": null,
  "message": "Promoção Nivea em janeiro"
}
```

**2. Copie o `session_id` da resposta**

**3. Segunda mensagem (continuando):**
```json
{
  "session_id": "cole-aqui-o-session-id",
  "message": "Ah, e o desconto é de 12%"
}
```

O sistema vai **combinar** as duas mensagens!

---

## 📊 TESTE DE STATUS DO SISTEMA

### **Verificar se tudo está OK:**
```bash
curl https://promoagente-func.azurewebsites.net/api/status
```

**Ou no navegador:**
```
https://promoagente-func.azurewebsites.net/api/status
```

**Resultado esperado:**
```json
{
  "status": "healthy",
  "functions": ["orchestrator", "extract", "validate", "summarize"],
  "timestamp": "..."
}
```

---

## 🎯 CHECKLIST DE TESTES

Use este checklist para testar tudo:

- [ ] Sistema responde (Status 200)
- [ ] Extrai título da promoção
- [ ] Identifica mecânica (progressiva, compre_ganhe, etc)
- [ ] Extrai período (início e fim)
- [ ] Extrai desconto/recompensa
- [ ] Detecta múltiplas promoções
- [ ] Mantém sessão entre mensagens
- [ ] Valida campos obrigatórios
- [ ] Retorna warnings para campos faltantes

---

## 💡 DICAS

### **Para testar localmente (desenvolvimento):**
```bash
# Inicie o servidor local
func start

# Em outro terminal
python test_orchestrator.py
```

### **Para testar no Azure (produção):**
```bash
# Já está rodando!
python test_orchestrator.py
```

### **Para ver logs em tempo real:**
```bash
func azure functionapp logstream promoagente-func
```

---

## 🐛 TROUBLESHOOTING

### **Erro 500:**
- Verifique os logs no Portal Azure
- Application Insights → Logs

### **Erro 401:**
- Credenciais Azure OpenAI incorretas
- Verificar OPENAI_API_KEY

### **Erro 404:**
- URL incorreta
- Function não deployada

### **Timeout:**
- Azure OpenAI pode estar lento
- Aumentar timeout no código

---

## 📱 TESTE NO FRONTEND

### **Se você tem o frontend React:**

1. **Configure o endpoint:**
```typescript
// src/config.ts
export const API_URL = 'https://promoagente-func.azurewebsites.net';
```

2. **Use o componente ChatPanel:**
- Digite uma promoção
- Veja o resultado em tempo real

3. **Verifique o Network:**
- F12 → Network
- Veja as chamadas para `/api/orchestrator`

---

## ✅ TESTE COMPLETO PASSO A PASSO

### **Teste Básico (5 minutos):**

1. **Abra o terminal**
2. **Execute:**
   ```bash
   python test_orchestrator.py
   ```
3. **Veja o resultado:**
   - ✅ Status 200 = Sucesso!
   - Dados extraídos aparecem no JSON

### **Teste Intermediário (10 minutos):**

1. **Abra o Postman**
2. **Teste 3 exemplos diferentes:**
   - Promoção simples
   - Promoção progressiva
   - Múltiplas promoções
3. **Verifique:**
   - Todos retornam 200?
   - Dados estão corretos?

### **Teste Avançado (15 minutos):**

1. **Teste continuação de sessão**
2. **Teste validação**
3. **Teste todos os endpoints**
4. **Verifique logs no Azure**

---

## 🎓 RECURSOS ÚTEIS

### **Scripts de Teste:**
- `test_orchestrator.py` - Teste completo
- `test_extractor_direct.py` - Teste só extração
- `test_azure_openai_local.py` - Teste credenciais

### **URLs Importantes:**
- API: https://promoagente-func.azurewebsites.net
- Portal Azure: https://portal.azure.com
- Logs: Application Insights

### **Comandos Úteis:**
```bash
# Ver logs
az functionapp log tail --name promoagente-func --resource-group geravi-ia

# Reiniciar
az functionapp restart --name promoagente-func --resource-group geravi-ia

# Ver configurações
az functionapp config appsettings list --name promoagente-func --resource-group geravi-ia
```

---

**🎉 Pronto! Agora você sabe como testar tudo!**

**Recomendo começar pelo Teste 1 (Script Python) - é o mais rápido e fácil!** 🚀
