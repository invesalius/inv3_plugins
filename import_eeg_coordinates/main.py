import wx

from . import gui


def load():
    w = gui.Window(wx.GetApp().GetTopWindow())
    w.Show()
