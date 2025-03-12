import wx
import numpy as np
import logging
import time
from skimage.morphology import binary_erosion, binary_dilation, disk, ball
from pubsub import pub as Publisher

import invesalius.project as prj
import invesalius.data.slice_ as slc
import invesalius.session as ses

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MaskMorphology')


class MaskMorphologyGUI(wx.Dialog):
    def __init__(
        self,
        parent,
        title="Mask Morphology",
        style=wx.DEFAULT_DIALOG_STYLE | wx.FRAME_FLOAT_ON_PARENT | wx.STAY_ON_TOP,
    ):
        super().__init__(parent, -1, title=title, style=style)
        self.slice = slc.Slice()
        self.project = prj.Project()
        logger.info("Initializing Mask Morphology plugin")
        self._init_gui()

    def _init_gui(self):
        # Operation selection
        lbl_operation = wx.StaticText(self, -1, "Operation:")
        self.choice_operation = wx.Choice(self, -1, choices=["Erosion", "Dilation"])
        self.choice_operation.SetSelection(0)  # Default to Erosion

        # Radius selection
        lbl_radius = wx.StaticText(self, -1, "Radius:")
        self.spin_radius = wx.SpinCtrl(self, -1, min=1, max=10, initial=1)

        # Structuring element selection
        lbl_struct = wx.StaticText(self, -1, "Structuring Element:")
        self.choice_struct = wx.Choice(self, -1, choices=["Disk (2D)", "Ball (3D)"])
        self.choice_struct.SetSelection(0)  # Default to Disk

        # Apply button
        btn_apply = wx.Button(self, -1, "Apply")
        btn_apply.Bind(wx.EVT_BUTTON, self.OnApply)

        # Close button
        btn_close = wx.Button(self, wx.ID_CLOSE)
        btn_close.Bind(wx.EVT_BUTTON, self.OnClose)

        # Layout
        grid_sizer = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=5)
        grid_sizer.Add(lbl_operation, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        grid_sizer.Add(self.choice_operation, 0, wx.EXPAND | wx.ALL, 5)
        grid_sizer.Add(lbl_radius, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        grid_sizer.Add(self.spin_radius, 0, wx.EXPAND | wx.ALL, 5)
        grid_sizer.Add(lbl_struct, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        grid_sizer.Add(self.choice_struct, 0, wx.EXPAND | wx.ALL, 5)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(btn_apply, 0, wx.EXPAND | wx.ALL, 5)
        button_sizer.Add(btn_close, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()
        logger.info("GUI initialized successfully")

    def OnApply(self, evt):
        logger.info("Apply button clicked")
        
        # Get current mask
        current_mask = self.slice.current_mask
        if current_mask is None:
            logger.warning("No mask selected")
            wx.MessageBox("No mask selected. Please create or select a mask first.", 
                         "No Mask Selected", wx.OK | wx.ICON_INFORMATION)
            return

        # Get parameters
        operation = self.choice_operation.GetSelection()  # 0 for Erosion, 1 for Dilation
        radius = self.spin_radius.GetValue()
        struct_type = self.choice_struct.GetSelection()  # 0 for Disk, 1 for Ball
        
        op_name = "Erosion" if operation == 0 else "Dilation"
        struct_name = "Disk (2D)" if struct_type == 0 else "Ball (3D)"
        
        logger.info(f"Operation: {op_name}, Radius: {radius}, Structure: {struct_name}")
        logger.info(f"Current mask: {current_mask.name}, Index: {current_mask.index}")

        # Get mask data
        mask_matrix = current_mask.matrix.copy()
        logger.info(f"Mask matrix shape: {mask_matrix.shape}")
        
        # Apply morphological operation
        # Note: We need to process the 3D mask as a binary image
        # The mask has a special structure with indices starting at 1
        # So we need to extract the actual binary data from indices 1:
        binary_mask = mask_matrix[1:, 1:, 1:] > 0
        logger.info(f"Binary mask shape: {binary_mask.shape}")
        logger.info(f"Binary mask non-zero elements: {np.count_nonzero(binary_mask)}")
        
        try:
            start_time = time.time()
            logger.info("Starting morphological operation")
            
            # Process each slice separately for 2D operations
            if struct_type == 0:  # Disk (2D)
                # Create a 2D structuring element
                struct_elem = disk(radius)
                logger.info(f"Created disk structuring element with shape: {struct_elem.shape}")
                
                # Process each slice separately
                result = np.zeros_like(binary_mask)
                for z in range(binary_mask.shape[0]):
                    if operation == 0:  # Erosion
                        result[z] = binary_erosion(binary_mask[z], struct_elem)
                    else:  # Dilation
                        result[z] = binary_dilation(binary_mask[z], struct_elem)
                    
                    # Log progress for every 10th slice
                    if z % 10 == 0 or z == binary_mask.shape[0] - 1:
                        logger.info(f"Processed slice {z+1}/{binary_mask.shape[0]}")
            else:  # Ball (3D)
                # Create a 3D structuring element
                struct_elem = ball(radius)
                logger.info(f"Created ball structuring element with shape: {struct_elem.shape}")
                
                # Apply 3D morphological operation
                if operation == 0:  # Erosion
                    logger.info("Applying 3D erosion")
                    result = binary_erosion(binary_mask, struct_elem)
                else:  # Dilation
                    logger.info("Applying 3D dilation")
                    result = binary_dilation(binary_mask, struct_elem)
            
            end_time = time.time()
            logger.info(f"Operation completed in {end_time - start_time:.2f} seconds")
            logger.info(f"Result non-zero elements: {np.count_nonzero(result)}")
            
            # Update the mask
            mask_matrix[1:, 1:, 1:] = result.astype(np.uint8) * 255
            
            # Update the mask in the project
            current_mask.matrix = mask_matrix
            current_mask.modified()
            logger.info("Mask updated in project")
            
            # Update the visualization
            Publisher.sendMessage('Reload actual slice')
            logger.info("Visualization updated")
            
            # Show success message
            wx.MessageBox(f"{op_name} with radius {radius} applied successfully.", 
                         "Operation Complete", wx.OK | wx.ICON_INFORMATION)
                         
        except Exception as e:
            logger.error(f"Error during morphological operation: {str(e)}", exc_info=True)
            wx.MessageBox(f"Error applying morphological operation: {str(e)}", 
                         "Operation Failed", wx.OK | wx.ICON_ERROR)

    def OnClose(self, evt):
        logger.info("Closing Mask Morphology plugin")
        self.Close() 