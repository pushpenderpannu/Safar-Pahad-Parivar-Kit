"""Safar Pahad Parivar - keyboard shortcuts for the kit's menu scripts.

Resolve can't put a keyboard shortcut on a Workspace > Scripts item, so this small helper runs in the
background (no window) and listens for a few keys - but ONLY while the main DaVinci Resolve window is in
front, you are on the Media / Cut / Edit page, and you are not typing in a text box. Everywhere else the
keys behave exactly as before.

    4  Hero Shot            8  Kids Moment              Ctrl+Alt+B  Import Brand Graphics
    5  A-Roll Family Talk   9  Reject                   Ctrl+Alt+M  Music - Import Library
    6  B-Roll Scenery       0  Clear Tag                Ctrl+Alt+S  SFX - Import Library
    7  Road Drive                                       Ctrl+Alt+Shift+K  pause / resume the helper

(Top-row number keys only - the numpad is left alone. After '+' or '-' the digits go to Resolve, so
typing +10 to move the playhead still works.)

    python spp_hotkeys.py            run (normally started with pythonw by the menu script / at login)
    python spp_hotkeys.py --stop     stop a running helper
    python spp_hotkeys.py --status   print whether it is running
"""
import ctypes, ctypes.wintypes as W, io, multiprocessing as mp, os, queue, sys, threading, time, traceback

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SITE = os.path.join(KIT, r"Tools\.venv\Lib\site-packages")
if os.path.isdir(_SITE) and _SITE not in sys.path:     # started with the base pythonw.exe (no console window)
    sys.path.append(_SITE)
MENU = os.path.join(KIT, r"Resolve\Scripts\Utility\Safar Pahad Parivar")
TAGS = os.path.join(MENU, r"2 Marking & Moments\Tag Shot Type")
LOGDIR = os.path.join(os.environ.get("LOCALAPPDATA", KIT), "Safar Pahad Parivar")
LOG = os.path.join(LOGDIR, "hotkeys_log.txt")
STOPFILE = os.path.join(LOGDIR, "hotkeys.stop")
MUTEX = "Local\\SPP_Hotkeys_Helper"

# key -> script (path relative to the menu folder, or a Tag Shot Type file name prefix)
DIGITS = {"4": "tag:1", "5": "tag:2", "6": "tag:3", "7": "tag:4", "8": "tag:7", "9": "tag:9", "0": "tag:0"}
CTRL_ALT = {"B": r"1 Setup\Import Brand Graphics.py",
            "M": r"6 Sound & Music\Music - Import Library.py",
            "S": r"6 Sound & Music\SFX - Import Library.py"}
PAGES = ("media", "cut", "edit")

u32 = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
VK_SHIFT, VK_CONTROL, VK_MENU, VK_LWIN, VK_RWIN = 0x10, 0x11, 0x12, 0x5B, 0x5C
WM_KEYDOWN, WM_SYSKEYDOWN, WM_KEYUP, WM_SYSKEYUP = 0x100, 0x104, 0x101, 0x105


