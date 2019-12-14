import os
import json
import threading
import wx.adv
import wx

from client.client import Client
from gui_general import HORIZONTAL, VERTICAL, PORT_VALID_CHARS, check_valid_data

TRAY_TOOLTIP = 'Name'
TRAY_ICON = './gui/icon.png'
CONFIG_PATH = './client/conf.json'

CONF = None

class SettingsPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.read_config()

        self.server_ip = wx.StaticText(self, label="Server ip", pos=(HORIZONTAL.TEXT, VERTICAL.FIRST_LINE))
        self.server_ip_text = wx.TextCtrl(self, value=CONF['ServerIp'],
                                          pos=(HORIZONTAL.TEXT_CTRL, VERTICAL.FIRST_LINE), size=(140, -1))
        self.Bind(wx.EVT_TEXT, self.on_set_ip, self.server_ip_text)

        self.server_port = wx.StaticText(self, label="Server port", pos=(HORIZONTAL.TEXT, VERTICAL.SECOND_LINE))
        self.server_port_text = wx.TextCtrl(self, value=str(CONF["ServerPort"]),
                                            pos=(HORIZONTAL.TEXT_CTRL, VERTICAL.SECOND_LINE), size=(210, -1))
        self.Bind(wx.EVT_TEXT, self.on_set_port, self.server_port_text)

        self.songs_path = wx.StaticText(self, label="Local songs path", pos=(HORIZONTAL.TEXT, VERTICAL.THIRD_LINE))
        self.songs_path_text = wx.TextCtrl(self, value=str(CONF["SongsPath"]), pos=(HORIZONTAL.TEXT_CTRL, VERTICAL.THIRD_LINE),
                                           size=(210, -1))
        self.Bind(wx.EVT_TEXT, self.on_set_path, self.songs_path_text)

        save_button = wx.Button(self, label='Save config', pos=(HORIZONTAL.TEXT, VERTICAL.FORTH_LINE))
        save_button.Bind(wx.EVT_BUTTON, self.on_save)

    def on_set_ip(self, event):
        CONF["ServerIp"] = event.GetString()

    def on_set_port(self, event):
        data = check_valid_data(event.GetString(), PORT_VALID_CHARS)
        if data and int(data) < 2**16 and int(data) > 0:
            CONF["ServerPort"] = int(data)
        else:
            self.server_port_text.SetValue(f'Port should be between 0 to {2**16}')

    def on_set_path(self, event):
        CONF["SongsPath"] = event.GetString()

    def on_save(self, event):
        with open(CONFIG_PATH, 'w') as f:
            json.dump(CONF, f)

    def read_config(self):
        global CONF
        try:
            with open(CONFIG_PATH, 'r') as f:
                CONF = json.load(f)
        except:
            CONF = {"ServerIp": "",
                    "ServerPort": "22222",
                    "SongsPath": "./songs_folder"}
            self.on_save(None)



class Mp3Panel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        song_name = wx.StaticText(self, label="Title")
        self.plaing_song = wx.TextCtrl(self, value="", size=(-1,100), style=wx.LC_REPORT | wx.BORDER_SUNKEN | wx.TE_READONLY)
        main_sizer.Add(song_name, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(self.plaing_song, 0, wx.ALL | wx.EXPAND, 5)

        botton_sizer = wx.BoxSizer(wx.HORIZONTAL)

        connect_button = wx.Button(self, label='Connect/DisConnect')
        connect_button.Bind(wx.EVT_BUTTON, self.on_connect)
        botton_sizer.Add(connect_button, 0, wx.ALL | wx.CENTRE, 5)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_refresh)

        main_sizer.Add(botton_sizer, 0, wx.ALL | wx.CENTRE, 5)

        self.SetSizer(main_sizer)

        self.client = None
        self.thr = None
        self.connected = False
        self.plaing_now = ''

    def on_connect(self, event):
        if not self.connected:
            if CONF["ServerIp"] and CONF["ServerPort"]:
                print('Connect')
                try:
                    self.client = Client(CONF["ServerIp"], CONF["ServerPort"], CONF["ServerIp"], CONF["SongsPath"])
                except:
                    wx.MessageBox('Could not connect to server, try again or change server ip/port')
                    return
                self.thr = threading.Thread(target=self.client.start, args=(), kwargs={})
                self.thr.start()
                self.connected = True
                self.timer.Start(500)
            else:
                wx.MessageBox('Must set the ip and port before connecting to a server')
        else:
            print('DisConnect')
            self.client.stop_request.set()
            self.connected = False
            self.timer.Stop()

    def on_refresh(self, event):
        if self.connected and self.client.plaing_now != self.plaing_now:
            print('refresh')
            self.plaing_song.SetValue(self.client.plaing_now)
            self.plaing_now = self.client.plaing_now
        elif not self.connected:
            print("refresh not connected")
            self.plaing_song.SetValue('')


class Mp3Frame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='SyncAlong', size=(400,250))
        # self.panel = Mp3Panel(self)
        panel = wx.Panel(self)

        notebook = wx.Notebook(panel)

        settings_panel = SettingsPanel(notebook) # Setting need to be created before other pages
        self.mp3_panel = Mp3Panel(notebook)

        notebook.AddPage(self.mp3_panel, 'Main')
        notebook.AddPage(settings_panel, 'Settings')

        sizer = wx.BoxSizer()
        sizer.Add(notebook, 1, wx.ALL | wx.EXPAND)
        panel.SetSizer(sizer)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event):
        self.Hide()

    def my_close(self):
        self.Hide()
        if self.mp3_panel.connected:
            self.mp3_panel.on_connect(None)
        self.Destroy()


def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        self.frame = frame
        super(TaskBarIcon, self).__init__()
        self.set_icon(TRAY_ICON)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        create_menu_item(menu, 'Show window', self.on_show_window)
        menu.AppendSeparator()
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.Icon(path)
        self.SetIcon(icon, TRAY_TOOLTIP)

    def on_left_down(self, event):
        print('Tray icon was left-clicked.')

    def on_show_window(self, event):
        self.frame.Show()

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.my_close()


class App(wx.App):
    def OnInit(self):
        frame = Mp3Frame()
        self.SetTopWindow(frame)
        TaskBarIcon(frame)
        frame.Show()
        return True


def main():
    app = App(False)
    app.MainLoop()


if __name__ == '__main__':
    main()
