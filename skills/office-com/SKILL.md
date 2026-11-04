---
name: office-com
description: >-
  Rules and a checker for automating Microsoft Office through COM — PowerPoint, Excel, or Word driven from PowerShell `New-Object -ComObject` or Python `win32com` — without closing or altering the user's own Office windows, and for proving that a Python-generated .xlsx really opens in Excel before it is delivered. Use this whenever a script drives Office via COM (converting .pptx to PDF, rendering slides to images, refreshing, printing, or saving a workbook), whenever an .xlsx written by openpyxl, xlsxwriter, or pandas `to_excel` is about to be handed over, and whenever Excel reports "部分內容有問題，要嘗試復原嗎" / "We found a problem with some content" or a script closed the user's PowerPoint or Excel. Surface forms: `-ComObject`, `PowerPoint.Application`, `Excel.Application`, `Word.Application`, `win32com.client.Dispatch`, `.Quit()`, `SaveAs(..., 32)`, `freeze_panes`, "轉 PDF", "簡報轉圖", "Excel 打不開", "檔案毀損".
---

# Office COM automation

Office on this machine is the user's working tool, usually open while scripts run. A COM script that quits the wrong instance closes the user's window and whatever they had not saved; this skill exists because one did exactly that, with a render script calling `$pp.Quit()` on the PowerPoint in which the user had the same deck open. Building spreadsheet or deck *content* is outside this skill; it covers which Office instance a script may touch, and the Excel-open check for generated workbooks.

## 1. Which instance did the script get?

| Call | PowerPoint | Excel |
| --- | --- | --- |
| PowerShell `New-Object -ComObject X.Application` | The user's, if PowerPoint is running — it is single-instance | A new private process (verified with the user's Excel open) |
| Python `win32com.client.Dispatch("X.Application")` | The user's, if running | **The user's, if running** — `Dispatch` tries `GetActiveObject` first and only creates an instance when that fails |
| Python `win32com.client.DispatchEx("X.Application")` | The user's, if running | A new private process |

Word is not verified here; decide ownership with the PID check below rather than assuming.

## 2. Procedure

1. **Record the app's process IDs before creating the COM object** (`POWERPNT`, `EXCEL`, `WINWORD`).
2. **Decide ownership.** The instance is the script's only if its process was not in that list. For Excel, map `Application.Hwnd` to a PID with `GetWindowThreadProcessId`, as `scripts/verify-xlsx.ps1` does. For PowerPoint, the instance is the script's only when no `POWERPNT` was running beforehand.
3. **Open a temp copy, never the user's path.** In a shared instance, opening a file the user already has open hands back their presentation or workbook, and closing it closes their window. When the target is locked, the copy is also how the check still runs. Write output to its own path as well, never over a file the user may have open.
4. **Touch only what the script opened.** Keep a reference to every document it opened and close only those. On an instance that is not the script's, never set `Visible`, `DisplayAlerts`, `ScreenUpdating`, or any other application property; those change the user's session.
5. **Quit only the script's own instance**, then release every COM reference, including documents, ranges, and slides. Any reference left alive keeps the process running after `Quit()` returns. Wait for the recorded PID to exit, and `Stop-Process` that PID, never a process name, only if it lingers.

PowerPoint to PDF, verified both with PowerPoint closed and with the user holding the same deck open:

```powershell
$before = @(Get-Process -Name POWERPNT -ErrorAction SilentlyContinue)
$pp = New-Object -ComObject PowerPoint.Application
# PowerPoint is single-instance: the process is ours only if none was running before.
$own = if ($before.Count -eq 0) { @(Get-Process -Name POWERPNT) } else { @() }
$copy = Join-Path $env:TEMP ("deck-" + [guid]::NewGuid().ToString("N") + [IO.Path]::GetExtension($src))
Copy-Item -LiteralPath $src -Destination $copy
$pres = $null
try {
    $pres = $pp.Presentations.Open($copy, -1, 0, 0)   # ReadOnly, not Untitled, no window
    $pres.SaveAs($pdf, 32)                              # 32 = ppSaveAsPDF
    $pres.Close()
} finally {
    if ($pres) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($pres) }
    if ($own.Count -gt 0) { $pp.Quit() }
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($pp)
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
    foreach ($proc in $own) { if (-not $proc.WaitForExit(10000)) { Stop-Process -Id $proc.Id -Force -Confirm:$false } }
    Remove-Item -LiteralPath $copy -ErrorAction SilentlyContinue
}
```

## 3. A Python-generated .xlsx is verified only by Excel opening it

pandas, openpyxl, unzipping the package, and cell-by-cell comparison all accept workbooks that Excel refuses. One such defect sat unnoticed in four workbooks for ten days. Before delivering any .xlsx written from Python, run:

```powershell
.\scripts\verify-xlsx.ps1 out\report.xlsx out\summary.xlsx
```

| Exit | Meaning |
| --- | --- |
| 0 | Every file opened in Excel without repair |
| 1 | At least one file failed; the line under each `FAIL` is Excel's message |
| 2 | No private Excel instance: Excel could not start, or COM handed back the user's instance. Nothing was touched. Ask the user to close Excel and rerun |

The script follows §2 itself: it opens temp copies in a hidden instance it started, and quits only that instance. Excel's message on failure is generic (`無法取得類別 Workbooks 的 Open 屬性` / `Unable to get the Open property of the Workbooks class`). To find the broken part, check the table below first. If the user has already opened the file in Excel and accepted the repair, Excel wrote a log to `%TEMP%\error*.xml` naming the part (for example the view of `sheetN.xml`).

| What Excel names | Cause | Fix |
| --- | --- | --- |
| A sheet's view (`檢視` / `View`) | openpyxl `ws.freeze_panes = None` removes `<pane>` but leaves `<selection pane="bottomLeft">` pointing at a pane that no longer exists (openpyxl 3.1.5) | Right after unfreezing, also set `ws.sheet_view.selection[0].pane = None` |

## 4. Verification

1. After the script ran, the set of `POWERPNT` / `EXCEL` / `WINWORD` process IDs is exactly what it was before.
2. If the user had an Office window open during the run, it is still open, with the same title.
3. Every .xlsx written from Python got exit 0 from `verify-xlsx.ps1`, run after the last write to that file.
4. No temp copies are left in `%TEMP%`.
