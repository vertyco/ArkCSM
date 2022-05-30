import asyncio
from datetime import datetime
import json
import logging
import os
import shutil

import aiohttp
import psutil
import pywinauto.mouse
import win32con
import win32evtlog
import win32gui
from pywinauto.application import Application

"""
Calculating aspect ratios
x = measured x coordinate / total pixel width (ex: 500/1280)
y = measured y coordinate / total pixel height (ex: 300/720)
"""
TEAMVIEWER = (0.59562272, 0.537674419)
START = (0.49975574, 0.863596872)
HOST = (0.143624817, 0.534317984)
RUN = (0.497313141, 0.748913988)
ACCEPT1 = (0.424035173, 0.544743701)
ACCEPT2 = (0.564240352, 0.67593397)
INVITE = (0.8390625, 0.281944444)
EXIT = (0.66171875, 0.041666667)

os.system('title ArkHandler')
logging.basicConfig(filename='logs.log',
                    filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')
log = logging.getLogger()
log.setLevel(logging.DEBUG)

DOWNLOAD_MESSAGE = "**The server has started downloading an update, and will go down once it starts installing.**"
INSTALL_MESSAGE = "**The server has started installing the update. Stand by...**"
COMPLETED_MESSAGE = "**The server has finished installing the update.**"

EVENTS = []

# Find valid appdata path
MAIN = f"{os.environ['LOCALAPPDATA']}/Packages/StudioWildcard.4558480580BB9_1w2mm55455e38/LocalState/Saved"
TARGET = f"{MAIN}/UWPConfig/UWP"
ARK_BOOT = "explorer.exe shell:appsFolder\StudioWildcard.4558480580BB9_1w2mm55455e38!AppARKSurvivalEvolved"
XAPP = "explorer.exe shell:appsFolder\Microsoft.XboxApp_8wekyb3d8bbwe!Microsoft.XboxApp"


def window_enumeration_handler(hwnd, windows):
    windows.append((hwnd, win32gui.GetWindowText(hwnd)))


def event(widget, log_event):
    global EVENTS
    EVENTS.append(log_event)
    tolog = EVENTS
    if len(EVENTS) > 7:
        tolog = EVENTS[-7:]
        EVENTS = tolog
    text = ""
    for i in tolog:
        text += f"{i}\n"
    widget.configure(text=text)


class ArkHandler:
    def __init__(self, widget, config):
        self.widget = widget
        self.config = config
        self.running = False
        self.checking_updates = False
        self.downloading = False
        self.updating = False
        self.installing = False
        self.booting = False
        self.last_update = None

        self.timestamp = ""

        self.top_windows = []

    async def import_config(self):
        if self.config["gameini"]:
            if os.path.exists(self.config["gameini"]) and os.path.exists(TARGET):
                s_file = os.path.join(self.config["gameini"], "Game.ini")
                t_file = os.path.join(TARGET, "Game.ini")
                if os.path.exists(t_file):
                    try:
                        os.remove(t_file)
                    except Exception as ex:
                        event(self.widget, f"Failed to sync Game.ini, check log for details.")
                        print(f"Failed to sync Game.ini\nError: {ex}")
                        log.warning(f"Failed to sync Game.ini\nError: {ex}")
                        return
                if not os.path.exists(s_file):
                    event(self.widget, f"Cannot find source Game.ini file, check log for details.")
                    print(f"Cannot find source Game.ini file!")
                    log.warning(f"Cannot find source Game.ini file!")
                    return
                shutil.copyfile(s_file, t_file)
                event(self.widget, "Game.ini synced.")
                print("Game.ini synced.")

        # sync GameUserSettings.ini file
        if self.config["gameuserini"]:
            if os.path.exists(self.config["gameuserini"]) and os.path.exists(TARGET):
                s_file = os.path.join(self.config["gameuserini"], "GameUserSettings.ini")
                t_file = os.path.join(TARGET, "GameUserSettings.ini")
                if os.path.exists(t_file):
                    try:
                        os.remove(t_file)
                    except Exception as ex:
                        event(self.widget, f"Failed to sync GameUserSettings.ini, check log for details.")
                        print(f"Failed to sync GameUserSettings.ini\nError: {ex}")
                        log.warning(f"Failed to sync GameUserSettings.ini\nError: {ex}")
                        return
                if not os.path.exists(s_file):
                    event(self.widget, "Cannot find source GameUserSettings.ini file, check log for details.")
                    print(f"Cannot find source GameUserSettings.ini file!")
                    log.warning(f"Cannot find source GameUserSettings.ini file!")
                    return
                shutil.copyfile(s_file, t_file)
                event(self.widget, "GameUserSettings.ini synced.")
                print("GameUserSettings.ini synced.")

    @staticmethod
    async def calc_position_click(clicktype, action=None):
        # get clicktype ratios
        x = clicktype[0]
        y = clicktype[1]

        # grab ark window
        window_handle = win32gui.FindWindow(None, "ARK: Survival Evolved")
        window_rect = win32gui.GetWindowRect(window_handle)
        # check if window is maximized and maximize it if not
        tup = win32gui.GetWindowPlacement(window_handle)
        if tup[1] != win32con.SW_SHOWMAXIMIZED:
            window = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(window, win32con.SW_MAXIMIZE)
            window_handle = win32gui.FindWindow(None, "ARK: Survival Evolved")
            window_rect = win32gui.GetWindowRect(window_handle)

        # sort window borders
        right = window_rect[2]
        bottom = window_rect[3] + 20

        # get click positions
        x_click = right * x
        y_click = bottom * y

        # click dat shit
        if action == "double":
            pywinauto.mouse.double_click(button='left', coords=(int(x_click), int(y_click)))
        else:
            pywinauto.mouse.click(button='left', coords=(int(x_click), int(y_click)))

    async def send_hook(self, title, message, color, msg=None):
        if not self.config["webhook"]:
            return
        if msg:
            data = {"username": "ArkHandler", "avatar_url": "https://i.imgur.com/Wv5SsBo.png", "embeds": [
                {
                    "description": message,
                    "title": title,
                    "color": color,
                    "footer": {"text": msg}
                }
            ]}
        else:
            data = {"username": "ArkHandler", "avatar_url": "https://i.imgur.com/Wv5SsBo.png", "embeds": [
                {
                    "description": message,
                    "title": title,
                    "color": color
                }
            ]}
        headers = {
            "Content-Type": "application/json"
        }
        event(self.widget, "Attempting to send webhook")
        print("Attempting to send webhook")
        try:
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=20)
                async with session.post(
                        url=self.config["webhook"],
                        data=json.dumps(data),
                        headers=headers,
                        timeout=timeout) as res:
                    if res.status == 204:
                        event(self.widget, f"Sent {title} Webhook - Status: {res.status}")
                        print(f"Sent {title} Webhook - Status: {res.status}")
                    else:
                        event(self.widget, f"{title} Webhook may have failed - Status: {res.status}")
                        print(f"{title} Webhook may have failed - Status: {res.status}")
                        log.warning(f"{title} Webhook may have failed - Status: {res.status}")
        except Exception as e:
            event(self.widget, f"SendHook Error, check logs")
            log.warning(f"SendHook: {e}")

    @staticmethod
    async def ark():
        if "ShooterGame.exe" in (p.name() for p in psutil.process_iter()):
            return True

    @staticmethod
    async def kill_ark():
        for p in psutil.process_iter():
            if p.name() == "ShooterGame.exe":
                p.kill()

    @staticmethod
    async def store():
        if "WinStore.App.exe" in (p.name() for p in psutil.process_iter()):
            return True

    async def kill_store(self):
        # check if teamviewer sponsored session window is open
        if not self.updating:
            for p in psutil.process_iter():
                if p.name() == "WinStore.App.exe":
                    try:
                        p.kill()
                    except Exception as ex:
                        log.warning(f"WinStore App failed to terminate!\nError: {ex}")

    async def close_tv(self):
        self.top_windows = []
        win32gui.EnumWindows(window_enumeration_handler, self.top_windows)
        for window in self.top_windows:
            if "sponsored session" in window[1].lower():
                event(self.widget, "Closing teamviewer sponsored session window")
                print("Closing teamviewer sponsored session window")
                handle = win32gui.FindWindow(None, window[1])
                win32gui.SetForegroundWindow(handle)
                win32gui.PostMessage(handle, win32con.WM_CLOSE, 0, 0)
                await asyncio.sleep(1)
                break

    async def watchdog(self):
        """Check every 30 seconds if Ark is running, and start the server if it is not."""
        while True:
            if await self.ark():
                if not self.running:
                    event(self.widget, "Ark is Running")
                    print("Ark is Running.")
                    self.running = True
            else:
                if not self.updating and not self.checking_updates and not self.booting:
                    event(self.widget, "Ark is not Running! Beginning reboot sequence...")
                    print("Ark is not Running! Beginning reboot sequence...")
                    try:
                        print("Importing config")
                        await self.import_config()
                        print("Sending hook")
                        await self.send_hook("Server Down", "Beginning reboot sequence...", 16739584)
                        print("Booting ark")
                        await self.boot_ark()
                    except Exception as e:
                        log.warning(f"Watchdog: {e}")
            await asyncio.sleep(30)

    async def boot_ark(self):
        self.running = False
        self.booting = True
        if await self.ark():
            print("Ark already running. Killing.")
            await self.kill_ark()
            await asyncio.sleep(20)
        await asyncio.sleep(5)
        await self.close_tv()
        # start ark
        event(self.widget, "Attempting to launch Ark")
        print("Attempting to launch Ark")
        os.system(ARK_BOOT)
        await asyncio.sleep(15)
        # make sure ark is actually fucking running and didnt crash
        if not await self.ark():
            event(self.widget, "Ark crashed, trying again... (Thanks Wildcard)")
            print("Ark crashed, trying again... (Thanks Wildcard)")
            os.system(ARK_BOOT)
            await asyncio.sleep(20)

        await self.calc_position_click(START, "double")
        await asyncio.sleep(8)
        await self.calc_position_click(HOST)
        await asyncio.sleep(4)
        await self.calc_position_click(RUN)
        await asyncio.sleep(2)
        await self.calc_position_click(ACCEPT1)
        await asyncio.sleep(2)
        await self.calc_position_click(ACCEPT2)

        event(self.widget, "Boot macro finished, loading server files.")
        print("Boot macro finished, loading server files.")
        await self.send_hook("Booting", "Loading server files...", 19357)
        await asyncio.sleep(10)
        event(self.widget, "Stopping LicenseManager")
        print("Stopping LicenseManager")
        os.system("net stop LicenseManager")
        await asyncio.sleep(60)
        await self.send_hook("Reboot Complete", "Server should be back online.", 65314)
        self.booting = False

    async def event_puller(self):
        """Gets most recent update event for ark and determines how recent it was"""
        while True:
            await asyncio.sleep(5)
            try:
                await self.pull_events()
            except Exception as e:
                log.warning(f"EventPuller: {e}")

    async def pull_events(self):
        server = 'localhost'
        logtype = 'System'
        now = datetime.now()
        hand = win32evtlog.OpenEventLog(server, logtype)
        flags = win32evtlog.EVENTLOG_SEQUENTIAL_READ | win32evtlog.EVENTLOG_BACKWARDS_READ
        events = win32evtlog.ReadEventLog(hand, flags, 0)
        for e in events:
            data = e.StringInserts
            if "-StudioWildcard" in str(data[0]):
                if self.last_update == e.TimeGenerated:
                    return

                eid = e.EventID
                string = data[0]

                td = now - e.TimeGenerated
                if td.total_seconds() < 3600:
                    recent = True
                else:
                    recent = False

                if eid == 44 and recent and not self.updating:
                    print(f"DOWNLOAD DETECTED: {string}")
                    await self.send_hook(
                        "Download Detected!",
                        DOWNLOAD_MESSAGE,
                        14177041,
                        f"File: {string}"
                    )
                    self.updating = True

                elif eid == 43 and recent and not self.installing:
                    print(f"INSTALL DETECTED: {string}")
                    await self.send_hook(
                        "Installing",
                        INSTALL_MESSAGE,
                        1127128,
                        f"File: {string}"
                    )
                    self.installing = True

                elif eid == 19 and recent:
                    if self.updating or self.installing:
                        print(f"UPDATE SUCCESS: {string}")
                        await self.send_hook(
                            "Update Complete",
                            COMPLETED_MESSAGE,
                            65314,
                            f"File: {string}"
                        )
                        await asyncio.sleep(20)
                        self.updating = False
                        self.installing = False
                        await self.boot_ark()
                self.last_update = e.TimeGenerated
                return

    async def update_checker(self):
        while True:
            try:
                await asyncio.sleep(600)
                await self.check_updates()
                await asyncio.sleep(100)
                await self.kill_store()
            except Exception as e:
                log.warning(f"UpdateChecker: {e}")

    async def check_updates(self):
        if not self.booting and self.running:
            self.checking_updates = True
            if not await self.store():
                os.system("explorer.exe shell:appsFolder\Microsoft.WindowsStore_8wekyb3d8bbwe!App")
                await asyncio.sleep(3)
            else:
                program = "microsoft store"
                self.top_windows = []
                win32gui.EnumWindows(window_enumeration_handler, self.top_windows)
                for window in self.top_windows:
                    if program in window[1].lower():
                        win32gui.ShowWindow(window[0], win32con.SW_MAXIMIZE)

            app = Application(backend="uia").connect(title="Microsoft Store")
            await asyncio.sleep(3)
            for button in app.windows()[0].descendants():
                if "Library" in str(button):
                    button.click_input()
                    await asyncio.sleep(2)
                    for button2 in app.windows()[0].descendants(control_type="Button"):
                        if "Get updates" in str(button2):
                            button2.click()
                            window = win32gui.GetForegroundWindow()
                            win32gui.ShowWindow(window, win32con.SW_MINIMIZE)
                            await asyncio.sleep(5)
            self.checking_updates = False

    async def wipe_checker(self):
        while True:
            print("Cheking wipe schedule")
            wipe = self.config["autowipe"]
            if not wipe["enabled"] or not wipe["times"]:
                await asyncio.sleep(30)
                continue
            now = datetime.now()
            for ts in wipe["times"]:
                time = datetime.strptime(ts, "%m/%d %H:%M")
                if time.month != now.month:
                    continue
                if time.day != now.day:
                    continue
                if time.hour != now.hour:
                    continue
                td = time.minute - now.minute

                if td == 0:
                    await self.wipe(wipe["clusterwipe"])
                    await asyncio.sleep(60)
                    break
            else:
                await asyncio.sleep(5)

    async def wipe(self, wipe_cluster_data):
        event(self.widget, "WIPING SERVER!!!")
        self.booting = True
        await self.kill_ark()
        if wipe_cluster_data:
            cpath = f"{MAIN}/clusters/solecluster/"
            if not os.listdir(cpath):
                pass
            else:
                for cname in os.listdir(cpath):
                    if "sync" in cname:
                        continue
                    os.remove(os.path.join(cpath, cname))

        maps = f"{MAIN}/Maps"
        for foldername in os.listdir(maps):
            if "ClientPaintingsCache" in foldername:
                continue
            if "sync" in foldername:
                continue
            mapfolder = f"{maps}/{foldername}"

            # Only the island has no subfolder
            subfolder = True
            if foldername == "SavedArks":
                subfolder = False

            if not subfolder:
                mapcontents = os.listdir(mapfolder)
            else:
                mapfolder = f"{mapfolder}/{os.listdir(mapfolder)[0]}"
                mapcontents = os.listdir(mapfolder)

            for item in mapcontents:
                if "ServerPaintingsCache" in item:
                    continue
                if "BanList" in item:
                    continue
                if os.path.isdir(os.path.join(mapfolder, item)):
                    continue
                os.remove(os.path.join(mapfolder, item))
        self.booting = False
        event(self.widget, "WIPE COMPLETE!!!")
