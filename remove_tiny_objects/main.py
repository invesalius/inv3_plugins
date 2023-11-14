import wx
from pubsub import pub as Publisher

import invesalius.data.slice_ as slc
from invesalius import project

from . import gui

def load():
    s = slc.Slice()
    p = project.Project()

    image_matrix = s.matrix
    spacing = s.spacing

    g = gui.Window(wx.GetApp().GetTopWindow(), image_matrix)
    g.Show()
