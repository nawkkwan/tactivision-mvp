param(
    [string]$ResourceGroup = "rg-tactivision-eastasia",
    # Azure for Students currently allows East Asia for both Container Apps
    # and Log Analytics in this subscription.
    [string]$Location = "eastasia",
    [string]$Environment = "tactivision-env",
    [string]$AppName = "tactivision-api"
)

$ErrorActionPreference = "Stop"
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
& "$env:SystemRoot\System32\chcp.com" 65001 | Out-Null

az account show --output none
if ($LASTEXITCODE -ne 0) { throw "Azure account check failed" }
az provider register --namespace Microsoft.App --wait
if ($LASTEXITCODE -ne 0) { throw "Microsoft.App provider registration failed" }
az provider register --namespace Microsoft.OperationalInsights --wait
if ($LASTEXITCODE -ne 0) { throw "Microsoft.OperationalInsights provider registration failed" }
az group create --name $ResourceGroup --location $Location --output none
if ($LASTEXITCODE -ne 0) { throw "Azure resource group creation failed" }

az containerapp up `
    --name $AppName `
    --resource-group $ResourceGroup `
    --location $Location `
    --environment $Environment `
    --source . `
    --ingress external `
    --target-port 8000 `
    --env-vars `
        "MAX_UPLOAD_BYTES=10485760" `
        "MODEL_PATH=/app/backend/models/best.pt" `
        "MODEL_SHA256=DA6A85A5230E4ACFDB4BB10A82B6BB148EADFCF51F7F4AE8787E40CB25E5F47F" `
        "YOLO_CONFIG_DIR=/tmp/ultralytics" `
        "CORS_ORIGINS=https://tactivision-mvp.pages.dev"
if ($LASTEXITCODE -ne 0) { throw "Azure Container App deployment failed" }

az containerapp update `
    --name $AppName `
    --resource-group $ResourceGroup `
    --cpu 1.0 `
    --memory 2.0Gi `
    --min-replicas 0 `
    --max-replicas 1 `
    --output none
if ($LASTEXITCODE -ne 0) { throw "Azure Container App resource update failed" }

$fqdn = az containerapp show `
    --name $AppName `
    --resource-group $ResourceGroup `
    --query properties.configuration.ingress.fqdn `
    --output tsv
if ($LASTEXITCODE -ne 0) { throw "Azure Container App URL lookup failed" }

Write-Host "Azure API: https://$fqdn"
Write-Host "Health:    https://$fqdn/health"
