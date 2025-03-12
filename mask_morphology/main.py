import wx
from . import gui

def load():
    """
    Load the Mask Morphology plugin.
    This function is called when the plugin is selected from the menu.
    """
    top_window = wx.GetApp().GetTopWindow()
    window = gui.MaskMorphologyGUI(top_window)
    window.ShowModal()
    window.Destroy() 