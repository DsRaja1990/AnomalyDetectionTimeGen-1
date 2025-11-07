@echo off
REM Azure Function App Deployment - No Cache Version
REM Run this batch file to deploy your function app with cache clearing

echo ========================================
echo Azure Function App Deployment (No Cache)
echo ========================================
echo.

REM Check if PowerShell is available
where powershell >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: PowerShell is not available. Please install PowerShell.
    pause
    exit /b 1
)

REM Prompt for function app details
set /p FUNCTION_APP_NAME="Enter your Function App name: "
set /p RESOURCE_GROUP_NAME="Enter your Resource Group name: "

if "%FUNCTION_APP_NAME%"=="" (
    echo ERROR: Function App name cannot be empty.
    pause
    exit /b 1
)

if "%RESOURCE_GROUP_NAME%"=="" (
    echo ERROR: Resource Group name cannot be empty.
    pause
    exit /b 1
)

echo.
echo Deploying Function App: %FUNCTION_APP_NAME%
echo Resource Group: %RESOURCE_GROUP_NAME%
echo Subscription: 93e72167-374e-4039-bd33-1012ae37cafb
echo.
echo This will:
echo   1. Stop the function app
echo   2. Clear all caches
echo   3. Deploy new code via zip
echo   4. Restart and sync triggers
echo.

set /p CONFIRM="Continue with deployment? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo Deployment cancelled.
    pause
    exit /b 0
)

echo.
echo Starting deployment...
echo.

REM Execute the PowerShell deployment script
powershell -ExecutionPolicy Bypass -File "deploy_no_cache.ps1" -FunctionAppName "%FUNCTION_APP_NAME%" -ResourceGroupName "%RESOURCE_GROUP_NAME%"

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS: DEPLOYMENT COMPLETED SUCCESSFULLY!
    echo ========================================
    echo.
    echo Your function app has been deployed with:
    echo   - All caches cleared
    echo   - Fresh code deployment
    echo   - Triggers synchronized
    echo.
    echo Check the function logs to verify the new deployment version is active.
    echo Look for the deployment version log message in your function execution.
) else (
    echo.
    echo ========================================
    echo ERROR: DEPLOYMENT FAILED!
    echo ========================================
    echo.
    echo Please check the error messages above and try again.
)

echo.
pause
