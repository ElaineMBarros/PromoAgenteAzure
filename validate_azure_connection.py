"""
Script de Validação de Conexão Azure
Verifica recursos disponíveis e configuração do ambiente
"""
import os
import sys
import json
from datetime import datetime

def print_header(text):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_success(text):
    """Imprime mensagem de sucesso"""
    print(f"✅ {text}")

def print_error(text):
    """Imprime mensagem de erro"""
    print(f"❌ {text}")

def print_info(text):
    """Imprime mensagem informativa"""
    print(f"ℹ️  {text}")

def check_azure_cli():
    """Verifica se Azure CLI está instalado"""
    import subprocess
    try:
        result = subprocess.run(
            ["az", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print_success("Azure CLI instalado")
            # Extrai versão
            version_line = result.stdout.split('\n')[0]
            print_info(f"   {version_line}")
            return True
        else:
            print_error("Azure CLI não está funcionando corretamente")
            return False
    except FileNotFoundError:
        print_error("Azure CLI não está instalado")
        print_info("   Instale: https://docs.microsoft.com/cli/azure/install-azure-cli")
        return False
    except Exception as e:
        print_error(f"Erro ao verificar Azure CLI: {e}")
        return False

def check_azure_login():
    """Verifica se está logado no Azure"""
    import subprocess
    try:
        result = subprocess.run(
            ["az", "account", "show"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            account_info = json.loads(result.stdout)
            print_success("Logado no Azure")
            print_info(f"   Subscription: {account_info.get('name')}")
            print_info(f"   ID: {account_info.get('id')}")
            print_info(f"   Tenant: {account_info.get('tenantId')}")
            return True, account_info
        else:
            print_error("Não está logado no Azure")
            print_info("   Execute: az login")
            return False, None
    except Exception as e:
        print_error(f"Erro ao verificar login: {e}")
        return False, None

def list_resource_groups():
    """Lista Resource Groups disponíveis"""
    import subprocess
    try:
        result = subprocess.run(
            ["az", "group", "list", "--query", "[].{Name:name, Location:location}", "-o", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            groups = json.loads(result.stdout)
            print_success(f"Resource Groups disponíveis: {len(groups)}")
            for group in groups:
                print_info(f"   • {group['Name']} ({group['Location']})")
            return groups
        else:
            print_error("Erro ao listar Resource Groups")
            return []
    except Exception as e:
        print_error(f"Erro ao listar Resource Groups: {e}")
        return []

def check_ai_resources(resource_group_name=None):
    """Verifica recursos de IA no Resource Group"""
    import subprocess
    
    if not resource_group_name:
        print_info("Para verificar recursos específicos, forneça o nome do Resource Group")
        return
    
    try:
        # Lista todos os recursos do RG
        result = subprocess.run(
            ["az", "resource", "list", "--resource-group", resource_group_name, "-o", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            resources = json.loads(result.stdout)
            print_success(f"Recursos no RG '{resource_group_name}': {len(resources)}")
            
            # Categoriza recursos
            openai_resources = []
            cosmos_resources = []
            storage_resources = []
            function_resources = []
            other_resources = []
            
            for resource in resources:
                res_type = resource.get('type', '').lower()
                name = resource.get('name')
                
                if 'openai' in res_type or 'cognitiveservices' in res_type:
                    openai_resources.append(name)
                elif 'cosmosdb' in res_type or 'documentdb' in res_type:
                    cosmos_resources.append(name)
                elif 'storage' in res_type:
                    storage_resources.append(name)
                elif 'function' in res_type or 'web' in res_type:
                    function_resources.append(name)
                else:
                    other_resources.append((name, res_type))
            
            # Exibe recursos categorizados
            if openai_resources:
                print_info("   🤖 OpenAI / Cognitive Services:")
                for name in openai_resources:
                    print(f"      • {name}")
            
            if cosmos_resources:
                print_info("   🗄️  Cosmos DB:")
                for name in cosmos_resources:
                    print(f"      • {name}")
            
            if storage_resources:
                print_info("   💾 Storage Accounts:")
                for name in storage_resources:
                    print(f"      • {name}")
            
            if function_resources:
                print_info("   ⚡ Functions / Web Apps:")
                for name in function_resources:
                    print(f"      • {name}")
            
            if other_resources:
                print_info("   📦 Outros Recursos:")
                for name, res_type in other_resources:
                    print(f"      • {name} ({res_type})")
            
            return resources
        else:
            print_error(f"Erro ao listar recursos do RG '{resource_group_name}'")
            print_info(f"   {result.stderr}")
            return []
            
    except Exception as e:
        print_error(f"Erro ao verificar recursos: {e}")
        return []

def check_openai_service(resource_group_name=None):
    """Verifica se há Azure OpenAI Service disponível"""
    import subprocess
    
    if not resource_group_name:
        return
    
    try:
        result = subprocess.run(
            ["az", "cognitiveservices", "account", "list", 
             "--resource-group", resource_group_name, "-o", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            services = json.loads(result.stdout)
            openai_services = [s for s in services if 'openai' in s.get('kind', '').lower()]
            
            if openai_services:
                print_success(f"Azure OpenAI Services encontrados: {len(openai_services)}")
                for service in openai_services:
                    print_info(f"   • {service['name']}")
                    print_info(f"     Endpoint: {service.get('properties', {}).get('endpoint')}")
                    print_info(f"     Location: {service.get('location')}")
                    print_info(f"     SKU: {service.get('sku', {}).get('name')}")
                return openai_services
            else:
                print_info("   Nenhum Azure OpenAI Service encontrado neste RG")
                return []
        else:
            print_info("   Não foi possível verificar Cognitive Services")
            return []
            
    except Exception as e:
        print_info(f"   Erro ao verificar OpenAI Service: {e}")
        return []

def main():
    """Função principal"""
    print_header("🔍 VALIDAÇÃO DE CONEXÃO AZURE")
    print(f"Executado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    # 1. Verifica Azure CLI
    print_header("1. Azure CLI")
    if not check_azure_cli():
        print("\n⚠️  Azure CLI é necessário para continuar")
        return
    
    # 2. Verifica Login
    print_header("2. Autenticação Azure")
    is_logged_in, account_info = check_azure_login()
    if not is_logged_in:
        print("\n⚠️  Faça login para continuar: az login")
        return
    
    # 3. Lista Resource Groups
    print_header("3. Resource Groups")
    groups = list_resource_groups()
    
    if not groups:
        print("\n⚠️  Nenhum Resource Group encontrado")
        return
    
    # 4. Pergunta qual RG verificar (se houver vários)
    print_header("4. Recursos de IA")
    
    # Procura por RGs com nome relacionado a IA
    ia_groups = [g for g in groups if 'ia' in g['Name'].lower() or 'ai' in g['Name'].lower() or 'cognitive' in g['Name'].lower()]
    
    if ia_groups:
        print_success(f"Resource Groups de IA encontrados: {len(ia_groups)}")
        for group in ia_groups:
            rg_name = group['Name']
            print_info(f"\n📂 Verificando RG: {rg_name}")
            resources = check_ai_resources(rg_name)
            check_openai_service(rg_name)
    else:
        print_info("Nenhum RG com nome relacionado a IA encontrado")
        print_info("Listando primeiro RG disponível como exemplo...")
        if groups:
            first_rg = groups[0]['Name']
            check_ai_resources(first_rg)
    
    # 5. Resumo final
    print_header("✅ VALIDAÇÃO COMPLETA")
    print_success("Azure conectado e configurado")
    print_info(f"   Subscription: {account_info.get('name')}")
    print_info(f"   Resource Groups: {len(groups)}")
    
    if ia_groups:
        print_success(f"Resource Groups de IA disponíveis: {len(ia_groups)}")
        for g in ia_groups:
            print_info(f"   • {g['Name']}")
    
    print("\n" + "=" * 70)
    print("📝 PRÓXIMOS PASSOS:")
    print("=" * 70)
    print("1. Provisionar recursos faltantes (Cosmos DB, Storage, etc)")
    print("2. Configurar variáveis de ambiente em local.settings.json")
    print("3. Testar Functions localmente: func start")
    print("4. Deploy para Azure: func azure functionapp publish <nome-function-app>")
    print("=" * 70)
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Validação cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
