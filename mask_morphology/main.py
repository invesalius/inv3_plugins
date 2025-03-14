import wx
from . import gui

def load():
    """
    Load the Mask Morphology plugin.
    This function is called when the plugin is selected from the menu.
    """
    top_window = wx.GetApp().GetTopWindow()
    window = gui.MaskMorphologyGUI(top_window)
    window.Show()

def get_plugin_info():
    """
    Return information about the plugin.
    
    This function is used by InVesalius to get information about the plugin
    for display in the plugin manager.
    
    Returns:
        dict: A dictionary containing plugin information
    """
    return {
        "name": "Mask Morphology",
        "description": "Apply morphological operations (erosion/dilation) to the current mask",
        "version": "1.0.0",
        "author": "Soumyadipta Dey",
        "contact": "soumyadiptadey7@gmail.com"
    }