def log(*a):
    try:
        os.makedirs(LOGDIR, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(time.strftime("%Y-%m-%d %H:%M:%S ") + " ".join(str(x) for x in a) + "\n")
    except Exception:
        pass


# ------------------------------------------------------------------ worker process (talks to Resolve)
def _resolve():
    sys.path.append(os.path.expandvars(r"%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"))
    import DaVinciResolveScript as d
    return d.scriptapp("Resolve")


def _script_path(action):
    if action.startswith("tag:"):
        pre = action[4:] + " "
        for f in sorted(os.listdir(TAGS)):
            if f.startswith(pre) and f.endswith(".py"):
                return os.path.join(TAGS, f)
        return None
    return os.path.join(MENU, action)


def worker(jobs, page_ok):
    r = None
    while True:
        try:
            job = jobs.get(timeout=0.35)
        except queue.Empty:
            job = None
        if job == "quit":
            return
        try:
            if r is None:
                r = _resolve()
                if r is None:                             # Resolve not open (or external scripting off)
                    page_ok.value = 0
                    time.sleep(3)
                    continue
            if job is None:
                page = r.GetCurrentPage() if r else None
                page_ok.value = 1 if page in PAGES else 0
                if page is None:                          # Resolve closed or restarted: reconnect
                    r = None
                    time.sleep(2)
                continue
            path = _script_path(job)
            if not path or not os.path.exists(path):
                log("missing script for", job, path)
                continue
            out = io.StringIO()
            old = sys.stdout
            sys.stdout = out
            try:
                g = {"__name__": "__main__", "__file__": path, "resolve": r}
                exec(compile(open(path, encoding="utf-8").read(), path, "exec"), g)
            finally:
                sys.stdout = old
            log(job, "->", out.getvalue().strip().splitlines()[:1])
            if not job.startswith("tag:"):
                import winsound
                winsound.MessageBeep(0x40)
        except Exception:
            r = None
            page_ok.value = 0
            log("worker error", job, traceback.format_exc(limit=2).strip().replace("\n", " | "))
            time.sleep(1.5)


# ------------------------------------------------------------------ focus watcher (main process thread)
class Focus:
    """Keeps 'is Resolve's main window in front and not in a text box' up to date (UI Automation)."""
    TEXT_TYPES = {50004, 50030, 50016}           # Edit, Document, Spinner

    def __init__(self):
        self.ok = False
        self.paused = False
        self.info = ""

    @staticmethod
    def fg_is_resolve():
        h = u32.GetForegroundWindow()
        if not h:
            return False
        b = ctypes.create_unicode_buffer(300)
        u32.GetWindowTextW(h, b, 300)
        if not b.value.startswith("DaVinci Resolve"):
            return False
        pid = W.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        hp = k32.OpenProcess(0x1000, False, pid.value)
        n = W.DWORD(600)
        p = ctypes.create_unicode_buffer(600)
        k32.QueryFullProcessImageNameW(hp, 0, p, ctypes.byref(n))
        k32.CloseHandle(hp)
        return os.path.basename(p.value).lower() == "resolve.exe"

    def run(self):
        import comtypes, comtypes.client
        comtypes.CoInitialize()
        comtypes.client.GetModule("UIAutomationCore.dll")
        from comtypes.gen.UIAutomationClient import CUIAutomation, IUIAutomation
        ua = comtypes.client.CreateObject(CUIAutomation, interface=IUIAutomation)
        while True:
            ok, info = False, "other app in front"
            try:
                if self.fg_is_resolve():
                    e = ua.GetFocusedElement()
                    ok = e.CurrentControlType not in self.TEXT_TYPES
                    info = "Resolve focus: %s %s" % (e.CurrentControlType, e.CurrentClassName)
            except Exception as ex:
                ok, info = False, "focus check failed: %s" % ex
            self.ok, self.info = ok, info
            time.sleep(0.06)


# ------------------------------------------------------------------ keyboard hook
class KBD(ctypes.Structure):
    _fields_ = [("vkCode", W.DWORD), ("scanCode", W.DWORD), ("flags", W.DWORD), ("time", W.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]


HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, W.WPARAM, W.LPARAM)
u32.CallNextHookEx.argtypes = [W.HHOOK, ctypes.c_int, W.WPARAM, W.LPARAM]
u32.CallNextHookEx.restype = ctypes.c_ssize_t
u32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, W.HINSTANCE, W.DWORD]
u32.SetWindowsHookExW.restype = W.HHOOK


def down(vk):
    return bool(u32.GetAsyncKeyState(vk) & 0x8000)


