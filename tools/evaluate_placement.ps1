param(
    [string]$Board = 'hardware/main/main.kicad_pcb',
    [string]$Out = '',
    [string[]]$ExcludeNet = @(),
    [string]$Compare = '',
    [string]$KiCadBin = 'C:/Program Files/KiCad/10.0/bin'
)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
if (-not $Out) { $Out = Join-Path $taskRoot ('hardware/verification/placement-score/' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff')) }
$env:KICAD_DOCUMENTS_HOME = Join-Path $taskRoot '.kicad-runtime/documents'
$env:KICAD_CONFIG_HOME = Join-Path $taskRoot '.kicad-runtime/config'
$taskArgs = @((Join-Path $PSScriptRoot 'evaluate_placement.py'), $Board, '--out', $Out)
foreach ($pattern in $ExcludeNet) { $taskArgs += @('--exclude-net', $pattern) }
if ($Compare) { $taskArgs += @('--compare', $Compare) }
& (Join-Path $KiCadBin 'python.exe') @taskArgs
if ($LASTEXITCODE -ne 0) { throw 'Placement evaluation failed; see output above.' }
