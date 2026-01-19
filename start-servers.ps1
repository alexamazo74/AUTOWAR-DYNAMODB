# AutoWAR Development Server Launcher
# This script starts both backend and frontend servers in background processes

Write-Host "Starting AutoWAR Development Servers..." -ForegroundColor Green

# Start backend server in background
Write-Host "Starting backend server (FastAPI) on port 8002..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath "python" -ArgumentList "-m uvicorn src.app.main:app --host 127.0.0.1 --port 8002 --log-level info" -WorkingDirectory "C:\AAM\autowar-dynamodb" -NoNewWindow -PassThru

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend server in background
Write-Host "Starting frontend server (HTTP) on port 8080..." -ForegroundColor Yellow
$frontendProcess = Start-Process -FilePath "python" -ArgumentList "-m http.server 8080" -WorkingDirectory "C:\AAM\autowar-dynamodb\frontend" -NoNewWindow -PassThru

# Wait a moment for frontend to start
Start-Sleep -Seconds 2

Write-Host "Servers started successfully!" -ForegroundColor Green
Write-Host "Backend: http://127.0.0.1:8002" -ForegroundColor Cyan
Write-Host "Frontend: http://127.0.0.1:8080" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White
Write-Host "Press Ctrl+C to stop all servers" -ForegroundColor Yellow

# Keep script running to show status
try {
    while ($true) {
        $backendRunning = Get-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
        $frontendRunning = Get-Process -Id $frontendProcess.Id -ErrorAction SilentlyContinue

        if (-not $backendRunning) {
            Write-Host "Backend server stopped unexpectedly!" -ForegroundColor Red
        }
        if (-not $frontendRunning) {
            Write-Host "Frontend server stopped unexpectedly!" -ForegroundColor Red
        }

        Start-Sleep -Seconds 5
    }
} catch {
    Write-Host "Stopping servers..." -ForegroundColor Yellow
    Stop-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $frontendProcess.Id -ErrorAction SilentlyContinue
    Write-Host "Servers stopped." -ForegroundColor Green
}