def main():
    os.makedirs(LOGDIR, exist_ok=True)
    k32.CreateMutexW(None, False, MUTEX)
    if ctypes.get_last_error() == 183:                     # ERROR_ALREADY_EXISTS
        return
    try:
        os.remove(STOPFILE)
    except OSError:
        pass
    base = getattr(sys, "_base_executable", sys.executable)
    pyw = os.path.join(os.path.dirname(base), "pythonw.exe")
    if os.path.exists(pyw):
        mp.set_executable(pyw)                            # worker without a console window
    jobs, page_ok = mp.Queue(), mp.Value("i", 0)
    wp = mp.Process(target=worker, args=(jobs, page_ok), daemon=True)
    wp.start()
    focus = Focus()
    threading.Thread(target=focus.run, daemon=True).start()
    st = {"held": set(), "relative": 0.0}

    def active():
        return focus.ok and page_ok.value == 1 and not focus.paused

    @HOOKPROC
    def proc(n, wparam, lparam):
        try:
            if n == 0:
                k = ctypes.cast(lparam, ctypes.POINTER(KBD)).contents
                vk = k.vkCode
                if wparam in (WM_KEYUP, WM_SYSKEYUP):
                    if vk in st["held"]:
                        st["held"].discard(vk)
                        return 1
                elif wparam in (WM_KEYDOWN, WM_SYSKEYDOWN) and vk != 0xE8:
                    ctrl, alt, shift = down(VK_CONTROL), down(VK_MENU), down(VK_SHIFT)
                    win = down(VK_LWIN) or down(VK_RWIN)
                    ch = chr(vk) if 0x30 <= vk <= 0x5A else ""
                    if ctrl and alt and shift and ch == "K" and focus.ok:
                        if vk not in st["held"]:
                            focus.paused = not focus.paused
                            import winsound
                            winsound.Beep(440 if focus.paused else 880, 120)
                            log("paused" if focus.paused else "resumed")
                            u32.keybd_event(0xE8, 0, 0, 0)
                            u32.keybd_event(0xE8, 0, 2, 0)
                        st["held"].add(vk)
                        return 1
                    if vk in (0xBB, 0xBD, 0x6B, 0x6D):            # + - (main and numpad): Resolve timecode entry
                        st["relative"] = time.time()
                    elif vk in (0x0D, 0x1B):
                        st["relative"] = 0.0
                    if not active() or win:
                        return u32.CallNextHookEx(None, n, wparam, lparam)
                    job = None
                    if ch in DIGITS and not (ctrl or alt or shift) and time.time() - st["relative"] > 4:
                        job = DIGITS[ch]
                    elif ch in CTRL_ALT and ctrl and alt and not shift:
                        job = CTRL_ALT[ch]
                    if job:
                        if vk not in st["held"]:                  # ignore auto-repeat
                            jobs.put(job)
                            if alt:                               # so releasing Alt doesn't open Resolve's menu bar
                                u32.keybd_event(0xE8, 0, 0, 0)
                                u32.keybd_event(0xE8, 0, 2, 0)
                        st["held"].add(vk)
                        return 1
        except Exception:
            pass
        return u32.CallNextHookEx(None, n, wparam, lparam)

    hook = u32.SetWindowsHookExW(13, proc, None, 0)          # WH_KEYBOARD_LL
    if not hook:
        log("could not install the keyboard hook", ctypes.get_last_error())
        return
    log("started (pid %d)" % os.getpid())
    tid = k32.GetCurrentThreadId()

    def stop_watch():
        state = os.path.join(LOGDIR, "hotkeys_state.txt")
        while not os.path.exists(STOPFILE):
            try:
                with open(state, "w", encoding="utf-8") as fh:
                    fh.write("%s | page ok: %s | paused: %s | keys active: %s | %s\n" % (
                        time.strftime("%H:%M:%S"), bool(page_ok.value), focus.paused, active(), focus.info))
            except Exception:
                pass
            time.sleep(1)
        u32.PostThreadMessageW(tid, 0x12, 0, 0)               # WM_QUIT
    threading.Thread(target=stop_watch, daemon=True).start()

    msg = W.MSG()
    while u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        u32.TranslateMessage(ctypes.byref(msg))
        u32.DispatchMessageW(ctypes.byref(msg))
    u32.UnhookWindowsHookEx(hook)
    jobs.put("quit")
    try:
        os.remove(STOPFILE)
    except OSError:
        pass
    log("stopped")


def running():
    h = k32.OpenMutexW(0x00100000, False, MUTEX)             # SYNCHRONIZE
    if h:
        k32.CloseHandle(h)
        return True
    return False


if __name__ == "__main__":
    mp.freeze_support()
    if "--stop" in sys.argv:
        os.makedirs(LOGDIR, exist_ok=True)
        open(STOPFILE, "w").close()
        print("stop requested")
    elif "--status" in sys.argv:
        print("running" if running() else "not running")
        try:
            print(open(os.path.join(LOGDIR, "hotkeys_state.txt"), encoding="utf-8").read().strip())
        except OSError:
            pass
    else:
        main()
