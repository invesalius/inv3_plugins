import os
import wx
from pubsub import pub as Publisher
import numpy as np
import invesalius.constants as const
import invesalius.data.imagedata_utils as img_utils
from invesalius.data.markers.marker import MarkerType
import invesalius.data.slice_ as sl
import invesalius.gui.dialogs as dlgs


class Window(wx.Dialog):
    def __init__(self, parent):
        super().__init__(
            parent,
            title="Import eeg coordinates",
            style=wx.DEFAULT_DIALOG_STYLE | wx.FRAME_FLOAT_ON_PARENT,
        )

        self._init_gui()

    def _init_gui(self):
        self.position_list = []
        self.label_list = []
        wildcard: str = "(*.csv)|*.csv"
        # Default system path
        current_dir = os.path.abspath(".")

        dlg_message = "Import Csv EEG"
        dlg_style = wx.FD_OPEN | wx.FD_CHANGE_DIR

        if sl.Slice().has_affine():
            dlg = dlgs.FileSelectionDialog(
                title=dlg_message, wildcard=wildcard, default_dir=current_dir
            )
            conversion_radio_box = wx.RadioBox(
                dlg,
                -1,
                _("File csv eeg"),
                choices=const.SURFACE_SPACE_CHOICES,
                style=wx.RA_SPECIFY_ROWS,
            )
            dlg.sizer.Add(conversion_radio_box, 0, wx.LEFT)
            dlg.FitSizers()
        else:
            dlg = wx.FileDialog(
                None,
                message=dlg_message,
                wildcard=wildcard,
                default_dir=current_dir,
                style=dlg_style,
            )
            # stl filter is default
            dlg.SetFilterIndex(0)
            conversion_radio_box = None

        # Show the dialog and retrieve the user response. If it is the OK response,
        # process the data.
        filename = None
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                if conversion_radio_box is not None:
                    data = np.genfromtxt(fname=filename, delimiter=',', encoding=None, dtype=None, skip_header=0)
                    for i in data:
                        position_world = [i[1], i[2], i[3]]
                        convert_to_inv = conversion_radio_box.GetSelection() == const.SURFACE_SPACE_WORLD
                        if convert_to_inv:
                            affine = sl.Slice().affine.copy()
                            affine = np.linalg.inv(affine)
                            position = img_utils.convert_world_to_voxel(position_world, affine)[0].tolist()
                            position_voxel = img_utils.convert_invesalius_to_voxel(position).tolist()
                        else:
                            position_voxel = position_world
                            position_voxel[2] = -position_world[2]

                        Publisher.sendMessage(
                            "Create marker",
                            marker_type=MarkerType.LANDMARK,
                            position=position_voxel,
                            label=i[4],
                        )
        except:
            wx.MessageBox("Invalid EEG coordinates file. \nFile should be structured as ´´electrode,x,y,z,label´´", "InVesalius 3")
            self._init_gui()

        dlg.Destroy()
        self.Destroy()


if __name__ == "__main__":
    app = wx.App()
    window = Window(None)
    window.Show()
    app.MainLoop()
