"""
Teste Completo do Fluxo End-to-End
Simula exatamente o que o frontend faz
"""
import requests
import json
from datetime import datetime
import base64

# URLs
ORCHESTRATOR_URL = "https://promoagente-func.azurewebsites.net/api/orchestrator"

print("🧪 TESTE COMPLETO DO FLUXO END-TO-END")
print("=" * 70)
print("Simulando exatamente o que o frontend faz...")
print("=" * 70)

# Estado da sessão (como no frontend)
session_id = None
current_state = None

def send_message(message: str):
    """Envia mensagem para o Orchestrator"""
    global session_id, current_state
    
    print(f"\n📤 ENVIANDO: '{message}'")
    print("-" * 70)
    
    payload = {
        "message": message
    }
    
    if session_id:
        payload["session_id"] = session_id
    
    if current_state:
        payload["current_state"] = current_state
    
    try:
        response = requests.post(
            ORCHESTRATOR_URL,
            json=payload,
            timeout=60
        )
        
        print(f"📥 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Atualiza estado (como o frontend faz)
            session_id = result.get("session_id")
            current_state = result.get("state")
            
            print(f"✅ Sucesso: {result.get('success')}")
            print(f"📋 Status: {result.get('status')}")
            print(f"💬 Resposta: {result.get('response', '')[:200]}...")
            
            # Verifica se tem Excel
            if current_state and current_state.get("data"):
                data = current_state["data"]
                if "excel_base64" in data:
                    print("\n🎉 EXCEL DETECTADO NO ESTADO!")
                    print(f"📁 Filename: {data.get('excel_filename')}")
                    print(f"📦 Base64 length: {len(data.get('excel_base64', ''))} chars")
                    
                    # Tenta salvar
                    try:
                        excel_bytes = base64.b64decode(data["excel_base64"])
                        filename = f"test_flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                        with open(filename, "wb") as f:
                            f.write(excel_bytes)
                        print(f"💾 Excel salvo: {filename}")
                        print(f"💾 Tamanho: {len(excel_bytes)} bytes")
                    except Exception as e:
                        print(f"❌ Erro ao salvar Excel: {e}")
            
            return result
        else:
            print(f"❌ Erro {response.status_code}")
            print(f"📄 Resposta: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"❌ Erro: {type(e).__name__}: {str(e)}")
        return None

# FLUXO COMPLETO
print("\n" + "=" * 70)
print("PASSO 1: Boas-vindas")
print("=" * 70)
result1 = send_message("olá")

print("\n" + "=" * 70)
print("PASSO 2: Enviar dados da promoção")
print("=" * 70)
result2 = send_message("""Tradicional – Combo Always
Cliente TRAD, família Higiene Feminina
Combo Always: Básico Seca 8un + Noturno 8un
Mínimo: 12 combos
Desconto: 8%
Vigência: 01/03 a 30/03""")

print("\n" + "=" * 70)
print("PASSO 3: Completar dados faltantes")
print("=" * 70)
result3 = send_message("""Condições: na compra de combo always
Segmento: distribuidores de São Paulo""")

print("\n" + "=" * 70)
print("PASSO 4: GERAR EXCEL (MOMENTO DA VERDADE!)")
print("=" * 70)
result4 = send_message("gerar excel")

# ANÁLISE FINAL
print("\n" + "=" * 70)
print("📊 ANÁLISE FINAL")
print("=" * 70)

if result4:
    print(f"✅ Orchestrator respondeu: {result4.get('success')}")
    print(f"📋 Status final: {result4.get('status')}")
    
    if result4.get('state') and result4['state'].get('data'):
        data = result4['state']['data']
        
        print("\n🔍 CAMPOS NO ESTADO:")
        for key in data.keys():
            if key == "excel_base64":
                print(f"  ✅ {key}: {len(data[key])} caracteres")
            elif key == "excel_filename":
                print(f"  ✅ {key}: {data[key]}")
            else:
                value = str(data[key])[:50]
                print(f"  - {key}: {value}...")
        
        if "excel_base64" in data and "excel_filename" in data:
            print("\n🎉 SUCESSO TOTAL!")
            print("✅ Excel gerado")
            print("✅ Base64 presente")
            print("✅ Filename presente")
            print("✅ Frontend deveria fazer download automático!")
        else:
            print("\n⚠️ PROBLEMA DETECTADO:")
            if "excel_base64" not in data:
                print("❌ excel_base64 NÃO está no estado")
            if "excel_filename" not in data:
                print("❌ excel_filename NÃO está no estado")
    else:
        print("\n❌ Estado vazio ou sem data")
else:
    print("❌ Orchestrator não respondeu ao comando 'gerar excel'")

print("\n" + "=" * 70)
print("🏁 TESTE FINALIZADO")
print("=" * 70)
