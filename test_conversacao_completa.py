"""
Teste de conversação completa - Múltiplas mensagens
Valida se o sistema mantém dados entre mensagens
"""
import requests
import json

BASE_URL = "https://promoagente-func.azurewebsites.net"

def test_conversacao():
    """Testa conversação multi-mensagem"""
    
    print("\n" + "="*70)
    print("🧪 TESTE DE CONVERSAÇÃO COMPLETA - MÚLTIPLAS MENSAGENS")
    print("="*70)
    
    session_id = None
    current_state = None
    
    # MENSAGEM 1: Dados iniciais
    print("\n📝 MENSAGEM 1: Dados iniciais da promoção")
    print("-" * 70)
    
    msg1 = """Promoção Luminous perfumaria grande
desconto direto de 10% na compra do SKU Luminous
8 caixas por SKU
de 01/04/2026 a 15/04/2026"""
    
    print(msg1)
    print("-" * 70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orchestrator",
            json={"message": msg1},
            timeout=90
        )
        
        if response.status_code == 200:
            result = response.json()
            session_id = result.get("session_id")
            current_state = result.get("state")
            
            print(f"\n✅ Status: {response.status_code}")
            print(f"📦 Session ID: {session_id}")
            print(f"\n🤖 Resposta:")
            print(result.get("response", ""))
            
            # Dados após msg 1
            dados1 = current_state.get("data", {})
            print(f"\n📊 DADOS APÓS MENSAGEM 1:")
            for key, value in dados1.items():
                if value and key not in ["multiple_promotions", "erro"]:
                    print(f"  ✅ {key}: {value}")
        else:
            print(f"❌ Erro: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return
    
    # MENSAGEM 2: Complementa informações
    print("\n\n📝 MENSAGEM 2: Complementando informações")
    print("-" * 70)
    
    msg2 = "a recompensa é o desconto de 10% e o segmento é distribuidores de São Paulo"
    
    print(msg2)
    print("-" * 70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orchestrator",
            json={
                "message": msg2,
                "session_id": session_id,
                "current_state": current_state
            },
            timeout=90
        )
        
        if response.status_code == 200:
            result = response.json()
            current_state = result.get("state")
            
            print(f"\n✅ Status: {response.status_code}")
            print(f"\n🤖 Resposta:")
            print(result.get("response", ""))
            
            # Dados após msg 2
            dados2 = current_state.get("data", {})
            print(f"\n📊 DADOS APÓS MENSAGEM 2:")
            for key, value in dados2.items():
                if value and key not in ["multiple_promotions", "erro"]:
                    print(f"  ✅ {key}: {value}")
            
            # VALIDAÇÃO CRÍTICA: Verifica se manteve dados da mensagem 1
            print(f"\n🔍 VALIDAÇÃO CRÍTICA:")
            print("-" * 70)
            
            campos_msg1 = ["titulo", "descricao", "periodo_inicio", "periodo_fim", "condicoes"]
            campos_mantidos = []
            campos_perdidos = []
            
            for campo in campos_msg1:
                if dados2.get(campo):
                    campos_mantidos.append(campo)
                elif dados1.get(campo):
                    campos_perdidos.append(campo)
            
            if campos_perdidos:
                print(f"❌ FALHA! Sistema PERDEU dados da mensagem 1:")
                print(f"   Campos perdidos: {', '.join(campos_perdidos)}")
            else:
                print(f"✅ SUCESSO! Sistema MANTEVE todos os dados da mensagem 1!")
                print(f"   Campos mantidos: {', '.join(campos_mantidos)}")
            
            # Verifica se adicionou novos campos
            campos_novos = []
            for campo in ["recompensas", "segmentacao"]:
                if dados2.get(campo) and not dados1.get(campo):
                    campos_novos.append(campo)
            
            if campos_novos:
                print(f"✅ Adicionou novos campos: {', '.join(campos_novos)}")
            
            print("-" * 70)
            
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("🏁 TESTE CONCLUÍDO!")
    print("="*70)


if __name__ == "__main__":
    test_conversacao()
