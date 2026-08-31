param(
    [Parameter(Mandatory = $true)]
    [string]$ToolkitDataRoot
)

$ErrorActionPreference = 'Stop'

$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$pathsFile = Join-Path $repositoryRoot 'evidence/toolkit-paths.json'
$identityFile = Join-Path $repositoryRoot 'build/module-identity.json'

$paths = Get-Content -Raw -LiteralPath $pathsFile | ConvertFrom-Json
$identity = Get-Content -Raw -LiteralPath $identityFile | ConvertFrom-Json

$requestedRoot = [System.IO.Path]::GetFullPath($ToolkitDataRoot).TrimEnd('\')
$verifiedRoot = [System.IO.Path]::GetFullPath([string]$paths.gameDataRoot).TrimEnd('\')
$liveModsFragment = "AppData\Local\Larian Studios\Baldur's Gate 3\Mods"

if ($requestedRoot.IndexOf($liveModsFragment, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
    throw "Refusing to synchronize into the live Mods directory: $requestedRoot"
}

if (-not $requestedRoot.Equals($verifiedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "ToolkitDataRoot must exactly match the verified Toolkit data root: $verifiedRoot"
}

if (-not (Test-Path -LiteralPath $requestedRoot -PathType Container)) {
    throw "Verified Toolkit data root does not exist: $requestedRoot"
}

$moduleFolder = [string]$identity.moduleFolder
$copySets = @(
    [pscustomobject]@{
        Source = Join-Path $repositoryRoot 'toolkit\Mods'
        Destination = Join-Path $requestedRoot 'Mods'
    },
    [pscustomobject]@{
        Source = Join-Path $repositoryRoot 'toolkit\Public'
        Destination = Join-Path $requestedRoot 'Public'
    },
    [pscustomobject]@{
        Source = Join-Path $repositoryRoot 'story\RawFiles\Goals'
        Destination = Join-Path $requestedRoot "Mods\$moduleFolder\Story\RawFiles\Goals"
    }
)

foreach ($copySet in $copySets) {
    if (-not (Test-Path -LiteralPath $copySet.Source -PathType Container)) {
        throw "Required repository source does not exist: $($copySet.Source)"
    }
}

foreach ($copySet in $copySets) {
    $sourcePrefix = [System.IO.Path]::GetFullPath($copySet.Source).TrimEnd('\') + '\'
    foreach ($file in Get-ChildItem -LiteralPath $copySet.Source -File -Recurse) {
        $relative = $file.FullName.Substring($sourcePrefix.Length)
        $destinationFile = Join-Path $copySet.Destination $relative
        $destinationDirectory = Split-Path -Parent $destinationFile
        if (-not (Test-Path -LiteralPath $destinationDirectory -PathType Container)) {
            New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
        }
        Copy-Item -LiteralPath $file.FullName -Destination $destinationFile -Force
    }
}

Write-Output "Synchronized $moduleFolder to verified Toolkit data root $requestedRoot"
