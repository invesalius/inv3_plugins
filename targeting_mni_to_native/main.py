import wx

from . import gui


def load():
    w = gui.MNItoNativeDialog(wx.GetApp().GetTopWindow())
    w.Show()
