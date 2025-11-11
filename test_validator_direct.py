"""
Teste Direto do ValidatorFunction
"""
import requests
import json

VALIDATOR_URL = "https://promoagente-func.azurewebsites.net/api/validate"

# Dados exatos do teste anterior
promo_data = {
    "titulo": "Combo Always",
    "mecanica": "combo",
    "descricao": "Combo Always: Básico Seca 8un + Noturno 8un",
    "canal": "TRAD",
    "segmentacao": "Distribuidores de São Paulo",
    "categoria": "Feminino",
    "produtos": ["Básico Seca 8un", "Noturno 8un"],
    "combo": "Básico Seca 8un + Noturno 8un",
    "qt_minima": 12,
    "condicoes": "Mínimo: 12 combos",
    "desconto_percentual": 8,
    "recompensas": "8% OFF",
    "periodo_inicio": "01/03/2026",
    "periodo_fim": "30/03/2026"
}

print("🧪 TESTE DIRETO DO VALIDATOR")
print("=" * 60)
print(f"📊 Dados da promoção:")
print(json.dumps(promo_data, indent=2, ensure_ascii=False))
print("=" * 60)

try:
    print("\n📤 Enviando para ValidatorFunction...")
    
    response = requests.post(
        VALIDATOR_URL,
        json={"promo_data": promo_data},
        timeout=90
    )
    
    print(f"\n📥 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Resposta recebida:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get("is_valid"):
            print("\n🎉 VÁLIDO!")
        else:
            print("\n⚠️ INVÁLIDO!")
            print(f"Feedback: {result.get('feedback')}")
            print(f"Issues: {result.get('issues')}")
    else:
        print(f"\n❌ Erro {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"\n❌ Erro: {type(e).__name__}: {str(e)}")

print("\n" + "=" * 60)
print("🏁 TESTE FINALIZADO")
print("=" * 60)
