# Quick Start Guide

## Navigate to the Project Root

The `docker-compose.yml` file is located in the project root directory. Make sure you're in the correct directory:

```powershell
cd C:\Users\smrit\Downloads\aston-ai-research-tool-main\aston-ai-research-tool-main
```

## Verify You're in the Right Place

You should see these files in the current directory:
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `DOCKER_SETUP.md`
- `start-docker.ps1`
- `start-docker.sh`
- `backend/` folder
- `frontend/` folder

## First Time Setup

1. **Create your `.env` file:**
   ```powershell
   Copy-Item backend\.env.example backend\.env
   ```

2. **Edit `backend\.env` and add your API keys:**
   - `OPENAI_API_KEY=your_key_here`
   - `TAVILY_API_KEY=your_key_here`
   - `PUSHER_*` credentials (optional)

## Start Docker

**Option 1: Using the startup script (recommended)**
```powershell
.\start-docker.ps1
```

**Option 2: Using docker compose directly**
```powershell
docker compose up --build
```

**Option 3: Run in background (detached mode)**
```powershell
docker compose up -d --build
```

## Run Database Migrations

After starting Docker, run migrations in a new terminal:

```powershell
cd C:\Users\smrit\Downloads\aston-ai-research-tool-main\aston-ai-research-tool-main
docker compose exec backend python manage.py migrate
```

## Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **phpMyAdmin**: http://localhost:8080

## Stop Docker

Press `Ctrl+C` in the terminal, or if running in detached mode:

```powershell
docker compose down
```

## Troubleshooting

**"no configuration file provided: not found"**
- Make sure you're in the project root directory (where `docker-compose.yml` is located)
- Check with: `Test-Path docker-compose.yml` (should return `True`)

**Port already in use**
- Stop other services using ports 3000, 8000, 3306, or 8080
- Or modify port mappings in `docker-compose.yml`

**Database connection errors**
- Wait a few seconds for the database to fully start
- Check logs: `docker compose logs db`
