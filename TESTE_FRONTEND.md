# 🧪 TESTE DO FRONTEND - Guia Rápido

## ✅ CORS CONFIGURADO

O backend Azure Functions agora aceita requisições de:
- ✅ `http://localhost:5174` (seu frontend)
- ✅ `http://localhost:5173` (alternativa)
- ✅ Azure Static Web Apps (produção)

---

## 🚀 COMO TESTAR AGORA

### **1. Abra o navegador:**
```
http://localhost:5174/
```

### **2. Abra o Console do Navegador:**
- Pressione **F12**
- Vá na aba **Console**

### **3. Teste direto com este código:**

Cole no console e execute:

```javascript
// Teste 1: Status do sistema
fetch('https://promoagente-func.azurewebsites.net/api/status')
  .then(r => r.json())
  .then(data => console.log('✅ Status:', data))
  .catch(err => console.error('❌ Erro Status:', err));

// Aguarde 2 segundos e execute o próximo...

// Teste 2: Orchestrator com promoção
fetch('https://promoagente-func.azurewebsites.net/api/orchestrator', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: null,
    message: 'Promoção Dove 15% OFF de 01/12/2024 a 31/12/2024'
  })
})
  .then(r => r.json())
  .then(data => {
    console.log('✅ Orchestrator Response:', data);
    if (data.success) {
      console.log('🎉 FUNCIONOU!');
      console.log('📊 Dados:', data.state.data);
    }
  })
  .catch(err => console.error('❌ Erro:', err));
```

---

## 🎯 RESULTADOS ESPERADOS

### **Teste 1 - Status:**
```json
{
  "status": "healthy",
  "message": "System operational",
  "timestamp": "..."
}
```

### **Teste 2 - Orchestrator:**
```json
{
  "success": true,
  "session_id": "xxxxx-xxxxx",
  "response": "📝 Informações registradas!...",
  "state": {
    "status": "needs_review",
    "data": {
      "titulo": "Promoção Dove",
      "desconto_percentual": "15",
      "periodo_inicio": "01/12/2024",
      "periodo_fim": "31/12/2024"
    }
  }
}
```

---

## 🐛 SE DER ERRO

### **Erro de CORS:**
```
Access to fetch at '...' from origin 'http://localhost:5174' has been blocked by CORS policy
```

**Solução:** CORS já está configurado! Recarregue a página (Ctrl+R)

### **Erro 500:**
```javascript
// Veja detalhes do erro
fetch('https://promoagente-func.azurewebsites.net/api/orchestrator', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: null,
    message: 'teste'
  })
})
.then(r => r.text())
.then(text => console.log('Response:', text));
```

### **Erro de conexão:**
- Verifique se o backend está no ar:
  ```
  https://promoagente-func.azurewebsites.net/api/status
  ```

---

## 📱 TESTANDO A INTERFACE

### **1. Use o chat da aplicação:**
- Digite uma promoção
- Clique em Enviar
- Aguarde resposta (3-5 segundos)

### **2. Exemplos para testar:**

**Simples:**
```
Promoção Coca-Cola 10% OFF de 01/11 a 30/11/2024
```

**Progressiva:**
```
Promoção progressiva Nivea de janeiro a março de 2026, até 8.4% OFF
```

**Múltiplas:**
```
Temos 3 promoções: Dove 10% em janeiro, Lux 15% em fevereiro, Rexona 20% em março
```

---

## 🔍 VERIFICAR CHAMADAS À API

### **Na aba Network (F12):**
1. Vá em **Network** / **Rede**
2. Filtre por **XHR** ou **Fetch**
3. Envie uma mensagem no chat
4. Veja a chamada para `/api/orchestrator`
5. Clique nela para ver:
   - **Headers:** Verificar URL e Content-Type
   - **Payload:** O que foi enviado
   - **Response:** O que voltou

---

## ✅ CHECKLIST DE VERIFICAÇÃO

Marque conforme testar:

- [ ] Frontend abre em localhost:5174
- [ ] Console não mostra erros
- [ ] Teste Status retorna 200
- [ ] Teste Orchestrator retorna 200
- [ ] Interface do chat funciona
- [ ] Promoção é extraída corretamente
- [ ] Dados estruturados aparecem
- [ ] Validação identifica campos faltantes

---

## 🎓 COMANDOS ÚTEIS

### **Ver todas as variáveis de ambiente:**
```javascript
// No console do navegador
console.log('API URL:', import.meta.env.VITE_API_BASE_URL);
```

### **Forçar reload sem cache:**
```
Ctrl + Shift + R  (ou Cmd + Shift + R no Mac)
```

### **Limpar cache e cookies:**
```
F12 → Application → Clear storage → Clear site data
```

---

## 📊 LOGS DO BACKEND

### **Ver logs em tempo real:**
```bash
az functionapp log tail --name promoagente-func --resource-group geravi-ia
```

### **Ver logs no Portal Azure:**
1. https://portal.azure.com
2. promoagente-func
3. Log stream (menu lateral)

---

## 🎯 TESTE COMPLETO PASSO A PASSO

### **1. Verifique o backend (5 seg):**
```bash
python test_orchestrator.py
```
✅ Deve retornar Status 200

### **2. Abra o frontend (1 min):**
- Navegue para http://localhost:5174/
- Verifique se carregou sem erros

### **3. Teste no console (1 min):**
- F12 → Console
- Cole os testes acima
- Verifique respostas

### **4. Teste na interface (2 min):**
- Digite promoção no chat
- Envie
- Veja resultado

### **5. Verifique Network (1 min):**
- F12 → Network
- Envie outra promoção
- Inspecione chamada à API

---

## 🎉 SUCESSO!

Se todos os testes passarem, você tem:
- ✅ Backend Azure Functions operacional
- ✅ Frontend React conectado
- ✅ CORS configurado
- ✅ Integração end-to-end funcionando
- ✅ Sistema pronto para uso!

---

**🚀 Agora é só usar a aplicação! O sistema está 100% funcional!**

**Qualquer erro, veja os logs no console (F12) ou execute:**
```bash
python test_orchestrator.py
