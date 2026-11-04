<#
.SYNOPSIS
    Read the text out of any error dialog belonging to a running process, including one hidden behind other windows.

.DESCRIPTION
    When a console=False build "hangs with no window", it has usually already shown a
    PyInstaller error dialog that is sitting behind whatever else is on screen. Dialogs
    use the window class #32770 and keep their message in a static child control, so the
    full text can be read without touching the screen or rebuilding anything.

.PARAMETER Name
    Image name of the process to inspect, with or without ".exe".

.PARAMETER AllWindows
    Also dump non-dialog top-level windows, not just class #32770.

.OUTPUTS
    Exit code 0 = at least one dialog was found and dumped, 1 = the process is running
    but has no dialog, 3 = no such process.

.EXAMPLE
    .\read-error-dialog.ps1 -Name MyApp
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Name,

    [switch]$AllWindows
)

$ErrorActionPreference = 'Stop'

if (-not ('ExeVerifyWin32' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;

public class ExeVerifyWin32 {
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr hWnd, EnumProc cb, IntPtr lParam);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassName(IntPtr hWnd, StringBuilder sb, int max);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder sb, int max);

    public static string ClassOf(IntPtr h) {
        StringBuilder sb = new StringBuilder(256);
        GetClassName(h, sb, sb.Capacity);
        return sb.ToString();
    }

    public static string TextOf(IntPtr h) {
        StringBuilder sb = new StringBuilder(4096);
        GetWindowText(h, sb, sb.Capacity);
        return sb.ToString();
    }

    public static bool Visible(IntPtr h) { return IsWindowVisible(h); }

    public static IntPtr[] TopLevel(uint pid) {
        List<IntPtr> found = new List<IntPtr>();
        EnumWindows(delegate(IntPtr h, IntPtr l) {
            uint owner;
            GetWindowThreadProcessId(h, out owner);
            if (owner == pid) { found.Add(h); }
            return true;
        }, IntPtr.Zero);
        return found.ToArray();
    }

    public static IntPtr[] Children(IntPtr parent) {
        List<IntPtr> found = new List<IntPtr>();
        EnumChildWindows(parent, delegate(IntPtr h, IntPtr l) {
            found.Add(h);
            return true;
        }, IntPtr.Zero);
        return found.ToArray();
    }
}
'@
}

$image = $Name -replace '\.exe$', ''
$procs = @(Get-Process -Name $image -ErrorAction SilentlyContinue)

if ($procs.Count -eq 0) {
    Write-Host "No process named '$image' is running."
    exit 3
}

$dialogs = 0

foreach ($p in $procs) {
    foreach ($hwnd in [ExeVerifyWin32]::TopLevel([uint32]$p.Id)) {
        $class = [ExeVerifyWin32]::ClassOf($hwnd)
        $isDialog = ($class -eq '#32770')

        if ((-not $isDialog) -and (-not $AllWindows)) { continue }

        $title = [ExeVerifyWin32]::TextOf($hwnd)
        $vis = [ExeVerifyWin32]::Visible($hwnd)

        Write-Host ''
        Write-Host ("-" * 72)
        Write-Host "PID $($p.Id)  hwnd 0x$($hwnd.ToString('X'))  class $class  visible $vis"
        Write-Host "Title: $title"

        if ($isDialog) { $dialogs++ }

        foreach ($child in [ExeVerifyWin32]::Children($hwnd)) {
            $text = [ExeVerifyWin32]::TextOf($child)
            if ($text -ne '') {
                Write-Host "  [$([ExeVerifyWin32]::ClassOf($child))] $text"
            }
        }
    }
}

Write-Host ''
if ($dialogs -gt 0) {
    Write-Host "$dialogs dialog(s) found. The text above is the real error - fix that rather than rebuilding to reproduce it."
    exit 0
}

Write-Host "No dialog (class #32770) found on any '$image' process."
if (-not $AllWindows) { Write-Host "Re-run with -AllWindows to dump every top-level window before concluding the process is silent." }
exit 1
