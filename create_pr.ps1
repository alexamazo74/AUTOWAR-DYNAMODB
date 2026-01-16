$token = $env:GITHUB_TOKEN
if (-not $token) {
    Write-Error "Environment variable GITHUB_TOKEN is not set. Set it and re-run the script."
    exit 1
}

$payload = @{
  title = 'chore: tests and report fixes'
  head = 'feature/tests-and-report-fixes'
  base = 'main'
  body = Get-Content -Raw 'C:\AAM\autowar-dynamodb\pr_body.md'
}

$json = $payload | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri 'https://api.github.com/repos/alexamazo74/AUTOWAR-DYNAMODB/pulls' -Method Post -Headers @{ Authorization = "token $token"; 'User-Agent'='autowar-agent' } -ContentType 'application/json' -Body $json | ConvertTo-Json
