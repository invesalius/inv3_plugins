#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import numpy as np
import wx
from invesalius.data import imagedata_utils
from pubsub import pub as Publisher

from . import schwarzp

INIT_FROM = "-10"
INIT_TO = "10"
INIT_SIZE = "250"

DISTANCE_TYPES = [
    "Euclidian",
    "Manhattan"
]


def np2bitmap(arr):
    try:
        height, width, bands = arr.shape
        npimg = arr
    except ValueError:
        height, width = arr.shape
        bands = 3
        arr = imagedata_utils.image_normalize(arr, 0, 255)
        npimg = np.zeros((height, width, bands), dtype=np.uint8)
        npimg[:, :, 0] = arr
        npimg[:, :, 1] = arr
        npimg[:, :, 2] = arr

    image = wx.Image(width, height)
    image.SetData(npimg.tostring())
    return image.ConvertToBitmap()


class GUISchwarzP(wx.Dialog):
    def __init__(
        self,
        parent,
        title="Schwarz-P creation",
        style=wx.DEFAULT_DIALOG_STYLE | wx.FRAME_FLOAT_ON_PARENT,
    ):
        wx.Dialog.__init__(self, parent, -1, title=title, style=style)

        self.np_img = None
        self._init_gui()
        self._bind_events()
        self.update_image()

    def _init_gui(self):

        options = [
            "Schwarz P",
            "Schwarz D",
            "Gyroid",
            "Neovius",
            "iWP",
            "P_W_Hybrid",
            "Blobs",
            "Voronoi",
        ]
        self.cb_option = wx.ComboBox(
            self, -1, options[0], choices=options, style=wx.CB_READONLY
        )

        self.schwarp_panel = SchwarzPPanel(self)
        self.blobs_panel = BlobsPanel(self)
        self.voronoi_panel = VoronoiPanel(self)

        self.spacing_panel = SpacingPanel(self)

        self.blobs_panel.Hide()
        self.voronoi_panel.Hide()

        self.image_panel = wx.Panel(self, -1)
        self.image_panel.SetMinSize(self.schwarp_panel.GetSizer().CalcMin())

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

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.cb_option, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.schwarp_panel, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.blobs_panel, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.voronoi_panel, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.spacing_panel, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.image_panel, 2, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.cb_new_inv_instance, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()

    def _bind_events(self):
        self.image_panel.Bind(wx.EVT_PAINT, self.OnPaint)
        #  self.image_panel.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

        self.cb_option.Bind(wx.EVT_COMBOBOX, self.OnSetValues)

        self.button_ok.Bind(wx.EVT_BUTTON, self.OnOk)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.OnCancel)

    def update_image(self):
        if self.cb_option.GetValue() == "Blobs":
            size_x = self.blobs_panel.spin_size_x.GetValue()
            size_y = self.blobs_panel.spin_size_y.GetValue()
            size_z = self.blobs_panel.spin_size_z.GetValue()
            gaussian = self.blobs_panel.spin_gaussian.GetValue()
            self.np_img = np2bitmap(
                schwarzp.create_blobs(size_x, size_y, 1, gaussian)[0]
            )
        elif self.cb_option.GetValue() == "Voronoi":
            if self.voronoi_panel.cb_distribution.GetValue() == "Random":
                size_x = self.voronoi_panel.random_options.spin_size_x.GetValue()
                size_y = self.voronoi_panel.random_options.spin_size_y.GetValue()
                size_z = self.voronoi_panel.random_options.spin_size_z.GetValue()
                number_sites = self.voronoi_panel.random_options.spin_nsites.GetValue()
                #  distance = self.voronoi_panel.cb_distance.GetSelection()
                normalize = self.voronoi_panel.cb_normalize.GetValue()
                borders = self.voronoi_panel.cb_borders.GetValue()
                self.np_img = np2bitmap(
                    schwarzp.create_voronoi(size_x, size_y, 1, number_sites, normalize, borders)[0]
                )
            else:
                size_x = self.voronoi_panel.non_random_options.spin_size_x.GetValue()
                size_y = self.voronoi_panel.non_random_options.spin_size_y.GetValue()
                size_z = self.voronoi_panel.non_random_options.spin_size_z.GetValue()
                nsites_x = self.voronoi_panel.non_random_options.spin_nsites_x .GetValue()
                nsites_y = self.voronoi_panel.non_random_options.spin_nsites_y.GetValue()
                nsites_z = self.voronoi_panel.non_random_options.spin_nsites_z.GetValue()
                #  distance = self.voronoi_panel.cb_distance.GetSelection()
                noise = self.voronoi_panel.non_random_options.cb_noise.GetValue()
                normalize = self.voronoi_panel.cb_normalize.GetValue()
                borders = self.voronoi_panel.cb_borders.GetValue()
                self.np_img = np2bitmap(
                    schwarzp.create_voronoi_non_random(size_x, size_y, 3, nsites_x, nsites_y, 1, normalize, noise, borders)[0]
                )
        else:
            init_x = self.schwarp_panel.spin_from_x.GetValue()
            end_x = self.schwarp_panel.spin_to_x.GetValue()
            size_x = self.schwarp_panel.spin_size_x.GetValue()

            init_y = self.schwarp_panel.spin_from_y.GetValue()
            end_y = self.schwarp_panel.spin_to_y.GetValue()
            size_y = self.schwarp_panel.spin_size_y.GetValue()

            init_z = self.schwarp_panel.spin_from_z.GetValue()
            end_z = self.schwarp_panel.spin_to_z.GetValue()
            size_z = self.schwarp_panel.spin_size_z.GetValue()

            self.np_img = np2bitmap(
                schwarzp.create_schwarzp(
                    self.cb_option.GetValue(),
                    init_x,
                    end_x,
                    init_y,
                    end_y,
                    1.0,
                    1.0,
                    size_x,
                    size_y,
                    1,
                )[0]
            )

    def OnCancel(self, evt):
        self.Destroy()

    def OnOk(self, evt):
        if self.cb_option.GetValue() == "Blobs":
            size_x = self.blobs_panel.spin_size_x.GetValue()
            size_y = self.blobs_panel.spin_size_y.GetValue()
            size_z = self.blobs_panel.spin_size_z.GetValue()
            gaussian = self.blobs_panel.spin_gaussian.GetValue()
            schwarp_f = schwarzp.create_blobs(size_x, size_y, size_z, gaussian)
        elif self.cb_option.GetValue() == "Voronoi":
            if self.voronoi_panel.cb_distribution.GetValue() == "Random":
                size_x = self.voronoi_panel.random_options.spin_size_x.GetValue()
                size_y = self.voronoi_panel.random_options.spin_size_y.GetValue()
                size_z = self.voronoi_panel.random_options.spin_size_z.GetValue()
                number_sites = self.voronoi_panel.random_options.spin_nsites.GetValue()
                #  distance = self.voronoi_panel.cb_distance.GetSelection()
                normalize = self.voronoi_panel.cb_normalize.GetValue()
                borders = self.voronoi_panel.cb_borders.GetValue()
                schwarp_f = schwarzp.create_voronoi(size_x, size_y, size_z, number_sites, normalize, borders)
            else:
                size_x = self.voronoi_panel.non_random_options.spin_size_x.GetValue()
                size_y = self.voronoi_panel.non_random_options.spin_size_y.GetValue()
                size_z = self.voronoi_panel.non_random_options.spin_size_z.GetValue()
                nsites_x = self.voronoi_panel.non_random_options.spin_nsites_x .GetValue()
                nsites_y = self.voronoi_panel.non_random_options.spin_nsites_y.GetValue()
                nsites_z = self.voronoi_panel.non_random_options.spin_nsites_z.GetValue()
                #  distance = self.voronoi_panel.cb_distance.GetSelection()
                noise = self.voronoi_panel.non_random_options.cb_noise.GetValue()
                normalize = self.voronoi_panel.cb_normalize.GetValue()
                borders = self.voronoi_panel.cb_borders.GetValue()
                schwarp_f = schwarzp.create_voronoi_non_random(size_x, size_y, size_z, nsites_x, nsites_y, nsites_z, normalize, noise, borders)
        else:
            init_x = self.schwarp_panel.spin_from_x.GetValue()
            end_x = self.schwarp_panel.spin_to_x.GetValue()
            size_x = self.schwarp_panel.spin_size_x.GetValue()

            init_y = self.schwarp_panel.spin_from_y.GetValue()
            end_y = self.schwarp_panel.spin_to_y.GetValue()
            size_y = self.schwarp_panel.spin_size_y.GetValue()

            init_z = self.schwarp_panel.spin_from_z.GetValue()
            end_z = self.schwarp_panel.spin_to_z.GetValue()
            size_z = self.schwarp_panel.spin_size_z.GetValue()
            schwarp_f = schwarzp.create_schwarzp(
                self.cb_option.GetValue(),
                init_x,
                end_x,
                init_y,
                end_y,
                init_z,
                end_z,
                size_x,
                size_y,
                size_z,
            )
        spacing = self.spacing_panel.get_spacing()
        schwarp_i16 = imagedata_utils.image_normalize(schwarp_f, min_=-1000, max_=1000)
        Publisher.sendMessage(
            "Create project from matrix",
            name="SchwarzP",
            matrix=schwarp_i16,
            spacing=spacing,
            new_instance=self.cb_new_inv_instance.GetValue(),
        )
        self.Close()

    def OnSetValues(self, evt):
        if self.cb_option.GetValue() == "Blobs":
            self.schwarp_panel.Hide()
            self.voronoi_panel.Hide()
            self.blobs_panel.Show()
            self.Layout()
        elif self.cb_option.GetValue() == "Voronoi":
            self.schwarp_panel.Hide()
            self.blobs_panel.Hide()
            self.voronoi_panel.Show()
            self.Layout()
        else:
            self.blobs_panel.Hide()
            self.voronoi_panel.Hide()
            self.schwarp_panel.Show()
            self.Layout()

        self.update_image()
        self.image_panel.Refresh()

    def OnEraseBackground(self, evt):
        pass

    def OnPaint(self, evt):
        dc = wx.PaintDC(self.image_panel)
        dc.SetBackground(wx.Brush("Black"))
        if self.np_img is not None:
            self.render_image(dc)

    def render_image(self, dc):
        psx, psy = self.image_panel.GetSize()
        isx, isy = self.np_img.GetSize()
        cx, cy = psx / 2.0 - isx / 2.0, psy / 2.0 - isy / 2.0
        gc = wx.GraphicsContext.Create(dc)
        gc.DrawBitmap(self.np_img, cx, cy, isx, isy)
        gc.Flush()


class SpacingPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self._init_gui()

    def _init_gui(self):
        self.spin_spc_x = wx.SpinCtrlDouble(self, -1, value="1.0", min=0.001, max=1000.0, inc=0.001)
        self.spin_spc_y = wx.SpinCtrlDouble(self, -1, value="1.0", min=0.001, max=1000.0, inc=0.001)
        self.spin_spc_z = wx.SpinCtrlDouble(self, -1, value="1.0", min=0.001, max=1000.0, inc=0.001)

        sizer_spacing = wx.StaticBoxSizer(
            wx.StaticBox(self, -1, "Spacing"), wx.HORIZONTAL
        )
        sizer_spacing.Add(wx.StaticText(self, -1, "X"), 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_spacing.Add(self.spin_spc_x, 0, wx.ALL, 5)
        sizer_spacing.Add(wx.StaticText(self, -1, "Y"), 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_spacing.Add(self.spin_spc_y, 0, wx.ALL, 5)
        sizer_spacing.Add(wx.StaticText(self, -1, "Z"), 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_spacing.Add(self.spin_spc_z, 0, wx.ALL, 5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(sizer_spacing, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()

    def get_spacing(self):
        spacing_x = self.spin_spc_x.GetValue()
        spacing_y = self.spin_spc_y.GetValue()
        spacing_z = self.spin_spc_z.GetValue()
        return (spacing_x, spacing_y, spacing_z)


class SchwarzPPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self._init_gui()
        self._bind_events()

    def _init_gui(self):
        # Dir X
        lbl_from_x = wx.StaticText(self, -1, "From:", style=wx.ALIGN_RIGHT)
        self.spin_from_x = wx.SpinCtrlDouble(
            self, -1, value=INIT_FROM, min=-1000.0, max=1000.0, inc=0.1
        )
        lbl_to_x = wx.StaticText(self, -1, "To:", style=wx.ALIGN_RIGHT)
        self.spin_to_x = wx.SpinCtrlDouble(
            self, -1, value=INIT_TO, min=-1000.0, max=1000.0, inc=0.1
        )
        lbl_size_x = wx.StaticText(self, -1, "Size:", style=wx.ALIGN_RIGHT)
        self.spin_size_x = wx.SpinCtrl(self, -1, value=INIT_SIZE, min=50, max=1000)

        # Dir Y
        lbl_from_y = wx.StaticText(self, -1, "From:", style=wx.ALIGN_RIGHT)
        self.spin_from_y = wx.SpinCtrlDouble(
            self, -1, value=INIT_FROM, min=-1000.0, max=1000.0, inc=0.1
        )
        lbl_to_y = wx.StaticText(self, -1, "To:", style=wx.ALIGN_RIGHT)
        self.spin_to_y = wx.SpinCtrlDouble(
            self, -1, value=INIT_TO, min=-1000.0, max=1000.0, inc=0.1
        )
        lbl_size_y = wx.StaticText(self, -1, "Size:", style=wx.ALIGN_RIGHT)
        self.spin_size_y = wx.SpinCtrl(self, -1, value=INIT_SIZE, min=50, max=1000)

        # Dir Z
        lbl_from_z = wx.StaticText(self, -1, "From:", style=wx.ALIGN_RIGHT)
        self.spin_from_z = wx.SpinCtrlDouble(
            self, -1, value=INIT_FROM, min=-1000.0, max=1000.0, inc=0.1
        )
        lbl_to_z = wx.StaticText(self, -1, "To:", style=wx.ALIGN_RIGHT)
        self.spin_to_z = wx.SpinCtrlDouble(
            self, -1, value=INIT_TO, min=-1000.0, max=1000.0, inc=0.1
        )
        lbl_size_z = wx.StaticText(self, -1, "Size:", style=wx.ALIGN_RIGHT)
        self.spin_size_z = wx.SpinCtrl(self, -1, value=INIT_SIZE, min=50, max=1000)

        sizer_dirx = wx.StaticBoxSizer(
            wx.StaticBox(self, -1, "Direction X"), wx.VERTICAL
        )
        sizer_dirx.Add(lbl_from_x, 0, wx.LEFT, 5)
        sizer_dirx.Add(self.spin_from_x, 0, wx.ALL, 5)
        sizer_dirx.Add(lbl_to_x, 0, wx.LEFT, 5)
        sizer_dirx.Add(self.spin_to_x, 0, wx.ALL, 5)
        sizer_dirx.Add(lbl_size_x, 0, wx.LEFT, 5)
        sizer_dirx.Add(self.spin_size_x, 0, wx.ALL, 5)

        sizer_diry = wx.StaticBoxSizer(
            wx.StaticBox(self, -1, "Direction Y"), wx.VERTICAL
        )
        sizer_diry.Add(lbl_from_y, 0, wx.LEFT, 5)
        sizer_diry.Add(self.spin_from_y, 0, wx.ALL, 5)
        sizer_diry.Add(lbl_to_y, 0, wx.LEFT, 5)
        sizer_diry.Add(self.spin_to_y, 0, wx.ALL, 5)
        sizer_diry.Add(lbl_size_y, 0, wx.LEFT, 5)
        sizer_diry.Add(self.spin_size_y, 0, wx.ALL, 5)

        sizer_dirz = wx.StaticBoxSizer(
            wx.StaticBox(self, -1, "Direction Z"), wx.VERTICAL
        )
        sizer_dirz.Add(lbl_from_z, 0, wx.LEFT, 5)
        sizer_dirz.Add(self.spin_from_z, 0, wx.ALL, 5)
        sizer_dirz.Add(lbl_to_z, 0, wx.LEFT, 5)
        sizer_dirz.Add(self.spin_to_z, 0, wx.ALL, 5)
        sizer_dirz.Add(lbl_size_z, 0, wx.LEFT, 5)
        sizer_dirz.Add(self.spin_size_z, 0, wx.ALL, 5)

        sizer_dirs = wx.BoxSizer(wx.HORIZONTAL)
        sizer_dirs.Add(sizer_dirx, 0, wx.ALL, 5)
        sizer_dirs.Add(sizer_diry, 0, wx.ALL, 5)
        sizer_dirs.Add(sizer_dirz, 0, wx.ALL, 5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(sizer_dirs, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()

    def _bind_events(self):
        self.spin_from_x.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_to_x.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_size_x.Bind(wx.EVT_SPINCTRL, self.OnSetValues)

        self.spin_from_y.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_to_y.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_size_y.Bind(wx.EVT_SPINCTRL, self.OnSetValues)

        self.spin_from_z.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_to_z.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_size_z.Bind(wx.EVT_SPINCTRL, self.OnSetValues)

    def OnSetValues(self, evt):
        self.Parent.OnSetValues(evt)


class BlobsPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self._init_gui()
        self._bind_events()

    def _init_gui(self):
        # X
        lbl_size_x = wx.StaticText(self, -1, "Size X:", style=wx.ALIGN_RIGHT)
        self.spin_size_x = wx.SpinCtrl(self, -1, value=INIT_SIZE, min=50, max=1000)
        # Y`
        lbl_size_y = wx.StaticText(self, -1, "Size Y:", style=wx.ALIGN_RIGHT)
        self.spin_size_y = wx.SpinCtrl(self, -1, value=INIT_SIZE, min=50, max=1000)
        # Z
        lbl_size_z = wx.StaticText(self, -1, "Size Z:", style=wx.ALIGN_RIGHT)
        self.spin_size_z = wx.SpinCtrl(self, -1, value=INIT_SIZE, min=50, max=1000)

        lbl_gaussian = wx.StaticText(self, -1, "Gaussian:", style=wx.ALIGN_RIGHT)
        self.spin_gaussian = wx.SpinCtrlDouble(
            self, -1, value="5.0", min=0.0, max=10.0, inc=0.1
        )

        main_sizer = wx.FlexGridSizer(rows=4, cols=2, vgap=5, hgap=5)
        main_sizer.AddMany(
            [
                (lbl_size_x, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.spin_size_x,),
                (lbl_size_y, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.spin_size_y,),
                (lbl_size_z, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.spin_size_z,),
                (lbl_gaussian, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.spin_gaussian,),
            ]
        )

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()

    def _bind_events(self):
        self.spin_size_x.Bind(wx.EVT_SPINCTRL, self.OnSetValues)
        self.spin_size_y.Bind(wx.EVT_SPINCTRL, self.OnSetValues)
        self.spin_size_z.Bind(wx.EVT_SPINCTRL, self.OnSetValues)
        self.spin_gaussian.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)

    def OnSetValues(self, evt):
        self.Parent.OnSetValues(evt)


class VoronoiPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self._init_gui()
        self._bind_events()

    def _init_gui(self):
        distributions = ["Random", "Non-random"]
        lbl_distributions = wx.StaticText(self, -1, "Distribution", style=wx.CB_READONLY)
        self.cb_distribution = wx.ComboBox(self, -1, value=distributions[0], choices=distributions)
        self.random_options = VoronoiRandomOptionsPanel(self)
        self.non_random_options = VoronoiNonRandomOptionsPanel(self)
        self.non_random_options.Hide()

        #  lbl_distance = wx.StaticText(self, -1, "Distance", style=wx.ALIGN_RIGHT)
        #  self.cb_distance = wx.ComboBox(
            #  self, -1, DISTANCE_TYPES[0], choices=DISTANCE_TYPES, style=wx.CB_READONLY
        #  )

        self.cb_normalize = wx.CheckBox(
            self, -1, "Normalize"
        )
        self.cb_normalize.SetValue(True)

        self.cb_borders = wx.CheckBox(self, -1, "Just borders")
        self.cb_borders.SetValue(False)

        distribution_sizer = wx.BoxSizer(wx.HORIZONTAL)
        distribution_sizer.Add(lbl_distributions, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        distribution_sizer.Add(self.cb_distribution, 1, wx.EXPAND | wx.ALL, 5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(distribution_sizer, 0, wx.ALL, 5)
        main_sizer.Add(self.random_options, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.non_random_options, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.cb_normalize, 0, wx.ALL, 5)
        main_sizer.Add(self.cb_borders, 0, wx.ALL, 5)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()

    def _bind_events(self):
        #  self.cb_distance.Bind(wx.EVT_COMBOBOX, self.OnSetValues)
        self.cb_distribution.Bind(wx.EVT_COMBOBOX, self.OnSetValues)
        self.cb_normalize.Bind(wx.EVT_CHECKBOX, self.OnSetValues)
        self.cb_borders.Bind(wx.EVT_CHECKBOX, self.OnSetValues)

    def OnSetValues(self, evt):
        if self.cb_distribution.GetValue() == "Random":
            self.random_options.Show()
            self.non_random_options.Hide()
        else:
            self.random_options.Hide()
            self.non_random_options.Show()
        self.Layout()
        self.Parent.OnSetValues(evt)


class VoronoiRandomOptionsPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self._init_gui()
        self._bind_events()

    def _init_gui(self):
        # X
        lbl_size_x = wx.StaticText(self, -1, "Size X:", style=wx.ALIGN_RIGHT)
        self.spin_size_x = wx.SpinCtrl(self, -1, value=INIT_SIZE, min=50, max=1000)
        # Y`
        lbl_size_y = wx.StaticText(self, -1, "Size Y:", style=wx.ALIGN_RIGHT)
        self.spin_size_y = wx.SpinCtrl(self, -1, value=INIT_SIZE, min=50, max=1000)
        # Z
        lbl_size_z = wx.StaticText(self, -1, "Size Z:", style=wx.ALIGN_RIGHT)
        self.spin_size_z = wx.SpinCtrl(self, -1, value=INIT_SIZE, min=50, max=1000)

        lbl_gaussian = wx.StaticText(self, -1, "Number of sites:", style=wx.ALIGN_RIGHT)
        self.spin_nsites = wx.SpinCtrl(self, -1, value="1000", min=5, max=1000000)

        main_sizer = wx.FlexGridSizer(rows=4, cols=2, vgap=5, hgap=5)
        main_sizer.AddMany(
            [
                (lbl_size_x, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.spin_size_x,),
                (lbl_size_y, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.spin_size_y,),
                (lbl_size_z, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.spin_size_z,),
                (lbl_gaussian, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.spin_nsites,),
            ]
        )
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()

    def _bind_events(self):
        self.spin_size_x.Bind(wx.EVT_SPINCTRL, self.OnSetValues)
        self.spin_size_y.Bind(wx.EVT_SPINCTRL, self.OnSetValues)
        self.spin_size_z.Bind(wx.EVT_SPINCTRL, self.OnSetValues)
        self.spin_nsites.Bind(wx.EVT_SPINCTRL, self.OnSetValues)

    def OnSetValues(self, evt):
        self.Parent.OnSetValues(evt)


class VoronoiNonRandomOptionsPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self._init_gui()
        self._bind_events()

    def _init_gui(self):
        # X
        lbl_size_x = wx.StaticText(self, -1, "Size X:", style=wx.ALIGN_RIGHT)
        self.spin_size_x = wx.SpinCtrl(self, -1, value=INIT_SIZE, min=50, max=1000)
        # Y`
        lbl_size_y = wx.StaticText(self, -1, "Size Y:", style=wx.ALIGN_RIGHT)
        self.spin_size_y = wx.SpinCtrl(self, -1, value=INIT_SIZE, min=50, max=1000)
        # Z
        lbl_size_z = wx.StaticText(self, -1, "Size Z:", style=wx.ALIGN_RIGHT)
        self.spin_size_z = wx.SpinCtrl(self, -1, value=INIT_SIZE, min=50, max=1000)

        # X
        lbl_nsite_x = wx.StaticText(self, -1, "Number of sites X:", style=wx.ALIGN_RIGHT)
        self.spin_nsites_x = wx.SpinCtrl(self, -1, value="10", min=5, max=1000)
        # Y`
        lbl_nsite_y = wx.StaticText(self, -1, "Number of sites Y:", style=wx.ALIGN_RIGHT)
        self.spin_nsites_y = wx.SpinCtrl(self, -1, value="10", min=5, max=1000)
        # Z
        lbl_nsite_z = wx.StaticText(self, -1, "Number of sites Z:", style=wx.ALIGN_RIGHT)
        self.spin_nsites_z = wx.SpinCtrl(self, -1, value="10", min=5, max=1000)

        self.cb_noise = wx.CheckBox(
            self, -1, "Add noise"
        )
        self.cb_noise.SetValue(False)

        main_sizer = wx.FlexGridSizer(rows=4, cols=4, vgap=5, hgap=5)
        main_sizer.AddMany(
            [
                (lbl_size_x, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.spin_size_x,),
                (lbl_nsite_x, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.spin_nsites_x,),
                (lbl_size_y, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.spin_size_y,),
                (lbl_nsite_y, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.spin_nsites_y,),
                (lbl_size_z, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.spin_size_z,),
                (lbl_nsite_z, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.spin_nsites_z,),
                (self.cb_noise,),
            ]
        )
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()

    def _bind_events(self):
        self.spin_size_x.Bind(wx.EVT_SPINCTRL, self.OnSetValues)
        self.spin_size_y.Bind(wx.EVT_SPINCTRL, self.OnSetValues)
        self.spin_size_z.Bind(wx.EVT_SPINCTRL, self.OnSetValues)
        self.spin_nsites_x.Bind(wx.EVT_SPINCTRL, self.OnSetValues)
        self.spin_nsites_y.Bind(wx.EVT_SPINCTRL, self.OnSetValues)
        self.spin_nsites_z.Bind(wx.EVT_SPINCTRL, self.OnSetValues)
        self.cb_noise.Bind(wx.EVT_CHECKBOX, self.OnSetValues)

    def OnSetValues(self, evt):
        self.Parent.OnSetValues(evt)


class MyApp(wx.App):
    def OnInit(self):
        self.GUISchwarzP = GUISchwarzP(None, -1, "")
        self.SetTopWindow(self.GUISchwarzP)
        self.GUISchwarzP.Show()
        return True


if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
