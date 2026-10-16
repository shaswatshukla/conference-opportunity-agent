param(
    [ValidateSet('discover', 'report', 'fixtures', 'test')]
    [string]$Action = 'discover',
    [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
if (-not $Python) {
    $bundledPython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    $venvPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
    if (Test-Path -LiteralPath $venvPython) { $Python = $venvPython }
    elseif (Test-Path -LiteralPath $bundledPython) { $Python = $bundledPython }
    else { $Python = 'python' }
}
$priorPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = $PSScriptRoot + ';' + (Join-Path $PSScriptRoot '.deps') + ';' + $priorPythonPath
$env:PYTHONUTF8 = '1'
try {
    if ($Action -eq 'test') { & $Python -m unittest discover -s (Join-Path $PSScriptRoot 'tests') -v }
    elseif ($Action -eq 'fixtures') { & $Python -m src.main discover --fixtures }
    else { & $Python -m src.main $Action }
    if ($LASTEXITCODE -ne 0) { throw 'Agent command failed. See the error above.' }
}
finally {
    $env:PYTHONPATH = $priorPythonPath
}
