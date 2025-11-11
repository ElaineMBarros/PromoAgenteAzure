"""
Script para testar OrchestratorFunction no Azure
"""
import requests
import json

# URL da function no Azure
ORCHESTRATOR_URL = "https://promoagente-func.azurewebsites.net/api/orchestrator"

def test_orchestrator():
    """Testa o Orchestrator com uma mensagem simples"""
    
    payload = {
        "message": "Promoção progressiva Nivea de janeiro a março de 2026, até 8.4% OFF"
    }
    
    print("🚀 Testando OrchestratorFunction no Azure...")
    print(f"📧 Enviando: {payload['message']}")
    print()
    
    try:
        response = requests.post(
            ORCHESTRATOR_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCESSO!")
            print()
            print("📋 Resposta:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"❌ ERRO {response.status_code}")
            print()
            print("Resposta:")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    test_orchestrator()
