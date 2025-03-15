import wx
from invesalius import project
from pubsub import pub as Publisher

MIN_SLIDER = 0
MAX_SLIDER = 100

class Window(wx.Dialog):
    def __init__(self, parent):
        super().__init__(
            parent,
            title="Change surface lighting properties",
            style=wx.DEFAULT_DIALOG_STYLE | wx.FRAME_FLOAT_ON_PARENT,
        )
        self.current_actor = None
        
        self._init_gui()
        self._bind_ps_events()
        if self.surface_combo.GetCount() > 0:
            Publisher.sendMessage("Get Actor", surface_index=self.surface_combo.GetSelection())

    def _init_gui(self):
        surface_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Surface"), wx.VERTICAL)
        self.surface_combo = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        self.surface_combo.Bind(wx.EVT_COMBOBOX, self.OnSelectSurface)

        self.fill_surfaces_combo()

        if self.surface_combo.GetCount() > 0:
            self.surface_combo.SetSelection(0)

        surface_sizer.Add(self.surface_combo, 1, wx.EXPAND | wx.ALL, 5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(surface_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        lighting_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Lighting Properties"), wx.VERTICAL)

        self.ambient_slider = wx.Slider(self, value=50, minValue=MIN_SLIDER, maxValue=MAX_SLIDER, style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.diffuse_slider = wx.Slider(self, value=50, minValue=MIN_SLIDER, maxValue=MAX_SLIDER, style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.specular_slider = wx.Slider(self, value=50, minValue=MIN_SLIDER, maxValue=MAX_SLIDER, style=wx.SL_HORIZONTAL | wx.SL_LABELS)

        self.ambient_slider.Bind(wx.EVT_SLIDER, self.OnAmbient)
        self.diffuse_slider.Bind(wx.EVT_SLIDER, self.OnDiffuse)
        self.specular_slider.Bind(wx.EVT_SLIDER, self.OnSpecular)

        lighting_sizer.Add(wx.StaticText(self, -1, "Ambient:"), 0, wx.ALL, 5)
        lighting_sizer.Add(self.ambient_slider, 0, wx.EXPAND | wx.ALL, 5)
        lighting_sizer.Add(wx.StaticText(self, -1, "Diffuse:"), 0, wx.ALL, 5)
        lighting_sizer.Add(self.diffuse_slider, 0, wx.EXPAND | wx.ALL, 5)
        lighting_sizer.Add(wx.StaticText(self, -1, "Specular:"), 0, wx.ALL, 5)
        lighting_sizer.Add(self.specular_slider, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(lighting_sizer, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(main_sizer)
        self.SetMinSize((300, 400))
        self.SetSize((300, 400))
        self.Layout()

    def _bind_ps_events(self):
        Publisher.subscribe(self.on_update_surfaces, "Update surface info in GUI")
        Publisher.subscribe(self.on_update_surfaces, "Remove surfaces")
        Publisher.subscribe(self.on_update_surfaces, "Change surface name")
        Publisher.subscribe(self.SetActor, "Send Actor")
    
    def SetActor(self, e_field_actor):
        self.current_actor = e_field_actor
        self.ambient_slider.SetValue(int(e_field_actor.GetProperty().GetAmbient() * 100))
        self.diffuse_slider.SetValue(int(e_field_actor.GetProperty().GetDiffuse() * 100))
        self.specular_slider.SetValue(int(e_field_actor.GetProperty().GetSpecular() * 100))

    def on_update_surfaces(self, *args, **_kwargs):
        last_idx = self.surface_combo.GetSelection()
        self.fill_surfaces_combo()
        if last_idx < len(self.surfaces_combo.GetItems()):
            self.surface_combo.SetSelection(last_idx)
            Publisher.sendMessage("Get Actor", surface_index=last_idx)
        else:
            self.surface_combo.SetSelection(0)
            Publisher.sendMessage("Get Actor", surface_index=0)
        

    def fill_surfaces_combo(self):
        inv_proj = project.Project()
        choices = [i.name for i in inv_proj.surface_dict.values()]
        try:
            initial_value = choices[0]
        except IndexError:
            initial_value = ""
        self.surface_combo.SetItems(choices)
        self.surface_combo.SetValue(initial_value)

    def OnSelectSurface(self, _event):
        surface_index = self.surface_combo.GetSelection()
        Publisher.sendMessage("Get Actor", surface_index=surface_index)



    def OnAmbient(self, _event):
        value = self.ambient_slider.GetValue() / 100
        Publisher.sendMessage("Set Ambient", value=value, actor=self.current_actor)

    def OnDiffuse(self, _event):
        value = self.diffuse_slider.GetValue() / 100
        Publisher.sendMessage("Set Diffuse", value=value, actor=self.current_actor)

    def OnSpecular(self, _event):
        value = self.specular_slider.GetValue() / 100
        Publisher.sendMessage("Set Specular", value=value, actor=self.current_actor)

if __name__ == "__main__":
    app = wx.App()
    window = Window(None)
    window.Show()
    app.MainLoop()