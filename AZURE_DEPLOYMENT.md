# Azure Deployment

This adapts the BEAS Azure deployment process to this project. The BEAS PDF uses FastAPI, PostgreSQL, and Nginx; this repository uses Django, MySQL, and a React static build served on port `3002`.

## Prerequisites

- Docker Desktop running.
- Azure CLI installed from `https://aka.ms/installazurecliwindows`.
- `az login` completed in PowerShell.
- Contributor access to the Azure subscription/resource group.
- Azure Container Registry admin access enabled, as in the BEAS process.
- An Azure Database for MySQL Flexible Server and database created.

## Required Azure Resources

Use UK South to match the BEAS document unless your project needs another region.

- Resource group, for example `AI-NetZero`.
- Azure Container Registry, for example `astonaiacr`.
- Azure Database for MySQL Flexible Server, for example `astonmysql`.
- MySQL database, for example `mydatabase`.
- Container Apps Environment, for example `aston-ai-env`.
- Container App for backend, for example `aston-ai-backend`.
- Container App for frontend, for example `aston-ai-frontend`.

## Environment Variables

Set these in PowerShell before running the script:

```powershell
$env:DJANGO_SECRET_KEY = "replace-with-a-strong-secret"
$env:DB_PASSWORD = "replace-with-azure-mysql-password"
$env:OPENAI_API_KEY = "optional-but-required-for-ai-features"
$env:TAVILY_API_KEY = "optional-but-required-for-search"
```

Optional:

```powershell
$env:PUSHER_APP_ID = ""
$env:PUSHER_KEY = ""
$env:PUSHER_SECRET = ""
$env:PUSHER_CLUSTER = ""
$env:CORS_ALLOWED_ORIGINS = "https://your-frontend-url"
$env:CSRF_TRUSTED_ORIGINS = "https://your-frontend-url"
```

## Deploy

From the project root:

```powershell
.\deploy-azure.ps1 `
  -ResourceGroup "AI-NetZero" `
  -Location "uksouth" `
  -AcrName "astonaiacr" `
  -ContainerAppsEnv "aston-ai-env" `
  -BackendAppName "aston-ai-backend" `
  -FrontendAppName "aston-ai-frontend" `
  -DbName "mydatabase" `
  -DbUser "myuser@astonmysql" `
  -DbHost "astonmysql.mysql.database.azure.com"
```

After the first run, copy the backend FQDN printed by the script and redeploy the frontend with the real API URL:

```powershell
.\deploy-azure.ps1 `
  -SkipInfrastructure `
  -FrontendApiUrl "https://your-backend-fqdn"
```

## Run Migrations

After the backend container is up, run migrations against Azure MySQL:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Use Azure Portal's Container App console/exec if available, or run the same commands from a trusted machine with the Azure MySQL connection variables set.

## Verify

- Backend root: `https://your-backend-fqdn/`
- Frontend: `https://your-frontend-fqdn/`
- Logs:

```powershell
az containerapp logs show --name aston-ai-backend --resource-group AI-NetZero --tail 50 --follow
az containerapp logs show --name aston-ai-frontend --resource-group AI-NetZero --tail 50 --follow
```

## Notes From The BEAS PDF That Still Apply

- Backend ingress must be external because this React app calls the API from the user's browser.
- ACR images are pushed from the terminal; the Azure Portal does not upload Docker images.
- ACR admin access must be enabled if Container Apps pulls images using registry username/password.
- Special characters in passwords are safer as separate environment variables than inside a URL connection string.
- Long PowerShell commands are fragile; this repo uses `deploy-azure.ps1` to keep arguments structured.
