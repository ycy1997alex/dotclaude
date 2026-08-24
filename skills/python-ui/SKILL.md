---
name: python-ui
description: >-
  Rules for Python desktop UI (tkinter / ttkbootstrap): modern appearance, safe window-close lifecycle, background-thread teardown, and where the app icon has to be checked. Use this for any task involving tkinter/ttkbootstrap widgets, desktop window lifecycle (close handling, after callbacks, worker threads), or a packaged desktop app's icon. This skill is the implementation half of the `ui-project` skill — load `ui-project` alongside it, always.
paths:
  - "**/*.py"
  - "**/*.spec"
---

# Python Desktop UI Rules

**Load the `ui-project` skill together with this one.** `ui-project` is the upper layer: it owns the documentation set (UI_README.html, 使用者指引.html) and PyInstaller packaging, including the `.ico` and `sys._MEIPASS` rules that the code below has to satisfy. This file covers only what goes inside the Python source.

## 1. Toolkit & appearance

- If the UI is (or will be) built on native Tk/tkinter: use **ttkbootstrap** to ensure a modern look. Pick a theme explicitly and state which one; prefer ttk/ttkbootstrap widgets over raw `tk.*` widgets whenever an equivalent exists (mixing the two produces inconsistent styling).
- If the project uses another framework (PyQt6, etc.), this rule does not apply — follow that framework's idioms instead.
- Before building a screen from scratch, offer the built-in `/design` command: it produces a multi-artboard canvas the user can rearrange and confirm visually, which settles layout questions faster than iterating on tkinter code. See the `ui-project` skill.

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

## 3. Application icon — the code side

The `.ico` file's own requirements (multi-resolution, how to generate one, the `icon=` entry in the .spec) belong to the `ui-project` skill's packaging section. Load it rather than re-deriving them here. What this file adds is the two things that live in the Python source:

1. **Window title-bar icon** — `root.iconbitmap(...)`, or `iconphoto` for a PNG-based icon. In onefile builds the path must go through the `sys._MEIPASS`-aware helper from `ui-project`, because onefile extracts to a temp directory and a hardcoded relative path breaks.
2. **Taskbar icon** — Windows groups by process and will otherwise show the Python interpreter's icon. Set an explicit AppUserModelID BEFORE creating the root window:

   ```python
   import ctypes
   ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("company.appname")
   ```

If no `.ico` exists at the expected path, stop and ask the user whether to generate one, or whether they simply forgot to put the intended file there. Never generate an icon unprompted.

## 4. Verification

Run the app; do not sign off on reading the code (global: Goal-Driven Execution):

1. **Close mid-operation** — start a long task, then close the window. The process actually exits, no `invalid command name` or `application has been destroyed` appears, and no serial/file/DB handle is left open.
2. **Close while idle** — the same, with unsaved state present: the confirm dialog appears and both answers behave.
3. **Widgets** — no raw `tk.*` widget sits next to a ttk equivalent in the same window.
4. **Icon** — after packaging, all three surfaces show the intended icon: the .exe in Explorer, the window title bar, and the taskbar while running. Explorer's icon comes from the .spec (`ui-project`); the other two come from §3.
