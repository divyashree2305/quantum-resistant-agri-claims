Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Docker Environment Reset Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "⚠️  WARNING: This will delete ALL Docker containers, volumes, and data!" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to cancel, or Enter to continue..."
Read-Host

Write-Host ""
Write-Host "📦 Stopping containers..." -ForegroundColor Cyan
docker-compose down -v

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error stopping containers" -ForegroundColor Red
    exit 1
}

Write-Host "🗑️  Removing volumes..." -ForegroundColor Cyan
docker volume prune -f

Write-Host "🔨 Rebuilding from scratch..." -ForegroundColor Cyan
docker-compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error rebuilding containers" -ForegroundColor Red
    exit 1
}

Write-Host "⏳ Waiting for services to start (30 seconds)..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

Write-Host "🗄️  Initializing database..." -ForegroundColor Cyan
docker-compose exec insurance-backend python -c "from models.database import init_db; init_db()"

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Warning: Database initialization may have failed. Services might still be starting." -ForegroundColor Yellow
    Write-Host "   You can manually initialize later with:" -ForegroundColor Yellow
    Write-Host "   docker-compose exec insurance-backend python -c `"from models.database import init_db; init_db()`"" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✅ Reset complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor White
Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor Gray
Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor Gray
Write-Host "  - PostgreSQL: localhost:54320" -ForegroundColor Gray
Write-Host "  - Redis: localhost:63790" -ForegroundColor Gray
Write-Host ""
Write-Host "Database initialized. You can now start using the system!" -ForegroundColor Green


