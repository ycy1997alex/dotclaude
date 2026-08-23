---
name: python-ui
description: >-
  Rules for Python desktop UI (tkinter / ttkbootstrap): modern appearance, safe window-close lifecycle, background-thread teardown, multi-resolution .ico app icons checked in three places (explorer / title-bar / taskbar). Apply to any task involving tkinter/ttkbootstrap, desktop window lifecycle (close handling, after callbacks, worker threads), or application icons.
paths:
  - "**/*.py"
  - "**/*.spec"
model: opus
effort: medium
---

# Python Desktop UI Rules

## 1. Toolkit & appearance

- If the UI is (or will be) built on native Tk/tkinter: use **ttkbootstrap** to ensure a modern look. Pick a theme explicitly and state which one; prefer ttk/ttkbootstrap widgets over raw `tk.*` widgets whenever an equivalent exists (mixing the two produces inconsistent styling).
- If the project uses another framework (PyQt6, etc.), this rule does not apply — follow that framework's idioms instead.

## 2. Safe window close

Every app must survive both a normal close and an abrupt close without data corruption, zombie threads, or orphaned resources.

- Intercept the close: `root.protocol("WM_DELETE_WINDOW", on_close)`. Never rely on default teardown.
- In `on_close`, in order:
  1. Cancel all scheduled `after()` callbacks (keep their ids when scheduling) — prevents `invalid command name` errors after destroy.
  2. Signal background threads to stop and `join()` with a timeout; design worker threads as `daemon=True` so a failed join cannot hang process exit.
  3. Close hardware/serial/file/DB handles.
  4. Persist unsaved state, or confirm with the user (`askyesno`) before discarding.
  5. `root.destroy()`.
- Threads must never touch tkinter widgets directly — marshal results through a `queue.Queue` polled via `after()`, so shutdown order stays deterministic.
- Wrap `mainloop()` in `try/finally` for cleanup that must run even on unhandled exceptions or console kill.
- Verify (global: Goal-Driven Execution): close the window mid-operation and confirm the process actually exits, no `invalid command name` / `application has been destroyed` errors appear, and no resources are left open.

## 3. .ico application icons

An app icon appears in THREE places, each with its own failure mode. All three must be checked:

1. **Explorer/directory icon** of the packaged .exe — from `icon=` in the PyInstaller .spec.
2. **Window title-bar icon** — `root.iconbitmap(...)` (or `iconphoto` for PNG-based).
3. **Taskbar icon** while the app runs.

Rules:

- If no .ico exists at the expected path, stop and ask the user whether to generate one, or whether they simply forgot to put the intended file there. Never generate an icon unprompted.
- The .ico file MUST be multi-resolution — at minimum 16, 32, 48, and 256 px. Verify before use:

  ```python
  from PIL import Image
  im = Image.open("app.ico")
  print(im.ico.sizes())  # expect (16,16), (32,32), (48,48), (256,256) to be present
  ```

  A single-size .ico renders blurry or falls back to a default icon in at least one of the three locations. If the check fails, regenerate the .ico (e.g., with Pillow from a ≥256px source PNG) before proceeding.
- In onefile builds, `iconbitmap` must load the .ico through the `sys._MEIPASS` path helper (see the PyInstaller packaging section of the `ui-project` skill), and the .ico must be added to the .spec `datas`.
- Windows may show the Python interpreter's icon in the taskbar instead of yours (icon grouping by process). Set an explicit AppUserModelID BEFORE creating the root window:

  ```python
  import ctypes
  ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("company.appname")
  ```

- Verify (global: Goal-Driven Execution): after packaging, visually confirm all three locations show the intended icon.
