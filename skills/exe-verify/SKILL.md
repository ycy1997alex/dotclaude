---
name: exe-verify
description: >-
  Verifies that a packaged Windows .exe actually runs, and diagnoses it when it does not — launching it and confirming a window really appears, reading the text out of a hidden PyInstaller error dialog, recovering a traceback from a throwaway console=True rebuild, and capturing one window (packaged or run from source) to check its icon or layout. Use this whenever a build has to be signed off or has failed to start: "打包好了幫我驗一下", "exe 閃退", "打包完打不開", "點兩下沒反應", "卡住不開視窗", "圖示沒換到", `DLL load failed while importing _ctypes`, `Failed to execute script`, or any report that a packaged app behaves differently from `python main.py`. The .spec conventions that prevent these failures live in the `ui-project` skill; the tkinter/ttkbootstrap source rules live in `python-ui`.
---

# Verifying a packaged .exe

Three scripts ship with this skill under `scripts/`. Run them; do not read them into context.

| Script | Purpose |
| --- | --- |
| `wait-for-window.ps1` | Launch (or attach to) an .exe and report whether a window actually appears |
| `read-error-dialog.ps1` | Dump the text of any error dialog a process is showing, including one hidden behind other windows |
| `capture-window.py` | Save one window's own rendering to a PNG — even when other windows cover it — for checks that have to be looked at |

## 1. What "done" means here

`exit 0` from the build is not done, and a green test suite is not done either — tests rarely construct a Window, so they never load the DLLs and Tk resources that fail at launch. A build is verified only when **the .exe was launched and a window really appeared**, confirmed by `wait-for-window.ps1`, followed by the app's single most common task performed once by hand (global: Goal-Driven Execution).

Run every check against the artifact the user will receive. A onedir build verified from inside `build/` proves nothing about the `dist/` copy.

If that task is driven by a script rather than performed by the user, do not send clicks at coordinates read from the app: on a scaled display Tk reports logical pixels and every click misses. The coordinate rule is in the `python-ui` verification section.

## 2. Launch check

```powershell
.\wait-for-window.ps1 -Path .\dist\MyApp.exe -TimeoutSeconds 30
```

| Exit | Meaning | Go to |
| --- | --- | --- |
| 0 | A window appeared; the title is printed | §6 if an icon or layout claim is being made |
| 1 | Processes still alive, no window after the timeout | §3 |
| 2 | Every process exited before a window appeared | §3, then §4 |
| 3 | Nothing with that image name was ever running | The launch itself failed — check the path and any AV quarantine |

Everything here enumerates by **image name**, never by the PID that `Start-Process` returned. A onefile build runs the bootloader as the parent process and the real Python interpreter as a child, so a check watching only the parent never sees the window and reports a hang that does not exist. The same asymmetry makes `Stop-Process` on the parent alone leave orphaned children that accumulate across runs.

A process sitting at roughly 9 MB resident with CPU frozen near 2 s is that bootloader waiting on a child, not a busy app.

## 3. No window? Read the hidden dialog before rebuilding anything

A `console=False` build that "hangs with no window" has usually already put a PyInstaller error dialog on screen, behind whatever else is open. Reading it costs seconds; rebuilding costs minutes and tells you the same thing.

```powershell
.\read-error-dialog.ps1 -Name MyApp
```

Exit 0 means a dialog was found and its full text is printed — that text is the real error, so fix it rather than rebuilding to reproduce it. Exit 1 means no dialog on any matching process; re-run with `-AllWindows` to dump every top-level window before concluding the process really is silent.

## 4. Still silent? Rebuild a throwaway console spec

Only when §3 finds nothing. Guessing at the cause from a silent exit wastes more time than this rebuild does.

1. Copy the .spec to `<name>-debug.spec`.
2. In the copy set `console=True` **and** change `name=` — with the same name the debug build overwrites the real artifact in `dist/`.
3. Build the copy and run the resulting .exe from a terminal. The traceback that went nowhere under `console=False` is now on stdout.
4. Fix the cause in the real .spec or in the source, rebuild the real artifact, and re-run §2.
5. Delete the debug .spec and its `dist/` and `build/` output. Leaving a console-window build beside the real one is how the wrong .exe gets shipped.

## 5. Known causes

