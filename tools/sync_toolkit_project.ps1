param(
    [Parameter(Mandatory = $true)]
    [string]$ToolkitDataRoot,

    [switch]$IncludeTestHarnesses,

    [switch]$EnableActionResourceProof
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

if ($EnableActionResourceProof -and -not $IncludeTestHarnesses) {
    throw "EnableActionResourceProof requires IncludeTestHarnesses"
}

$moduleFolder = [string]$identity.moduleFolder
$productionGoalNames = @(
    'AESN_00_Init.txt',
    'AESN_10_Roster.txt',
    'AESN_20_Policy.txt',
    'AESN_30_Combat.txt',
    'AESN_40_HpTransaction.txt',
    'AESN_50_Applications.txt',
    'AESN_55_Components.txt',
    'AESN_56_Relentless.txt',
    'AESN_60_Merge.txt',
    'AESN_65_Reconciliation.txt'
)
$copySets = @(
    [pscustomobject]@{
        Source = Join-Path $repositoryRoot 'toolkit\Mods'
        Destination = Join-Path $requestedRoot 'Mods'
        FilterProductionGoals = $false
    },
    [pscustomobject]@{
        Source = Join-Path $repositoryRoot 'toolkit\Public'
        Destination = Join-Path $requestedRoot 'Public'
        FilterProductionGoals = $false
    },
    [pscustomobject]@{
        Source = Join-Path $repositoryRoot 'story\RawFiles\Goals'
        Destination = Join-Path $requestedRoot "Mods\$moduleFolder\Story\RawFiles\Goals"
        FilterProductionGoals = $true
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
        if (
            $copySet.FilterProductionGoals -and
            -not $IncludeTestHarnesses -and
            $productionGoalNames -notcontains $file.Name
        ) {
            # Exact excluded files are removed from the Toolkit project so a
            # previous proof build cannot leak commands or banners into a
            # production publish. The repository copy remains recoverable.
            if (Test-Path -LiteralPath $destinationFile -PathType Leaf) {
                Remove-Item -LiteralPath $destinationFile -Force
            }
            continue
        }
        $destinationDirectory = Split-Path -Parent $destinationFile
        if (-not (Test-Path -LiteralPath $destinationDirectory -PathType Container)) {
            New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
        }
        Copy-Item -LiteralPath $file.FullName -Destination $destinationFile -Force
    }
}

if (-not $IncludeTestHarnesses) {
    # Remove any older AESN goal that is no longer present in the repository,
    # as well as current proof goals. This prevents a renamed/deleted harness
    # from surviving a later production synchronization.
    $productionGoalsDestination = Join-Path $requestedRoot "Mods\$moduleFolder\Story\RawFiles\Goals"
    if (Test-Path -LiteralPath $productionGoalsDestination -PathType Container) {
        foreach (
            $stagedGoal in Get-ChildItem -LiteralPath $productionGoalsDestination -File -Filter 'AESN_*.txt'
        ) {
            if ($productionGoalNames -notcontains $stagedGoal.Name) {
                Remove-Item -LiteralPath $stagedGoal.FullName -Force
            }
        }
    }
}

if ($EnableActionResourceProof) {
    # Enable only the copied Toolkit fixture. The repository source remains
    # fail-closed so a later production sync cannot accidentally retain it.
    $actionProofGoal = Join-Path $requestedRoot "Mods\$moduleFolder\Story\RawFiles\Goals\AESN_87_ActionResourceProof.txt"
    if (-not (Test-Path -LiteralPath $actionProofGoal -PathType Leaf)) {
        throw "Action-resource proof goal was not synchronized: $actionProofGoal"
    }
    $disabledProofFact = 'NOT DB_AESN_ActionProofHarnessEnabled(1);'
    $enabledProofFact = 'DB_AESN_ActionProofHarnessEnabled(1);'
    $actionProofText = Get-Content -Raw -LiteralPath $actionProofGoal
    if (-not $actionProofText.Contains($disabledProofFact)) {
        throw "Action-resource proof goal does not contain its disabled gate"
    }
    $actionProofText = $actionProofText.Replace($disabledProofFact, $enabledProofFact)
    Set-Content -LiteralPath $actionProofGoal -Value $actionProofText -Encoding Ascii -NoNewline
}

if ($EnableActionResourceProof) {
    Write-Output "Synchronized $moduleFolder with the isolated action-resource proof enabled at $requestedRoot"
} elseif ($IncludeTestHarnesses) {
    Write-Output "Synchronized $moduleFolder with test harnesses to verified Toolkit data root $requestedRoot"
} else {
    Write-Output "Synchronized production $moduleFolder to verified Toolkit data root $requestedRoot"
}
