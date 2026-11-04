"""Give a Tk window a correctly sized title-bar icon and taskbar icon on Windows.

Tk's iconbitmap() hands ONE HICON to both WM_SETICON slots, so the title bar
(ICON_SMALL) and the taskbar (ICON_BIG) receive the same bitmap and at least one
of them is scaled from the wrong size or falls back to a default icon. This
helper loads the .ico once per slot, at the size Windows asks for in that slot.

Call it after the window exists and after any iconbitmap()/iconphoto() call,
because both of those overwrite the slots again.
"""
import ctypes
from ctypes import wintypes

WM_SETICON = 0x0080
ICON_SMALL, ICON_BIG = 0, 1
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x0010
SM_CXICON, SM_CYICON = 11, 12
SM_CXSMICON, SM_CYSMICON = 49, 50
GA_ROOT = 2

_user32 = ctypes.windll.user32
# Every handle is declared pointer-sized: with ctypes' default c_int restype a
# 64-bit HICON is truncated and WM_SETICON silently receives a garbage handle.
_user32.LoadImageW.restype = wintypes.HANDLE
_user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
                               ctypes.c_int, ctypes.c_int, wintypes.UINT]
_user32.SendMessageW.restype = ctypes.c_void_p
_user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
_user32.GetAncestor.restype = wintypes.HWND
_user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]


def set_window_icons(window, ico_path):
    """Load ico_path separately for ICON_SMALL and ICON_BIG and assign each slot."""
    window.update_idletasks()  # Tk creates the native wrapper window lazily
    hwnd = _user32.GetAncestor(window.winfo_id(), GA_ROOT)
    for slot, sm_cx, sm_cy in ((ICON_SMALL, SM_CXSMICON, SM_CYSMICON),
                               (ICON_BIG, SM_CXICON, SM_CYICON)):
        cx, cy = _user32.GetSystemMetrics(sm_cx), _user32.GetSystemMetrics(sm_cy)
        hicon = _user32.LoadImageW(None, str(ico_path), IMAGE_ICON, cx, cy, LR_LOADFROMFILE)
        if not hicon:
            raise ctypes.WinError()
        _user32.SendMessageW(hwnd, WM_SETICON, slot, hicon)
