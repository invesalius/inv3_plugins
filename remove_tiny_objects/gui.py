import os
import tempfile

import invesalius.data.slice_ as slc
import numpy as np
import scipy.ndimage as nd
import wx
from invesalius import project
from pubsub import pub as Publisher

from . import count

INIT_MIN_SIZE = "10"


class Window(wx.Dialog):
    def __init__(
        self,
        parent,
        image_matrix,
        title="Remove tiny objects",
        style=wx.DEFAULT_DIALOG_STYLE | wx.FRAME_FLOAT_ON_PARENT,
    ):
        super().__init__(parent, -1, title=title, style=style)

        self.mask = None
        self.preview_matrix = None

        self._init_gui()
        self._bind_events()

        self._find_regions_actual_mask()
        if self.mask:
            self.mask.add_modified_callback(self.on_modified_mask)

    def _find_regions(self, matrix):
        labels, num_labels = nd.label(matrix)
        return labels, num_labels

    def _find_regions_actual_mask(self):
        s = slc.Slice()
        self.mask = s.current_mask
        if self.mask:
            s.do_threshold_to_all_slices()
            labels, num_labels = self._find_regions(self.mask.matrix[1:, 1:, 1:])
            counts = count.count_regions(labels, num_labels)
            self.txt_num_regions.SetValue(str(num_labels))

            if self.preview_matrix is None:
                _tmp, self.preview_matrix = self.create_temp_mask()

            self.counts = counts
            self.num_labels = num_labels
            s.aux_matrices["REMOVE_TINY"] = self.preview_matrix
            s.to_show_aux = "REMOVE_TINY"

            self._update_preview_matrix()

    def _update_preview_matrix(self):
        min_size = self.txt_min_size.GetValue()
        self.preview_matrix[:] = (self.counts <= min_size) * 255
        Publisher.sendMessage("Reload actual slice")

    def _init_gui(self):
        self.txt_min_size = wx.SpinCtrl(
            self, -1, value=INIT_MIN_SIZE, min=1, max=10 ** 10
        )

        self.txt_num_regions = wx.TextCtrl(self, -1, "0")

        self.btn_remove = wx.Button(self, -1, "Remove")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(
            wx.StaticText(self, -1, "Maximum size to remove"), 0, wx.EXPAND | wx.ALL, 5
        )
        sizer.Add(self.txt_min_size, 1, wx.EXPAND | wx.ALL, 5)

        sizer.Add(
            wx.StaticText(self, -1, "Number of regions"), 0, wx.EXPAND | wx.ALL, 5
        )
        sizer.Add(self.txt_num_regions, 1, wx.EXPAND | wx.ALL, 5)

        sizer.Add(self.btn_remove, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

    def _bind_events(self):
        self.txt_min_size.Bind(wx.EVT_SPINCTRL, self.OnSetMinSize)
        self.btn_remove.Bind(wx.EVT_BUTTON, self.OnRemove)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def create_temp_mask(self):
        temp_file = tempfile.mktemp()
        sz, sy, sx = self.mask.matrix.shape
        matrix = np.memmap(
            temp_file, mode="w+", dtype="uint8", shape=(sz - 1, sy - 1, sx - 1)
        )
        return temp_file, matrix

    def OnSetMinSize(self, evt):
        self._update_preview_matrix()

    def on_modified_mask(self):
        print("On modified mask")
        self._find_regions_actual_mask()
        self._update_preview_matrix()

    def OnClose(self, evt):
        if self.mask:
            removed = self.mask.remove_modified_callback(self.on_modified_mask)
            print(f"It was removed? {removed}")

            s = slc.Slice()
            if self.preview_matrix is not None:
                filename = self.preview_matrix.filename
                del self.preview_matrix
                os.remove(filename)

            try:
                del s.aux_matrices["REMOVE_TINY"]
            except KeyError:
                pass

            if s.to_show_aux == "REMOVE_TINY":
                s.to_show_aux = ""

            Publisher.sendMessage("Reload actual slice")

        evt.Skip()

    def OnRemove(self, evt):
        if self.mask and self.preview_matrix is not None:
            s = slc.Slice()
            s.discard_all_buffers()
            cp_mask = self.mask.matrix.copy()
            m = self.mask.matrix[1:, 1:, 1:]
            m[self.preview_matrix > 127] = 1
            self.mask.was_edited = True
            self.preview_matrix[:] = 0
            self.mask.save_history(0, 'VOLUME', self.mask.matrix.copy(), cp_mask)
            Publisher.sendMessage("Reload actual slice")
