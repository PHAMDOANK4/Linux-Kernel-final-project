#!/usr/bin/env python3
"""
crypto_gui.py - GUI demo for AES-256-CBC encryption/decryption
using the crypto_kernel Linux kernel module.

Usage:
  sudo chmod 666 /dev/crypto_kernel   # after insmod
  ./crypto_gui.py
"""

import os
import sys
import ctypes
import ctypes.util
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# ── ioctl definitions (mirrors crypto_ioctl.h) ──────────────────────────────

CRYPTO_DEVICE_PATH = "/dev/crypto_kernel"
CRYPTO_BUFFER_MAX = 4096

_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS

_IOC_NONE = 0
_IOC_WRITE = 1
_IOC_READ = 2

def _IOC(dir, type, nr, size):
    return (dir << _IOC_DIRSHIFT) | (type << _IOC_TYPESHIFT) | (nr << _IOC_NRSHIFT) | (size << _IOC_SIZESHIFT)

def _IOWR(type, nr, size):
    return _IOC(_IOC_READ | _IOC_WRITE, type, nr, size)

class CryptoData(ctypes.Structure):
    _fields_ = [
        ("input", ctypes.POINTER(ctypes.c_uint8)),
        ("input_len", ctypes.c_uint32),
        ("output", ctypes.POINTER(ctypes.c_uint8)),
        ("output_len", ctypes.c_uint32),
    ]

CRYPTO_MAGIC = ord('C')
DATA_SIZE = ctypes.sizeof(CryptoData())
CRYPTO_ENCRYPT = _IOWR(CRYPTO_MAGIC, 1, DATA_SIZE)
CRYPTO_DECRYPT = _IOWR(CRYPTO_MAGIC, 2, DATA_SIZE)

AES_BLOCK_SIZE = 16

# ── C library ioctl wrapper ──────────────────────────────────────────────────

_libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
_libc.ioctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_void_p]
_libc.ioctl.restype = ctypes.c_int

def _c_ioctl(fd, cmd, arg):
    ret = _libc.ioctl(fd, cmd, ctypes.byref(arg))
    if ret < 0:
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err))
    return ret


class CryptoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AES-256-CBC Encryption Tool (kernel module)")
        self.root.geometry("640x540")
        self.root.minsize(500, 420)
        self.fd = None

        self.open_device()
        self.create_widgets()

    def open_device(self):
        try:
            self.fd = os.open(CRYPTO_DEVICE_PATH, os.O_RDWR)
        except OSError as e:
            self.fd = None

    def create_widgets(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # ── row 0: input ──
        ttk.Label(main, text="Input text (plaintext):").pack(anchor=tk.W)
        self.input_text = scrolledtext.ScrolledText(main, height=4)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # ── row 1: buttons ──
        btn_row = ttk.Frame(main)
        btn_row.pack(fill=tk.X, pady=4)

        self.encrypt_btn = ttk.Button(btn_row, text=">> Encrypt", command=self.do_encrypt)
        self.encrypt_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.decrypt_btn = ttk.Button(btn_row, text="Decrypt <<", command=self.do_decrypt)
        self.decrypt_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.copy_btn = ttk.Button(btn_row, text="Copy hex", command=self.copy_hex)
        self.copy_btn.pack(side=tk.LEFT)

        self.status_lbl = ttk.Label(btn_row, text="")
        self.status_lbl.pack(side=tk.RIGHT, padx=(10, 0))

        # ── row 2: ciphertext ──
        ttk.Label(main, text="Ciphertext (hex):").pack(anchor=tk.W)
        self.cipher_text = scrolledtext.ScrolledText(main, height=3)
        self.cipher_text.pack(fill=tk.X, pady=(0, 5))

        # ── row 3: decrypted output ──
        ttk.Label(main, text="Decrypted output:").pack(anchor=tk.W)
        self.output_text = scrolledtext.ScrolledText(main, height=3)
        self.output_text.pack(fill=tk.X, pady=(0, 5))

        # ── device status ──
        if self.fd is not None:
            ttk.Label(main, text="\u2705 /dev/crypto_kernel connected",
                      foreground="green").pack(anchor=tk.W)
        else:
            ttk.Label(main,
                      text="\u274c /dev/crypto_kernel NOT connected\n"
                      "  Run: sudo insmod crypto_kernel.ko && sudo chmod 666 /dev/crypto_kernel",
                      foreground="red").pack(anchor=tk.W)

    # ── helpers ─────────────────────────────────────────────────────────────

    def _get_hex(self):
        raw = self.cipher_text.get("1.0", tk.END).rstrip("\n")
        return raw.replace(" ", "").replace("\n", "").strip()

    def copy_hex(self):
        hex_str = self._get_hex()
        if hex_str:
            self.root.clipboard_clear()
            self.root.clipboard_append(hex_str)

    def _ioctl(self, cmd, data):
        input_arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
        out_len = CRYPTO_BUFFER_MAX + AES_BLOCK_SIZE
        output_arr = (ctypes.c_uint8 * out_len)()

        cd = CryptoData()
        cd.input = input_arr
        cd.input_len = len(data)
        cd.output = output_arr
        cd.output_len = out_len

        _c_ioctl(self.fd, cmd, cd)
        return bytes(output_arr[:cd.output_len]), cd.output_len

    # ── operations ──────────────────────────────────────────────────────────

    def do_encrypt(self):
        if self.fd is None:
            messagebox.showerror("Error", "Device not connected.\nLoad the kernel module first.")
            return

        plaintext = self.input_text.get("1.0", tk.END).rstrip("\n")
        if not plaintext:
            messagebox.showwarning("Warning", "Enter text to encrypt.")
            return

        data = plaintext.encode("utf-8")
        if len(data) > CRYPTO_BUFFER_MAX:
            messagebox.showerror("Error", f"Input too long (max {CRYPTO_BUFFER_MAX} bytes).")
            return

        try:
            cipher_bytes, out_len = self._ioctl(CRYPTO_ENCRYPT, data)
        except OSError as e:
            messagebox.showerror("Encryption failed", str(e))
            return

        hex_str = cipher_bytes.hex().upper()
        self.cipher_text.delete("1.0", tk.END)
        self.cipher_text.insert("1.0", hex_str)
        self.status_lbl.config(text=f"Encrypted: {len(data)} \u2192 {out_len} bytes")

    def do_decrypt(self):
        if self.fd is None:
            messagebox.showerror("Error", "Device not connected.\nLoad the kernel module first.")
            return

        hex_str = self._get_hex()
        if not hex_str:
            messagebox.showwarning("Warning", "No ciphertext to decrypt.")
            return

        try:
            cipher_bytes = bytes.fromhex(hex_str)
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid hex: {e}")
            return

        if len(cipher_bytes) == 0 or len(cipher_bytes) % AES_BLOCK_SIZE != 0:
            messagebox.showerror("Error", "Ciphertext length must be non-zero and a multiple of 16.")
            return

        try:
            plain_bytes, out_len = self._ioctl(CRYPTO_DECRYPT, cipher_bytes)
        except OSError as e:
            messagebox.showerror("Decryption failed", str(e))
            return

        plaintext = plain_bytes.decode("utf-8", errors="replace")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", plaintext)
        self.status_lbl.config(text=f"Decrypted: {len(cipher_bytes)} \u2192 {out_len} bytes")

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


def main():
    root = tk.Tk()
    app = CryptoGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.close(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
