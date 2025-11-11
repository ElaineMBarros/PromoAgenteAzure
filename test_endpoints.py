"""
Script de teste dos endpoints Azure
"""
import requests
import json

BASE_URL = "https://promoagente-func.azurewebsites.net"

def test_chat():
    """Testa o endpoint /api/chat"""
    url = f"{BASE_URL}/api/chat"
    payload = {
        "message": "Olá, quero criar uma promoção"
    }
    
    print(f"\n🧪 Testando: {url}")
    print(f"📤 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"📊 Status: {response.status_code}")
        print(f"📥 Response: {response.text[:500]}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_extract():
    """Testa o endpoint /api/extract"""
    url = f"{BASE_URL}/api/extract"
    payload = {
        "text": "Promoção de desconto de 10% na compra de 5 caixas"
    }
    
    print(f"\n🧪 Testando: {url}")
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"📊 Status: {response.status_code}")
        print(f"📥 Response: {response.text[:200]}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_status():
    """Testa o endpoint /api/status"""
    url = f"{BASE_URL}/api/status"
    
    print(f"\n🧪 Testando: {url}")
    try:
        response = requests.get(url, timeout=30)
        print(f"📊 Status: {response.status_code}")
        print(f"📥 Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("   TESTE DE ENDPOINTS AZURE FUNCTIONS")
    print("=" * 60)
    
    results = {
        "/api/chat": test_chat(),
        "/api/extract": test_extract(),
        "/api/status": test_status()
    }
    
    print("\n" + "=" * 60)
    print("   RESULTADO DOS TESTES")
    print("=" * 60)
    for endpoint, success in results.items():
        status = "✅ OK" if success else "❌ FALHOU"
        print(f"{endpoint:20} {status}")
    print("=" * 60)
