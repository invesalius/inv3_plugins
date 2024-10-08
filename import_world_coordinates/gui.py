import wx
from pubsub import pub as Publisher
import numpy as np

import invesalius.data.coordinates as dco
import invesalius.data.imagedata_utils as img_utils
from invesalius.data.markers.marker import MarkerType
import invesalius.data.slice_ as sl


class Window(wx.Dialog):
    def __init__(
        self,
        parent,
        title="Import World Coordinates into InVesalius",
        style=wx.DEFAULT_DIALOG_STYLE | wx.FRAME_FLOAT_ON_PARENT | wx.STAY_ON_TOP,
    ):
        wx.Dialog.__init__(self, parent, -1, title=title, style=style)

        self.x = -48.48
        self.y = -28.06
        self.z = 60.10
        self.rx = -2.44
        self.ry = -0.14
        self.rz = -1.48

        self.arx = 0
        self.ary = 180
        self.arz = 0

        self._init_gui()

        self.set_original_coordinates(
            self.x, self.y, self.z, self.rx, self.ry, self.rz, self.arx, self.ary, self.arz
        )

        self._bind_events()

    def set_original_coordinates(self, sx, sy, sz, srx, sry, srz, arx, ary, arz):
        self.x = sx
        self.y = sy
        self.z = sz
        self.rx = srx
        self.ry = sry
        self.rz = srz

        self.apply_rx = arx
        self.apply_ry = ary
        self.apply_rz = arz

        self.txt_x.ChangeValue(str(sx))
        self.txt_y.ChangeValue(str(sy))
        self.txt_z.ChangeValue(str(sz))
        self.txt_rx.ChangeValue(str(srx))
        self.txt_ry.ChangeValue(str(sry))
        self.txt_rz.ChangeValue(str(srz))

        self.txt_apply_rx.ChangeValue(str(arx))
        self.txt_apply_ry.ChangeValue(str(ary))
        self.txt_apply_rz.ChangeValue(str(arz))

    def _init_gui(self):
        self.txt_x = wx.TextCtrl(self, -1)
        self.txt_y = wx.TextCtrl(self, -1)
        self.txt_z = wx.TextCtrl(self, -1)
        self.txt_rx = wx.TextCtrl(self, -1)
        self.txt_ry = wx.TextCtrl(self, -1)
        self.txt_rz = wx.TextCtrl(self, -1)

        self.txt_apply_rx = wx.TextCtrl(self, -1)
        self.txt_apply_ry = wx.TextCtrl(self, -1)
        self.txt_apply_rz = wx.TextCtrl(self, -1)

        self.check_rotation = wx.CheckBox(self, -1, "Rotation")
        self.check_rotation.SetValue(True)

        self.button_create_marker = wx.Button(self, wx.ID_OK, label="Create Marker")
        self.button_close = wx.Button(self, wx.ID_CLOSE)

        button_sizer = wx.StdDialogButtonSizer()
        button_sizer.AddButton(self.button_create_marker)
        button_sizer.AddButton(self.button_close)
        button_sizer.Realize()

        sizer_original = wx.FlexGridSizer(3, 2, 5, 5)
        sizer_original.AddMany(
            (
                (wx.StaticText(self, -1, "X"), 0, wx.ALIGN_CENTER_VERTICAL),
                (self.txt_x, 0, wx.EXPAND),
                (wx.StaticText(self, -1, "Y"), 0, wx.ALIGN_CENTER_VERTICAL),
                (self.txt_y, 0, wx.EXPAND),
                (wx.StaticText(self, -1, "Z"), 0, wx.ALIGN_CENTER_VERTICAL),
                (self.txt_z, 0, wx.EXPAND),
            )
        )

        original_sbox = wx.StaticBoxSizer(wx.HORIZONTAL, self, "Translation")
        original_sbox.Add(sizer_original, 0, wx.EXPAND | wx.ALL, 5)

        sizer_new = wx.FlexGridSizer(3, 2, 5, 5)
        sizer_new.AddMany(
            (
                (wx.StaticText(self, -1, "RX"), 0, wx.ALIGN_CENTER_VERTICAL),
                (self.txt_rx, 0, wx.ALIGN_CENTER_VERTICAL),
                (wx.StaticText(self, -1, "RY"), 0, wx.ALIGN_CENTER_VERTICAL),
                (self.txt_ry, 0, wx.ALIGN_CENTER_VERTICAL),
                (wx.StaticText(self, -1, "RZ"), 0, wx.ALIGN_CENTER_VERTICAL),
                (self.txt_rz, 0, wx.ALIGN_CENTER_VERTICAL),
            )
        )
        new_sbox = wx.StaticBoxSizer(wx.HORIZONTAL, self, "Orientation (rad)")
        new_sbox.Add(sizer_new, 0, wx.EXPAND | wx.ALL, 5)

        content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        content_sizer.Add(original_sbox, 1, wx.EXPAND | wx.ALL, 5)
        content_sizer.Add(new_sbox, 1, wx.EXPAND | wx.ALL, 5)

        sizer_apply = wx.FlexGridSizer(2, 3, 5, 5)
        sizer_apply.AddMany(
            (
                (wx.StaticText(self, -1, "RX"), 0, wx.ALIGN_CENTER_VERTICAL),
                (wx.StaticText(self, -1, "RY"), 0, wx.ALIGN_CENTER_VERTICAL),
                (wx.StaticText(self, -1, "RZ"), 0, wx.ALIGN_CENTER_VERTICAL),
                (self.txt_apply_rx, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.txt_apply_ry, 0, wx.ALIGN_CENTER_VERTICAL),
                (self.txt_apply_rz, 0, wx.ALIGN_CENTER_VERTICAL),
            )
        )
        new_abox = wx.StaticBoxSizer(wx.HORIZONTAL, self, "Apply rotation (degree)")
        new_abox.Add(sizer_apply, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(content_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        main_sizer.Add(self.check_rotation, 0, wx.LEFT | wx.ALIGN_LEFT, 7)
        main_sizer.Add(new_abox, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 7)
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()

    def _bind_events(self):
        self.button_create_marker.Bind(wx.EVT_BUTTON, self.OnCreateMarker)
        self.button_close.Bind(wx.EVT_BUTTON, self.OnClose)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.check_rotation.Bind(wx.EVT_CHECKBOX, self.OnEnableRotation)

    def OnCreateMarker(self, evt):
        try:
            x = float(self.txt_x.GetValue())
        except ValueError:
            x = self.x

        try:
            y = float(self.txt_y.GetValue())
        except ValueError:
            y = self.y

        try:
            z = float(self.txt_z.GetValue())
        except ValueError:
            z = self.z

        try:
            rx = float(self.txt_rx.GetValue())
        except ValueError:
            rx = self.rx

        try:
            ry = float(self.txt_ry.GetValue())
        except ValueError:
            ry = self.ry

        try:
            rz = float(self.txt_rz.GetValue())
        except ValueError:
            rz = self.rz

        m_coord = dco.coordinates_to_transformation_matrix(
            position=[x, y, z],
            orientation=[np.rad2deg(rx), np.rad2deg(ry), np.rad2deg(rz)],
            axes="sxyz",
        )
        affine = sl.Slice().affine.copy()
        m_coord_transformed = affine @ m_coord
        position, orientation = dco.transformation_matrix_to_coordinates(
            m_coord_transformed,
            axes="sxyz",
        )

        if self.check_rotation.GetValue():
            try:
                arx = float(self.txt_apply_rx.GetValue())
            except ValueError:
                arx = self.apply_rx
            try:
                ary = float(self.txt_apply_ry.GetValue())
            except ValueError:
                ary = self.apply_ry
            try:
                arz = float(self.txt_apply_rz.GetValue())
            except ValueError:
                arz = self.apply_rz
            m_displacement = dco.coordinates_to_transformation_matrix(
                position=[0, 0, 0],
                orientation=[arx, ary, arz],
                axes="sxyz",
            )
            position, orientation = dco.transformation_matrix_to_coordinates(
                m_coord_transformed @ m_displacement,
                axes="sxyz",
            )

        position_voxel = img_utils.convert_invesalius_to_voxel(position)
        Publisher.sendMessage(
            "Create marker",
            marker_type=MarkerType.COIL_TARGET,
            position=position_voxel.tolist(),
            orientation=orientation.tolist(),
        )

    def OnEnableRotation(self, evt):
        if evt.IsChecked():
            self.txt_apply_rx.Enable()
            self.txt_apply_ry.Enable()
            self.txt_apply_rz.Enable()
        else:
            self.txt_apply_rx.Disable()
            self.txt_apply_ry.Disable()
            self.txt_apply_rz.Disable()

    def OnClose(self, evt):
        self.Destroy()
