---
name: powershell
description: Windows PowerShell 5.1 conventions for .ps1 scripts — file and console encoding, syntax that does not exist in 5.1, native-command interop, and how to verify a script that will run unattended.
paths:
  - "**/*.ps1"
  - "**/*.psm1"
  - "**/*.psd1"
---

# PowerShell 5.1 (Windows)

This machine runs Windows PowerShell **5.1**, not PowerShell 7. The two differ enough that a snippet copied from a PowerShell 7 answer often fails here with a parser error rather than a runtime one — meaning the whole script dies before its first line executes. Everything below is 5.1 behaviour, verified on this machine (ANSI code page 950).

## 1. Encoding — the single biggest source of silent breakage

**Save every `.ps1` as UTF-8 with BOM.** Without the BOM, PowerShell 5.1 decodes the file using the ANSI code page (cp950 here), so 臺灣繁體中文 comments turn into mojibake and the script usually dies with *"the string is missing the terminator"* — an error that points at a quote, not at the real cause.

**Never rely on a cmdlet's default output encoding.** Three defaults are in play and none of them agree:

| What you write | Default encoding in stock 5.1 |
|---|---|
| `Set-Content` / `Add-Content` | ANSI code page — cp950 on this machine |
| `Out-File`, `>`, `>>` | UTF-16LE with BOM |
| `[System.IO.File]::WriteAllText` | UTF-8 without BOM |

A file written by `Set-Content` and read back by anything expecting UTF-8 is corrupted, and a UTF-16LE file breaks most non-Windows tooling. Always pass `-Encoding` explicitly:

```powershell
Set-Content -Path out.txt -Value $text -Encoding utf8
$text | Out-File -FilePath out.txt -Encoding utf8
```

Note that in 5.1 `-Encoding utf8` means **UTF-8 with BOM**. When a consumer needs UTF-8 *without* a BOM (git, most Linux tooling, JSON parsers that are strict about it), write it through .NET:

```powershell
[System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding $false))
```

## 2. Console and native-command encoding

- **Arguments to a native `.exe` are safe.** They are handed over as UTF-16, so emoji and 中文 survive intact — `git commit -m "✨ feat: 加上匯出功能"` works even with `$OutputEncoding` at its default.
- **Piping into a native command is not.** Bytes on a pipe are encoded with `$OutputEncoding`, which defaults to **US-ASCII** in 5.1; every non-ASCII character becomes `?`. Write a UTF-8 file and pass a path instead of piping. If piping is unavoidable, set it first:

  ```powershell
  $OutputEncoding = [System.Text.UTF8Encoding]::new($false)
  ```

- **A script that runs under Task Scheduler must set `[Console]::OutputEncoding` to UTF-8 itself**, and must be verified by a real scheduled run. Running it by hand in a terminal does not reproduce the failure, because an interactive console usually has a different code page than the one the scheduler hands the process.

  ```powershell
  [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
  ```

## 3. Syntax that does not exist in 5.1

Using any of these is a **parse error** — the script does not run at all, so a `try/catch` cannot save it.

| Not available | Use instead |
|---|---|
| `cmd-a && cmd-b` | `cmd-a; if ($?) { cmd-b }` |
| `cmd-a \|\| cmd-b` | `cmd-a; if (-not $?) { cmd-b }` |
| `$x ? $a : $b` | `if ($x) { $a } else { $b }` |
| `$x ?? $y` | `if ($null -eq $x) { $y } else { $x }` |
| `$x?.Prop` | `if ($null -ne $x) { $x.Prop }` |
| `ConvertFrom-Json -AsHashtable` | Returns a `PSCustomObject`; index with `.Prop` or convert manually |
| `Get-Content -Raw` on a huge file, then `-split` | Fine, but prefer `-ReadCount` streaming for very large files |

Comparisons against `$null` go **`$null` first** — `if ($null -eq $x)`. Written the other way round, an array `$x` compares element-wise and returns an array, which is truthy.

