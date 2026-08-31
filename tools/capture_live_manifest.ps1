param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [string]$ModsPath = 'C:\Users\Tom Girard\AppData\Local\Larian Studios\Baldur''s Gate 3\Mods',

    [string]$ModSettingsPath = 'C:\Users\Tom Girard\AppData\Local\Larian Studios\Baldur''s Gate 3\PlayerProfiles\Public\modsettings.lsx'
)

$ErrorActionPreference = 'Stop'

function Get-FileRecord {
    param(
        [Parameter(Mandatory = $true)]
        [System.IO.FileInfo]$File,

        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $stream = [System.IO.File]::OpenRead($File.FullName)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hash = [System.BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-', '')
    }
    finally {
        $stream.Dispose()
        $sha.Dispose()
    }

    [pscustomobject]@{
        path = $RelativePath.Replace('\', '/')
        length = $File.Length
        lastWriteUtc = $File.LastWriteTimeUtc.ToString('o')
        sha256 = $hash
    }
}

$resolvedModsPath = [System.IO.Path]::GetFullPath($ModsPath)
$modFiles = @()
if (Test-Path -LiteralPath $resolvedModsPath -PathType Container) {
    $rootPrefix = $resolvedModsPath.TrimEnd('\') + '\'
    $modFiles = @(
        Get-ChildItem -LiteralPath $resolvedModsPath -File -Recurse |
            Sort-Object FullName |
            ForEach-Object {
                $relative = $_.FullName.Substring($rootPrefix.Length)
                Get-FileRecord -File $_ -RelativePath $relative
            }
    )
}

$resolvedSettingsPath = [System.IO.Path]::GetFullPath($ModSettingsPath)
$settingsRecord = $null
if (Test-Path -LiteralPath $resolvedSettingsPath -PathType Leaf) {
    $settingsFile = Get-Item -LiteralPath $resolvedSettingsPath
    $settingsRecord = Get-FileRecord -File $settingsFile -RelativePath 'modsettings.lsx'
}

$manifest = [pscustomobject]@{
    mods = [pscustomobject]@{
        exists = (Test-Path -LiteralPath $resolvedModsPath -PathType Container)
        files = $modFiles
    }
    modSettings = $settingsRecord
}

$resolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
$outputDirectory = Split-Path -Parent $resolvedOutput
if (-not (Test-Path -LiteralPath $outputDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resolvedOutput -Encoding UTF8
