@echo off
REM ==============================================================================
REM NetIntel Real-Time Network Intelligence Platform - Windows Launcher
REM ==============================================================================

cls
echo ==============================================================================
echo   NetIntel: Network Intelligence Platform ^& Live Power BI Analytics
echo ==============================================================================
echo.
echo   Select an option to run:
echo   [1] Run All (Engine + Streamlit Dashboard + Power BI Live API)
echo   [2] Launch Streamlit Observability Dashboard
echo   [3] Run Telemetry Collection Engine (Continuous)
echo   [4] Start Power BI Local Live REST API (port 8080)
echo   [5] Start Power BI Desktop Auto-Refresher Daemon
echo   [6] Sync / Export Star Schema Datasets for Power BI
echo   [7] Inject Network Simulation Scenario (High Latency Spike)
echo   [8] Run Automated Unit Tests (pytest)
echo   [9] Generate Intelligence & Viva Reports (into output/)
echo   [10] Exit
echo.

set /p choice="Enter choice (1-10): "

if "%choice%"=="1" (
    python manage.py run-all
) else if "%choice%"=="2" (
    python manage.py dashboard
) else if "%choice%"=="3" (
    python manage.py engine
) else if "%choice%"=="4" (
    python manage.py powerbi-stream
) else if "%choice%"=="5" (
    python manage.py auto-refresh --interval 5
) else if "%choice%"=="6" (
    python manage.py powerbi-export
    pause
) else if "%choice%"=="7" (
    python manage.py simulate high_latency --count 15
    pause
) else if "%choice%"=="8" (
    python manage.py test
    pause
) else if "%choice%"=="9" (
    python manage.py report
    pause
) else (
    echo Exiting...
)
