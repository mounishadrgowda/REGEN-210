$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"
$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"
$nodeModulesDir = Join-Path $frontendDir "node_modules"
$backendProcess = $null

function Invoke-InDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [scriptblock]$ScriptBlock
    )

    Push-Location $Path
    try {
        & $ScriptBlock
    }
    finally {
        Pop-Location
    }
}

function Ensure-Backend {
    if (-not (Test-Path $venvPython)) {
        Write-Host "Creating backend virtual environment..."
        Invoke-InDirectory $backendDir {
            python -m venv .venv
        }
    }

    $depsReady = $false
    & $venvPython -c "import fastapi, uvicorn" *> $null
    if ($LASTEXITCODE -eq 0) {
        $depsReady = $true
    }

    if (-not $depsReady) {
        Write-Host "Installing backend dependencies..."
        Invoke-InDirectory $backendDir {
            & $venvPython -m pip install --upgrade pip
            & $venvPython -m pip install -r requirements.txt
        }
    }
}

function Ensure-Frontend {
    if (-not (Test-Path $nodeModulesDir)) {
        Write-Host "Installing frontend dependencies..."
        Invoke-InDirectory $frontendDir {
            npm install
        }
    }
}

function Test-PortInUse {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $connection = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        $connected = $connection.AsyncWaitHandle.WaitOne(500, $false)
        return $connected -and $client.Connected
    }
    finally {
        $client.Close()
    }
}

function Assert-PortFree {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [Parameter(Mandatory = $true)]
        [string]$ServiceName
    )

    if (Test-PortInUse $Port) {
        throw "$ServiceName port $Port is already in use. Stop the existing process and run this script again."
    }
}

function Wait-ForBackend {
    $healthUrl = "http://127.0.0.1:8000/health"
    $deadline = (Get-Date).AddSeconds(30)

    Write-Host "Waiting for backend at $healthUrl ..."
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                Write-Host "Backend is ready."
                return
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }

    throw "Backend did not become ready within 30 seconds."
}

try {
    Ensure-Backend
    Ensure-Frontend
    Assert-PortFree 8000 "Backend"
    Assert-PortFree 5173 "Frontend"

    Write-Host "Starting FastAPI backend on http://127.0.0.1:8000 ..."
    $backendProcess = Start-Process `
        -FilePath $venvPython `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $backendDir `
        -NoNewWindow `
        -PassThru

    Wait-ForBackend

    Write-Host ""
    Write-Host "Starting Vite frontend on http://127.0.0.1:5173 ..."
    Write-Host "Open http://127.0.0.1:5173 in your browser."
    Write-Host "Press Ctrl+C to stop both services."
    Write-Host ""

    Invoke-InDirectory $frontendDir {
        npm run dev -- --host 127.0.0.1
    }
}
finally {
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Write-Host "Stopping FastAPI backend..."
        Stop-Process -Id $backendProcess.Id -Force
    }
}
