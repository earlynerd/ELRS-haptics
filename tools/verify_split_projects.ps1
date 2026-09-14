param([string]$KiCadBin = 'C:/Program Files/KiCad/10.0/bin')
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$cli = Join-Path $KiCadBin 'kicad-cli.exe'
$python = Join-Path $KiCadBin 'python.exe'
$env:KICAD_DOCUMENTS_HOME = Join-Path $taskRoot '.kicad-runtime/documents'
$env:KICAD_CONFIG_HOME = Join-Path $taskRoot '.kicad-runtime/config'
$evidence = Join-Path $taskRoot 'hardware/verification/project-split'
foreach ($name in @('main', 'satellite')) {
    $base = Join-Path $taskRoot "hardware/$name/$name"
    & $cli sch export netlist --format kicadxml -o "$evidence/$name.xml" "$base.kicad_sch"
    if ($LASTEXITCODE -ne 0) { throw "$name netlist export failed" }
    & $cli sch erc --format json -o "$evidence/$name-erc.json" "$base.kicad_sch"
    if ($LASTEXITCODE -ne 0) { throw "$name ERC execution failed" }
    & $cli pcb drc --schematic-parity --refill-zones --format json -o "$evidence/$name-drc.json" "$base.kicad_pcb"
    if ($LASTEXITCODE -ne 0) { throw "$name DRC execution failed" }
    & $python "$PSScriptRoot/check_split_projects.py" $name
    if ($LASTEXITCODE -ne 0) { throw "$name preservation/routing checks failed" }
}