| What you see | Cause | Where the fix is written down |
| --- | --- | --- |
| `ImportError: DLL load failed while importing _ctypes` (or `pyexpat`, `tcl86t`) | conda keeps its native DLLs in `<sys.prefix>\Library\bin`, which is not on PyInstaller's dependency search path | `ui-project`, PyInstaller packaging section |
| `Library not found` warnings in the build log, and the .exe dies on launch | Same as above. `Analysis(pathex=[...])` does not fix it — `pathex` is module search, DLL resolution is `PATH` | `ui-project`, PyInstaller packaging section |
| Title bar or taskbar shows the ttkbootstrap logo instead of the app icon | `bs.Window()` calls `Tk.iconphoto` with its own logo, which outranks `iconbitmap` | `python-ui`, Application icon section |
| Taskbar icon is blurry, the wrong size, or a default icon while the title bar looks right | `iconbitmap()` puts one HICON in both `WM_SETICON` slots | `python-ui`, Application icon section |
| Taskbar keeps showing the previous icon after the icon file was changed | Windows caches the taskbar icon by AppUserModelID | `python-ui`, Application icon section |
| Explorer icon is blurry or falls back to a default | Single-resolution `.ico` | `ui-project`, PyInstaller packaging section |
| It worked before the env changed | A stale `excludes=[...]`, or a gap the old env was masking. Rebuild and re-verify **every** .spec in the project, not just the edited one | `ui-project`, PyInstaller packaging section |

## 6. Checks that have to be looked at

An icon, a layout, or a font-fallback claim cannot be signed off from a window title. It needs pixels — but **never pixels read off the screen**, whether full-screen or cropped to the window's rectangle: both capture whatever else the user has open on top of it.

```powershell
.\wait-for-window.ps1 -Path .\dist\MyApp.exe -KeepRunning
Start-Sleep -Seconds 3   # let the first layout pass finish; see below
python capture-window.py --title "MyApp" --out window.png
```

**Wait for the window to settle before capturing.** `wait-for-window.ps1` returns the moment the top-level window exists, which is before the app has finished building and painting its widgets. A capture taken then shows frames with nothing in them — empty labelframes, missing buttons and labels, plots at a provisional size — and looks exactly like a layout bug in the app. Observed on a ttkbootstrap app with embedded matplotlib canvases: captured immediately, most of the controls were blank; captured 3 s later, complete. So wait a few seconds between the two commands (longer for apps with heavy startup work), and before reporting any "missing or blank widget" as a bug, re-capture after another few seconds — if the second PNG differs, the first one was simply taken too early.

`capture-window.py` takes the pixels from `PrintWindow(PW_RENDERFULLCONTENT)` — the window renders itself into a private bitmap — so a window sitting behind Explorer or an editor is still captured as itself, and nothing the user has open can leak into the file. An earlier version cropped a screen grab to the window's rectangle after calling `SetForegroundWindow`; Windows silently refuses that call to a background process, so the grab captured the user's Explorer window on top (folder and file names included) and still exited 0. Only when `PrintWindow` comes back blank does the script fall back to a screen grab, and only after `WindowFromPoint` confirms every point of a 7×7 grid belongs to the target; if anything covers it, the script exits non-zero **without writing a file** — ask the user to uncover the window rather than working around it. The `method :` line of its output says which path was taken.

It also sets per-monitor DPI awareness before reading any coordinate (without it, a scaled display hands back logical coordinates and both the bitmap size and the crop come out wrong), crops to the DWM frame bounds so the invisible resize border is excluded, and refuses to guess when more than one window matches. That DPI handling is why this script is the only capture path, for a packaged .exe and for a window run from source alike: an ad-hoc PowerShell or Python grab that skipped it once cropped a correct window short, and the crop was misread as a layout bug in the app. Requires Pillow. Read the PNG back yourself — the script's exit code proves the crop is the right size, not that the icon is right. If a capture ever shows anything other than the app's window, delete it immediately and tell the user what it contained.

## 7. Cleanup

Nothing this skill starts may outlive it:

- Stop the app by image name: `Get-Process -Name MyApp | Stop-Process -Force`. `wait-for-window.ps1` does this on success unless `-KeepRunning` was passed, and deliberately leaves processes alive on failure so §3 has something to inspect.
- Delete the debug .spec from §4 along with its build output.
- Delete capture PNGs that were only evidence for one check, or move them somewhere the user asked for.

## 8. Verification

1. `wait-for-window.ps1` exited 0 against the artifact in `dist/`, and the printed title is the app's, not a leftover process's.
2. The single most common task was performed once in the running app.
3. If §4 ran: the debug .spec and its output are gone, and the real artifact was rebuilt and re-checked afterwards.
4. If an icon or layout claim is being made: the capture was taken after the window settled (§6), the captured PNG was opened and looked at, all three surfaces agree (`ui-project` verification section), and the PNG shows only the app's window — no other window, desktop, or taskbar content anywhere in it.
5. No processes from any of these runs are still on the user's desktop.
