@echo off
chcp 65001 > nul
title New Results - Sistema Gestão Sindical
color 0A

echo ==================================================
echo 🚀 INICIANDO NEW RESULTS - VERSÃO COMPLETA
echo ==================================================
echo.

:: Entra na pasta correta
cd /d "C:\Users\marce\Desktop\Automacao_Gestao_Sindical"

:: Inicia o painel principal atualizado
echo ⏳ Carregando interface principal... Aguarde...
echo.

:: Abre o navegador automaticamente alguns segundos após iniciar
start "" cmd /c "timeout /t 4 > nul && start http://localhost:8501"

if exist ".venv\Scripts\python.exe" (
	.venv\Scripts\python.exe -m streamlit run app_plataforma.py --server.port=8501
) else (
	python -m streamlit run app_plataforma.py --server.port=8501
)

:: Essa linha abaixo SÓ VAI SER EXECUTADA quando você fechar o sistema
pause
exit