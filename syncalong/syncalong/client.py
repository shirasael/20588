import os
import threading
import wx.adv
import wx

from client.client import Client
from gui_general import HORIZONTAL, VERTICAL, PORT_VALID_CHARS, check_valid_data

TRAY_TOOLTIP = 'Name'
TRAY_ICON = './gui/icon.png'


SERVER_IP = '127.0.0.1'
SERVER_PORT = 22222
SONGS_PATH = ''
DEFAULT_SONGS_PATH = os.path.join(os.path.dirname(__file__), 'songs_folder')

class SettingsPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.server_ip = wx.StaticText(self, label="Server ip", pos=(HORIZONTAL.TEXT, VERTICAL.FIRST_LINE))
        self.server_ip_text = wx.TextCtrl(self, value="Enter Server ip",
                                          pos=(HORIZONTAL.TEXT_CTRL, VERTICAL.FIRST_LINE), size=(140, -1))
        self.Bind(wx.EVT_TEXT, self.on_set_ip, self.server_ip_text)

        self.server_port = wx.StaticText(self, label="Server port", pos=(HORIZONTAL.TEXT, VERTICAL.SECOND_LINE))
        self.server_port_text = wx.TextCtrl(self, value=str(SERVER_PORT),
                                            pos=(HORIZONTAL.TEXT_CTRL, VERTICAL.SECOND_LINE), size=(210, -1))
        self.Bind(wx.EVT_TEXT, self.on_set_port, self.server_port_text)

        self.songs_path = wx.StaticText(self, label="Local songs path", pos=(HORIZONTAL.TEXT, VERTICAL.THIRD_LINE))
        self.songs_path_text = wx.TextCtrl(self, value=str(DEFAULT_SONGS_PATH), pos=(HORIZONTAL.TEXT_CTRL, VERTICAL.THIRD_LINE),
                                           size=(210, -1))
        self.Bind(wx.EVT_TEXT, self.on_set_path, self.songs_path_text)

    def on_set_ip(self, event):
        global SERVER_IP
        SERVER_IP = event.GetString()

    def on_set_port(self, event):
        global SERVER_PORT
        data = check_valid_data(event.GetString(), PORT_VALID_CHARS)
        if data and int(data) < 2**16 and int(data) > 0:
            SERVER_PORT = int(data)
        else:
            self.server_port_text.SetValue(f'Port should be between 0 to {2**16}')

    def on_set_path(self, event):
        global SONGS_PATH
        SONGS_PATH = event.GetString()


class Mp3Panel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        song_name = wx.StaticText(self, label="Title")
        self.plaing_song = wx.TextCtrl(self, value="", size=(-1,100), style=wx.LC_REPORT | wx.BORDER_SUNKEN | wx.TE_READONLY)
        main_sizer.Add(song_name, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(self.plaing_song, 0, wx.ALL | wx.EXPAND, 5)

        botton_sizer = wx.BoxSizer(wx.HORIZONTAL)

        connect_button = wx.Button(self, label='Connect')
        connect_button.Bind(wx.EVT_BUTTON, self.on_connect)
        botton_sizer.Add(connect_button, 0, wx.ALL | wx.CENTRE, 5)

        disconnect_button = wx.Button(self, label='DisConnect')
        disconnect_button.Bind(wx.EVT_BUTTON, self.on_disconnect)
        botton_sizer.Add(disconnect_button, 0, wx.ALL | wx.CENTRE, 5)

        refresh_button = wx.Button(self, label='Refresh')
        refresh_button.Bind(wx.EVT_BUTTON, self.on_refresh)
        botton_sizer.Add(refresh_button, 0, wx.ALL | wx.CENTRE, 5)

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
            if SERVER_IP and SERVER_PORT:
                print('Connect')
                songs_path = SONGS_PATH if SONGS_PATH else DEFAULT_SONGS_PATH
                try:
                    self.client = Client(SERVER_IP, SERVER_PORT, SERVER_IP, songs_path)
                except:
                    wx.MessageBox('Could not connect to server, try again or change server ip/port')
                    return
                self.thr = threading.Thread(target=self.client.start, args=(), kwargs={})
                self.thr.start()
                self.connected = True
                self.timer.Start(500)
            else:
                wx.MessageBox('Must set the ip and port before connecting to a server')                

    def on_disconnect(self, event):
        if self.connected:
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

        self.mp3_panel = Mp3Panel(notebook)
        settings_panel = SettingsPanel(notebook)

        notebook.AddPage(self.mp3_panel, 'Main')
        notebook.AddPage(settings_panel, 'Setting')

        sizer = wx.BoxSizer()
        sizer.Add(notebook, 1, wx.ALL | wx.EXPAND)
        panel.SetSizer(sizer)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event):
        self.Hide()

    def my_close(self):
        self.Hide()
        self.mp3_panel.on_disconnect(None)
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
