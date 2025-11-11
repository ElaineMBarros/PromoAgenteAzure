"""
Teste direto do backend Azure - sem frontend
Testa o fluxo completo de conversação
"""
import requests
import json
from datetime import datetime

# URL do backend Azure
BASE_URL = "https://promoagente-func.azurewebsites.net"

def test_conversation():
    """Testa conversação completa"""
    
    print("\n" + "="*60)
    print("🧪 TESTE DIRETO DO BACKEND AZURE")
    print("="*60)
    
    session_id = None
    current_state = None
    
    # TESTE 1: Primeira mensagem (boas-vindas)
    print("\n📝 TESTE 1: Primeira mensagem")
    print("-" * 60)
    
    response1 = requests.post(
        f"{BASE_URL}/api/orchestrator",
        json={
            "message": "Olá quero criar uma promoção",
            "session_id": session_id,
            "current_state": current_state
        },
        timeout=30
    )
    
    print(f"Status: {response1.status_code}")
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"✅ Sucesso!")
        print(f"\n🤖 Resposta:")
        print(data1.get("response", ""))
        print(f"\n📊 Status: {data1.get('status')}")
        print(f"📦 Session ID: {data1.get('session_id')}")
        
        # Salva para próxima mensagem
        session_id = data1.get("session_id")
        current_state = data1.get("state")
        
        # Mostra dados extraídos
        if current_state and current_state.get("data"):
            print(f"\n📋 Dados extraídos: {current_state['data']}")
    else:
        print(f"❌ Erro: {response1.text}")
        return False
    
    input("\n⏸️  Pressione Enter para continuar para TESTE 2...")
    
    # TESTE 2: Segunda mensagem (dados parciais)
    print("\n📝 TESTE 2: Segunda mensagem (dados parciais)")
    print("-" * 60)
    
    response2 = requests.post(
        f"{BASE_URL}/api/orchestrator",
        json={
            "message": "Promoção Dove 10% OFF comprando 3 unidades",
            "session_id": session_id,
            "current_state": current_state
        },
        timeout=30
    )
    
    print(f"Status: {response2.status_code}")
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"✅ Sucesso!")
        print(f"\n🤖 Resposta:")
        print(data2.get("response", ""))
        print(f"\n📊 Status: {data2.get('status')}")
        
        # Atualiza estado
        current_state = data2.get("state")
        
        # Mostra dados extraídos
        if current_state and current_state.get("data"):
            print(f"\n📋 Dados extraídos:")
            for key, value in current_state['data'].items():
                if value and key != "multiple_promotions":
                    print(f"  ✅ {key}: {value}")
        
        # VERIFICA SE VALIDOU (NÃO DEVERIA!)
        if data2.get("status") == "needs_review" or "validação" in data2.get("response", "").lower():
            print("\n⚠️  PROBLEMA DETECTADO!")
            print("❌ Sistema validou sem ter todos os campos!")
            print("❌ Deveria apenas mostrar dados extraídos e pedir campos faltantes")
        else:
            print("\n✅ OK! Sistema pediu campos faltantes (não validou)")
    else:
        print(f"❌ Erro: {response2.text}")
        return False
    
    input("\n⏸️  Pressione Enter para continuar para TESTE 3...")
    
    # TESTE 3: Terceira mensagem (completar dados)
    print("\n📝 TESTE 3: Terceira mensagem (completar dados)")
    print("-" * 60)
    
    response3 = requests.post(
        f"{BASE_URL}/api/orchestrator",
        json={
            "message": "Tipo desconto, válida de 01/12/2024 a 31/12/2024",
            "session_id": session_id,
            "current_state": current_state
        },
        timeout=30
    )
    
    print(f"Status: {response3.status_code}")
    
    if response3.status_code == 200:
        data3 = response3.json()
        print(f"✅ Sucesso!")
        print(f"\n🤖 Resposta:")
        print(data3.get("response", ""))
        print(f"\n📊 Status: {data3.get('status')}")
        
        # Mostra dados finais
        final_state = data3.get("state")
        if final_state and final_state.get("data"):
            print(f"\n📋 Dados finais:")
            for key, value in final_state['data'].items():
                if value and key not in ["multiple_promotions", "summary"]:
                    print(f"  ✅ {key}: {value}")
        
        # VERIFICA SE VALIDOU (AGORA DEVERIA!)
        if data3.get("status") == "ready":
            print("\n✅ PERFEITO! Sistema validou na hora certa!")
        elif data3.get("status") == "needs_review":
            print("\n⚠️  Sistema validou mas encontrou problemas")
        else:
            print(f"\n⚠️  Status inesperado: {data3.get('status')}")
    else:
        print(f"❌ Erro: {response3.text}")
        return False
    
    print("\n" + "="*60)
    print("🎉 TESTE COMPLETO!")
    print("="*60)
    return True


if __name__ == "__main__":
    try:
        test_conversation()
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
