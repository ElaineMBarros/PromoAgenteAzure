# 🤖 INTEGRAÇÃO DOS PROMPTS - PromoAgente

## 📋 **SITUAÇÃO ATUAL**

### **O que está acontecendo:**
ChatFunction usa APENAS `prompts/persona.md` para conversar e coletar dados.

**Resultado:**
- ✅ IA conversa bem (direto e objetivo)
- ✅ Coleta informações
- ❌ **NÃO estrutura os dados corretamente**
- ❌ **NÃO usa extraction.md**

### **O que deveria acontecer:**
1. **persona.md** → Conversar e coletar dados
2. **extraction.md** → Estruturar dados JSON
3. **Salvar** → Cosmos DB com estrutura correta

---

## 🎯 **SOLUÇÃO: FLUXO DE 2 AGENTES**

### **Agente 1: Conversador (persona.md)**
**Responsabilidade:** Conversar com usuário e coletar dados

**Quando usar:**
- Início da conversa
- Faltam informações
- Usuário quer ajustar algo

**Prompt:** `prompts/persona.md`

---

### **Agente 2: Extrator (extraction.md)**
**Responsabilidade:** Extrair e estruturar dados em JSON

**Quando usar:**
- Usuário forneceu dados completos de uma promoção
- Percebe-se que há informações suficientes para extrair

**Prompt:** `prompts/extraction.md`

---

## 🔄 **LÓGICA DE ORQUESTRAÇÃO**

```python
async def process_message(session_id, message, history):
    """
    Orquestra entre persona e extraction
    """
    
    # 1. Sempre conversa primeiro (persona.md)
    conversa_response = await chat_with_persona(message, history)
    
    # 2. Detectar se há dados para extrair
    if should_extract_data(conversa_response, history):
        # Usa extraction.md para estruturar
        extracted_data = await extract_structured_data(message, history)
        
        # 3. Salvar no Cosmos DB
        if extracted_data:
            await cosmos_adapter.save_promotion(session_id, extracted_data)
            
            # Adicionar indicador na resposta
            conversa_response += "\n\n[DADOS_EXTRAÍDOS_E_SALVOS]"
    
    return conversa_response
```

---

## 🔍 **DETECTANDO QUANDO EXTRAIR**

### **Sinais de que deve extrair:**

1. **Resposta contém "✅ Dados registrados"**
2. **Usuário confirma:** "confirmo", "está certo", "pode salvar"
3. **Dados completos detectados:**
   - Tem título ou descrição
   - Tem mecânica
   - Tem período
   - Tem condições/produtos

### **Código de detecção:**

```python
def should_extract_data(ai_response: str, history: List) -> bool:
    """
    Decide se deve chamar extraction.md
    """
    # Verificar marcadores
    if "✅ Dados registrados" in ai_response:
        return True
    
    if "Confirma os dados" in ai_response:
        return True
    
    # Verificar se última mensagem do usuário foi confirmação
    if history and len(history) > 0:
        last_user_msg = history[-1].get('content', '').lower()
        confirms = ['confirmo', 'sim', 'está certo', 'correto', 'pode salvar']
        if any(word in last_user_msg for word in confirms):
            return True
    
    return False
```

---

## 📝 **IMPLEMENTAÇÃO NA ChatFunction**

### **Estrutura atual (simplificada):**
```python
# Apenas persona.md
messages = [
    {"role": "system", "content": persona_prompt},
    *history,
    {"role": "user", "content": message}
]

response = openai.chat.completions.create(messages=messages)
```

### **Estrutura necessária (com extração):**
```python
# 1. Conversar (persona.md)
messages_chat = [
    {"role": "system", "content": persona_prompt},
    *history,
    {"role": "user", "content": message}
]

chat_response = openai.chat.completions.create(messages=messages_chat)
response_text = chat_response.content

# 2. Detectar se deve extrair
if should_extract_data(response_text, history):
    # Montar contexto completo da conversa
    full_conversation = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in history
    ])
    full_conversation += f"\nuser: {message}"
    
    # 3. Extrair dados estruturados (extraction.md)
    messages_extract = [
        {"role": "system", "content": extraction_prompt},
        {"role": "user", "content": full_conversation}
    ]
    
    extract_response = openai.chat.completions.create(
        messages=messages_extract,
        response_format={"type": "json_object"}  # Força JSON
    )
    
    # 4. Parse JSON
    try:
        extracted_data = json.loads(extract_response.content)
        
        # 5. Salvar no Cosmos DB
        await cosmos_adapter.save_promotion(session_id, extracted_data)
        
        logger.info(f"Promoção extraída e salva: {extracted_data.get('titulo')}")
        
    except json.JSONDecodeError:
        logger.error("Erro ao parsear JSON extraído")

# 6. Salvar mensagens no histórico
await cosmos_adapter.save_message(session_id, message, response_text)

return response_text
```

---

