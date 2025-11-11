"""
Teste com promoção real - Nivea Farmácia
"""
import requests
import json

BASE_URL = "https://promoagente-func.azurewebsites.net"

def test_promo_real():
    """Testa com texto real de promoção"""
    
    print("\n" + "="*60)
    print("🧪 TESTE COM PROMOÇÃO REAL - NIVEA FARMÁCIA")
    print("="*60)
    
    # Texto exatamente como o usuário passou
    texto_promo = """farma p quer nivea mas so quer rollon
se colocar creme junto abre 5
se colocar body junto sobe pra 7
minimo 6 caixas por familia
nao lembro data acho do dia 10 ao 30"""
    
    print("\n📝 TEXTO DA PROMOÇÃO:")
    print("-" * 60)
    print(texto_promo)
    print("-" * 60)
    
    # Envia para o Orchestrator
    print("\n🚀 Enviando para o backend...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orchestrator",
            json={
                "message": texto_promo
            },
            timeout=90
        )
        
        print(f"\n📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Sucesso!")
            print(f"\n🤖 Resposta do Sistema:")
            print("-" * 60)
            print(result.get("response", ""))
            print("-" * 60)
            
            print(f"\n📋 Status: {result.get('status')}")
            print(f"📦 Session ID: {result.get('session_id')}")
            
            # Mostra dados extraídos
            state = result.get("state", {})
            promo_data = state.get("data", {})
            
            if promo_data:
                print(f"\n📊 DADOS EXTRAÍDOS:")
                print("-" * 60)
                for key, value in promo_data.items():
                    if value and key not in ["multiple_promotions", "erro"]:
                        print(f"  ✅ {key}: {value}")
                print("-" * 60)
            
            # Analisa resultado
            print(f"\n🔍 ANÁLISE:")
            print("-" * 60)
            
            campos_obrigatorios = [
                "titulo", "mecanica", "descricao", 
                "periodo_inicio", "periodo_fim",
                "condicoes", "recompensas", "produtos", "segmentacao"
            ]
            
            campos_presentes = [c for c in campos_obrigatorios if promo_data.get(c)]
            campos_faltando = [c for c in campos_obrigatorios if not promo_data.get(c)]
            
            print(f"✅ Campos presentes ({len(campos_presentes)}/9): {', '.join(campos_presentes)}")
            if campos_faltando:
                print(f"⚠️  Campos faltando ({len(campos_faltando)}/9): {', '.join(campos_faltando)}")
            
            if len(campos_presentes) == 9:
                print(f"\n🎉 PERFEITO! Todos os 9 campos obrigatórios foram extraídos!")
                print(f"   Sistema vai validar na próxima mensagem.")
            else:
                print(f"\n💡 Faltam {len(campos_faltando)} campos.")
                print(f"   Sistema vai pedir essas informações.")
            
            print("-" * 60)
            
            return result
            
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_promo_real()
    
    print("\n" + "="*60)
    print("🏁 TESTE CONCLUÍDO!")
    print("="*60)
