import os
import wx
import wx.lib.mixins.listctrl  as  listmix
from mutagen.mp3 import MP3

from server.music_server import MusicServer
from server.ntp_server import NTPServer
from common.signal_packet import DEFAULT_WAIT_SECONDS

from gui_general import HORIZONTAL, VERTICAL, PORT_VALID_CHARS, check_valid_data


SERVER_PORT = 22222
SONGS_PATH = os.path.join(os.path.dirname(__file__), 'songs_folder')

class FileDrop(wx.FileDropTarget):
    def __init__(self, window):
        wx.FileDropTarget.__init__(self)
        self.window = window

    def OnDropFiles(self, x, y, filenames):
        for name in filenames:
            if MP3(name):
                self.window.InsertItem(self.window.ItemCount, name)
        return True


class EditableListCtrl(wx.ListCtrl, listmix.TextEditMixin):
    def __init__(self, parent, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent=parent, size=size, style=style)
        listmix.TextEditMixin.__init__(self)

        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_rightclick)

    def on_rightclick(self, event):
        self.menu_title_by_id = {wx.NewId(): ("Remove from list", (lambda *args: None)),
                            wx.NewId(): ("Move Down", self.move_down),
                            wx.NewId(): ("Move Up", self.move_up),
                            wx.NewId(): ("Move to Start", self.move_to_start),
                            wx.NewId(): ("Move to End", self.move_to_end)}

        self.item = event.GetItem()

        menu = wx.Menu()
        for id,(title,_) in self.menu_title_by_id.items():
            menu.Append( id, title )
            wx.EVT_MENU( menu, id, self.MenuSelectionCb )

        self.PopupMenu(menu, event.GetPoint())
        menu.Destroy()

    def MenuSelectionCb(self, event):
        self.DeleteItem(self.item.GetId())
        self.menu_title_by_id[event.GetId()][1]()

    def move_down(self):
        self.InsertItem(self.item.GetId()+1, self.item.GetText())

    def move_up(self):
        self.InsertItem(self.item.GetId()-1, self.item.GetText())

    def move_to_start(self):
        self.InsertItem(0, self.item.GetText())

    def move_to_end(self):
        self.InsertItem(self.ItemCount, self.item.GetText())


class SettingsPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.server_port = wx.StaticText(self, label="Server port", pos=(HORIZONTAL.TEXT, VERTICAL.SECOND_LINE))
        self.server_port_text = wx.TextCtrl(self, value=str(SERVER_PORT),
                                            pos=(HORIZONTAL.TEXT_CTRL, VERTICAL.SECOND_LINE), size=(210, -1))
        self.Bind(wx.EVT_TEXT, self.on_set_port, self.server_port_text)

        self.songs_path = wx.StaticText(self, label="Local songs path", pos=(HORIZONTAL.TEXT, VERTICAL.THIRD_LINE))
        self.songs_path_text = wx.TextCtrl(self, value=str(SONGS_PATH), pos=(HORIZONTAL.TEXT_CTRL, VERTICAL.THIRD_LINE),
                                           size=(210, -1))
        self.Bind(wx.EVT_TEXT, self.on_set_path, self.songs_path_text)


    def on_set_port(self, event):
        global SERVER_PORT
        data = check_valid_data(event.GetString(), PORT_VALID_CHARS)
        if data and int(data) < 2**16 and int(data) > 0:
            SERVER_PORT = int(data)
        else:
            self.server_port_text.SetValue(f'Port should be between 1 to {2**16-1}')
        print(SERVER_PORT)

    def on_set_path(self, event):
        global SONGS_PATH
        SONGS_PATH = event.GetString()


