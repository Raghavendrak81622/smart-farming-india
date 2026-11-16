param(
    [ValidateSet('start','prepare')][string]$Action = 'start',
    [int]$Port = 8000,
    [string]$Python
)
$ErrorActionPreference = 'Stop'
if (-not $Python) {
    $venv = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
    if (Test-Path -LiteralPath $venv) { $Python = $venv }
}
if (-not $Python -and (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.deps'))) {
    $node = Get-Command node -ErrorAction SilentlyContinue
    if ($node -and $node.Source -like '*OpenAI.CodexPrimaryRuntime*') {
        $candidate = Join-Path (Split-Path (Split-Path (Split-Path $node.Source))) 'python/python.exe'
        if (Test-Path -LiteralPath $candidate) { $Python = $candidate }
    }
    if (-not $Python -and (Get-Command Get-AppxPackage -ErrorAction SilentlyContinue)) {
        $package = Get-AppxPackage -Name 'OpenAI.CodexPrimaryRuntime*' | Sort-Object Version -Descending | Select-Object -First 1
        if ($package.InstallLocation) {
            $candidate = Join-Path $package.InstallLocation 'dependencies/python/python.exe'
            if (Test-Path -LiteralPath $candidate) { $Python = $candidate }
        }
    }
}
if (-not $Python) { $Python = 'python' }
& $Python (Join-Path $PSScriptRoot 'start_farming.py') $Action --port $Port
exit $LASTEXITCODE
