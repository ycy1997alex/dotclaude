"""Capture one window's own pixels to a PNG - never the screen behind or above it.

Icon and layout checks cannot be signed off from a window title, they have to be
looked at. The pixels come from PrintWindow(PW_RENDERFULLCONTENT), which asks the
window to render itself into a private bitmap: a window sitting behind Explorer or an
editor is still captured as itself, and nothing else the user has open can end up in
the file.

Grabbing the screen region instead is what once leaked a covering Explorer window -
the user's folder and file names - into a capture that still exited 0. Raising the
window first does not prevent that: Windows refuses SetForegroundWindow to a
background process, and the call fails silently.

If PrintWindow hands back nothing usable (some GPU-composited windows render blank
this way), the script falls back to a screen grab ONLY after sampling a grid of points
with WindowFromPoint and confirming every one belongs to the target window. Otherwise
it exits non-zero without writing a file.

The DPI call at import time is not optional: an unaware process is handed logical
coordinates on a scaled display, so the bitmap size and the crop would both be wrong.

The result is cropped to DwmGetWindowAttribute(EXTENDED_FRAME_BOUNDS), because
GetWindowRect includes the invisible resize border.

Requires Pillow.

    python capture-window.py --pid 1234 --out window.png
    python capture-window.py --title "MyApp" --out window.png
"""

import argparse
import ctypes
import sys
import time
from ctypes import wintypes

# Must happen before any coordinate is read.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except (AttributeError, OSError):
    ctypes.windll.user32.SetProcessDPIAware()

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
SW_RESTORE = 9
DWMWA_EXTENDED_FRAME_BOUNDS = 9
PW_RENDERFULLCONTENT = 2
GA_ROOT = 2
DIB_RGB_COLORS = 0
GRID = 7  # occlusion check samples GRID x GRID points across the window

# Handles are pointer-sized on 64-bit Windows; without these declarations ctypes
# passes and returns them as 32-bit c_int and silently truncates them.
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.IsIconic.argtypes = [wintypes.HWND]
user32.GetWindowDC.argtypes = [wintypes.HWND]
user32.GetWindowDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
user32.PrintWindow.restype = wintypes.BOOL
user32.WindowFromPoint.argtypes = [wintypes.POINT]
user32.WindowFromPoint.restype = wintypes.HWND
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT,
                            ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT]
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteDC.argtypes = [wintypes.HDC]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD),
    ]


def visible_windows():
    """Every visible top-level window, as (hwnd, pid, title)."""
    out = []

    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        out.append((hwnd, pid.value, buf.value))
        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return out


def frame_bounds(hwnd):
    """The window's visible bounds, excluding the invisible DWM resize border."""
    rect = wintypes.RECT()
    try:
        hresult = ctypes.windll.dwmapi.DwmGetWindowAttribute(
            wintypes.HWND(hwnd),
            ctypes.c_uint(DWMWA_EXTENDED_FRAME_BOUNDS),
            ctypes.byref(rect),
            ctypes.sizeof(rect),
        )
        if hresult == 0:
            return rect, "DwmGetWindowAttribute"
    except (AttributeError, OSError):
        pass

    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        sys.exit("Both DwmGetWindowAttribute and GetWindowRect failed for hwnd 0x%X" % hwnd)
    return rect, "GetWindowRect (includes the invisible border)"


def pick(windows, pid, title):
    if pid is not None:
        matches = [w for w in windows if w[1] == pid]
    else:
        matches = [w for w in windows if title.lower() in w[2].lower()]

    if not matches:
        sys.exit("No visible window matched. Is it still starting, or did it die?")
    if len(matches) > 1:
        listing = "\n".join("  pid %d  %r" % (w[1], w[2]) for w in matches)
        sys.exit("Ambiguous - %d windows matched:\n%s" % (len(matches), listing))
    return matches[0]


