<#
.SYNOPSIS
    Launch a packaged .exe (or attach to a running one) and report whether it actually puts a window on screen.

.DESCRIPTION
    A PyInstaller onefile build runs the bootloader as the parent process and the real
    Python interpreter as a child, so a check that only looks at the PID returned by
    Start-Process never sees the window and reports a hang that is not there. Every
    lookup below enumerates by image name, which covers both processes.

.PARAMETER Path
    The .exe to launch.

.PARAMETER Name
    Image name of an already-running process to attach to, with or without ".exe".

.PARAMETER TimeoutSeconds
    How long to wait for a window before declaring failure. Default 30.

.PARAMETER KeepRunning
    On success, leave the app running instead of stopping it.

.OUTPUTS
    Exit code 0 = a window appeared, 1 = timed out with the process still alive,
    2 = the process exited before any window appeared, 3 = nothing to attach to.

.EXAMPLE
    .\wait-for-window.ps1 -Path .\dist\MyApp.exe -TimeoutSeconds 30
#>
[CmdletBinding(DefaultParameterSetName = 'Launch')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'Launch')]
    [string]$Path,

    [Parameter(Mandatory = $true, ParameterSetName = 'Attach')]
    [string]$Name,

    [int]$TimeoutSeconds = 30,

    [switch]$KeepRunning
)

$ErrorActionPreference = 'Stop'

function Get-Targets([string]$image) {
    # Enumerate by image name so the onefile bootloader AND its Python child are both seen.
    return @(Get-Process -Name $image -ErrorAction SilentlyContinue)
}

if ($PSCmdlet.ParameterSetName -eq 'Launch') {
    $exe = (Resolve-Path -LiteralPath $Path).Path
    $image = [System.IO.Path]::GetFileNameWithoutExtension($exe)

    $already = Get-Targets $image
    if ($already.Count -gt 0) {
        Write-Warning "$($already.Count) process(es) named '$image' were already running. Their windows cannot be told apart from this launch - close them first, or the result is meaningless."
    }

    Write-Host "Launching $exe"
    Start-Process -FilePath $exe | Out-Null
} else {
    $image = $Name -replace '\.exe$', ''
}

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$sawProcess = $false
$found = $null

while ((Get-Date) -lt $deadline) {
    $procs = Get-Targets $image

    if ($procs.Count -gt 0) {
        $sawProcess = $true
        $withWindow = @($procs | Where-Object { $_.MainWindowTitle -ne '' })
        if ($withWindow.Count -gt 0) {
            $found = $withWindow[0]
            break
        }
    } elseif ($sawProcess) {
        Write-Host "FAIL: every '$image' process exited before a window appeared."
        Write-Host "      A silent exit from a console=False build means the traceback went nowhere. Rebuild a throwaway console=True spec (see the skill body) to read it."
        exit 2
    }

    Start-Sleep -Milliseconds 500
}

if ($null -ne $found) {
    Write-Host "PASS: window found."
    Write-Host "      PID   : $($found.Id)"
    Write-Host "      Title : $($found.MainWindowTitle)"

    if (-not $KeepRunning) {
        # Stop every process with this image name. Killing only the parent leaves the
        # Python child orphaned, and those accumulate across runs.
        foreach ($p in (Get-Targets $image)) {
            try { Stop-Process -Id $p.Id -Force -ErrorAction Stop } catch { }
        }
        Write-Host "      Stopped all '$image' processes."
    }
    exit 0
}

if (-not $sawProcess) {
    Write-Host "FAIL: no process named '$image' was ever running."
    exit 3
}

Write-Host "FAIL: no window after $TimeoutSeconds s. Processes still alive:"
Get-Targets $image |
    Select-Object Id,
                  @{ N = 'WS_MB';  E = { [math]::Round($_.WorkingSet64 / 1MB, 1) } },
                  @{ N = 'CPU_s';  E = { [math]::Round($_.CPU, 1) } },
                  @{ N = 'Title';  E = { $_.MainWindowTitle } } |
    Format-Table -AutoSize |
    Out-String |
    Write-Host

Write-Host "Next step, in this order:"
Write-Host "  1. .\read-error-dialog.ps1 -Name $image   # a hidden error dialog is the usual cause, and it costs seconds to check"
Write-Host "  2. only if that finds nothing, rebuild with a throwaway console=True spec"
Write-Host "Note: a resident set around 9 MB with CPU frozen near 2 s is the onefile bootloader waiting on a child, not a hung app."
Write-Host "Processes were left running for step 1. Clean up with: Get-Process -Name $image | Stop-Process -Force"
exit 1
