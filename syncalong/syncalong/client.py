import os
import threading
import wx.adv
import wx

from client.client import Client

TRAY_TOOLTIP = 'Name' 
TRAY_ICON = './gui/icon.png'

## Settings panel posisions
class HORIZONTAL:
    TEXT = 20
    TEXT_CTRL = 150

class VERTICAL:
    FIRST_LINE = 0
    SECOND_LINE = 30
    THIRD_LINE = 60

SERVER_IP = '127.0.0.1'
SERVER_PORT = 22222
SONGS_PATH = os.path.join(os.path.dirname(__file__), 'songs_folder')

class ExamplePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.quote = wx.StaticText(self, label="Your quote :", pos=(20, 30))

        # A multiline TextCtrl - This is here to show how the events work in this program, don't pay too much attention to it
        self.logger = wx.TextCtrl(self, pos=(300,20), size=(200,300), style=wx.TE_MULTILINE | wx.TE_READONLY)

        # A button
        self.button =wx.Button(self, label="Save", pos=(200, 325))
        self.Bind(wx.EVT_BUTTON, self.OnClick,self.button)

        # the edit control - one line version.
        self.lblname = wx.StaticText(self, label="Your name :", pos=(20,60))
        self.editname = wx.TextCtrl(self, value="Enter here your name", pos=(150, 60), size=(140,-1))
        self.Bind(wx.EVT_TEXT, self.EvtText, self.editname)
        self.Bind(wx.EVT_CHAR, self.EvtChar, self.editname)

        # the combobox Control
        self.sampleList = ['friends', 'advertising', 'web search', 'Yellow Pages']
        self.lblhear = wx.StaticText(self, label="How did you hear from us ?", pos=(20, 90))
        self.edithear = wx.ComboBox(self, pos=(150, 90), size=(95, -1), choices=self.sampleList, style=wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, self.edithear)
        self.Bind(wx.EVT_TEXT, self.EvtText,self.edithear)

        # Checkbox
        self.insure = wx.CheckBox(self, label="Do you want Insured Shipment ?", pos=(20,180))
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, self.insure)

        # Radio Boxes
        radioList = ['blue', 'red', 'yellow', 'orange', 'green', 'purple', 'navy blue', 'black', 'gray']
        rb = wx.RadioBox(self, label="What color would you like ?", pos=(20, 210), choices=radioList,  majorDimension=3,
                         style=wx.RA_SPECIFY_COLS)
        self.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, rb)

    def EvtRadioBox(self, event):
        self.logger.AppendText('EvtRadioBox: %d\n' % event.GetInt())
    def EvtComboBox(self, event):
        self.logger.AppendText('EvtComboBox: %s\n' % event.GetString())
    def OnClick(self,event):
        self.logger.AppendText(" Click on object with Id %d\n" %event.GetId())
    def EvtText(self, event):
        self.logger.AppendText('EvtText: %s\n' % event.GetString())
    def EvtChar(self, event):
        self.logger.AppendText('EvtChar: %d\n' % event.GetKeyCode())
        event.Skip()
    def EvtCheckBox(self, event):
        self.logger.AppendText('EvtCheckBox: %d\n' % event.Checked())

