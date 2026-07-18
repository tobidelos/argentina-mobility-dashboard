@echo off
echo ==============================================
echo    Observatorio de Movilidad Urbana (ETL/BI)
echo ==============================================
echo.
echo 1. Ejecutar ETL (main.py)
echo 2. Lanzar Dashboard (Streamlit)
echo 3. Correr Tests (Pytest)
echo 4. Salir
echo.

set /p choice=Selecciona una opcion (1-4): 

if "%choice%"=="1" (
    echo.
    echo Ejecutando Pipeline ETL...
    venv\Scripts\python main.py
    pause
    goto end
)
if "%choice%"=="2" (
    echo.
    echo Iniciando Dashboard en el navegador...
    venv\Scripts\streamlit run src\dashboard.py
    goto end
)
if "%choice%"=="3" (
    echo.
    echo Corriendo Pruebas Unitarias...
    venv\Scripts\pytest tests/
    pause
    goto end
)
if "%choice%"=="4" (
    goto end
)

echo Opcion invalida.
pause
:end
