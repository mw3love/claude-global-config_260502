# -*- coding: utf-8 -*-
"""특정 창 하나만 안전하게 캡처(PrintWindow) — 전체화면 캡처로 다른 창이 찍히는 사고 방지."""
import sys
import ctypes
from ctypes import wintypes
import win32gui
import win32ui
import win32con
from PIL import Image

def find_window(title_substr):
    result = []
    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title_substr in title:
                result.append(hwnd)
    win32gui.EnumWindows(cb, None)
    return result

def shot(hwnd, out_path):
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    w, h = right - left, bottom - top
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
    saveDC.SelectObject(saveBitMap)
    result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)  # PW_RENDERFULLCONTENT
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)
    img.save(out_path)
    return result

if __name__ == "__main__":
    title_substr = sys.argv[1]
    out_path = sys.argv[2]
    hwnds = find_window(title_substr)
    if not hwnds:
        print("NOT_FOUND")
        sys.exit(1)
    r = shot(hwnds[0], out_path)
    print("OK", r, out_path)
