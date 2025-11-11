@echo off
REM Script para criar ambiente Python 3.11 com Conda
REM Para PromoAgente Azure Functions

echo ========================================
echo  PromoAgente - Setup Python 3.11
echo ========================================
echo.

echo [1/5] Criando ambiente conda com Python 3.11...
call conda create -n promoagente-azure python=3.11 -y

echo.
echo [2/5] Ativando ambiente...
call conda activate promoagente-azure

echo.
echo [3/5] Atualizando pip...
python -m pip install --upgrade pip

echo.
echo [4/5] Instalando dependencias do projeto...
pip install -r requirements.txt

echo.
echo [5/5] Instalando Azure Functions...
pip install azure-functions

echo.
echo ========================================
echo  INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo Para ativar o ambiente, execute:
echo    conda activate promoagente-azure
echo.
echo Para verificar a versao do Python:
echo    python --version
echo.
echo Proximos passos:
echo    1. Instalar Azure Functions Core Tools
echo    2. Criar estrutura de Functions
echo    3. Testar localmente
echo.
pause
