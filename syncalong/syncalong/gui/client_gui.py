import wx.adv
import wx
TRAY_TOOLTIP = 'Name' 
TRAY_ICON = 'icon.png' 

class Mp3Panel(wx.Panel):    
    def __init__(self, parent):
        super().__init__(parent)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.row_obj_dict = {}

        self.list_ctrl = wx.ListCtrl(
            self, size=(-1, 100), 
            style=wx.LC_REPORT | wx.BORDER_SUNKEN
        )
        self.list_ctrl.InsertColumn(0, 'Title', width=200)
        self.list_ctrl.InsertColumn(1, 'Artist', width=140)
        self.list_ctrl.InsertColumn(2, 'Album', width=140)
        main_sizer.Add(self.list_ctrl, 0, wx.ALL | wx.EXPAND, 5)        
        edit_button = wx.Button(self, label='Update server')
        edit_button.Bind(wx.EVT_BUTTON, self.on_update)
        main_sizer.Add(edit_button, 0, wx.ALL | wx.CENTER, 5)        
        self.SetSizer(main_sizer)

    def on_update(self, event):
        print('in on_update')

class Mp3Frame(wx.Frame):    
    def __init__(self):
        super().__init__(parent=None,
                         title='SyncAlong')
        self.panel = Mp3Panel(self)


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