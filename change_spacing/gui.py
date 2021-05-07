import wx
from pubsub import pub as Publisher


class GUIIsotropic(wx.Dialog):
    def __init__(
        self,
        parent,
        title="Change spacing",
        style=wx.DEFAULT_DIALOG_STYLE | wx.FRAME_FLOAT_ON_PARENT | wx.STAY_ON_TOP,
    ):
        wx.Dialog.__init__(self, parent, -1, title=title, style=style)

        self.spacing_original_x = 1.0
        self.spacing_original_y = 1.0
        self.spacing_original_z = 1.0

        self.spacing_new_x = 1.0
        self.spacing_new_y = 1.0
        self.spacing_new_z = 1.0

        self._init_gui()

        self.set_original_spacing(
            self.spacing_original_x, self.spacing_original_y, self.spacing_original_z
        )

        self.set_new_spacing(self.spacing_new_x, self.spacing_new_y, self.spacing_new_z)

        self._bind_events()

    def set_original_spacing(self, sx, sy, sz):
        self.spacing_original_x = sx
        self.spacing_original_y = sy
        self.spacing_original_z = sz

        self.txt_spacing_original_x.ChangeValue(str(sx))
        self.txt_spacing_original_y.ChangeValue(str(sy))
        self.txt_spacing_original_z.ChangeValue(str(sz))

    def set_new_spacing(self, sx, sy, sz):
        self.spacing_new_x = sx
        self.spacing_new_y = sy
        self.spacing_new_z = sz

        self.txt_spacing_new_x.ChangeValue(str(sx))
        self.txt_spacing_new_y.ChangeValue(str(sy))
        self.txt_spacing_new_z.ChangeValue(str(sz))

    def _init_gui(self):
        self.txt_spacing_original_x = wx.TextCtrl(self, -1, style=wx.TE_READONLY)
        self.txt_spacing_original_y = wx.TextCtrl(self, -1, style=wx.TE_READONLY)
        self.txt_spacing_original_z = wx.TextCtrl(self, -1, style=wx.TE_READONLY)

        self.txt_spacing_new_x = wx.TextCtrl(self, -1)
        self.txt_spacing_new_y = wx.TextCtrl(self, -1)
        self.txt_spacing_new_z = wx.TextCtrl(self, -1)

        self.check_isotropic = wx.CheckBox(self, -1, "Isotropic")
        self.check_isotropic.SetValue(True)

        self.cb_new_inv_instance = wx.CheckBox(
            self, -1, "Launch new InVesalius instance"
        )
        self.cb_new_inv_instance.SetValue(True)

        self.button_ok = wx.Button(self, wx.ID_OK)
        self.button_cancel = wx.Button(self, wx.ID_CANCEL)

        button_sizer = wx.StdDialogButtonSizer()
        button_sizer.AddButton(self.button_ok)
        button_sizer.AddButton(self.button_cancel)
        button_sizer.Realize()

        sizer_original = wx.FlexGridSizer(3, 2, 5, 5)
        sizer_original.AddMany(
            (
                (wx.StaticText(self, -1, "X"), 0, wx.ALIGN_CENTER_VERTICAL),
                (self.txt_spacing_original_x, 0, wx.EXPAND),
                (wx.StaticText(self, -1, "Y"), 0, wx.ALIGN_CENTER_VERTICAL),
                (self.txt_spacing_original_y, 0, wx.EXPAND),
                (wx.StaticText(self, -1, "Z"), 0, wx.ALIGN_CENTER_VERTICAL),
                (self.txt_spacing_original_z, 0, wx.EXPAND),
            )
        )

        original_sbox = wx.StaticBoxSizer(wx.HORIZONTAL, self, "Original spacing")
        original_sbox.Add(sizer_original, 0, wx.EXPAND | wx.ALL, 5)

        sizer_new = wx.FlexGridSizer(3, 2, 5, 5)
        sizer_new.AddMany(
            (
                (wx.StaticText(self, -1, "X"), 0, wx.ALIGN_CENTER_VERTICAL),
                (self.txt_spacing_new_x, 0, wx.EXPAND),
                (wx.StaticText(self, -1, "Y"), 0, wx.ALIGN_CENTER_VERTICAL),
                (self.txt_spacing_new_y, 0, wx.EXPAND),
                (wx.StaticText(self, -1, "Z"), 0, wx.ALIGN_CENTER_VERTICAL),
                (self.txt_spacing_new_z, 0, wx.EXPAND),
            )
        )
        new_sbox = wx.StaticBoxSizer(wx.HORIZONTAL, self, "New spacing")
        new_sbox.Add(sizer_new, 0, wx.EXPAND | wx.ALL, 5)

        content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        content_sizer.Add(original_sbox, 1, wx.EXPAND | wx.ALL, 5)
        content_sizer.Add(new_sbox, 1, wx.EXPAND | wx.ALL, 5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(content_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        main_sizer.Add(self.check_isotropic, 0, wx.RIGHT | wx.ALIGN_RIGHT, 7)
        main_sizer.Add(self.cb_new_inv_instance, 0, wx.RIGHT | wx.ALIGN_RIGHT, 7)
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()

    def _bind_events(self):
        self.txt_spacing_new_x.Bind(wx.EVT_KILL_FOCUS, self.OnSetNewSpacing)
        self.txt_spacing_new_y.Bind(wx.EVT_KILL_FOCUS, self.OnSetNewSpacing)
        self.txt_spacing_new_z.Bind(wx.EVT_KILL_FOCUS, self.OnSetNewSpacing)

        self.button_ok.Bind(wx.EVT_BUTTON, self.OnOk)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.OnCancel)

    def OnSetNewSpacing(self, evt):
        if self.check_isotropic.GetValue():
            try:
                new_spacing_value = float(evt.GetEventObject().GetValue())
            except ValueError:
                self.set_new_spacing(
                    self.spacing_new_x, self.spacing_new_y, self.spacing_new_z
                )
                return

            self.set_new_spacing(
                new_spacing_value, new_spacing_value, new_spacing_value
            )
        else:
            try:
                new_spacing_x = float(self.txt_spacing_new_x.GetValue())
            except ValueError:
                new_spacing_x = self.spacing_new_x

            try:
                new_spacing_y = float(self.txt_spacing_new_y.GetValue())
            except ValueError:
                new_spacing_y = self.spacing_new_y

            try:
                new_spacing_z = float(self.txt_spacing_new_z.GetValue())
            except ValueError:
                new_spacing_z = self.spacing_new_z

            self.set_new_spacing(new_spacing_x, new_spacing_y, new_spacing_z)

    def OnOk(self, evt):
        self.EndModal(wx.ID_OK)

    def OnCancel(self, evt):
        self.EndModal(wx.ID_CANCEL)
