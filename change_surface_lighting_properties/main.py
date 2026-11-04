import wx
from pubsub import pub as Publisher
from . import gui

def bind_events():
    Publisher.subscribe(SetAmbient, "Set Ambient")
    Publisher.subscribe(SetDiffuse, "Set Diffuse")
    Publisher.subscribe(SetSpecular, "Set Specular")


def SetAmbient(value, actor, surface):
    actor.GetProperty().SetAmbient(value)
    Publisher.sendMessage("Update surface presentation", surface=surface)
    Publisher.sendMessage("Render volume viewer")

def SetDiffuse(value, actor, surface):
    actor.GetProperty().SetDiffuse(value)
    Publisher.sendMessage("Update surface presentation", surface=surface)
    Publisher.sendMessage("Render volume viewer")

def SetSpecular(value, actor, surface):
    actor.GetProperty().SetSpecular(value)
    Publisher.sendMessage("Update surface presentation", surface=surface)
    Publisher.sendMessage("Render volume viewer")



def load():
    bind_events()
    w = gui.Window(wx.GetApp().GetTopWindow())
    w.Show()
