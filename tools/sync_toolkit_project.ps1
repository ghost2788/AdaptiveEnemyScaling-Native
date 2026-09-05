param(
    [Parameter(Mandatory = $true)]
    [string]$ToolkitDataRoot,

    [string]$CatalogPath,

    [switch]$IncludeTestHarnesses,

    [switch]$EnableActionResourceProof,

    [switch]$EnableWorldHardenedProof,

    [switch]$EnableBossPriorityProof
)

$ErrorActionPreference = 'Stop'

$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$pathsFile = Join-Path $repositoryRoot 'evidence/toolkit-paths.json'
$identityFile = Join-Path $repositoryRoot 'build/module-identity.json'
$expectedCatalogHash = 'F54D4F4304F46E54976D206917D1FD30FB8226009C776DB1494C85553E47817A'

$paths = Get-Content -Raw -LiteralPath $pathsFile | ConvertFrom-Json
$identity = Get-Content -Raw -LiteralPath $identityFile | ConvertFrom-Json
$requestedRoot = [System.IO.Path]::GetFullPath($ToolkitDataRoot).TrimEnd('\')
$verifiedRoot = [System.IO.Path]::GetFullPath([string]$paths.gameDataRoot).TrimEnd('\')
$liveModsFragment = "AppData\Local\Larian Studios\Baldur's Gate 3\Mods"
$moduleFolder = [string]$identity.moduleFolder

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
if ($EnableWorldHardenedProof -and -not $IncludeTestHarnesses) {
    throw "EnableWorldHardenedProof requires IncludeTestHarnesses"
}
if ($EnableBossPriorityProof -and -not $IncludeTestHarnesses) {
    throw "EnableBossPriorityProof requires IncludeTestHarnesses"
}

if ([string]::IsNullOrWhiteSpace($CatalogPath)) {
    $CatalogPath = Join-Path $repositoryRoot 'artifacts\hp-catalog\Status_AESN_HP_Total.txt'
}
$catalogSource = [System.IO.Path]::GetFullPath($CatalogPath)
$catalogTool = Join-Path $repositoryRoot 'tools\hp_catalog.py'
if (-not (Test-Path -LiteralPath $catalogSource -PathType Leaf)) {
    throw "Required HP total catalog does not exist: $catalogSource"
}
if (-not (Test-Path -LiteralPath $catalogTool -PathType Leaf)) {
    throw "Required catalog validator does not exist: $catalogTool"
}
$python = Get-Command python -ErrorAction Stop
Push-Location $repositoryRoot
try {
    & $python.Source -m tools.hp_catalog check $catalogSource
    if ($LASTEXITCODE -ne 0) {
        throw "HP total catalog failed semantic validation: $catalogSource"
    }
} finally {
    Pop-Location
}
$sha256 = [System.Security.Cryptography.SHA256]::Create()
try {
    $catalogHash = ([System.BitConverter]::ToString(
        $sha256.ComputeHash([System.IO.File]::ReadAllBytes($catalogSource))
    )).Replace('-', '')
} finally {
    $sha256.Dispose()
}
if (-not $catalogHash.Equals($expectedCatalogHash, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "HP total catalog hash is not the accepted candidate: $catalogHash"
}

function Get-AesnMetaIdentity([string]$Path) {
    [xml]$xml = Get-Content -Raw -LiteralPath $Path
    $uuid = $xml.SelectSingleNode("//node[@id='ModuleInfo']/attribute[@id='UUID']")
    $publishHandle = $xml.SelectSingleNode("//node[@id='ModuleInfo']/attribute[@id='PublishHandle']")
    return [pscustomobject]@{
        Uuid = if ($null -eq $uuid) { '' } else { [string]$uuid.value }
        PublishHandle = if ($null -eq $publishHandle) { '' } else { [string]$publishHandle.value }
    }
}

$sourceMeta = Join-Path $repositoryRoot "toolkit\Mods\$moduleFolder\meta.lsx"
if (-not (Test-Path -LiteralPath $sourceMeta -PathType Leaf)) {
    throw "Required repository metadata does not exist: $sourceMeta"
}
$sourceMetaIdentity = Get-AesnMetaIdentity $sourceMeta
if ([string]::IsNullOrWhiteSpace($sourceMetaIdentity.Uuid) -or
    -not $sourceMetaIdentity.Uuid.Equals([string]$identity.moduleUuid, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Repository metadata module UUID does not match module identity"
}
$destinationMeta = Join-Path $requestedRoot "Mods\$moduleFolder\meta.lsx"
if (Test-Path -LiteralPath $destinationMeta -PathType Leaf) {
    $destinationMetaIdentity = Get-AesnMetaIdentity $destinationMeta
    if ([string]::IsNullOrWhiteSpace($destinationMetaIdentity.Uuid) -or
        -not $destinationMetaIdentity.Uuid.Equals($sourceMetaIdentity.Uuid, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Existing Toolkit metadata module UUID does not match repository metadata"
    }
    if (-not [string]::IsNullOrWhiteSpace($sourceMetaIdentity.PublishHandle) -and
        -not [string]::IsNullOrWhiteSpace($destinationMetaIdentity.PublishHandle) -and
        -not $destinationMetaIdentity.PublishHandle.Equals($sourceMetaIdentity.PublishHandle, [System.StringComparison]::Ordinal)) {
        throw "Existing Toolkit metadata PublishHandle does not match repository metadata"
    }
}

$productionGoalNames = @(
    'AESN_00_Init.txt',
    'AESN_10_Roster.txt',
    'AESN_20_Policy.txt',
    'AESN_25_WorldHardened.txt',
    'AESN_30_Combat.txt',
    'AESN_40_HpTransaction.txt',
    'AESN_45_HpTotal.txt',
    'AESN_47_HpMigration.txt',
    'AESN_50_Applications.txt',
    'AESN_55_Components.txt',
    'AESN_56_Relentless.txt',
    'AESN_60_Merge.txt',
    'AESN_65_Reconciliation.txt',
    'AESN_66_WorldHardenedRuntime.txt'
)
$proofGoalNames = @(
    'AESN_35_PendingReloadProbe.txt',
    'AESN_81_HpWoundedProof.txt', 'AESN_82_HpCatalogProof.txt',
    'AESN_83_HpTooltipProof.txt', 'AESN_84_HpIntegrationProof.txt',
    'AESN_84_WorldHardenedHarness.txt', 'AESN_85_BossPriorityHarness.txt',
    'AESN_86_PolicyHarness.txt', 'AESN_87_ActionResourceProof.txt',
    'AESN_88_ReconciliationHarness.txt', 'AESN_89_SaveLoadProbe.txt',
    'AESN_90_Diagnostics.txt', 'AESN_91_MergeHarness.txt',
    'AESN_92_HpApplyHarness.txt', 'AESN_93_HpPlanHarness.txt',
    'AESN_94_NarrativeCombatHarness.txt', 'AESN_95_HostilityHarness.txt',
    'AESN_96_StatHarness.txt', 'AESN_97_ActionHarness.txt',
    'AESN_98_CAP05_Harness.txt', 'AESN_99_TestHarness.txt'
)
$copySets = @(
    [pscustomobject]@{
        Source = Join-Path $repositoryRoot 'toolkit\Mods'
        Destination = Join-Path $requestedRoot 'Mods'
        FilterProductionGoals = $false
        PreserveExistingMetadata = $true
    },
    [pscustomobject]@{
        Source = Join-Path $repositoryRoot 'toolkit\Public'
        Destination = Join-Path $requestedRoot 'Public'
        FilterProductionGoals = $false
        PreserveExistingMetadata = $false
    },
    [pscustomobject]@{
        Source = Join-Path $repositoryRoot 'story\RawFiles\Goals'
        Destination = Join-Path $requestedRoot "Mods\$moduleFolder\Story\RawFiles\Goals"
        FilterProductionGoals = $true
        PreserveExistingMetadata = $false
    }
)

# All fallible source, catalog, root, and metadata checks occur before mutation.
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
        if ($copySet.FilterProductionGoals -and -not $IncludeTestHarnesses -and
            $productionGoalNames -notcontains $file.Name) {
            continue
        }
        if ($copySet.PreserveExistingMetadata -and
            $relative.Equals("$moduleFolder\meta.lsx", [System.StringComparison]::OrdinalIgnoreCase) -and
            (Test-Path -LiteralPath $destinationFile -PathType Leaf)) {
            continue
        }
        $destinationDirectory = Split-Path -Parent $destinationFile
        if (-not (Test-Path -LiteralPath $destinationDirectory -PathType Container)) {
            New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
        }
        Copy-Item -LiteralPath $file.FullName -Destination $destinationFile -Force
    }
}

$catalogDestination = Join-Path $requestedRoot "Public\$moduleFolder\Stats\Generated\Data\Status_AESN_HP_Total.txt"
$catalogDirectory = Split-Path -Parent $catalogDestination
if (-not (Test-Path -LiteralPath $catalogDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $catalogDirectory -Force | Out-Null
}
Copy-Item -LiteralPath $catalogSource -Destination $catalogDestination -Force

if (-not $IncludeTestHarnesses) {
    $productionGoalsDestination = Join-Path $requestedRoot "Mods\$moduleFolder\Story\RawFiles\Goals"
    foreach ($proofGoalName in $proofGoalNames) {
        $proofGoal = Join-Path $productionGoalsDestination $proofGoalName
        if (Test-Path -LiteralPath $proofGoal -PathType Leaf) {
            Remove-Item -LiteralPath $proofGoal -Force
        }
    }
    foreach ($proofStatName in @('Status_AESN_HpTooltipProof.txt')) {
        $proofStat = Join-Path $requestedRoot "Public\$moduleFolder\Stats\Generated\Data\$proofStatName"
        if (Test-Path -LiteralPath $proofStat -PathType Leaf) {
            Remove-Item -LiteralPath $proofStat -Force
        }
    }
}

if ($EnableActionResourceProof) {
    $actionProofGoal = Join-Path $requestedRoot "Mods\$moduleFolder\Story\RawFiles\Goals\AESN_87_ActionResourceProof.txt"
    $disabledProofFact = 'NOT DB_AESN_ActionProofHarnessEnabled(1);'
    if (-not (Test-Path -LiteralPath $actionProofGoal -PathType Leaf)) {
        throw "Action-resource proof goal was not synchronized: $actionProofGoal"
    }
    $actionProofText = Get-Content -Raw -LiteralPath $actionProofGoal
    if (-not $actionProofText.Contains($disabledProofFact)) {
        throw "Action-resource proof goal does not contain its disabled gate"
    }
    Set-Content -LiteralPath $actionProofGoal -Value $actionProofText.Replace($disabledProofFact, 'DB_AESN_ActionProofHarnessEnabled(1);') -Encoding Ascii -NoNewline
}
if ($EnableWorldHardenedProof) {
    $worldProofGoal = Join-Path $requestedRoot "Mods\$moduleFolder\Story\RawFiles\Goals\AESN_84_WorldHardenedHarness.txt"
    $disabledWorldProofFact = 'NOT DB_AESN_WorldHarnessEnabled(1);'
    if (-not (Test-Path -LiteralPath $worldProofGoal -PathType Leaf)) {
        throw "World-Hardened proof goal was not synchronized: $worldProofGoal"
    }
    $worldProofText = Get-Content -Raw -LiteralPath $worldProofGoal
    if (-not $worldProofText.Contains($disabledWorldProofFact)) {
        throw "World-Hardened proof goal does not contain its disabled gate"
    }
    Set-Content -LiteralPath $worldProofGoal -Value $worldProofText.Replace($disabledWorldProofFact, 'DB_AESN_WorldHarnessEnabled(1);') -Encoding Ascii -NoNewline
}
if ($EnableBossPriorityProof) {
    $bossPriorityProofGoal = Join-Path $requestedRoot "Mods\$moduleFolder\Story\RawFiles\Goals\AESN_85_BossPriorityHarness.txt"
    $disabledBossPriorityProofFact = 'NOT DB_AESN_BossPriorityHarnessEnabled(1);'
    if (-not (Test-Path -LiteralPath $bossPriorityProofGoal -PathType Leaf)) {
        throw "Boss-priority proof goal was not synchronized: $bossPriorityProofGoal"
    }
    $bossPriorityProofText = Get-Content -Raw -LiteralPath $bossPriorityProofGoal
    if (-not $bossPriorityProofText.Contains($disabledBossPriorityProofFact)) {
        throw "Boss-priority proof goal does not contain its disabled gate"
    }
    Set-Content -LiteralPath $bossPriorityProofGoal -Value $bossPriorityProofText.Replace($disabledBossPriorityProofFact, 'DB_AESN_BossPriorityHarnessEnabled(1);') -Encoding Ascii -NoNewline
}

Write-Output "Synchronized candidate $moduleFolder to verified Toolkit data root $requestedRoot"
