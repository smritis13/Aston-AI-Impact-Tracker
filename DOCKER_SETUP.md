# Docker Local Development Setup Guide

This guide will help you set up and run the Aston AI Research Tool locally using Docker.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose (usually included with Docker Desktop)

## Quick Start

1. **Clone/Navigate to the project directory:**
   ```bash
   cd aston-ai-research-tool-main
   ```

2. **Create environment file:**
   ```bash
   cp backend/.env.example backend/.env
   ```

3. **Edit `backend/.env` file:**
   Add your API keys and configuration:
   ```env
   DJANGO_SECRET_KEY=your-secret-key-here
   DJANGO_DEBUG=True
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   PUSHER_APP_ID=your_pusher_app_id
   PUSHER_KEY=your_pusher_key
   PUSHER_SECRET=your_pusher_secret
   PUSHER_CLUSTER=your_pusher_cluster
   ```

4. **Start all services:**
   ```bash
   docker-compose up --build
   ```

5. **Run database migrations (in a new terminal):**
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

6. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - phpMyAdmin: http://localhost:8080

## Services

The Docker Compose setup includes:

- **backend**: Django REST API server (port 8000)
- **frontend**: React development server (port 3000)
- **db**: MySQL 8 database (port 3306)
- **phpmyadmin**: Database management interface (port 8080)

## Common Commands

### Start services:
```bash
docker-compose up
```

### Start services in detached mode (background):
```bash
docker-compose up -d
```

### Stop services:
```bash
docker-compose down
```

### Stop services and remove volumes (clean slate):
```bash
docker-compose down -v
```

### View logs:
```bash
docker-compose logs -f
```

### View logs for a specific service:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Execute commands in containers:
```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Access backend shell
docker-compose exec backend python manage.py shell

# Access database shell
docker-compose exec db mysql -u myuser -pmypassword mydb
```

### Rebuild containers after code changes:
```bash
docker-compose up --build
```

## Database Management

### Access phpMyAdmin:
- URL: http://localhost:8080
- Username: `myuser`
- Password: `mypassword`

### Database credentials:
- Host: `db` (from within Docker) or `localhost` (from host)
- Port: `3306`
- Database: `mydb`
- Username: `myuser`
- Password: `mypassword`
- Root Password: `secret`

## Troubleshooting

### Port already in use:
If ports 3000, 8000, 3306, or 8080 are already in use, you can modify the port mappings in `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"  # Change host port from 3000 to 3001
```

### Database connection errors:
1. Wait for the database to be fully ready (healthcheck ensures this)
2. Check that the database service is running: `docker-compose ps`
3. Verify environment variables in `backend/.env`

### Backend won't start:
1. Check logs: `docker-compose logs backend`
2. Ensure `.env` file exists in `backend/` directory
3. Verify all required environment variables are set

### Frontend won't start:
1. Check logs: `docker-compose logs frontend`
2. Ensure `node_modules` volume is properly mounted
3. Try rebuilding: `docker-compose up --build frontend`

### Clear everything and start fresh:
```bash
docker-compose down -v
docker-compose up --build
```

## Development Workflow

1. **Code changes**: Since volumes are mounted, code changes are reflected immediately
2. **Backend changes**: Django dev server auto-reloads
3. **Frontend changes**: React dev server hot-reloads
4. **Database changes**: Run migrations after model changes:
   ```bash
   docker-compose exec backend python manage.py makemigrations
   docker-compose exec backend python manage.py migrate
   ```

## Environment Variables

All environment variables are loaded from `backend/.env` file. See `backend/.env.example` for required variables.

**Required for full functionality:**
- `OPENAI_API_KEY`: For AI features
- `TAVILY_API_KEY`: For web search functionality
- `PUSHER_*`: For real-time updates (optional but recommended)

**Database variables** are automatically set by Docker Compose and don't need to be changed unless you modify the database service configuration.

## Notes

- The backend uses Django's development server (not gunicorn) for local development
- Database data persists in a Docker volume (`db_data`)
- ChromaDB data is stored in `backend/chromadb/` directory
- Frontend node_modules are stored in a Docker volume for faster rebuilds
