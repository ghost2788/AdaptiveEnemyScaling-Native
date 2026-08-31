param(
    [Parameter(Mandatory = $true)]
    [string]$Before,

    [Parameter(Mandatory = $true)]
    [string]$After
)

$ErrorActionPreference = 'Stop'

function Get-ComparableRecords {
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Manifest
    )

    $records = @()
    foreach ($file in @($Manifest.mods.files)) {
        $records += "mods|$($file.path)|$($file.length)|$($file.lastWriteUtc)|$($file.sha256)"
    }
    if ($null -ne $Manifest.modSettings) {
        $file = $Manifest.modSettings
        $records += "settings|$($file.path)|$($file.length)|$($file.lastWriteUtc)|$($file.sha256)"
    }
    $records | Sort-Object
}

$beforeManifest = Get-Content -Raw -LiteralPath $Before | ConvertFrom-Json
$afterManifest = Get-Content -Raw -LiteralPath $After | ConvertFrom-Json
$beforeRecords = @(Get-ComparableRecords -Manifest $beforeManifest)
$afterRecords = @(Get-ComparableRecords -Manifest $afterManifest)
$differences = @(Compare-Object -ReferenceObject $beforeRecords -DifferenceObject $afterRecords)

if ($beforeManifest.mods.exists -ne $afterManifest.mods.exists -or $differences.Count -gt 0) {
    Write-Output 'Live state changed.'
    $differences | ForEach-Object {
        Write-Output "$($_.SideIndicator) $($_.InputObject)"
    }
    exit 1
}

Write-Output 'Live Mods and modsettings state is unchanged.'
exit 0

