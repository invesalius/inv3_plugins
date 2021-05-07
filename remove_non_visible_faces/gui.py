import wx
from invesalius import project
from invesalius.gui.utils import calc_width_needed
from invesalius.utils import new_name_by_pattern
from pubsub import pub as Publisher

from .remove_non_visible_faces import remove_non_visible_faces


class Window(wx.Dialog):
    def __init__(self, parent):
        super().__init__(
            parent,
            title="Remove non-visible faces",
            style=wx.DEFAULT_DIALOG_STYLE | wx.FRAME_FLOAT_ON_PARENT,
        )

        self._init_gui()
        self._bind_events()
        self._bind_ps_events()

    def _init_gui(self):
        self.surfaces_combo = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        self.surfaces_combo.SetMinClientSize(
            (calc_width_needed(self.surfaces_combo, 25), -1)
        )
        self.overwrite_check = wx.CheckBox(self, -1, "Overwrite surface")
        self.remove_visible_check = wx.CheckBox(self, -1, "Remove visible faces")
        self.apply_button = wx.Button(self, wx.ID_APPLY, "Apply")
        close_button = wx.Button(self, wx.ID_CLOSE, "Close")

        self.fill_surfaces_combo()

        combo_sizer = wx.BoxSizer(wx.HORIZONTAL)
        combo_sizer.Add(
            wx.StaticText(self, -1, "Surface"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT,
            5,
        )
        combo_sizer.Add(self.surfaces_combo, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        button_sizer = wx.StdDialogButtonSizer()
        button_sizer.AddButton(self.apply_button)
        button_sizer.AddButton(close_button)
        button_sizer.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(combo_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.overwrite_check, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.remove_visible_check, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizerAndFit(sizer)

    def _bind_events(self):
        self.Bind(wx.EVT_BUTTON, self.on_apply, id=wx.ID_APPLY)
        self.Bind(wx.EVT_BUTTON, self.on_quit, id=wx.ID_CLOSE)
        self.Bind(wx.EVT_CLOSE, self.on_quit)

    def _bind_ps_events(self):
        Publisher.subscribe(self.on_update_surfaces, "Update surface info in GUI")
        Publisher.subscribe(self.on_update_surfaces, "Remove surfaces")
        Publisher.subscribe(self.on_update_surfaces, "Change surface name")

    def fill_surfaces_combo(self):
        inv_proj = project.Project()
        choices = [i.name for i in inv_proj.surface_dict.values()]
        try:
            initial_value = choices[0]
            enable = True
        except IndexError:
            initial_value = ""
            enable = False

        self.surfaces_combo.SetItems(choices)
        self.surfaces_combo.SetValue(initial_value)
        self.apply_button.Enable(enable)

    def on_quit(self, evt):
        print("closing")
        self.Destroy()

    def on_apply(self, evt):
        inv_proj = project.Project()
        idx = self.surfaces_combo.GetSelection()
        surface = list(inv_proj.surface_dict.values())[idx]
        remove_visible = self.remove_visible_check.GetValue()
        overwrite = self.overwrite_check.GetValue()
        new_polydata = remove_non_visible_faces(
            surface.polydata, remove_visible=remove_visible
        )
        if overwrite:
            name = surface.name
            colour = surface.colour
            index = surface.index
        else:
            name = new_name_by_pattern(f"{surface.name}_removed_nonvisible")
            colour = None
            index = None
        Publisher.sendMessage(
            "Create surface from polydata",
            polydata=new_polydata,
            name=name,
            overwrite=overwrite,
            index=idx,
            colour=colour,
        )
        Publisher.sendMessage('Fold surface task')

    def on_update_surfaces(self, *args, **kwargs):
        last_idx = self.surfaces_combo.GetSelection()
        self.fill_surfaces_combo()
        if last_idx < len(self.surfaces_combo.GetItems()):
            self.surfaces_combo.SetSelection(last_idx)
        else:
            self.surfaces_combo.SetSelection(0)


if __name__ == "__main__":
    app = wx.App()
    window = Window(None)
    window.Show()
    app.MainLoop()