class Mp3Panel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.list_ctrl = EditableListCtrl(
            self, size=(-1, 500),
            style=wx.LC_REPORT | wx.BORDER_SUNKEN
        )
        self.list_ctrl.InsertColumn(0, 'Song Path', width=200)

        dt = FileDrop(self.list_ctrl)        
        self.list_ctrl.SetDropTarget(dt)
        main_sizer.Add(self.list_ctrl, 0, wx.ALL | wx.EXPAND, 5)

        self.initialize_songs_list()

        botton_sizer = wx.BoxSizer(wx.HORIZONTAL)

        connect_button = wx.Button(self, label='Start')
        connect_button.Bind(wx.EVT_BUTTON, self.on_start)
        botton_sizer.Add(connect_button, 0, wx.ALL | wx.CENTRE, 5)

        connect_button = wx.Button(self, label='Stop')
        connect_button.Bind(wx.EVT_BUTTON, self.on_stop)
        botton_sizer.Add(connect_button, 0, wx.ALL | wx.CENTRE, 5)

        connect_button = wx.Button(self, label='Pause/Unpause')
        connect_button.Bind(wx.EVT_BUTTON, self.on_pause)
        botton_sizer.Add(connect_button, 0, wx.ALL | wx.CENTRE, 5)

        connect_button = wx.Button(self, label='Play next')
        connect_button.Bind(wx.EVT_BUTTON, self.on_play_next)
        botton_sizer.Add(connect_button, 0, wx.ALL | wx.CENTRE, 5)

        main_sizer.Add(botton_sizer, 0, wx.ALL | wx.CENTRE, 5)

        self.SetSizer(main_sizer)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_play_trigger)

        self.music_s = None
        self.ntp_s = None
        self.song_list = []

        self.running = False
        self.paused = False

    def on_start(self, event):
        print('start')
        if not self.running:
            print(SERVER_PORT)
            if SERVER_PORT:
                if not self.music_s:
                    self.music_s = MusicServer("0.0.0.0", SERVER_PORT)
                if not self.ntp_s:
                    self.ntp_s = NTPServer("0.0.0.0", 123)
                self.ntp_s.start()
                self.music_s.start()
                self.running = True
                self.on_play_trigger(event)
            else:
                wx.MessageBox('Must set the port before running to a server')

    def on_stop(self, event):
        print('stop')
        if self.running:
            self.timer.Stop()
            self.music_s.signal_stop_all()
            self.running = False

            self.ntp_s = self.ntp_s.close()
            self.music_s = self.music_s.close()

    def on_pause(self, event):
        print('pause/unpause')
        if self.running:
            if self.paused:
                if self.timer_time_left:
                    self.timer.StartOnce(self.timer_time_left)
                self.music_s.signal_unpause_all()
                self.timer_time_left = 0
            else:
                self.timer_time_left = self.timer.GetInterval()
                self.music_s.signal_pause_all()      
            self.paused = not self.paused

    def on_play_next(self, event):
        print('play next')
        if self.running:
            self.on_stop(event)
            self.on_play_trigger(event)

    def on_play_trigger(self, event):
        print('play')
        if self.running and self.music_s.clients and self.list_ctrl.ItemCount > 0:
            song = self.list_ctrl.GetItem(0)
            self.music_s.serve_music_file(song.GetText())
            self.music_s.signal_play_all(song.GetText())
            song_length = MP3(song.GetText()).info.length*1000
            print(song_length)
            self.timer.StartOnce(song_length) # Timer works with milliseconds and MP3 works with Seconds
            self.list_ctrl.DeleteItem(song.GetId())
        else:
            self.timer.StartOnce(1000)

    def initialize_songs_list(self):
        for dirname, _, files in os.walk(SONGS_PATH):
            for file in files:
                path = os.path.join(dirname, file)
                if MP3(path):
                    self.list_ctrl.InsertItem(self.list_ctrl.ItemCount, path)
        

class Mp3Frame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='SyncAlong', size=(500,650))
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
        self.mp3_panel.on_stop(event)
        self.Destroy()

class App(wx.App):
    def OnInit(self):
        frame = Mp3Frame()
        self.SetTopWindow(frame)
        frame.Show()
        return True


def main():
    app = App(False)
    app.MainLoop()


if __name__ == '__main__':
    main()
