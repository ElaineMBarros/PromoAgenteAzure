"""
Script para adaptar Validator e Sumarizer para Azure OpenAI
"""
import re

# Função para adaptar um arquivo
def adapt_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Trocar import
    content = content.replace(
        'from openai import AsyncOpenAI',
        'from openai import AsyncAzureOpenAI'
    )
    
    # 2. Trocar config
    content = re.sub(
        r'# Configuração\nOPENAI_API_KEY.*?\nOPENAI_MODEL.*?\n',
        '''# Configuração Azure OpenAI
AZURE_OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("OPENAI_API_ENDPOINT", "https://eastus.api.cognitive.microsoft.com/")
AZURE_OPENAI_DEPLOYMENT = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
''',
        content,
        flags=re.DOTALL
    )
    
    # 3. Trocar check de API key
    content = content.replace(
        'if not OPENAI_API_KEY:',
        'if not AZURE_OPENAI_KEY:'
    )
    content = content.replace(
        '"OpenAI API Key não configurada"',
        '"Azure OpenAI API Key não configurada"'
    )
    
    # 4. Trocar client
    content = re.sub(
        r'client = AsyncOpenAI\(api_key=OPENAI_API_KEY\)',
        '''client = AsyncAzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )''',
        content
    )
    
    # 5. Trocar model no create
    content = re.sub(
        r'model=OPENAI_MODEL,',
        'model=AZURE_OPENAI_DEPLOYMENT,',
        content
    )
    
    # 6. Trocar log
    content = re.sub(
        r'logger\.info\(f"🤖 Chamando OpenAI \(modelo: {OPENAI_MODEL}\)"\)',
        'logger.info(f"🤖 Chamando Azure OpenAI (deployment: {AZURE_OPENAI_DEPLOYMENT})")',
        content
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {filepath} atualizado")

# Adaptar ValidatorFunction
adapt_file('ValidatorFunction/__init__.py')

# Adaptar SumarizerFunction  
adapt_file('SumarizerFunction/__init__.py')

print("\n🎉 Todas as functions adaptadas para Azure OpenAI!")
