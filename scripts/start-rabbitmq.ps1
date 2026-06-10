$ErrorActionPreference = "Stop"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is not available in PATH. Install Docker Desktop and retry."
}

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    docker compose up -d rabbitmq
    Write-Host "RabbitMQ is starting. AMQP: localhost:5672, Management UI: http://localhost:15672"
}
finally {
    Pop-Location
}