## 4. Native-command interop

- **Do not redirect a native command's stderr with `2>&1`.** In 5.1 each stderr line is wrapped in an `ErrorRecord` (`NativeCommandError`) and `$?` becomes `$false` even when the exe returned exit code 0. Check `$LASTEXITCODE` instead:

  ```powershell
  & git status
  if ($LASTEXITCODE -ne 0) { throw "git failed with $LASTEXITCODE" }
  ```

- `$?` reflects the last *PowerShell* operation; `$LASTEXITCODE` reflects the last *native* one. They are not interchangeable.
- Call an executable whose path contains spaces with the call operator: `& "C:\Program Files\App\app.exe" arg1`.
- To stop PowerShell parsing an argument that starts with `-` or contains `@`, use the stop-parsing token: `git log --% --format=%H`.

## 5. Error handling

`-ErrorAction SilentlyContinue` suppresses the error *output* but the cmdlet still failed, so the script's exit code is still non-zero. To make a failure genuinely non-fatal, promote it to terminating and swallow it:

```powershell
try { Remove-Item $path -ErrorAction Stop } catch { }
```

Without `-ErrorAction Stop`, a non-terminating error skips the `catch` entirely.

## 6. Destructive and interactive traps

- **`New-Item -Force` on an existing file truncates it.** To create a file only when missing:

  ```powershell
  if (-not (Test-Path $path)) { New-Item -ItemType File -Path $path | Out-Null }
  ```

- `Remove-Item`, `Stop-Process`, and `Clear-Content` may prompt. In an unattended script pass `-Confirm:$false` when the action is intended.
- Never use `Read-Host`, `Get-Credential`, `Out-GridView`, `$Host.UI.PromptForChoice`, or `pause` in a script that runs unattended — under Task Scheduler stdin is closed and the process either errors or hangs until it is killed.

## 7. Here-strings

The closing `'@` or `"@` **must sit at column 0** on its own line. Indenting it is a parse error. Use the single-quoted form `@'...'@` unless you need `$variable` expansion — the double-quoted form `@"..."@` expands `$` and backticks, which mangles JSON, regex, and money amounts.

```powershell
@'
{ "path": "$notAVariable", "amount": "$15M" }
'@ | Out-File -Encoding utf8 data.json
```

## 8. Unix commands that do not exist

`head`, `tail`, `which`, `touch`, `wc`, `mkdir -p`, `rm -rf`, `ln -s`, `chmod`, `2>/dev/null`, and `VAR=x cmd` are all shell-isms with no PowerShell equivalent. The mappings are in the PowerShell tool's own reference; the point for a `.ps1` file is that a bash idiom that "looks close enough" will fail at parse time, not at run time.

Environment variables: read with `$env:NAME`, set with `$env:NAME = 'value'`. There is no inline `VAR=x cmd` prefix form.

## 9. Verification

A `.ps1` is not finished until it has been run the way it will actually be used (global: Goal-Driven Execution):

1. **Encoding on disk** — the first three bytes are `EF BB BF`. Check with `[System.IO.File]::ReadAllBytes($path)[0..2]`.
2. **Parses at all** — `powershell.exe -NoProfile -Command "& { . '$path' }"` or `[System.Management.Automation.PSParser]::Tokenize()` reports no errors. A parse error means nothing in the file ran.
3. **Runs clean without a profile** — `powershell.exe -NoProfile -ExecutionPolicy Bypass -File <path>`. A script that only works with your profile loaded will fail under Task Scheduler.
4. **Non-ASCII survives** — open any file the script wrote and confirm the 中文 is intact, not `????` and not mojibake.
5. **Scheduled runs are tested as scheduled runs.** If the script is for Task Scheduler, trigger the task and read its output file. An interactive run does not reproduce the console-encoding or stdin failures.
6. **Exit code is meaningful** — `$LASTEXITCODE` after the run is 0 on success and non-zero on the failure paths the script is supposed to detect.
