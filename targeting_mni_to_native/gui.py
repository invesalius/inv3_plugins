import os
import wx
import numpy as np
import ants
import shutil
import threading
from pubsub import pub as Publisher

import invesalius.constants as const
import invesalius.data.slice_ as slc
import invesalius.data.imagedata_utils as img_utils


class MNItoNativeDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="MNI to Native Coordinate", size=(300, 420))
        self.subject_path = None
        self.mni_path = None
        self.warp_file = None
        self.affine_file = None
        self._init_gui()

    def _init_gui(self):
        panel = wx.Panel(self)
        self.panel = panel
        vbox = wx.BoxSizer(wx.VERTICAL)

        instruct_lbl = wx.StaticText(panel, label="Select a brain region or enter coordinates manually:")
        vbox.Add(instruct_lbl, 0, wx.ALL, 10)

        # --- Coordinate Selection ---
        self.mni_coordinates = {
            # Prefrontal Cortex
            "DLPFC (Left)": [-38, 44, 26],
            "DLPFC (Right)": [38, 44, 26],
            "vmPFC": [0, 45, -15],
            "OFC (Left)": [-24, 42, -14],
            "OFC (Right)": [24, 42, -14],
            "ACC": [0, 38, 20],

            # Motor & Premotor Cortex
            "PMd (Left)": [-26, 2, 60],
            "PMd (Right)": [26, 2, 60],
            "M1 Hand (Left)": [-38, -22, 56],
            "M1 Hand (Right)": [38, -22, 56],
            "SMA": [0, -4, 54],

            # Parietal Cortex
            "PPC (Left)": [-40, -46, 48],
            "IPL (Left)": [-48, -40, 44],
            "Precuneus": [0, -60, 36],
            "PCC": [0, -52, 26],

            # Temporal Cortex
            "MTG (Left)": [-60, -40, -5],
            "STG (Left)": [-50, -20, 10],
            "TPJ (Left)": [-54, -54, 22],

            # Occipital Cortex
            "V1 (Primary Visual)": [0, -90, 0],
            "Lateral Occipital (Left)": [-40, -76, 6],

            # Cingulate & Insula
            "dACC": [0, 24, 36],
            "Anterior Insula (Left)": [-32, 22, 2],

            # Custom
            "Custom/Manual Entry": None
        }
        choices = [
            "--- Prefrontal Cortex ---",
            "DLPFC (Left)",
            "DLPFC (Right)",
            "vmPFC",
            "OFC (Left)",
            "OFC (Right)",
            "ACC",
            "--- Motor & Premotor Cortex ---",
            "PMd (Left)",
            "PMd (Right)",
            "M1 Hand (Left)",
            "M1 Hand (Right)",
            "SMA",
            "--- Parietal Cortex ---",
            "PPC (Left)",
            "IPL (Left)",
            "Precuneus",
            "PCC",
            "--- Temporal Cortex ---",
            "MTG (Left)",
            "STG (Left)",
            "TPJ (Left)",
            "--- Occipital Cortex ---",
            "V1 (Primary Visual)",
            "Lateral Occipital (Left)",
            "--- Cingulate & Insula ---",
            "dACC",
            "Anterior Insula (Left)",
            "---",
            "Custom/Manual Entry"
        ]

        self.combo = wx.ComboBox(panel, choices=choices, style=wx.CB_READONLY)
        self.combo.SetValue("Custom/Manual Entry")
        self.combo.Bind(wx.EVT_COMBOBOX, self._on_region_select)
        self.last_valid_selection = "Custom/Manual Entry"
        vbox.Add(self.combo, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        self.input_x, self.input_y, self.input_z = [wx.TextCtrl(panel, value="0", style=wx.TE_RIGHT) for _ in range(3)]

        grid = wx.FlexGridSizer(3, 2, 10, 10)
        for label, ctrl in zip(["MNI X (RAS):", "MNI Y (RAS):", "MNI Z (RAS):"],
                               [self.input_x, self.input_y, self.input_z]):
            grid.Add(wx.StaticText(panel, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
            grid.Add(ctrl, 0, wx.EXPAND)
        grid.AddGrowableCol(1, 1)
        vbox.Add(grid, 0, wx.ALL | wx.EXPAND, 10)

        # --- MRI/MNI Selection Boxes ---
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        mni_box = wx.BoxSizer(wx.VERTICAL)
        mni_btn = wx.Button(panel, label="Select MNI Template")
        mni_btn.Bind(wx.EVT_BUTTON, self._on_select_mni)
        mni_btn.SetToolTip("Choose the standard MNI template")
        self.mni_status = wx.StaticText(panel, label="❌ MNI not selected")
        mni_box.Add(mni_btn, 0, wx.EXPAND)
        mni_box.Add(self.mni_status, 0, wx.TOP, 5)

        subj_box = wx.BoxSizer(wx.VERTICAL)
        subj_btn = wx.Button(panel, label="Select Subject MRI")
        subj_btn.Bind(wx.EVT_BUTTON, self._on_select_subject)
        subj_btn.SetToolTip("Choose the subject's native MRI scan")
        self.subj_status = wx.StaticText(panel, label="❌ Subject MRI not selected")
        subj_box.Add(subj_btn, 0, wx.EXPAND)
        subj_box.Add(self.subj_status, 0, wx.TOP, 5)

        hbox.Add(mni_box, 1, wx.ALL, 5)
        hbox.Add(subj_box, 1, wx.ALL, 5)
        vbox.Add(hbox, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # --- Transform Info ---
        self.trans_status = wx.StaticText(panel, label="❌ Transform files not found")
        vbox.Add(self.trans_status, 0, wx.LEFT | wx.TOP, 15)

        tf_btn_box = wx.BoxSizer(wx.HORIZONTAL)
        load_btn = wx.Button(panel, label="Load Transform")
        load_btn.Bind(wx.EVT_BUTTON, self._on_load_transform)
        load_btn.SetToolTip(
            "(Optional) Load existing warp and affine transform files if you already have them. "
            "If not, load the MNI template and subject MRI, select a brain region, and click 'Transform and Go'."
        )
        tf_btn_box.Add(load_btn, 1, wx.RIGHT, 5)

        self.save_btn = wx.Button(panel, label="Save Transform")
        self.save_btn.Bind(wx.EVT_BUTTON, self._on_save_transform)
        self.save_btn.Disable()
        tf_btn_box.Add(self.save_btn, 1)

        vbox.Add(tf_btn_box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # --- Status & Progress ---
        self.status = wx.StaticText(panel, label="Load the MNI and MRI first...")
        vbox.Add(self.status, 0, wx.LEFT | wx.TOP, 15)

        hbar = wx.BoxSizer(wx.HORIZONTAL)
        self.gauge = wx.Gauge(panel, range=100, size=(200, 15))
        hbar.AddStretchSpacer()
        hbar.Add(self.gauge, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        hbar.AddStretchSpacer()
        vbox.Add(hbar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # --- Transform Button + Marker Checkbox in Horizontal Box ---
        btn_box = wx.BoxSizer(wx.HORIZONTAL)

        self.go_btn = wx.Button(panel, label="Transform and Go")
        self.go_btn.Bind(wx.EVT_BUTTON, self._start_transform_thread)
        self.go_btn.Disable()  # Initially disabled

        self.create_marker_cb = wx.CheckBox(panel, label="Create coil target")
        self.create_marker_cb.SetValue(True)

        btn_box.Add(self.create_marker_cb, 0, wx.ALIGN_CENTER_VERTICAL)
        btn_box.Add(self.go_btn, 0, wx.RIGHT, 10)

        vbox.Add(btn_box, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        panel.SetSizer(vbox)
        self.Layout()
        self.Centre()
        self._update_file_status()

    def _on_region_select(self, event):
        region = self.combo.GetValue()
        if region.startswith("---"):  # Don't allow selecting headers
            wx.CallAfter(self.combo.SetValue, self.last_valid_selection)
            return
        coords = self.mni_coordinates.get(region)
        self.last_valid_selection = region
        if coords:
            self.input_x.SetValue(str(coords[0]))
            self.input_y.SetValue(str(coords[1]))
            self.input_z.SetValue(str(coords[2]))
            for ctrl in [self.input_x, self.input_y, self.input_z]:
                ctrl.Disable()
        else:
            for ctrl in [self.input_x, self.input_y, self.input_z]:
                ctrl.Enable()
                ctrl.SetFocus()

    def _on_select_mni(self, event):
        self.mni_path = self._open_file_dialog("Select MNI Template")
        self._update_file_status()

    def _on_select_subject(self, event):
        self.subject_path = self._open_file_dialog("Select Subject MRI")
        self._update_file_status()

    def _on_load_transform(self, event):
        affine = self._open_file_dialog("Select Transform Affine (.mat)", wildcard="*.mat")
        warp = self._open_file_dialog("Select Warp Transform (.nii.gz)", wildcard="*.nii.gz")
        if affine and warp:
            self.affine_file = affine
            self.warp_file = warp
            self._update_status("Transform loaded.")
            self._update_file_status()

    def _on_save_transform(self, event):
        if not self.warp_file or not self.affine_file:
            wx.MessageBox("No transform to save. Please run a registration first.", "Warning")
            return

        # Derive base name from subject or use default
        base_name = os.path.splitext(os.path.basename(self.subject_path or "transform"))[0]

        # Suggest default names
        default_affine = f"{base_name}_GenericAffine.mat"
        default_warp = f"{base_name}_InverseWarp.nii.gz"

        with wx.FileDialog(
                self, "Save Affine Transform (.mat)",
                defaultFile=default_affine,
                wildcard="*.mat", style=wx.FD_SAVE
        ) as affine_dlg:
            if affine_dlg.ShowModal() == wx.ID_OK:
                shutil.copyfile(self.affine_file, affine_dlg.GetPath())

                with wx.FileDialog(
                        self, "Save Warp Transform (.nii.gz)",
                        defaultFile=default_warp,
                        wildcard="*.nii.gz", style=wx.FD_SAVE
                ) as warp_dlg:
                    if warp_dlg.ShowModal() == wx.ID_OK:
                        shutil.copyfile(self.warp_file, warp_dlg.GetPath())
            self._update_status("Transform saved successfully.")

    def _start_transform_thread(self, event):
        self.status.SetLabel("Starting transformation...")
        self.gauge.Pulse()
        thread = threading.Thread(target=self._transform, daemon=True)
        thread.start()

    def _register_if_needed(self):
        if self.warp_file and self.affine_file:
            return self.warp_file, self.affine_file

        self._update_status("Running ANTs registration (a few minutes)...")
        mni = ants.image_read(self.mni_path)
        subj = ants.image_read(self.subject_path)
        reg = ants.registration(fixed=mni, moving=subj, type_of_transform='SyN')

        for fpath in reg['invtransforms']:
            if "affine" in fpath.lower():
                self.affine_file = fpath
            elif "warp" in fpath.lower():
                self.warp_file = fpath

        self._update_file_status("Registration complete")
        return self.warp_file, self.affine_file

    def _transform(self):
        try:
            mni_ras = [float(self.input_x.GetValue()),
                       float(self.input_y.GetValue()),
                       float(self.input_z.GetValue())]
            mni_lps = [mni_ras[0], -mni_ras[1], mni_ras[2]]

            invwarp, affine = self._register_if_needed()
            self._update_status("Applying transforms...")
            composed = ants.compose_ants_transforms([
                ants.read_transform(invwarp),
                ants.read_transform(affine)
            ])
            native_lps = composed.apply_to_point(mni_lps)

            affine_matrix = slc.Slice().affine
            voxel = img_utils.convert_world_to_voxel(native_lps, np.linalg.inv(affine_matrix))[0]

            wx.CallAfter(Publisher.sendMessage, "Toggle toolbar button", id=const.SLICE_STATE_CROSS)
            wx.CallAfter(Publisher.sendMessage, "Update slices position", position=voxel)
            wx.CallAfter(Publisher.sendMessage, "Set cross focal point", position=np.append(voxel,[0,0,0]))
            wx.CallAfter(Publisher.sendMessage, "Update volume viewer pointer", position=[voxel[0], -voxel[1], voxel[2]])

            # Determine label for marker
            region_label = self.combo.GetValue()
            if region_label == "Custom/Manual Entry":
                region_label = None
            # Conditionally create marker
            if self.create_marker_cb.IsChecked():
                wx.CallAfter(Publisher.sendMessage, "Create marker", label=region_label)
                wx.CallAfter(Publisher.sendMessage, "Create coil target from landmark", label=region_label)

            self.save_btn.Enable()
            self._update_status("✅ Done")
        except Exception as e:
            self._update_status(f"❌ Error: {str(e)}")
        finally:
            wx.CallAfter(self.gauge.SetValue, 0)

    def _update_file_status(self, status="Ready to transform."):
        self.mni_status.SetLabel("✅ MNI selected" if self.mni_path else "❌ MNI not selected")
        self.subj_status.SetLabel("✅ Subject MRI selected" if self.subject_path else "❌ Subject MRI not selected")
        self.trans_status.SetLabel("✅ Warp + Affine available" if self.warp_file and self.affine_file else "❌ Transform files not found")

        ready = bool(self.warp_file and self.affine_file) or bool(self.mni_path and self.subject_path)
        self.status.SetLabel(status if ready else "Load the MNI and MRI first, or load a transform.")
        self.go_btn.Enable(ready)

    def _update_status(self, msg):
        wx.CallAfter(self.status.SetLabel, msg)

    def _open_file_dialog(self, message, wildcard="*.nii;*.nii.gz"):
        with wx.FileDialog(self, message, wildcard=wildcard, style=wx.FD_OPEN) as dlg:
            return dlg.GetPath() if dlg.ShowModal() == wx.ID_OK else None

    def _save_file_dialog(self, message, wildcard):
        with wx.FileDialog(self, message, wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            return dlg.GetPath() if dlg.ShowModal() == wx.ID_OK else None