## 🎯 **EXEMPLO COMPLETO DE FLUXO**

### **Mensagem 1:**
```
Usuário: "Quero criar uma promoção"
IA (persona.md): "Pode me passar os dados da promoção?"
```
**Ação:** Não extrai (faltam dados)

---

### **Mensagem 2:**
```
Usuário: "Combo Always Cliente TRAD, família Higiene Feminina. 
Combo Always: Básico Seca 8un + Noturno 8un. 
Mínimo: 12 combos. Desconto: 8%. Vigência: 01/03 a 30/03."

IA (persona.md): "✅ Dados registrados!
- Título: Tradicional – Combo Always
- Mecânica: Combo
- Descrição: Combo Always: Básico Seca 8un + Noturno 8un
- Período: 01/03 a 30/03
- Condições: 12 combos mínimos
- Recompensas: Desconto de 8%
Confirma os dados ou deseja ajustar algo?"
```

**Ação:**
1. ✅ Detecta "✅ Dados registrados"
2. ✅ Chama extraction.md com TODO o histórico
3. ✅ extraction.md retorna JSON estruturado:

```json
{
  "titulo": "Tradicional – Combo Always",
  "mecanica": "combo",
  "descricao": "Combo Always: Básico Seca 8un + Noturno 8un. Mínimo: 12 combos.",
  "canal": "TRAD",
  "categoria": "Higiene Feminina",
  "produtos": ["Always Básico Seca 8un", "Always Noturno 8un"],
  "combo": "Always Básico Seca 8un + Always Noturno 8un",
  "qt_minima": "12",
  "condicoes": "Mínimo de 12 combos",
  "desconto_percentual": "8",
  "recompensas": "8% de desconto",
  "periodo_inicio": "01/03/2026",
  "periodo_fim": "30/03/2026"
}
```

4. ✅ Salva no Cosmos DB na collection `promotions`

---

### **Mensagem 3:**
```
Usuário: "Confirmo"
IA (persona.md): "✅ Promoção registrada! 
Deseja cadastrar mais promoções ou finalizar?"
```

**Ação:** Promoção já foi salva na mensagem anterior

---

## 📦 **ESTRUTURA NO COSMOS DB**

### **Collection: messages**
```json
{
  "id": "msg_xxx",
  "session_id": "session_xxx",
  "user_message": "Combo Always...",
  "ai_response": "✅ Dados registrados!...",
  "timestamp": "2025-11-06T..."
}
```

### **Collection: promotions**
```json
{
  "id": "promo_xxx",
  "session_id": "session_xxx",
  "titulo": "Tradicional – Combo Always",
  "mecanica": "combo",
  "descricao": "Combo Always...",
  "canal": "TRAD",
  "categoria": "Higiene Feminina",
  "produtos": ["Always Básico Seca 8un", "Always Noturno 8un"],
  "qt_minima": "12",
  "desconto_percentual": "8",
  "periodo_inicio": "01/03/2026",
  "periodo_fim": "30/03/2026",
  "created_at": "2025-11-06T...",
  "status": "confirmed"
}
```

---

## 🔧 **MODIFICAÇÕES NECESSÁRIAS**

### **1. ChatFunction/__init__.py**

Adicionar:
- Função `should_extract_data()`
- Função `extract_structured_data()`
- Lógica de orquestração
- Salvar promoção no Cosmos DB

### **2. Cosmos DB Adapter**

Já tem o método:
```python
await cosmos_adapter.save_promotion(session_id, promo_data)
```

---

## ⏱️ **ESTIMATIVA DE IMPLEMENTAÇÃO**

**Tempo necessário:** 2-3 horas

**Etapas:**
1. Adicionar função `should_extract_data()` - 30 min
2. Implementar `extract_structured_data()` - 1h
3. Integrar na ChatFunction - 30 min
4. Testar e ajustar - 1h

---

## 🎯 **PRÓXIMO PASSO**

**Opção A:** Implementar agora (2-3h)
- Sistema completo com extração estruturada
- Dados salvos corretamente no Cosmos DB
- Excel pode ser gerado depois

**Opção B:** Fazer depois
- Sistema atual funciona (conversa OK)
- Mas não salva dados estruturados
- Excel não pode ser gerado sem estrutura

**Opção C:** Implementação parcial
- Apenas detection + extração simples
- Testar conceito
- Refinar depois

---

## 💡 **RECOMENDAÇÃO**

**Implementar Opção A** para ter sistema completo:
- Conversa com persona.md ✅
- Extrai com extraction.md ✅
- Salva estruturado ✅
- Pronto para Excel depois ✅

**Ou parar por hoje:**
- Sistema já está 85% funcional
- Chat funcionando
- Cosmos DB integrado
- Falta apenas orquestração dos prompts

---

**Última atualização:** 06/11/2025 20:00  
**Status:** Documentação completa  
**Próximo:** Decisão sobre implementação
