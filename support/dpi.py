import sys

def configure(log):
    if sys.platform != 'win32':
        return
    import ctypes
    try:
        fn = ctypes.WinDLL('user32', use_last_error=True).SetProcessDpiAwarenessContext
        fn.argtypes = [ctypes.c_void_p]
        fn.restype = ctypes.c_bool
        if fn(ctypes.c_void_p(-4)):
            log.info('DPI Per-Monitor V2 requested')
        else:
            log.warning('DPI request rejected: %s', ctypes.get_last_error())
    except AttributeError:
        ctypes.windll.user32.SetProcessDPIAware()
