"""
Extinction map from Lallement et al 2019, for dust within 3 kpc based on
Gaia & 2MASS observations.

Paper DOI: 10.1051/0004-6361/201834695

Data file FTP: https://cdsarc.cds.unistra.fr/ftp/J/A+A/625/A135/
"""

__all__ = ["Lallement", ]
__author__ = "M.J. Huston"
__date__ = "2024-11-06"
__license__ = "GPLv3"
__version__ = "1.0.0"

import gzip
import h5py
import shutil
import numpy as np
from ._extinction import ExtinctionMap, EXTINCTION_DIR
import time
from scipy.interpolate import RegularGridInterpolator
import os
from .. import const
import requests

current_map_name = None
current_map_data = None

class Lallement(ExtinctionMap):
    """
    Extinction map from Lallement et al. 2019

    Attributes
    ----------
    extinction_map_name : str
        name of the Extinction Map
    l_deg : float
        galactic longitude in degree set by "update_sight-line"
    b_deg : float
        galactic latitude in degree set by "update_sight-line"

    ref_wavelength : float
        reference wavelength for the extinction

    A_or_E : float or function
        total extinction or color excess, from the extinction map.
        if it is a function it will be called

    A_or_E_type : str
        Output type from the extinction map.
        If it starts with "A", A_or_E is handled  as a total extinction.
        If it starts with "E": A_or_E is handled as a color excess.

    Methods
    -------

    update_extinction_in_map():
        placeholder for function that updates the total extinction or color excess
        in self.extinction_map_name

    get_map_properties():
        returns the basic parameters of the extinction map
        used for Communication between ExtinctionLaw and ExtinctionMap

    """

    def __init__(self, dr=0.005, return_functions=True, **kwargs):
        super().__init__(**kwargs)
        # name of the extinction map used
        self.extinction_map_name = "Lallement"
        self.return_functions = return_functions
        # A0 = value at 5500 angstroms
        self.ref_wavelength = 0.55
        self.A_or_E_type = 'A0'
        # placeholder for and location...
        self.l_deg = None
        self.b_deg = None
        self.extinction_in_map = None
        self.dr = dr #: step size for extinction integration in kpc
        if not os.path.isfile(f'{const.EXTINCTIONS_DIR}/map3D_GAIAdr2_feb2019.h5'):
            print("Missing Lallement extinction table. Download and unpacking may take several minutes but only needs done once.")
            map_url = 'https://cdsarc.cds.unistra.fr/ftp/J/A+A/625/A135/map3D_GAIAdr2_feb2019.h5.gz'
            map_filename = f'{const.EXTINCTIONS_DIR}/'+map_url.split("/")[-1]
            with open(map_filename, "wb") as f:
                r = requests.get(map_url)
                f.write(r.content)
                print('Map retrieved.')
            with gzip.open(map_filename,'rb') as f_in, open(map_filename[:-3],'wb') as f_out:
                shutil.copyfileobj(f_in,f_out)
            os.remove(map_filename)
            print('File unzipped; ready to use.')
            
        # Check whether the map is already loaded from the prior population
        global current_map_name, current_map_data
        if (current_map_name is not None) and (current_map_data is not None):
            if current_map_name==self.extinction_map_name:
                self.map_data = current_map_data
            else:
                self.map_data = np.array(h5py.File(f'{const.EXTINCTIONS_DIR}/map3D_GAIAdr2_feb2019.h5')['stilism']['cube_datas'])
                current_map_name = self.extinction_map_name
                current_map_data = self.map_data
        else:
            self.map_data = np.array(h5py.File(f'{const.EXTINCTIONS_DIR}/map3D_GAIAdr2_feb2019.h5')['stilism']['cube_datas'])
            current_map_name = self.extinction_map_name
            current_map_data = self.map_data
        # 5 pc grid spacing: -3 to 3 kpc in x,y; -400 to 400 pc in z
        self.grid_dr = 0.005
        self.grid_x_mid = 600
        self.grid_y_mid = 600
        self.grid_z_mid = 80
        # Data units are mag/pc in A0, 5500 angstrom
        
    def ext_func(self,l_deg,b_deg,dist):
        '''
        Get extinction value for multiple stars given their positions.
        '''
        # Set up points along lines to integrate through
        n_pts, dr_rem = np.divmod(dist,self.dr)
        dist_max = np.max(dist)
        dist_pts = np.arange(0,dist_max,self.dr)[np.newaxis,:]
        # Convert to nearest neighbor map array indices
        l_rad, b_rad = l_deg[:,np.newaxis]*np.pi/180, b_deg[:,np.newaxis]*np.pi/180
        xm_pts = np.maximum(np.minimum(np.around(dist_pts*np.cos(b_rad)*np.cos(l_rad)/self.grid_dr).astype(int), self.grid_x_mid), -self.grid_x_mid) + self.grid_x_mid
        ym_pts = np.maximum(np.minimum(np.around(dist_pts*np.cos(b_rad)*np.sin(l_rad)/self.grid_dr).astype(int), self.grid_y_mid), -self.grid_y_mid) + self.grid_y_mid
        zm_pts = np.maximum(np.minimum(np.around(dist_pts*np.sin(b_rad)/self.grid_dr).astype(int), self.grid_z_mid), -self.grid_z_mid) + self.grid_z_mid
        # Get differential extinction along sightlines
        dm_dr_pts = self.map_data[xm_pts,ym_pts,zm_pts]
        # Sum up dA/dr * dr for each point in foreground
        # to get total extinction for each star
        return np.sum(dm_dr_pts*self.dr*1e3*(dist_pts<(dist[:,np.newaxis])), axis=1)

    def update_extinction_in_map(self, radius, force=False, **kwargs):
        """
        Returns the extinction for the current sight line and radial distance, or returns function to do so.

        Parameters
        ----------
        radius: float [kpc]
            radial distance of the current slice
        """

        if self.return_functions:
            self.extinction_in_map = self.ext_func
        else:
            self.extinction_in_map = self.ext_func(self.l_deg, self.b_deg, radius)
