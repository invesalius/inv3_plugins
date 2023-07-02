import numpy as np
import vtk
import wx
from pubsub import pub as Publisher
from six import with_metaclass

from invesalius.data import styles

# erosion and dilation related
import cv2
import nibabel as nib
from copy import deepcopy
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from sklearn.cluster import KMeans


from . import gui

class FunctionalOverlayStyle(styles.DefaultInteractorStyle):
    gui = None
    def __init__(self, viewer):
        super().__init__(viewer)

        # NOTE: Currently we load pre-computed files here
        self.datapath = '/home/chunhei/Desktop/projects/gsoc/resources/'
        self.func_frame = nib.load(self.datapath + 'sing_func_subj.nii.gz').get_fdata()
        self.func_conn = nib.load(self.datapath + 'G1_func_subspace.nii.gz').get_fdata()
        self.yeo7 = nib.load(self.datapath + 'yeo7vol_subspace.nii.gz').get_fdata()
        self.yeo17 = nib.load(self.datapath + 'yeo17vol_subspace.nii.gz').get_fdata()

        self.cluster_smoothness = 10
        self.AddObserver("LeftButtonPressEvent", self.OnPressLeftButtonOverlay)


    def SetUp(self):
        print("SetUP")
        if self.gui is None:
            self.create_gui()

    def CleanUp(self):
        print("CleanUp")
        if self.gui is not None:
            self.destroy_gui()

    def OnPressLeftButtonOverlay(self, obj, evt):

        # Set the overlay
        # we transpose and flip since the functional frames are not rotated in the same way structurals are
        if self.gui.choice_morph == "TimeFrame":
            # NOTE: not done implemented
            tmp = deepcopy(self.func_frame).T[:,::-1]
            # -> Idea is to generate one hue but with different intensity for the whole volume, intensity depending on the BOLD value
            return
        
        elif self.gui.choice_morph == "Yeo-7":
            self.cluster_smoothness = 7
            tmp = deepcopy(self.yeo7)
            clust_vol = tmp.astype(int).T[:,::-1]
        elif self.gui.choice_morph == "Yeo-17":
            self.cluster_smoothness = 17
            tmp = deepcopy(self.yeo17)
            clust_vol = tmp.astype(int).T[:,::-1]
        elif self.gui.choice_morph == "Betamaps":
            # NOTE: not done implemented
            print("NOT SUPPORTED OPTION YET")
            return
        elif self.gui.choice_morph == "Seedbased":
            # NOTE: not done implemented
            print("NOT SUPPORTED OPTION YET")
            return
        else:
            tmp = deepcopy(self.func_conn).T[:,::-1]
            # 0. Clustering of colors and values from tmp
            # - Arbitrary clustering (for now) for Functional-Connectivity option
            tmp[np.isnan(tmp)] = -10000 # artificially cluster together the nans

            kmeans = KMeans(init="k-means++", n_clusters=self.cluster_smoothness, n_init=4, random_state=0)
            res = kmeans.fit_predict(tmp.flatten().reshape(-1,1))
            # convert the clustered regions back to volume shape
            clust_vol = res.reshape(tmp.shape)


        # 1. Create layer of shape first
        self.viewer.slice_.aux_matrices['color_overlay'] = clust_vol
        self.viewer.slice_.aux_matrices['color_overlay'] = self.viewer.slice_.aux_matrices['color_overlay'].astype(int)

        # 2. Attribute different hue accordingly
        color = cm.rainbow(np.linspace(0, 1, self.cluster_smoothness), alpha=0.4)
        self.viewer.slice_.aux_matrices_colours['color_overlay'] = {k+1:color[k] for k in range(self.cluster_smoothness)}
        self.viewer.slice_.aux_matrices_colours['color_overlay'][0] = (0.0, 0.0, 0.0, 0.0) # add transparent color for nans and non GM voxels

        # 3. Show colors
        self.viewer.slice_.to_show_aux = 'color_overlay'
        self.viewer.discard_mask_cache(all_orientations=True, vtk_cache=True)


        Publisher.sendMessage('Reload actual slice')

    @classmethod
    def create_gui(cls):
        if cls.gui is None:
            top_window = wx.GetApp().GetTopWindow()
            cls.gui = gui.FunctionalOverlayGUI(top_window)
            cls.gui.Show()

    @classmethod
    def destroy_gui(cls):
        if cls.gui is not None:
            cls.gui.Destroy()
            cls.gui = None