class SettingsPanel(wx.Panel): 
    def __init__(self, parent):
        super().__init__(parent)

        self.server_ip = wx.StaticText(self, label="Server ip", pos=(HORIZONTAL.TEXT,VERTICAL.FIRST_LINE))
        self.server_ip_text = wx.TextCtrl(self, value="Enter Server ip", pos=(HORIZONTAL.TEXT_CTRL, VERTICAL.FIRST_LINE), size=(140,-1))
        self.Bind(wx.EVT_TEXT, self.on_set_ip, self.server_ip_text)

        self.server_port = wx.StaticText(self, label="Server port", pos=(HORIZONTAL.TEXT,VERTICAL.SECOND_LINE))
        self.server_port_text = wx.TextCtrl(self, value=str(SERVER_PORT), pos=(HORIZONTAL.TEXT_CTRL, VERTICAL.SECOND_LINE), size=(140,-1))
        self.Bind(wx.EVT_TEXT, self.on_set_port, self.server_port_text)

        self.songs_path = wx.StaticText(self, label="Local songs path", pos=(HORIZONTAL.TEXT,VERTICAL.THIRD_LINE))
        self.songs_path_text = wx.TextCtrl(self, value=str(SONGS_PATH), pos=(HORIZONTAL.TEXT_CTRL, VERTICAL.THIRD_LINE), size=(200,-1))
        self.Bind(wx.EVT_TEXT, self.on_set_path, self.songs_path_text)

    def on_set_ip(self, event):
        SERVER_IP = event.GetString()

    def on_set_port(self, event):
        SERVER_PORT = event.GetInt()

    def on_set_path(self, event):
        SONGS_PATH = event.GetInt()

class Mp3Panel(wx.Panel): 
    def __init__(self, parent):
        super().__init__(parent)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.list_ctrl = wx.ListCtrl(
            self, size=(-1, 100), 
            style=wx.LC_REPORT | wx.BORDER_SUNKEN
        )
        self.list_ctrl.InsertColumn(0, 'Title', width=200)
        self.list_ctrl.InsertColumn(1, 'Artist', width=140)
        self.list_ctrl.InsertColumn(2, 'Album', width=140)
        main_sizer.Add(self.list_ctrl, 0, wx.ALL | wx.EXPAND, 5)

        botton_sizer = wx.BoxSizer(wx.HORIZONTAL)

        connect_button = wx.Button(self, label='Connect')
        connect_button.Bind(wx.EVT_BUTTON, self.on_connect)
        botton_sizer.Add(connect_button, 0, wx.ALL | wx.CENTRE, 5)

        disconnect_button = wx.Button(self, label='DisConnect')
        disconnect_button.Bind(wx.EVT_BUTTON, self.on_disconnect)
        botton_sizer.Add(disconnect_button, 0, wx.ALL | wx.CENTRE, 5)

        main_sizer.Add(botton_sizer, 0, wx.ALL | wx.CENTRE, 5)

        self.SetSizer(main_sizer)

        self.client = None
        self.thr = None

    def on_connect(self, event):
        self.client = Client(SERVER_IP, SERVER_PORT, SERVER_IP, SONGS_PATH)
        self.thr = threading.Thread(target=self.client.start, args=(), kwargs={})
        self.thr.start()

    def on_disconnect(self, event):
    	import ipdb;ipdb.set_trace()
    	self.thr.stop = True


class Mp3Frame(wx.Frame):    
    def __init__(self):
        super().__init__(parent=None,
                         title='SyncAlong')
        #self.panel = Mp3Panel(self)
        panel = wx.Panel(self)

        notebook = wx.Notebook(panel)

        mp3_panel = Mp3Panel(notebook)
        settings_panel = SettingsPanel(notebook)
        ex_panel = ExamplePanel(notebook)

        notebook.AddPage(mp3_panel, 'Main')
        notebook.AddPage(settings_panel, 'Setting')
        notebook.AddPage(ex_panel, 'test')


        sizer = wx.BoxSizer()
        sizer.Add(notebook, 1, wx.ALL | wx.EXPAND)
        panel.SetSizer(sizer)

        self.Centre() 
        self.Show() 
        self.Fit()


def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item


def create_window(frameType):
    frame = frameType()
    return frame


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
        print ('Tray icon was left-clicked.')

    def on_show_window(self, event):
        create_window(Mp3Frame).Show()

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Close()


class App(wx.App):
    def OnInit(self):
        frame = create_window(Mp3Frame)
        self.SetTopWindow(frame)
        TaskBarIcon(frame)
        frame.Show()
        return True

def main():
    app = App(False)
    app.MainLoop()


if __name__ == '__main__':
    main()