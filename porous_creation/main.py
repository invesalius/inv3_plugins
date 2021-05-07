import wx

from . import gui


def load():
    g = gui.GUISchwarzP(wx.GetApp().GetTopWindow())
    g.Show()
