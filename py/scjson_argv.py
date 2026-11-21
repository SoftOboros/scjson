"""Serialize engine arguments for text-valued CLI options on each platform.

Agent Name: python-engine-command-arguments

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""
import os
import shlex
import subprocess


def format_command(argv):
    """Return command text that preserves each argument when parsed locally.

    :param argv: Executable and arguments in invocation order.
    :returns: Quoted command text for a reference-engine option.
    """
    if os.name == "nt":
        return subprocess.list2cmdline(argv)
    return shlex.join(argv)


def split_command(command):
    """Parse reference-engine command text without invoking a shell.

    :param command: Command text supplied by a CLI option or environment variable.
    :returns: Executable and arguments for subprocess invocation.
    """
    if os.name != "nt":
        return shlex.split(command)
    if not command.strip():
        return []

    import ctypes
    from ctypes import wintypes

    # CommandLineToArgvW preserves native backslashes and quoted arguments.
    parse = ctypes.windll.shell32.CommandLineToArgvW
    parse.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    parse.restype = ctypes.POINTER(wintypes.LPWSTR)
    free = ctypes.windll.kernel32.LocalFree
    free.argtypes = [wintypes.HLOCAL]
    free.restype = wintypes.HLOCAL
    count = ctypes.c_int()
    args = parse(command.lstrip(), ctypes.byref(count))
    if not args:
        raise ctypes.WinError()
    try:
        return args[:count.value]
    finally:
        free(args)
