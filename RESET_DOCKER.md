# How to Reset Docker Environment

This guide shows you how to completely reset your Docker environment to start fresh.

## ⚠️ WARNING
These commands will **DELETE ALL DATA** including:
- Database data (all log entries, checkpoints, epoch keys)
- Redis data (sessions, cache)
- Any other persistent data stored in Docker volumes

---

## Method 1: Complete Reset (Recommended)

This stops containers, removes them, removes volumes, and rebuilds everything.

### Step-by-Step Reset

```bash
# 1. Stop all running containers
docker-compose down

# 2. Remove containers, networks, and volumes (this deletes ALL data)
docker-compose down -v

# 3. Remove images (optional - saves disk space but requires rebuild)
docker-compose down --rmi all -v

# 4. Rebuild and start everything from scratch
docker-compose up -d --build
```

### One-Liner (Complete Reset)
```bash
docker-compose down -v && docker-compose up -d --build
```

---

## Method 2: Reset Specific Components

### Reset Database Only
```bash
# Stop containers
docker-compose down

# Remove only the postgres volume
docker volume rm cyber_postgres_data

# Or remove all volumes
docker-compose down -v

# Restart
docker-compose up -d
```

### Reset Everything Including Images
```bash
# This removes containers, volumes, AND images
docker-compose down --rmi all -v

# Rebuild from scratch
docker-compose up -d --build
```

---

## Method 3: Nuclear Option (Complete Cleanup)

If you want to completely remove everything Docker-related:

```bash
# 1. Stop and remove everything
docker-compose down --rmi all -v

# 2. Remove all unused Docker resources (optional but thorough)
docker system prune -a --volumes

# This will ask for confirmation and remove:
# - All stopped containers
# - All networks not used by at least one container
# - All images without at least one container associated
# - All build cache
# - All volumes

# 3. Verify everything is gone
docker-compose ps
docker volume ls | grep cyber

# 4. Rebuild from scratch
docker-compose up -d --build
```

---

## Method 4: Reset with Fresh Database Initialization

After resetting, you need to initialize the database:

```bash
# 1. Complete reset
docker-compose down -v

# 2. Rebuild and start
docker-compose up -d --build

# 3. Wait for services to be ready (about 30 seconds)
sleep 30

# 4. Initialize database
docker-compose exec insurance-backend python -c "from models.database import init_db; init_db()"

# 5. Verify
docker-compose exec insurance-backend python -c "from models.database import get_session, LogEntry; db = get_session(); print(f'Log entries: {db.query(LogEntry).count()}'); db.close()"
```

---

## Method 5: Reset Script (Automated)

Create a reset script for convenience:

**`scripts/reset_docker.sh`**:
```bash
#!/bin/bash

echo "⚠️  WARNING: This will delete ALL Docker containers, volumes, and data!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

echo "📦 Stopping containers..."
docker-compose down -v

echo "🗑️  Removing volumes..."
docker volume prune -f

echo "🔨 Rebuilding from scratch..."
docker-compose up -d --build

echo "⏳ Waiting for services to start..."
sleep 30

echo "🗄️  Initializing database..."
docker-compose exec insurance-backend python -c "from models.database import init_db; init_db()"

echo "✅ Reset complete!"
echo ""
echo "Services:"
echo "  - Backend API: http://localhost:8000"
echo "  - Frontend: http://localhost:3000"
echo "  - PostgreSQL: localhost:54320"
echo "  - Redis: localhost:63790"
```

Make it executable:
```bash
chmod +x scripts/reset_docker.sh
```

Run it:
```bash
./scripts/reset_docker.sh
```

---

## Method 6: Windows PowerShell Reset Script

For Windows users:

**`scripts/reset_docker.ps1`**:
```powershell
Write-Host "WARNING: This will delete ALL Docker containers, volumes, and data!" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to cancel, or Enter to continue..."
Read-Host

Write-Host "Stopping containers..." -ForegroundColor Cyan
docker-compose down -v

Write-Host "Removing volumes..." -ForegroundColor Cyan
docker volume prune -f

Write-Host "Rebuilding from scratch..." -ForegroundColor Cyan
docker-compose up -d --build

Write-Host "Waiting for services to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

Write-Host "Initializing database..." -ForegroundColor Cyan
docker-compose exec insurance-backend python -c "from models.database import init_db; init_db()"

Write-Host "Reset complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Services:"
Write-Host "  - Backend API: http://localhost:8000"
Write-Host "  - Frontend: http://localhost:3000"
Write-Host "  - PostgreSQL: localhost:54320"
Write-Host "  - Redis: localhost:63790"
```

Run it:
```powershell
.\scripts\reset_docker.ps1
```

---

## Quick Reference

| Command | What It Does |
|---------|--------------|
| `docker-compose down` | Stops containers, removes containers and networks |
| `docker-compose down -v` | **Stops containers AND removes volumes (deletes data)** |
| `docker-compose down --rmi all -v` | **Removes containers, volumes, AND images** |
| `docker-compose up -d --build` | Builds and starts containers in detached mode |
| `docker-compose ps` | Shows running containers |
| `docker-compose logs` | Shows logs from all services |
| `docker volume ls` | Lists all volumes |
| `docker-compose exec <service> <command>` | Run command in running container |

---

## Verify Reset

After resetting, verify everything is fresh:

```bash
# Check containers are running
docker-compose ps

# Check database is empty
docker-compose exec insurance-backend python -c "from models.database import get_session, LogEntry, Checkpoint; db = get_session(); print(f'Log entries: {db.query(LogEntry).count()}'); print(f'Checkpoints: {db.query(Checkpoint).count()}'); db.close()"

# Check logs
docker-compose logs --tail=50

# Test API health
curl http://localhost:8000/health
```

---

## Troubleshooting

### If containers won't start:
```bash
# Check Docker is running
docker ps

# Check for port conflicts
netstat -an | grep -E "8000|3000|54320|63790"

# Remove orphaned containers
docker-compose down --remove-orphans -v
```

### If database connection fails:
```bash
# Check postgres is ready
docker-compose exec postgres pg_isready -U insurance -d insurance_claims

# Check logs
docker-compose logs postgres
docker-compose logs insurance-backend
```

### If volumes are stuck:
```bash
# Force remove specific volume
docker volume rm cyber_postgres_data

# Or remove all unused volumes
docker volume prune -f
```

---

## Common Reset Scenarios

### Scenario 1: Fresh Start (Everything Clean)
```bash
docker-compose down -v
docker-compose up -d --build
sleep 30
docker-compose exec insurance-backend python -c "from models.database import init_db; init_db()"
```

### Scenario 2: Reset But Keep Images (Faster Rebuild)
```bash
docker-compose down -v
docker-compose up -d --build
```

### Scenario 3: Reset Database Only (Keep Containers Running)
```bash
# Stop backend
docker-compose stop insurance-backend

# Clear database
docker-compose exec insurance-backend python scripts/clear_database.py

# Restart backend
docker-compose start insurance-backend
```

### Scenario 4: Complete Nuclear Reset
```bash
docker-compose down --rmi all -v
docker system prune -a --volumes
docker-compose up -d --build
```


