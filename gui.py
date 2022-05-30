import asyncio
import json
import os
from time import sleep

import customtkinter as ckt

from executor import threader

GREEN = "#2f4a2a"
RED = "#542929"
TEXT = "#03a892"


class ArkCSM(ckt.CTk):
    WIDTH = 780
    HEIGHT = 520

    def __init__(self, loop, config):
        super().__init__()
        self.loop = loop
        self.config = config
        self.title("Ark Cross-play Server Manager")
        self.geometry(f"{ArkCSM.WIDTH}x{ArkCSM.HEIGHT}")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed

        # ============ create two frames ============
        # configure grid layout (2x1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ============ left frame ============
        # configure grid layout (1x11)
        self.frame_left = ckt.CTkFrame(master=self, width=180, corner_radius=0)
        self.frame_left.grid(row=0, column=0, sticky="nswe")
        self.frame_left.grid_rowconfigure(0, minsize=10)  # empty row with minsize as spacing
        self.frame_left.grid_rowconfigure(5, weight=1)  # empty row as spacing
        self.frame_left.grid_rowconfigure(7, minsize=20)  # empty row with minsize as spacing
        self.frame_left.grid_rowconfigure(11, minsize=10)  # empty row with minsize as spacing

        self.title_label = ckt.CTkLabel(master=self.frame_left,
                                        text="ARK CSM",
                                        text_font=("Roboto Medium", -16))  # font name and size in px
        self.title_label.grid(row=1, column=0, pady=10, padx=10)

        # ============ toggles ===========
        self.autorun = ckt.CTkSwitch(master=self.frame_left, text="Auto Run", command=self.toggle_autorun)
        self.autorun.grid(row=8, column=0, pady=10, padx=20, sticky="w")

        self.autowipe = ckt.CTkSwitch(master=self.frame_left, text="Auto Wipe", command=self.toggle_autowipe)
        self.autowipe.grid(row=9, column=0, pady=10, padx=20, sticky="w")

        self.darkmode = ckt.CTkSwitch(master=self.frame_left, text="Dark Mode", command=self.change_mode)
        self.darkmode.grid(row=10, column=0, pady=10, padx=20, sticky="w")

        self.save = ckt.CTkButton(
            master=self.frame_left,
            text="Cycle Themes",
            fg_color=("gray75", "gray30"),
            command=self.cycle_themes
        )
        self.save.grid(row=2, column=0, pady=10, padx=20)

        # ============ right frame ============
        self.frame_right = ckt.CTkFrame(master=self)
        self.frame_right.grid(row=0, column=1, sticky="nswe", padx=20, pady=20)
        self.frame_right.columnconfigure(0, weight=1)

        # ============ right info frame ============
        self.frame_info = ckt.CTkFrame(master=self.frame_right)
        self.frame_info.grid(row=0, column=0, columnspan=3, rowspan=3, pady=20, padx=20, sticky="nsew")
        self.frame_info.columnconfigure(0, weight=3)
        self.frame_info.rowconfigure(2, minsize=180)
        self.events_label = ckt.CTkLabel(master=self.frame_info, text="Active Events")
        self.events_label.grid(column=0, row=0, sticky="n")
        self.events = ckt.CTkLabel(master=self.frame_info, text="")
        self.events.grid(column=0, row=1, sticky="n", rowspan=3, padx=10)

        # WEBHOOK
        self.webhook_label = ckt.CTkLabel(master=self.frame_right, text="WebHook URL")
        self.webhook_label.grid(row=7, column=0, sticky="n")
        hook = self.config["webhook"] if self.config["webhook"] else "Enter WebHook URL Here"
        color = "#34633c" if self.config["webhook"] else None
        self.webhook_entry = ckt.CTkEntry(
            master=self.frame_right,
            width=120,
            placeholder_text=hook,
            fg_color=color,
            text_color=TEXT,
            placeholder_text_color=TEXT
        )
        self.webhook_entry.grid(row=8, column=0, columnspan=2, pady=10, padx=20, sticky="we")
        self.webhook_save = ckt.CTkButton(master=self.frame_right, text="Save", command=self.save_webhook)
        self.webhook_save.grid(row=8, column=2, columnspan=1, pady=10, padx=20, sticky="we")

        # GAME.INI
        self.gameini_label = ckt.CTkLabel(master=self.frame_right, text="Game.ini Path")
        self.gameini_label.grid(row=9, column=0, sticky="n")
        hook = self.config["gameini"] if self.config["gameini"] else "Enter Game.ini Path Here"
        color = GREEN if self.config["gameini"] else None
        self.gameini_entry = ckt.CTkEntry(
            master=self.frame_right,
            width=120,
            placeholder_text=hook,
            fg_color=color,
            text_color=TEXT,
            placeholder_text_color=TEXT
        )
        self.gameini_entry.grid(row=10, column=0, columnspan=2, pady=10, padx=20, sticky="we")
        self.gameini_save = ckt.CTkButton(master=self.frame_right, text="Save", command=self.save_gameini)
        self.gameini_save.grid(row=10, column=2, columnspan=1, pady=10, padx=20, sticky="we")

        # # GAMEUSERSETTINGS.INI
        self.gameuserini_label = ckt.CTkLabel(master=self.frame_right, text="GameUserSettings.ini Path")
        self.gameuserini_label.grid(row=11, column=0, sticky="n")
        hook = self.config["gameuserini"] if self.config["gameuserini"] else "Enter Gameusersettings.ini Path Here"
        color = GREEN if self.config["gameuserini"] else None
        self.gameuserini_entry = ckt.CTkEntry(
            master=self.frame_right,
            width=120,
            placeholder_text=hook,
            fg_color=color,
            text_color=TEXT,
            placeholder_text_color=TEXT
        )
        self.gameuserini_entry.grid(row=12, column=0, columnspan=2, pady=10, padx=20, sticky="we")
        self.gameuserini_save = ckt.CTkButton(master=self.frame_right, text="Save", command=self.save_gameuserini)
        self.gameuserini_save.grid(row=12, column=2, columnspan=1, pady=10, padx=20, sticky="we")

        # ============ initialize from settings ============
        if self.config["darkmode"]:
            ckt.set_appearance_mode("dark")
            self.darkmode.select()
        else:
            ckt.set_appearance_mode("light")

        if self.config["autorun"]:
            self.autorun.select()

        if self.config["autowipe"]["enabled"]:
            self.autowipe.select()

    def cycle_themes(self):
        current = self.config["theme"]
        if current == "blue":
            self.config["theme"] = "dark-blue"
            window = ckt.CTkToplevel(self)
            window.geometry("300x50")
            label = ckt.CTkLabel(window, text=f"Theme color will be set to Dark Blue on app restart!")
            label.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        elif current == "dark-blue":
            self.config["theme"] = "green"
            window = ckt.CTkToplevel(self)
            window.geometry("300x50")
            label = ckt.CTkLabel(window, text=f"Theme color will be set to Green on app restart!")
            label.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        elif current == "green":
            self.config["theme"] = "sweetkind"
            window = ckt.CTkToplevel(self)
            window.geometry("300x50")
            label = ckt.CTkLabel(window, text=f"Theme color will be set to SweetKind on app restart!")
            label.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        else:
            self.config["theme"] = "blue"
            window = ckt.CTkToplevel(self)
            window.geometry("300x50")
            label = ckt.CTkLabel(window, text=f"Theme color will be set to Blue on app restart!")
            label.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        with open("config.json", "w") as f:
            f.write(json.dumps(self.config))

    def save_webhook(self):
        text = self.webhook_entry.get()
        saved = self.config["webhook"]
        print(text)
        if text and "discord.com/api/webhooks" in text:
            self.config["webhook"] = text
            self.webhook_entry.delete(0, "end")
            self.webhook_entry.insert(0, "Webhook URL Saved!")
            with open("config.json", "w") as f:
                f.write(json.dumps(self.config))
            self.update()
            sleep(2)
            self.webhook_entry.delete(0, "end")
            self.webhook_entry.insert(0, text)
        else:
            self.webhook_entry.configure(fg_color=RED)
            self.webhook_entry.delete(0, "end")
            self.webhook_entry.insert(0, "Invalid URL!")
            self.update()
            sleep(2)
            if saved:
                self.webhook_entry.delete(0, "end")
                self.webhook_entry.insert(0, saved)
                self.webhook_entry.configure(fg_color=GREEN)
            else:
                self.webhook_entry.delete(0, "end")
                self.webhook_entry.insert(0, "Enter WebHook URL Here")
                self.webhook_entry.configure(fg_color=None)

    def save_gameini(self):
        text = self.gameini_entry.get()
        saved = self.config["gameini"]
        if text and "Invalid" not in text and "Saved" not in text and "Enter" not in text:
            self.config["gameini"] = text
            self.gameini_entry.delete(0, "end")
            self.gameini_entry.insert(0, "Game.ini Path Saved!")
            with open("config.json", "w") as f:
                f.write(json.dumps(self.config))
            self.update()
            sleep(2)
            self.gameini_entry.delete(0, "end")
            self.gameini_entry.insert(0, text)
        else:
            self.gameini_entry.configure(fg_color=RED)
            self.gameini_entry.delete(0, "end")
            self.gameini_entry.insert(0, "Invalid Path!")
            self.update()
            sleep(2)
            if saved:
                self.gameini_entry.delete(0, "end")
                self.gameini_entry.insert(0, saved)
                self.gameini_entry.configure(fg_color=GREEN)
            else:
                self.gameini_entry.delete(0, "end")
                self.gameini_entry.insert(0, "Enter Game.ini Path Here")
                self.gameini_entry.configure(fg_color=None)

    def save_gameuserini(self):
        text = self.gameuserini_entry.get()
        saved = self.config["gameuserini"]
        if text and "Invalid" not in text and "Saved" not in text and "Enter" not in text:
            self.config["gameuserini"] = text
            self.gameuserini_entry.delete(0, "end")
            self.gameuserini_entry.insert(0, "GameUserSettings.ini Path Saved!")
            with open("config.json", "w") as f:
                f.write(json.dumps(self.config))
            self.update()
            sleep(2)
            self.gameuserini_entry.delete(0, "end")
            self.gameuserini_entry.insert(0, text)
        else:
            self.gameuserini_entry.configure(fg_color=RED)
            self.gameuserini_entry.delete(0, "end")
            self.gameuserini_entry.insert(0, "Invalid Path!")
            self.update()
            sleep(2)
            if saved:
                self.gameuserini_entry.delete(0, "end")
                self.gameuserini_entry.insert(0, saved)
                self.gameuserini_entry.configure(fg_color=GREEN)
            else:
                self.gameuserini_entry.delete(0, "end")
                self.gameuserini_entry.insert(0, "Enter GameUserSettings.ini Path Here")
                self.gameuserini_entry.configure(fg_color=None)

    def toggle_autorun(self):
        if self.autorun.get():
            self.config["autorun"] = True
            print("Turning autorun on")
            threader(self.events, self.loop)
        else:
            self.config["autorun"] = False
            print("Turning autorun off")
            self.loop.stop()
        with open("config.json", "w") as f:
            f.write(json.dumps(self.config))

    def toggle_autowipe(self):
        if self.autowipe.get():
            self.config["autowipe"]["enabled"] = True
            print("Turning autowipe on")
        else:
            self.config["autowipe"]["enabled"] = False
            print("Turning autowipe off")
        with open("config.json", "w") as f:
            f.write(json.dumps(self.config))

    def change_mode(self):
        if self.darkmode.get() == 1:
            ckt.set_appearance_mode("dark")
            self.config["darkmode"] = True
            print("Turning darkmode on")
        else:
            ckt.set_appearance_mode("light")
            self.config["darkmode"] = False
            print("Turning darkmode off")
        with open("config.json", "w") as f:
            f.write(json.dumps(self.config))

    def button_event(self):
        print("Button Pressed")

    def on_closing(self, event=0):
        self.loop.stop()
        self.destroy()

    def start(self):
        self.mainloop()


default_config = {
    "autorun": False,
    "webhook": None,
    "gameini": None,
    "gameuserini": None,
    "darkmode": True,  # Modes: "System" (standard), "Dark", "Light"
    "theme": "blue",  # Themes: "blue" (standard), "green", "dark-blue"
    "autowipe": {"enabled": False, "month": 0, "day": 0, "hour": 0}
}

if __name__ == "__main__":
    if not os.path.exists("config.json"):
        with open("config.json", "w") as file:
            file.write(json.dumps(default_config))
        conf = default_config
    else:
        with open("config.json", "r") as file:
            conf = json.load(file)
    ckt.set_default_color_theme(conf["theme"])
    print(conf)
    mainloop = asyncio.new_event_loop()
    try:
        ArkCSM(mainloop, conf).start()
    finally:
        mainloop.stop()
