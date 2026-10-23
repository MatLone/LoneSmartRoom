"""Current-user Windows DPAPI; no plaintext fallback."""
import ctypes
from ctypes import wintypes
import os


class Blob(ctypes.Structure):
    _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]


class DPAPI:
    def _call(self, value, decrypt=False):
        if os.name != 'nt':
            raise RuntimeError('Windows DPAPI is required')
        buffer = ctypes.create_string_buffer(value)
        source = Blob(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
        result = Blob()
        crypt = ctypes.WinDLL('crypt32', use_last_error=True)
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree.restype = ctypes.c_void_p
        function = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
        function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                             ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        function.restype = wintypes.BOOL
        if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(result)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            return ctypes.string_at(result.data, result.size)
        finally:
            ctypes.memset(result.data, 0, result.size)
            kernel.LocalFree(result.data)

    def seal(self, value):
        return self._call(value)

    def open(self, value):
        return self._call(value, True)
