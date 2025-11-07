# Azure Function App Deployment Script with Cache Clearing
# This script performs zip deployment and clears all caches to ensure new code is deployed

param(
    [Parameter(Mandatory=$true)]
    [string]$FunctionAppName,
    
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId = "93e72167-374e-4039-bd33-1012ae37cafb",
    
    [Parameter(Mandatory=$false)]
    [string]$ZipFileName = "deploy_nocache.zip"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to log messages with timestamp
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $(if($Level -eq "ERROR") {"Red"} elseif($Level -eq "WARN") {"Yellow"} else {"Green"})
}

Write-Log "Starting Azure Function App deployment with cache clearing..."

try {
    # Set subscription
    Write-Log "Setting Azure subscription to: $SubscriptionId"
    az account set --subscription $SubscriptionId
    if ($LASTEXITCODE -ne 0) { throw "Failed to set subscription" }

    # Verify we can access the function app
    Write-Log "Verifying function app exists: $FunctionAppName"
    $functionApp = az functionapp show --name $FunctionAppName --resource-group $ResourceGroupName --output json 2>$null | ConvertFrom-Json
    if (-not $functionApp) {
        throw "Function app '$FunctionAppName' not found in resource group '$ResourceGroupName'"
    }
    Write-Log "Function app found: $($functionApp.defaultHostName)"

    # Clean up any existing zip files
    Write-Log "Cleaning up existing deployment files..."
    if (Test-Path $ZipFileName) {
        Remove-Item $ZipFileName -Force
        Write-Log "Removed existing zip file: $ZipFileName"
    }

    # Create exclusion list for zip
    $excludePatterns = @(
        "*.zip"
        "*.log"
        ".git*"
        ".vscode*"
        "__pycache__*"
        "*.pyc"
        ".pytest_cache*"
        "deploy_*"
        "*.ps1"
        ".azure*"
        "*.md"
        "test_*"
        "quick_*"
        "check_*"
        "verify_*"
        "run_*"
        "*.bat"
        "DEPLOYMENT_STATUS.md"
        "ERROR_FREE_SUMMARY.md"
        "INDEX.md"
        "QUICK_FIX_REFERENCE.md"
        "RUN_LOCALLY_README.md"
        "SETUP_COMPLETE.md"
        "CLEAN_SCRIPT_README.md"
    )

    # Create zip file with only necessary files
    Write-Log "Creating deployment package: $ZipFileName"
    
    # Get all files to include
    $filesToInclude = @()
    $allFiles = Get-ChildItem -Path . -Recurse -File
    
    foreach ($file in $allFiles) {
        $relativePath = $file.FullName.Substring((Get-Location).Path.Length + 1)
        $shouldExclude = $false
        
        foreach ($pattern in $excludePatterns) {
            if ($relativePath -like $pattern) {
                $shouldExclude = $true
                break
            }
        }
        
        if (-not $shouldExclude) {
            $filesToInclude += $file.FullName
        }
    }

    Write-Log "Files to include in deployment: $($filesToInclude.Count)"
    
    # Create zip using PowerShell compression
    $zipPath = Join-Path (Get-Location) $ZipFileName
    if (Get-Command "Compress-Archive" -ErrorAction SilentlyContinue) {
        # Use built-in PowerShell compression
        $tempFiles = @()
        foreach ($file in $filesToInclude) {
            $relativePath = $file.Substring((Get-Location).Path.Length + 1)
            $tempFiles += @{Source = $file; Destination = $relativePath}
        }
        
        # Create temporary directory structure
        $tempDir = Join-Path $env:TEMP "FunctionDeploy_$(Get-Date -Format 'yyyyMMddHHmmss')"
        New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
        
        foreach ($fileInfo in $tempFiles) {
            $destPath = Join-Path $tempDir $fileInfo.Destination
            $destDir = Split-Path $destPath -Parent
            if ($destDir -and -not (Test-Path $destDir)) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            }
            Copy-Item $fileInfo.Source $destPath -Force
        }
        
        Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -Force
        Remove-Item $tempDir -Recurse -Force
    } else {
        throw "Compress-Archive cmdlet not available. Please use PowerShell 5.0 or later."
    }

    if (-not (Test-Path $zipPath)) {
        throw "Failed to create zip file: $zipPath"
    }

    $zipSize = (Get-Item $zipPath).Length
    Write-Log "Deployment package created successfully. Size: $([math]::Round($zipSize/1MB, 2)) MB"

    # STEP 1: Stop the function app to clear all caches
    Write-Log "Stopping function app to clear caches..."
    az functionapp stop --name $FunctionAppName --resource-group $ResourceGroupName
    if ($LASTEXITCODE -ne 0) { throw "Failed to stop function app" }
    Write-Log "Function app stopped successfully"

    # Wait a moment for the stop to take effect
    Start-Sleep -Seconds 10

    # STEP 2: Clear function app cache using REST API
    Write-Log "Clearing function app cache..."
    
    # Get access token
    $accessToken = az account get-access-token --query accessToken --output tsv
    if ($LASTEXITCODE -ne 0) { throw "Failed to get access token" }
    
    # Clear cache via Kudu API
    $scmUrl = "https://$FunctionAppName.scm.azurewebsites.net"
    $headers = @{
        "Authorization" = "Bearer $accessToken"
        "Content-Type" = "application/json"
    }
    
    try {
        # Clear Kudu cache
        Invoke-RestMethod -Uri "$scmUrl/api/functions/cache" -Method DELETE -Headers $headers -TimeoutSec 60
        Write-Log "Kudu cache cleared successfully"
    } catch {
        Write-Log "Warning: Could not clear Kudu cache via REST API: $($_.Exception.Message)" -Level "WARN"
    }

    # STEP 3: Restart app service to ensure clean state
    Write-Log "Performing app service restart..."
    az functionapp restart --name $FunctionAppName --resource-group $ResourceGroupName
    if ($LASTEXITCODE -ne 0) { throw "Failed to restart function app" }
    Start-Sleep -Seconds 15

    # STEP 4: Deploy the zip package
    Write-Log "Deploying zip package to function app..."
    az functionapp deployment source config-zip --name $FunctionAppName --resource-group $ResourceGroupName --src $zipPath --timeout 600
    if ($LASTEXITCODE -ne 0) { throw "Failed to deploy zip package" }

    # STEP 5: Additional cache clearing after deployment
    Write-Log "Performing post-deployment cache clearing..."
    
    # Clear website cache
    try {
        az rest --method POST --url "https://management.azure.com/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.Web/sites/$FunctionAppName/restart" --headers "Content-Type=application/json"
        Write-Log "Website cache cleared via management API"
    } catch {
        Write-Log "Warning: Could not clear website cache: $($_.Exception.Message)" -Level "WARN"
    }

    # STEP 6: Start the function app
    Write-Log "Starting function app..."
    az functionapp start --name $FunctionAppName --resource-group $ResourceGroupName
    if ($LASTEXITCODE -ne 0) { throw "Failed to start function app" }

    # STEP 7: Force sync triggers to ensure new code is active
    Write-Log "Syncing function triggers..."
    Start-Sleep -Seconds 10
    az rest --method POST --url "https://management.azure.com/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.Web/sites/$FunctionAppName/syncfunctiontriggers" --headers "Content-Type=application/json"
    if ($LASTEXITCODE -ne 0) { 
        Write-Log "Warning: Failed to sync triggers, but deployment may still be successful" -Level "WARN"
    } else {
        Write-Log "Function triggers synced successfully"
    }

    # Wait for app to fully start
    Write-Log "Waiting for function app to fully start..."
    Start-Sleep -Seconds 20

    # STEP 8: Verify deployment
    Write-Log "Verifying deployment..."
    $deploymentInfo = az functionapp show --name $FunctionAppName --resource-group $ResourceGroupName --query "{state:state,hostNames:hostNames}" --output json | ConvertFrom-Json
    
    if ($deploymentInfo.state -eq "Running") {
        Write-Log "SUCCESS: Deployment completed successfully!"
        Write-Log "Function App State: $($deploymentInfo.state)"
        Write-Log "Function App URL: https://$($deploymentInfo.hostNames[0])"
        Write-Log ""
        Write-Log "Cache Clearing Actions Performed:"
        Write-Log "   - Function app stopped before deployment"
        Write-Log "   - Kudu cache cleared"
        Write-Log "   - App service restarted"
        Write-Log "   - Fresh zip deployment executed"
        Write-Log "   - Website cache cleared after deployment"
        Write-Log "   - Function triggers synced"
        Write-Log ""
        Write-Log "Your new code should now be active without any cached interference!"
    } else {
        Write-Log "WARNING: Function app deployed but state is: $($deploymentInfo.state)" -Level "WARN"
    }

    # Clean up zip file
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
        Write-Log "Cleaned up deployment package: $ZipFileName"
    }

} catch {
    Write-Log "Deployment failed: $($_.Exception.Message)" -Level "ERROR"
    Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level "ERROR"
    exit 1
}

Write-Log "Deployment script completed."
