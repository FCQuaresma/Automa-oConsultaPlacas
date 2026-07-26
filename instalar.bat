@echo off
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python nao foi encontrado neste computador.
    echo Baixe e instale em https://www.python.org/downloads/
    echo IMPORTANTE: na instalacao, marque a opcao "Add python.exe to PATH".
    pause
    exit /b 1
)

echo Instalando dependencias, aguarde...
python -m pip install -r requirements.txt

echo.
echo Instalacao concluida. Agora use o arquivo run.bat para rodar as consultas.
pause
