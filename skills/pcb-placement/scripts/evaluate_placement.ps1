param(
    [Parameter(Mandatory=$true)][string]$Board,
    [string]$Out = '',
    [string[]]$ExcludeNet = @(),
    [string]$Compare = '',
    [string]$KiCadBin = 'C:/Program Files/KiCad/10.0/bin'
)
$ErrorActionPreference = 'Stop'
if (-not $Out) { $Out = Join-Path (Get-Location) ('placement-reports/' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff')) }
$taskArgs = @((Join-Path $PSScriptRoot 'evaluate_placement.py'), $Board, '--out', $Out, '--kicad-cli', (Join-Path $KiCadBin 'kicad-cli.exe'))
foreach ($pattern in $ExcludeNet) { $taskArgs += @('--exclude-net', $pattern) }
if ($Compare) { $taskArgs += @('--compare', $Compare) }
& (Join-Path $KiCadBin 'python.exe') @taskArgs
if ($LASTEXITCODE -ne 0) { throw 'Placement evaluation failed; see output above.' }
