param(
  [string]$ResourceGroup = "AI-NetZero",
  [string]$Location = "uksouth",
  [string]$AcrName = "astonaiacr",
  [string]$ContainerAppsEnv = "aston-ai-env",
  [string]$BackendAppName = "aston-ai-backend",
  [string]$FrontendAppName = "aston-ai-frontend",
  [string]$BackendImage = "django-backend",
  [string]$FrontendImage = "react-frontend",
  [string]$DbName = "mydatabase",
  [string]$DbUser = "myuser@astonmysql",
  [string]$DbHost = "astonmysql.mysql.database.azure.com",
  [string]$DbPort = "3306",
  [string]$FrontendApiUrl = "",
  [switch]$SkipInfrastructure
)

$ErrorActionPreference = "Stop"

function Require-Command($Name) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "$Name is not installed or is not on PATH."
  }
}

function App-Exists($Name) {
  az containerapp show --name $Name --resource-group $ResourceGroup --only-show-errors 1>$null 2>$null
  return $LASTEXITCODE -eq 0
}

Require-Command az
Require-Command docker

if (-not $env:DJANGO_SECRET_KEY) { throw "Set DJANGO_SECRET_KEY in this PowerShell session before running." }
if (-not $env:DB_PASSWORD) { throw "Set DB_PASSWORD in this PowerShell session before running." }

if (-not $SkipInfrastructure) {
  az group create --name $ResourceGroup --location $Location --only-show-errors | Out-Null

  az acr show --name $AcrName --resource-group $ResourceGroup --only-show-errors 1>$null 2>$null
  if ($LASTEXITCODE -ne 0) {
    az acr create --name $AcrName --resource-group $ResourceGroup --sku Standard --admin-enabled true --only-show-errors | Out-Null
  } else {
    az acr update --name $AcrName --admin-enabled true --only-show-errors | Out-Null
  }

  az containerapp env show --name $ContainerAppsEnv --resource-group $ResourceGroup --only-show-errors 1>$null 2>$null
  if ($LASTEXITCODE -ne 0) {
    az containerapp env create --name $ContainerAppsEnv --resource-group $ResourceGroup --location $Location --only-show-errors | Out-Null
  }
}

$AcrLoginServer = az acr show --name $AcrName --resource-group $ResourceGroup --query loginServer -o tsv
$AcrUsername = az acr credential show --name $AcrName --query username -o tsv
$AcrPassword = az acr credential show --name $AcrName --query "passwords[0].value" -o tsv

az acr login --name $AcrName --only-show-errors | Out-Null

$BackendTag = "$AcrLoginServer/${BackendImage}:latest"
$FrontendTag = "$AcrLoginServer/${FrontendImage}:latest"

if (-not $FrontendApiUrl) {
  $FrontendApiUrl = "https://$BackendAppName.$Location.azurecontainerapps.io"
  Write-Host "No FrontendApiUrl supplied. If Azure gives the backend a generated FQDN, rerun with -FrontendApiUrl after backend creation."
}

docker build -t $BackendTag -f backend/Dockerfile backend
docker push $BackendTag

docker build -t $FrontendTag --build-arg "REACT_APP_API_URL=$FrontendApiUrl" frontend
docker push $FrontendTag

$BackendSecrets = @(
  "django-secret-key=$env:DJANGO_SECRET_KEY",
  "db-password=$env:DB_PASSWORD"
)

$BackendEnvVars = @(
  "DJANGO_SETTINGS_MODULE=config.settings",
  "DJANGO_DEBUG=False",
  "DJANGO_SECRET_KEY=secretref:django-secret-key",
  "DB_NAME=$DbName",
  "DB_USER=$DbUser",
  "DB_PASSWORD=secretref:db-password",
  "DB_HOST=$DbHost",
  "DB_PORT=$DbPort",
  "DB_SSL=True",
  "PYTHONUNBUFFERED=1"
)

if ($env:OPENAI_API_KEY) { $BackendSecrets += "openai-api-key=$env:OPENAI_API_KEY"; $BackendEnvVars += "OPENAI_API_KEY=secretref:openai-api-key" }
if ($env:TAVILY_API_KEY) { $BackendSecrets += "tavily-api-key=$env:TAVILY_API_KEY"; $BackendEnvVars += "TAVILY_API_KEY=secretref:tavily-api-key" }
if ($env:PUSHER_APP_ID) { $BackendSecrets += "pusher-app-id=$env:PUSHER_APP_ID"; $BackendEnvVars += "PUSHER_APP_ID=secretref:pusher-app-id" }
if ($env:PUSHER_KEY) { $BackendSecrets += "pusher-key=$env:PUSHER_KEY"; $BackendEnvVars += "PUSHER_KEY=secretref:pusher-key" }
if ($env:PUSHER_SECRET) { $BackendSecrets += "pusher-secret=$env:PUSHER_SECRET"; $BackendEnvVars += "PUSHER_SECRET=secretref:pusher-secret" }
if ($env:PUSHER_CLUSTER) { $BackendEnvVars += "PUSHER_CLUSTER=$env:PUSHER_CLUSTER" }
if ($env:CORS_ALLOWED_ORIGINS) { $BackendEnvVars += "CORS_ALLOWED_ORIGINS=$env:CORS_ALLOWED_ORIGINS" }
if ($env:CSRF_TRUSTED_ORIGINS) { $BackendEnvVars += "CSRF_TRUSTED_ORIGINS=$env:CSRF_TRUSTED_ORIGINS" }

if (App-Exists $BackendAppName) {
  az containerapp update --name $BackendAppName --resource-group $ResourceGroup --image $BackendTag --secrets $BackendSecrets --set-env-vars $BackendEnvVars --only-show-errors | Out-Null
} else {
  az containerapp create `
    --name $BackendAppName `
    --resource-group $ResourceGroup `
    --environment $ContainerAppsEnv `
    --image $BackendTag `
    --target-port 8000 `
    --ingress external `
    --registry-server $AcrLoginServer `
    --registry-username $AcrUsername `
    --registry-password $AcrPassword `
    --secrets $BackendSecrets `
    --env-vars $BackendEnvVars `
    --only-show-errors | Out-Null
}

if (App-Exists $FrontendAppName) {
  az containerapp update --name $FrontendAppName --resource-group $ResourceGroup --image $FrontendTag --only-show-errors | Out-Null
} else {
  az containerapp create `
    --name $FrontendAppName `
    --resource-group $ResourceGroup `
    --environment $ContainerAppsEnv `
    --image $FrontendTag `
    --target-port 3002 `
    --ingress external `
    --registry-server $AcrLoginServer `
    --registry-username $AcrUsername `
    --registry-password $AcrPassword `
    --only-show-errors | Out-Null
}

Write-Host "Backend URL:"
az containerapp show --name $BackendAppName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv

Write-Host "Frontend URL:"
az containerapp show --name $FrontendAppName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv
