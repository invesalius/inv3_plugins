"""
Mask Statistics Plugin for InVesalius

Shows detailed stats about the currently selected mask including
voxel counts, physical volume, and dimensions.

Author: Prateek Rai
Version: 1.0
"""

import csv
import os
import wx
import numpy as np
from invesalius.data.slice_ import Slice


def load():
    """
    Main entry point - gets called when user clicks the plugin menu item.
    """
    try:
        # Get the currently selected mask from InVesalius
        slice_instance = Slice()
        current_mask = slice_instance.current_mask
        
        # Make sure a mask is actually selected
        if current_mask is None:
            show_error_dialog(
                "No Active Mask",
                "No active mask selected.\n\n"
                "Please create or select a mask first."
            )
            return
        
        # Extract the data we need
        matrix = current_mask.matrix
        spacing = current_mask.spacing
        mask_name = current_mask.name
        
        # Check if mask is empty (no voxels set)
        actual_mask = matrix[1:, 1:, 1:]
        if np.count_nonzero(actual_mask) == 0:
            show_error_dialog(
                "Empty Mask",
                f"The mask '{mask_name}' contains no voxels.\n\n"
                "Please segment some data first."
            )
            return
        
        # Crunch the numbers
        stats = compute_mask_statistics(matrix, spacing, mask_name)
        
        # Show results
        show_statistics_dialog(stats)
        
    except Exception as e:
        # Catch any unexpected errors
        show_error_dialog(
            "Plugin Error",
            f"Something went wrong:\n\n{str(e)}\n\n"
            f"This might be a version mismatch issue."
        )
        import traceback
        traceback.print_exc()


def compute_mask_statistics(matrix, spacing, mask_name):
    """
    Calculate all the statistics for the mask.
    
    Note: InVesalius stores mask data in matrix[1:, 1:, 1:] - the first
    index in each dimension is used for internal bookkeeping.
    """
    # Get the actual mask data (skip the bookkeeping indices)
    actual_mask = matrix[1:, 1:, 1:]
    
    # Count voxels
    total_voxels = actual_mask.size
    non_zero_voxels = np.count_nonzero(actual_mask)
    zero_voxels = total_voxels - non_zero_voxels
    occupation_percentage = (non_zero_voxels / total_voxels * 100) if total_voxels > 0 else 0
    
    # Calculate physical volume
    # Each voxel has a volume = z_spacing * y_spacing * x_spacing
    voxel_volume_mm3 = spacing[0] * spacing[1] * spacing[2]
    physical_volume_mm3 = non_zero_voxels * voxel_volume_mm3
    physical_volume_cm3 = physical_volume_mm3 / 1000.0
    
    # Get dimensions
    depth, height, width = actual_mask.shape
    
    # Calculate physical dimensions in mm
    physical_depth_mm = depth * spacing[0]
    physical_height_mm = height * spacing[1]
    physical_width_mm = width * spacing[2]
    
    # Value statistics (for non-zero voxels)
    unique_values = np.unique(actual_mask)
    masked_values = actual_mask[actual_mask > 0]
    
    if len(masked_values) > 0:
        min_value = np.min(masked_values)
        max_value = np.max(masked_values)
        mean_value = np.mean(masked_values)
    else:
        min_value = max_value = mean_value = 0
    
    return {
        "name": mask_name,
        "shape": (depth, height, width),
        "spacing": spacing,
        "total_voxels": total_voxels,
        "non_zero_voxels": non_zero_voxels,
        "zero_voxels": zero_voxels,
        "occupation_percentage": occupation_percentage,
        "physical_depth_mm": physical_depth_mm,
        "physical_height_mm": physical_height_mm,
        "physical_width_mm": physical_width_mm,
        "voxel_volume_mm3": voxel_volume_mm3,
        "physical_volume_mm3": physical_volume_mm3,
        "physical_volume_cm3": physical_volume_cm3,
        "unique_values": len(unique_values),
        "min_value": int(min_value),
        "max_value": int(max_value),
        "mean_value": float(mean_value),
    }


def export_to_csv(stats):
    """
    Export statistics to a CSV file.
    """
    app = wx.GetApp()
    if not app:
        return
    
    parent = app.GetTopWindow()
    
    # Ask user where to save
    wildcard = "CSV files (*.csv)|*.csv"
    default_filename = f"{stats['name']}_statistics.csv"
    
    dialog = wx.FileDialog(
        parent,
        "Save Statistics as CSV",
        defaultFile=default_filename,
        wildcard=wildcard,
        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
    )
    
    if dialog.ShowModal() != wx.ID_OK:
        dialog.Destroy()
        return  # User cancelled
    
    filepath = dialog.GetPath()
    dialog.Destroy()
    
    try:
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Metric', 'Value', 'Unit'])
            
            # Write statistics
            writer.writerow(['Mask Name', stats['name'], ''])
            writer.writerow([])
            
            writer.writerow(['Dimension X', stats['shape'][2], 'voxels'])
            writer.writerow(['Dimension Y', stats['shape'][1], 'voxels'])
            writer.writerow(['Dimension Z', stats['shape'][0], 'voxels'])
            writer.writerow([])
            
            writer.writerow(['Spacing X', f"{stats['spacing'][2]:.4f}", 'mm'])
            writer.writerow(['Spacing Y', f"{stats['spacing'][1]:.4f}", 'mm'])
            writer.writerow(['Spacing Z', f"{stats['spacing'][0]:.4f}", 'mm'])
            writer.writerow([])
            
            writer.writerow(['Total Voxels', stats['total_voxels'], 'voxels'])
            writer.writerow(['Masked Voxels', stats['non_zero_voxels'], 'voxels'])
            writer.writerow(['Zero Voxels', stats['zero_voxels'], 'voxels'])
            writer.writerow(['Occupancy', f"{stats['occupation_percentage']:.2f}", '%'])
            writer.writerow([])
            
            writer.writerow(['Physical Volume', f"{stats['physical_volume_mm3']:.2f}", 'mm³'])
            writer.writerow(['Physical Volume', f"{stats['physical_volume_cm3']:.4f}", 'cm³'])
            writer.writerow([])
            
            writer.writerow(['Min Value', stats['min_value'], ''])
            writer.writerow(['Max Value', stats['max_value'], ''])
            writer.writerow(['Mean Value', f"{stats['mean_value']:.2f}", ''])
            writer.writerow(['Unique Values', stats['unique_values'], ''])
        
        wx.MessageBox(
            f"Statistics exported to:\n{filepath}",
            "Export Successful",
            wx.OK | wx.ICON_INFORMATION,
            parent
        )
        
    except Exception as e:
        wx.MessageBox(
            f"Failed to save CSV:\n{str(e)}",
            "Export Error",
            wx.OK | wx.ICON_ERROR,
            parent
        )


def show_statistics_dialog(stats):
    """Display the statistics in a nice dialog window."""
    app = wx.GetApp()
    if not app:
        print("[Error] Couldn't get wx.App instance")
        return
    
    parent = app.GetTopWindow()
    
    # Create the dialog
    dialog = wx.Dialog(
        parent,
        title=f"Mask Statistics: {stats['name']}",
        size=(550, 600),
        style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
    )
    
    main_sizer = wx.BoxSizer(wx.VERTICAL)
    
    # Title
    title_label = wx.StaticText(dialog, label="Mask Statistics Report")
    title_font = title_label.GetFont()
    title_font.PointSize += 3
    title_font = title_font.Bold()
    title_label.SetFont(title_font)
    main_sizer.Add(title_label, 0, wx.ALL | wx.ALIGN_CENTER, 10)
    
    # Add tabs for different info sections
    notebook = wx.Notebook(dialog)
    
    notebook.AddPage(create_overview_panel(notebook, stats), "Overview")
    notebook.AddPage(create_details_panel(notebook, stats), "Detailed Stats")
    notebook.AddPage(create_technical_panel(notebook, stats), "Technical Info")
    
    main_sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 10)
    
    # Button panel
    button_sizer = wx.BoxSizer(wx.HORIZONTAL)
    
    # Export CSV button
    export_btn = wx.Button(dialog, label="Export CSV")
    export_btn.Bind(wx.EVT_BUTTON, lambda evt: export_to_csv(stats))
    button_sizer.Add(export_btn, 0, wx.RIGHT, 10)
    
    # Close button
    ok_button = wx.Button(dialog, wx.ID_OK, "Close")
    button_sizer.Add(ok_button, 0)
    
    main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
    
    dialog.SetSizer(main_sizer)
    dialog.ShowModal()
    dialog.Destroy()


def create_overview_panel(parent, stats):
    """Overview tab - shows the most important stats."""
    panel = wx.Panel(parent)
    sizer = wx.BoxSizer(wx.VERTICAL)
    
    info_lines = [
        ("Mask Name:", stats['name']),
        ("", ""),
        ("Dimensions:", f"{stats['shape'][2]} × {stats['shape'][1]} × {stats['shape'][0]} voxels"),
        ("Physical Size:", f"{stats['physical_width_mm']:.1f} × {stats['physical_height_mm']:.1f} × {stats['physical_depth_mm']:.1f} mm"),
        ("", ""),
        ("Total Voxels:", f"{stats['total_voxels']:,}"),
        ("Masked Voxels:", f"{stats['non_zero_voxels']:,}"),
        ("Occupation:", f"{stats['occupation_percentage']:.2f}%"),
        ("", ""),
        ("Physical Volume:", f"{stats['physical_volume_cm3']:.2f} cm³"),
        ("", f"({stats['physical_volume_mm3']:.2f} mm³)"),
    ]
    
    for label, value in info_lines:
        if label == "":
            sizer.Add((-1, 5))  # spacer
        else:
            line_sizer = wx.BoxSizer(wx.HORIZONTAL)
            label_text = wx.StaticText(panel, label=label)
            label_font = label_text.GetFont()
            label_font = label_font.Bold()
            label_text.SetFont(label_font)
            line_sizer.Add(label_text, 0, wx.RIGHT, 10)
            value_text = wx.StaticText(panel, label=str(value))
            line_sizer.Add(value_text, 1, wx.EXPAND)
            sizer.Add(line_sizer, 0, wx.EXPAND | wx.ALL, 5)
    
    panel.SetSizer(sizer)
    return panel


def create_details_panel(parent, stats):
    """Detailed stats tab - more granular information."""
    panel = wx.Panel(parent)
    sizer = wx.BoxSizer(wx.VERTICAL)
    
    info_lines = [
        ("Voxel Statistics:", ""),
        ("  Total voxels:", f"{stats['total_voxels']:,}"),
        ("  Non-zero voxels:", f"{stats['non_zero_voxels']:,}"),
        ("  Zero voxels:", f"{stats['zero_voxels']:,}"),
        ("  Occupation rate:", f"{stats['occupation_percentage']:.4f}%"),
        ("", ""),
        ("Value Statistics:", ""),
        ("  Unique values:", f"{stats['unique_values']}"),
        ("  Min value:", f"{stats['min_value']}"),
        ("  Max value:", f"{stats['max_value']}"),
        ("  Mean value:", f"{stats['mean_value']:.2f}"),
        ("", ""),
        ("Volume Calculations:", ""),
        ("  Single voxel volume:", f"{stats['voxel_volume_mm3']:.4f} mm³"),
        ("  Total mask volume:", f"{stats['physical_volume_mm3']:.2f} mm³"),
        ("  Total mask volume:", f"{stats['physical_volume_cm3']:.4f} cm³"),
    ]
    
    for label, value in info_lines:
        if label == "":
            sizer.Add((-1, 5))
        else:
            line_sizer = wx.BoxSizer(wx.HORIZONTAL)
            label_text = wx.StaticText(panel, label=label)
            if not label.startswith("  "):
                label_font = label_text.GetFont()
                label_font = label_font.Bold()
                label_text.SetFont(label_font)
            line_sizer.Add(label_text, 0, wx.RIGHT, 10)
            if value:
                value_text = wx.StaticText(panel, label=str(value))
                line_sizer.Add(value_text, 1, wx.EXPAND)
            sizer.Add(line_sizer, 0, wx.EXPAND | wx.ALL, 3)
    
    panel.SetSizer(sizer)
    return panel


def create_technical_panel(parent, stats):
    """Technical info tab - array shapes, spacing, etc."""
    panel = wx.Panel(parent)
    sizer = wx.BoxSizer(wx.VERTICAL)
    
    info_lines = [
        ("Array Shape:", f"{stats['shape']}"),
        ("  Depth (Z):", f"{stats['shape'][0]} slices"),
        ("  Height (Y):", f"{stats['shape'][1]} pixels"),
        ("  Width (X):", f"{stats['shape'][2]} pixels"),
        ("", ""),
        ("Voxel Spacing:", f"{stats['spacing']}"),
        ("  Z-spacing:", f"{stats['spacing'][0]:.4f} mm"),
        ("  Y-spacing:", f"{stats['spacing'][1]:.4f} mm"),
        ("  X-spacing:", f"{stats['spacing'][2]:.4f} mm"),
        ("", ""),
        ("Physical Dimensions:", ""),
        ("  Depth:", f"{stats['physical_depth_mm']:.2f} mm"),
        ("  Height:", f"{stats['physical_height_mm']:.2f} mm"),
        ("  Width:", f"{stats['physical_width_mm']:.2f} mm"),
    ]
    
    for label, value in info_lines:
        if label == "":
            sizer.Add((-1, 5))
        else:
            line_sizer = wx.BoxSizer(wx.HORIZONTAL)
            label_text = wx.StaticText(panel, label=label)
            if not label.startswith("  "):
                label_font = label_text.GetFont()
                label_font = label_font.Bold()
                label_text.SetFont(label_font)
            line_sizer.Add(label_text, 0, wx.RIGHT, 10)
            if value:
                value_text = wx.StaticText(panel, label=str(value))
                line_sizer.Add(value_text, 1, wx.EXPAND)
            sizer.Add(line_sizer, 0, wx.EXPAND | wx.ALL, 3)
    
    panel.SetSizer(sizer)
    return panel


def show_error_dialog(title, message):
    """Show a simple error message box."""
    app = wx.GetApp()
    if not app:
        print(f"[Error] {title}: {message}")
        return
    
    parent = app.GetTopWindow()
    wx.MessageBox(message, title, wx.OK | wx.ICON_WARNING, parent)


# Future ideas to extend this plugin:
# - Show histogram of mask values with matplotlib
# - Compare stats between multiple masks
# - Calculate surface area using marching cubes
# - Real-time updates when mask changes (use pubsub)
# - Find centroid and bounding box
# - Detect disconnected regions (connectivity analysis)
# - Quality checks: find holes, thin regions, artifacts
