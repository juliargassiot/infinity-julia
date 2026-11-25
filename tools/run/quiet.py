#!/usr/bin/env python3
"""Runs Godot on a hidden Windows desktop, so its windows never appear on Julia's screen.

    py -3 tools/run/quiet.py [--timing] <godot arguments>

Output and the exit code pass through. If this runner ends, Godot ends with it. --timing waits until
no other Godot or Blender runs, and holds later launches until it ends, so frame times are clean.
"""
import ctypes
import glob
import os
import subprocess
import sys
import time
from ctypes import wintypes

GODOT_GLOB = (r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\GodotEngine.GodotEngine_*"
              r"\Godot_v4.7.2-stable_win64_console.exe")
DESKTOP = "InfinityJuliaQuiet"
TIMING_LOCK = "Local\\InfinityJuliaGpuTiming"
GPU_USERS = ("godot", "blender")

GENERIC_ALL = 0x10000000
STARTF_USESTDHANDLES = 0x100
HANDLE_FLAG_INHERIT = 1
CREATE_SUSPENDED = 0x4
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
INFINITE = 0xFFFFFFFF

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


class StartupInfo(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR),
                ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR),
                ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD),
                ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD),
                ("dwXCountChars", wintypes.DWORD), ("dwYCountChars", wintypes.DWORD),
                ("dwFillAttribute", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
                ("lpReserved2", wintypes.LPVOID), ("hStdInput", wintypes.HANDLE),
                ("hStdOutput", wintypes.HANDLE), ("hStdError", wintypes.HANDLE)]


class ProcessInformation(ctypes.Structure):
    _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
                ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD)]


class IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in
                ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]


class JobLimits(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD), ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]


user32.CreateDesktopW.restype = wintypes.HANDLE
user32.CreateDesktopW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPVOID,
                                  wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID]
kernel32.GetStdHandle.restype = wintypes.HANDLE
kernel32.SetHandleInformation.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD]
kernel32.CreateProcessW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.LPVOID,
                                    wintypes.LPVOID, wintypes.BOOL, wintypes.DWORD,
                                    wintypes.LPVOID, wintypes.LPCWSTR,
                                    ctypes.POINTER(StartupInfo),
                                    ctypes.POINTER(ProcessInformation)]
kernel32.CreateJobObjectW.restype = wintypes.HANDLE
kernel32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID,
                                             wintypes.DWORD]
kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
kernel32.CreateMutexW.restype = wintypes.HANDLE
kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.ReleaseMutex.argtypes = [wintypes.HANDLE]


def find_godot():
    found = os.environ.get("GODOT") or next(
        iter(sorted(glob.glob(os.path.expandvars(GODOT_GLOB)))), None)
    if not found:
        sys.exit("quiet: Godot 4.7.2 was not found; set GODOT to its console executable.")
    return found


def fail(what):
    sys.exit(f"quiet: {what} failed (Windows error {ctypes.get_last_error()})")


def gpu_users():
    listing = subprocess.run(["tasklist", "/fo", "csv", "/nh"],
                             capture_output=True, text=True).stdout
    names = (line.split(",")[0].strip('"') for line in listing.splitlines() if line)
    return sorted({name for name in names if name.lower().startswith(GPU_USERS)})


def wait_until_alone():
    reported = None
    while busy := gpu_users():
        if busy != reported:
            print(f"quiet: timing run waits for {', '.join(busy)}", file=sys.stderr, flush=True)
            reported = busy
        time.sleep(2)


def job_ending_with_this_process():
    job = kernel32.CreateJobObjectW(None, None)
    limits = JobLimits(LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)
    if not job or not kernel32.SetInformationJobObject(
            job, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION, ctypes.byref(limits),
            ctypes.sizeof(limits)):
        fail("CreateJobObject")
    return job


def launch(args, job):
    if not user32.CreateDesktopW(DESKTOP, None, None, 0, GENERIC_ALL, None):
        fail("CreateDesktop")
    info = StartupInfo(cb=ctypes.sizeof(StartupInfo), lpDesktop=f"WinSta0\\{DESKTOP}",
                       dwFlags=STARTF_USESTDHANDLES)
    handles = [kernel32.GetStdHandle(n) for n in (-10, -11, -12)]
    for handle in handles:
        if handle:
            kernel32.SetHandleInformation(handle, HANDLE_FLAG_INHERIT, HANDLE_FLAG_INHERIT)
    info.hStdInput, info.hStdOutput, info.hStdError = handles
    process = ProcessInformation()
    line = ctypes.create_unicode_buffer(subprocess.list2cmdline([find_godot(), *args]))
    if not kernel32.CreateProcessW(None, line, None, None, True, CREATE_SUSPENDED, None, None,
                                   ctypes.byref(info), ctypes.byref(process)):
        fail("CreateProcess")
    if not kernel32.AssignProcessToJobObject(job, process.hProcess):
        fail("AssignProcessToJobObject")
    kernel32.ResumeThread(process.hThread)
    return process.hProcess


def main():
    args = sys.argv[1:]
    timing = "--timing" in args
    if timing:
        args.remove("--timing")
    job = job_ending_with_this_process()
    lock = kernel32.CreateMutexW(None, False, TIMING_LOCK)
    kernel32.WaitForSingleObject(lock, INFINITE)
    try:
        if timing:
            wait_until_alone()
        process = launch(args, job)
    finally:
        if not timing:
            kernel32.ReleaseMutex(lock)
    kernel32.WaitForSingleObject(process, INFINITE)
    code = wintypes.DWORD()
    kernel32.GetExitCodeProcess(process, ctypes.byref(code))
    return code.value


if __name__ == "__main__":
    sys.exit(main())
