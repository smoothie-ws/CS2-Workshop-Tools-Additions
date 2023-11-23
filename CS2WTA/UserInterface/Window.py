import ctypes

from ctypes.wintypes import DWORD, ULONG
from ctypes import windll, c_bool, c_int, POINTER, Structure
from PyQt6.QtCore import Qt


class ACCENTPOLICY(Structure):
    _fields_ = [
        ('AccentState', DWORD),
        ('AccentFlags', DWORD),
        ('GradientColor', DWORD),
        ('AnimationId', DWORD),
    ]


class WINCOMPATTRDATA(Structure):
    _fields_ = [
        ('Attribute', DWORD),
        ('Data', POINTER(ACCENTPOLICY)),
        ('SizeOfData', ULONG),
    ]


SetWindowCompositionAttribute = windll.user32.SetWindowCompositionAttribute
SetWindowCompositionAttribute.restype = c_bool
SetWindowCompositionAttribute.argtypes = [c_int, POINTER(WINCOMPATTRDATA)]


def blur_background(window):
    window.setWindowFlag(Qt.WindowType.FramelessWindowHint)
    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    accent_policy = ACCENTPOLICY()
    accent_policy.AccentState = 3

    win_comp_attr_data = WINCOMPATTRDATA()
    win_comp_attr_data.Attribute = 19
    win_comp_attr_data.SizeOfData = ctypes.sizeof(accent_policy)
    win_comp_attr_data.Data = ctypes.pointer(accent_policy)

    SetWindowCompositionAttribute(c_int(int(window.winId())), ctypes.pointer(win_comp_attr_data))
