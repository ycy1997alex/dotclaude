---
name: python-ui
description: >-
  Rules for Python desktop UI (tkinter / ttkbootstrap): modern appearance, safe window-close lifecycle, worker threads that report back to the UI, modal dialogs, title-bar and taskbar icons, and how to drive and capture the app while verifying it. Use this for any task involving tkinter/ttkbootstrap widgets, desktop window lifecycle (close handling, after callbacks, worker / serial / BLE threads), a Toplevel dialog, a packaged desktop app's icon, or automating or screenshotting a Tk window to check it — "對話框", "視窗卡住", "工作列圖示", "自動點按鈕測試", "截圖看版面". This skill is the implementation half of the `ui-project` skill — load `ui-project` alongside it, always.
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
- Background threads never call any Tk method — no widget method, and not `after()` either. With threaded Tcl (the default for conda and python.org builds on Windows) every cross-thread Tk call waits for the main loop: a worker calling `root.after(0, ...)` was measured blocked 1.3 s while the UI thread spent 1.5 s rendering, so a serial or BLE reader stalls every time the screen redraws. Workers only `put()` callables into a `queue.SimpleQueue`; one main-thread poll runs them:

  ```python
  inbox = queue.SimpleQueue()  # worker threads only ever call inbox.put(callable)

  def drain():
      self.poll_id = root.after(50, drain)  # re-arm before running anything
      while True:
          try:
              fn = inbox.get_nowait()
          except queue.Empty:
              return
          fn()
  ```

  Re-arm at the top, not after the loop. A callable that opens a modal dialog runs a nested event loop until the dialog closes; re-armed at the top, the poll keeps draining during that time, while re-armed at the bottom the whole queue stalls until the user dismisses the dialog (measured: 0.06 s vs 1.0 s). Either way only one poll id is pending, so step 1 of `on_close` cancels it with a single `after_cancel(self.poll_id)`.

- Wrap `mainloop()` in `try/finally` for cleanup that must run even on unhandled exceptions or console kill.

## 3. Application icon — the code side

The `.ico` file's own requirements (multi-resolution, how to generate one, the `icon=` entry in the .spec) belong to the `ui-project` skill's packaging section. Load it rather than re-deriving them here. What this file adds is the three things that live in the Python source:

1. **Title-bar and taskbar icon** — `root.iconbitmap(...)` alone is not enough: Tk hands one HICON to both `WM_SETICON` slots, so the title bar (`ICON_SMALL`) and the taskbar (`ICON_BIG`) get the same bitmap (measured: 32×32 in both slots, and 40×40 in both at 125 % scaling), and the taskbar shows a wrongly scaled icon or falls back to a default one. Copy `assets/win_icon.py` into the project and call it after `iconbitmap()` / `iconphoto()`, which would otherwise overwrite the slots again:

   ```python
   root.iconbitmap(default=resource_path("app.ico"))       # dialogs and other Toplevels
   win_icon.set_window_icons(root, resource_path("app.ico"))  # per-slot sizes for the main window
   ```

   It loads the `.ico` once per slot at `GetSystemMetrics(SM_CXSMICON)` / `(SM_CXICON)` and declares every handle as pointer-sized; with ctypes' default `c_int` return type a 64-bit HICON is truncated and the icon silently fails to change. In onefile builds the path must go through the `sys._MEIPASS`-aware helper from `ui-project`, because onefile extracts to a temp directory and a hardcoded relative path breaks.

2. **Taskbar grouping** — Windows groups by process and will otherwise show the Python interpreter's icon. Set an explicit AppUserModelID BEFORE creating the root window:

   ```python
   import ctypes
   ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("company.appname.2")
   ```

   Windows caches the taskbar icon by this ID, so a release that **changes the icon** must also change the ID (bump the trailing number) or the taskbar keeps showing the old image. Do not change it on releases where the icon stayed the same: a user's pinned taskbar shortcut is tied to the ID, and a new ID splits the pin and the running window into two separate buttons.

