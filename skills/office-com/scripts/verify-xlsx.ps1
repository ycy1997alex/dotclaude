<#
.SYNOPSIS
Opens each .xlsx in a private, hidden Excel instance and reports whether Excel accepts it without repair.

.DESCRIPTION
Python writers (openpyxl, xlsxwriter, pandas) can produce a workbook that every Python reader accepts
but Excel rejects with "We found a problem with some content" and repairs on open. Only Excel itself
detects that, so this script asks Excel. With DisplayAlerts off, Workbooks.Open throws on such a file.

Each file is copied to a temp folder first, so the original is never locked or opened in the user's
Excel. If the COM call hands back an Excel instance the user already had running, the script touches
nothing in it and exits 2; it only ever quits the instance it started itself.

Usage: verify-xlsx.ps1 a.xlsx b.xlsx ...   (space-separated; also works under powershell.exe -File)

Exit codes: 0 every file opened cleanly, 1 at least one file failed, 2 no private Excel instance.
#>
param(
    [Parameter(Mandatory = $true, Position = 0, ValueFromRemainingArguments = $true)][string[]]$Path
)

Add-Type -Namespace Native -Name User32 -MemberDefinition @'
[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
'@

$before = @(Get-Process -Name EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
try {
    $xl = New-Object -ComObject Excel.Application
} catch {
    Write-Output "FAIL  Excel could not be started: $($_.Exception.Message)"
    exit 2
}
[uint32]$xlPid = 0
[void][Native.User32]::GetWindowThreadProcessId([IntPtr]$xl.Hwnd, [ref]$xlPid)

if ($before -contains $xlPid) {
    # The user's own Excel: do not change its settings, open files in it, or quit it.
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl)
    Write-Output "FAIL  COM returned the Excel instance the user already has open (PID $xlPid). Nothing was touched; ask the user to close Excel and rerun."
    exit 2
}

$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("verify-xlsx-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempDir | Out-Null
$failed = 0
try {
    $xl.DisplayAlerts = $false
    foreach ($p in $Path) {
        if (-not (Test-Path -LiteralPath $p)) {
            $failed++
            Write-Output "FAIL  $p"
            Write-Output "      file not found"
            continue
        }
        $src = (Resolve-Path -LiteralPath $p).Path
        $copy = Join-Path $tempDir ([guid]::NewGuid().ToString("N") + [System.IO.Path]::GetExtension($src))
        Copy-Item -LiteralPath $src -Destination $copy
        try {
            $wb = $xl.Workbooks.Open($copy, 0, $true)  # UpdateLinks = 0, ReadOnly = true
            $wb.Close($false)
            [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wb)
            Write-Output "OK    $src"
        } catch {
            $failed++
            Write-Output "FAIL  $src"
            Write-Output "      $($_.Exception.Message)"
        }
    }
} finally {
    $xl.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl)
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    # Quit() returns before the process is gone; this PID is verified to be the one started above.
    $proc = Get-Process -Id $xlPid -ErrorAction SilentlyContinue
    if ($proc -and -not $proc.WaitForExit(10000)) {
        Stop-Process -Id $xlPid -Force -Confirm:$false
    }
    try { Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction Stop } catch { }
}

if ($failed -gt 0) { exit 1 }
exit 0