def print_window(hwnd, frame):
    """Ask the window to render itself into a private bitmap, cropped to `frame`.

    Returns None when PrintWindow or GetDIBits fails. Pixels covering the window on
    screen never reach this bitmap.
    """
    from PIL import Image

    wr = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(wr)):
        return None
    width, height = wr.right - wr.left, wr.bottom - wr.top
    if width <= 0 or height <= 0:
        return None

    window_dc = user32.GetWindowDC(hwnd)
    mem_dc = gdi32.CreateCompatibleDC(window_dc)
    bitmap = gdi32.CreateCompatibleBitmap(window_dc, width, height)
    previous = gdi32.SelectObject(mem_dc, bitmap)
    try:
        printed = user32.PrintWindow(hwnd, mem_dc, PW_RENDERFULLCONTENT)
        # GetDIBits requires the bitmap not to be selected into a DC.
        gdi32.SelectObject(mem_dc, previous)
        header = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), width, -height, 1, 32, 0, 0, 0, 0, 0, 0)
        buf = ctypes.create_string_buffer(width * height * 4)
        rows = gdi32.GetDIBits(mem_dc, bitmap, 0, height, buf, ctypes.byref(header), DIB_RGB_COLORS)
    finally:
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(hwnd, window_dc)

    if not printed or rows != height:
        return None
    image = Image.frombuffer("RGB", (width, height), buf, "raw", "BGRX", 0, 1)
    return image.crop((frame.left - wr.left, frame.top - wr.top,
                       frame.right - wr.left, frame.bottom - wr.top))


def is_blank(image):
    """True when every channel holds a single value - a failed render, not a real window."""
    return all(low == high for low, high in image.getextrema())


def covered_points(hwnd, frame):
    """How many of the GRID x GRID sample points inside `frame` show some other window."""
    inset = 8  # stay clear of the frame edge, where a neighbouring window may legitimately touch
    left, top = frame.left + inset, frame.top + inset
    width, height = frame.right - frame.left - 2 * inset, frame.bottom - frame.top - 2 * inset
    covered = 0
    for i in range(GRID):
        for j in range(GRID):
            point = wintypes.POINT(left + width * i // (GRID - 1), top + height * j // (GRID - 1))
            owner = user32.WindowFromPoint(point)
            if not owner or user32.GetAncestor(owner, GA_ROOT) != hwnd:
                covered += 1
    return covered


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--pid", type=int, help="capture the window owned by this process id")
    group.add_argument("--title", help="capture the window whose title contains this text")
    ap.add_argument("--out", default="window.png", help="output PNG path (default: window.png)")
    ap.add_argument("--no-raise", action="store_true",
                    help="in the screen-grab fallback, do not try to bring the window to the foreground first")
    args = ap.parse_args()

    hwnd, pid, title = pick(visible_windows(), args.pid, args.title)

    # A minimised window renders nothing, through PrintWindow or otherwise.
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
        time.sleep(0.4)

    rect, source = frame_bounds(hwnd)
    box = (rect.left, rect.top, rect.right, rect.bottom)
    expected = (rect.right - rect.left, rect.bottom - rect.top)

    image = print_window(hwnd, rect)
    method = "PrintWindow (unaffected by covering windows)"

    if image is None or is_blank(image):
        if not args.no_raise:
            user32.ShowWindow(hwnd, SW_RESTORE)
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.4)
        covered = covered_points(hwnd, rect)
        if covered:
            sys.exit("PrintWindow returned nothing usable, and %d of %d sample points show another window "
                     "on top of the target. Refusing a screen grab - it would capture whatever covers it. "
                     "No file written. Ask the user to uncover the window, then re-run."
                     % (covered, GRID * GRID))
        from PIL import ImageGrab  # imported late so --help works without Pillow

        # all_screens=True so a window on a secondary monitor with negative coordinates works.
        image = ImageGrab.grab(bbox=box, all_screens=True)
        method = "screen grab (PrintWindow was blank; window verified unobscured)"
        if is_blank(image):
            sys.exit("Both PrintWindow and the screen grab came back blank. No file written.")

    if image.size != expected:
        sys.exit("Captured size %r != window size %r. The DPI awareness call did not take effect. No file written."
                 % (image.size, expected))
    image.save(args.out)

    print("pid    : %d" % pid)
    print("title  : %s" % title)
    print("bounds : %r  -> %dx%d  (%s)" % (box, expected[0], expected[1], source))
    print("method : %s" % method)
    print("saved  : %s  %dx%d" % (args.out, image.size[0], image.size[1]))


if __name__ == "__main__":
    main()