3. **ttkbootstrap overrides both of the above.** `bs.Window()` calls `Tk.iconphoto` with ttkbootstrap's own logo by default, and `iconphoto` outranks `iconbitmap(default=...)`, so the title bar and the taskbar show the ttkbootstrap icon instead of the project's `.ico`. Nothing raises, and reading the source will not reveal it. Pass `iconphoto=None` whenever the window is created through ttkbootstrap:

   ```python
   root = bs.Window(themename="litera", iconphoto=None)
   root.iconbitmap(default=resource_path("app.ico"))
   win_icon.set_window_icons(root, resource_path("app.ico"))
   ```

If no `.ico` exists at the expected path, stop and ask the user whether to generate one, or whether they simply forgot to put the intended file there. Never generate an icon unprompted.

## 4. Modal dialogs

A hand-built modal dialog (`Toplevel` + `transient(root)` + `grab_set()` + `wait_window()`) that opens while the main window is minimized locks the app. Tk withdraws a transient dialog whose master is iconic, and the grab then swallows the taskbar's restore request, so clicking the taskbar button does nothing and the app looks frozen. The centring math also runs on the minimized window's off-screen coordinates (measured: around (-31850, -31860)). Restore the master first, then compute the position:

```python
def open_modal(root):
    if root.state() == "iconic":
        root.deiconify()
    root.update_idletasks()
    dlg = tk.Toplevel(root)
    dlg.transient(root)
    # ...centre on root, then grab_set() and wait_window()
```

This applies to every place that can open a modal dialog without the user having just clicked in the window: timers, `after()` callbacks, the queue drain from §2, and error handlers.

## 5. Verification

Run the app; do not sign off on reading the code (global: Goal-Driven Execution):

1. **Close mid-operation** — start a long task, then close the window. The process actually exits, no `invalid command name` or `application has been destroyed` appears, and no serial/file/DB handle is left open.
2. **Close while idle** — the same, with unsaved state present: the confirm dialog appears and both answers behave.
3. **Widgets** — no raw `tk.*` widget sits next to a ttk equivalent in the same window.
4. **Modal while minimized** — minimize the main window, trigger each dialog that can open on its own (§4), and confirm it appears and the taskbar button restores the app.
5. **Icon** — after packaging, all three surfaces show the intended icon: the .exe in Explorer, the window title bar, and the taskbar while running. Explorer's icon comes from the .spec (`ui-project`); the other two come from §3. This one cannot be signed off from a window title — it has to be looked at.

Two rules for how the app is exercised during these checks:

- **Drive widgets in-process, never by screen coordinates.** Call `button.invoke()`, `entry.insert()`, `var.set()` on the real widgets from a test harness or an `after()` hook: it runs the same Tk event path, including `validatecommand` and variable traces. Clicking by coordinates from another process breaks on any scaled display. Python/Tk is DPI-unaware, so `winfo_rootx()` and `winfo_screenwidth()` are logical pixels (1536×864 at 125 %), while a driver that called `SetProcessDPIAware` sends physical pixels (1920×1080); every click lands at 1/1.25 of the intended position and misses. If coordinates are truly unavoidable (a packaged .exe with no harness), read the scale factor at runtime by comparing `GetSystemMetrics(SM_CXSCREEN)` before and after `SetProcessDPIAware`, never assume 1:1.
- **Capture windows only with `capture-window.py` from the `exe-verify` skill**, for a packaged .exe and for `python main.py` alike. Never write an ad-hoc screenshot script and never take a full-screen screenshot. A grab script that does not declare DPI awareness gets virtualized coordinates from `GetWindowRect`, crops the window short, and the cropped image looks like a layout bug in the app. Before reporting any layout problem from a capture, have the app print `winfo_geometry()` and `winfo_reqwidth()` / `winfo_reqheight()` of the window and the suspect widgets, and check that the capture agrees with them.
