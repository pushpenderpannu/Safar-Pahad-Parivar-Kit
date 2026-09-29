# Safar Pahad Parivar - turn the kit's keyboard shortcuts on (and keep them on after every Windows start) or off.
#
#   4 Hero Shot   5 Family Talk   6 Scenery   7 Road Drive   8 Kids Moment   9 Reject   0 Clear Tag
#   Ctrl+Alt+B  Import Brand Graphics     Ctrl+Alt+M  Music - Import Library     Ctrl+Alt+S  SFX - Import Library
#   Ctrl+Alt+Shift+K  pause / resume (high beep = on, low beep = paused)
#
# Resolve can't put shortcuts on menu scripts, so a tiny background helper does it. It only reacts while the
# Resolve window is in front, on the Media / Cut / Edit page, and you're not typing in a text box. The number
# keys 4-0 were Resolve's multicam angle keys; while the helper is on they tag clips instead (numpad untouched).
import os, subprocess, sys, time
_h = os.path.join(os.environ["APPDATA"], r"Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\Safar Pahad Parivar")
_k = open(os.path.join(_h, "kit_path.txt"), encoding="utf-8-sig").read().strip()
TOOL = os.path.join(_k, r"Tools\spp_hotkeys.py")
PY = os.path.join(_k, r"Tools\.venv\Scripts\python.exe")
PYW = os.path.join(_k, r"Tools\.venv\Scripts\pythonw.exe")
try:    # the venv's pythonw launcher opens a console window on some PCs - use the real pythonw.exe behind it
    for _l in open(os.path.join(_k, r"Tools\.venv\pyvenv.cfg"), encoding="utf-8"):
        if _l.split("=")[0].strip() == "home" and os.path.exists(os.path.join(_l.split("=", 1)[1].strip(), "pythonw.exe")):
            PYW = os.path.join(_l.split("=", 1)[1].strip(), "pythonw.exe")
except Exception:
    pass
STARTUP = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup\SPP Keyboard Shortcuts.vbs")
NOWIN = 0x08000000


STOPFILE = os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Safar Pahad Parivar\hotkeys.stop")


def status():
    import ctypes
    h = ctypes.windll.kernel32.OpenMutexW(0x00100000, False, "Local\\SPP_Hotkeys_Helper")
    if h:
        ctypes.windll.kernel32.CloseHandle(h)
    return bool(h)


if not os.path.exists(PYW):
    print("The kit's Python tools are not installed. In PowerShell run:\n  " + os.path.join(_k, r"Tools\setup_word_timing.ps1"))
elif status():
    os.makedirs(os.path.dirname(STOPFILE), exist_ok=True)
    open(STOPFILE, "w").close()
    try:
        os.remove(STARTUP)
    except OSError:
        pass
    time.sleep(1.5)
    print("Keyboard shortcuts are OFF (4-0 are Resolve's multicam keys again). Run this again to turn them on.")
else:
    if not os.path.isdir(os.path.join(_k, r"Tools\.venv\Lib\site-packages\comtypes")):
        print("Installing a small helper package (comtypes) ...")
        subprocess.run([PY, "-m", "pip", "install", "-q", "comtypes"], capture_output=True, creationflags=NOWIN)
    with open(STARTUP, "w", encoding="utf-8") as fh:
        fh.write('CreateObject("WScript.Shell").Run """%s"" ""%s""", 0, False\n' % (PYW, TOOL))
    subprocess.Popen([PYW, TOOL], creationflags=NOWIN | 0x00000008, close_fds=True)   # DETACHED_PROCESS
    time.sleep(2)
    print("Keyboard shortcuts are %s (and will start with Windows):" % ("ON" if status() else "starting"))
    print("   4 Hero   5 Family Talk   6 Scenery   7 Road   8 Kids   9 Reject   0 Clear tag")
    print("   Ctrl+Alt+B brand graphics   Ctrl+Alt+M music library   Ctrl+Alt+S SFX library")
    print("   Ctrl+Alt+Shift+K pause/resume.   Run this script again to turn them off.")
