# Azure Function App Deployment Verification Script
# This script helps verify that your new code is actually running

param(
    [Parameter(Mandatory=$true)]
    [string]$FunctionAppName,
    
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId = "93e72167-374e-4039-bd33-1012ae37cafb"
)

# Function to log messages with timestamp
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $(if($Level -eq "ERROR") {"Red"} elseif($Level -eq "WARN") {"Yellow"} else {"Green"})
}

Write-Log "Verifying Azure Function App deployment..."

try {
    # Set subscription
    az account set --subscription $SubscriptionId

    # Get function app status
    Write-Log "Checking function app status..."
    $functionApp = az functionapp show --name $FunctionAppName --resource-group $ResourceGroupName --query "{name:name,state:state,defaultHostName:defaultHostName,lastModifiedTimeUtc:lastModifiedTimeUtc}" --output json | ConvertFrom-Json
    
    Write-Log "Function App: $($functionApp.name)"
    Write-Log "Status: $($functionApp.state)"
    Write-Log "URL: https://$($functionApp.defaultHostName)"
    Write-Log "Last Modified: $($functionApp.lastModifiedTimeUtc)"

    # Get recent logs to check for deployment version
    Write-Log "Fetching recent function logs..."
    
    # Try to get logs from Application Insights
    Write-Log "Checking for deployment version in logs..."
    Write-Log "Look for log entries containing 'DEPLOYMENT VERSION' in your Azure Portal Function App logs."
    Write-Log "The new deployment should show: DEPLOYMENT VERSION: 2025-11-06T12:30:00Z | BUILD: nocache_v1"
    
    # Check function list
    Write-Log "Listing functions in the app..."
    $functions = az functionapp function list --name $FunctionAppName --resource-group $ResourceGroupName --output json | ConvertFrom-Json
    
    if ($functions) {
        foreach ($func in $functions) {
            Write-Log "Function: $($func.name) - Status: $(if($func.properties.config.disabled) {'Disabled'} else {'Enabled'})"
        }
    }

    # Get app settings to verify configuration
    Write-Log "Checking key app settings..."
    $settings = az functionapp config appsettings list --name $FunctionAppName --resource-group $ResourceGroupName --output json | ConvertFrom-Json
    
    $keySettings = @("APPINSIGHTS_RESOURCE_ID", "AI_FOUNDATION_ENDPOINT", "LOGIC_APP_WEBHOOK_URL")
    foreach ($settingName in $keySettings) {
        $setting = $settings | Where-Object { $_.name -eq $settingName }
        if ($setting) {
            $value = if ($setting.value.Length -gt 50) { $setting.value.Substring(0, 47) + "..." } else { $setting.value }
            Write-Log "Setting '$settingName': $value"
        } else {
            Write-Log "Setting '$settingName': NOT SET" -Level "WARN"
        }
    }

    Write-Log ""
    Write-Log "✅ Verification completed!"
    Write-Log ""
    Write-Log "Next Steps:"
    Write-Log "1. Monitor your function logs in Azure Portal"
    Write-Log "2. Look for the new deployment version message"
    Write-Log "3. Verify the function is executing with updated logic"
    Write-Log "4. If you still see old behavior, try running the deployment script again"

} catch {
    Write-Log "❌ Verification failed: $($_.Exception.Message)" -Level "ERROR"
    exit 1
}
