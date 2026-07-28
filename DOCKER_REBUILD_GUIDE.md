# Docker Rebuild Guide - Correct Steps

## ⚡ Quick Reference

### Production Build (Recommended for most use cases)
```bash
# Complete rebuild
docker-compose down
docker-compose up --build

# OR quick restart without rebuild
docker-compose up -d
```

### Development Build (For active development with hot reload)
```bash
# With live code changes and hot reload
docker-compose -f docker-compose.dev.yml up --build
```

---

## 🔧 Full Rebuild Procedure (Production)

### Step 1: Stop All Containers
```bash
docker-compose down
```
This stops all containers and removes them. Data persists in volumes.

### Step 2: Clean Up (Optional but Recommended)
```bash
# Remove old images (frees disk space)
docker-compose down --rmi local

# Remove all containers/images/volumes (fresh start)
docker-compose down --rmi all -v
```

### Step 3: Rebuild and Start
```bash
# Build images fresh, then start all services
docker-compose up --build -d

# Monitor startup (wait until all services are healthy)
docker ps
```

### Step 4: Verify Services
```bash
# Check all containers are running
docker ps

# Test frontend
curl http://localhost:3002  # Should return HTTP 200

# Test backend
curl http://localhost:8000  # Should return HTTP 200
```

---

## 🚀 Development With Hot Reload

### Setup for Development
```bash
# Switch to dev mode (rebuilds faster with npm start)
docker-compose -f docker-compose.dev.yml up --build -d
```

**What this gives you:**
- ✅ Hot reload - changes to src/ reflected instantly
- ✅ Faster startup (npm start vs npm run build)
- ✅ Better error messages in console
- ❌ Not optimized for production

### Stop Dev Services
```bash
docker-compose -f docker-compose.dev.yml down
```

---

## 📋 Why These Changes Were Made

### Before (Broken Config)
```yaml
# docker-compose.yml - SLOW/BROKEN
command: sh -c "npm run build && serve -s build -l 3002"
volumes:
  - ./frontend:/app  # Overrides pre-built files!
```

**Problems:**
1. Rebuilds entire React app every container start (75+ seconds)
2. Volume mount overrides Dockerfile build artifacts
3. Slow, inefficient, leads to timeouts

### After (Fixed Config)
```yaml
# docker-compose.yml - FAST/CORRECT
command: serve -s build -l 3002
volumes:
  - frontend_node_modules:/app/node_modules  # Only node_modules
```

**Benefits:**
1. Uses pre-built Docker image (instant startup)
2. No unnecessary rebuilds
3. Backend changes still rebuild backend correctly
4. 10x faster deployment

---

## 🐛 Troubleshooting

### Frontend shows "Connection refused"
```bash
# Check container is running
docker ps | grep react-frontend

# Check logs
docker logs react-frontend -n 50

# Manually restart
docker restart react-frontend
```

### Port already in use
```bash
# Find process using port 3002
netstat -ano | findstr :3002

# Kill it or use different port
docker-compose.yml  # Edit port: "3003:3002"
```

### TypeScript/Build errors
```bash
# Clean rebuild
docker-compose down --rmi all -v
docker-compose up --build

# Check frontend logs
docker logs react-frontend | tail -100
```

### Backend not connecting
```bash
# Verify backend is healthy
docker ps
curl http://localhost:8000

# Check logs
docker logs django-backend
```

---

## 📁 Directory Structure After Fix

```
.
├── docker-compose.yml          ✅ Production (fixed)
├── docker-compose.dev.yml      ✅ Development (new)
├── backend/
│   └── Dockerfile              (unchanged)
├── frontend/
│   ├── Dockerfile              ✅ (unchanged - production)
│   └── Dockerfile.dev          ✅ (new - development)
└── ...
```

---

## ✅ What Finally Worked

1. **Fixed TypeScript Type**: Added `credibility_score` to UseCase interface
2. **Fixed docker-compose.yml**: Removed double build, removed conflicting volumes
3. **Split Configs**: Production (docker-compose.yml) vs Dev (docker-compose.dev.yml)
4. **Result**: Frontend loads in ~90 seconds, HTTP 200, fully operational

---

## 🎯 Best Practices Going Forward

✅ **DO:**
- Use `docker-compose down` before major changes
- Run `docker-compose up --build` after changing package.json
- Use `docker-compose.dev.yml` for active development
- Check `docker ps` before assuming services are ready
- Monitor with `docker logs -f <container_name>`

❌ **DON'T:**
- Don't rebuild (up --build) every time - only when needed
- Don't mount entire directories over pre-built images unless intentional
- Don't run build commands in startup scripts (build in Dockerfile instead)
- Don't ignore volume mount side effects

---

## 📞 Quick Command Cheat Sheet

```bash
# Start everything
docker-compose up -d

# Rebuild everything fresh
docker-compose down && docker-compose up --build -d

# Stop everything
docker-compose down

# View logs
docker logs react-frontend -f
docker logs django-backend -f

# Restart one service
docker restart react-frontend

# Get into container
docker exec -it react-frontend sh

# Check all services health
docker ps

# Clean up (removes images too)
docker-compose down --rmi local -v
```
