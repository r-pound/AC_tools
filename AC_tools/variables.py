#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Variable store/dictionarys for use in AC_tools

Use help(<name of function>) to get details on a particular function.

Notes
 - This code will be updated to use a user configuration approach (*.rc file) shortly
"""

# - Required modules:
# I/O / Low level
import re
import os
#import platform
import pandas as pd
from netCDF4 import Dataset
#import Scientific.IO.NetCDF as S
import sys
import glob
# Math/Analysis
import numpy as np

# the below import needs to be updated,
# imports should be specific and in individual functions
# import tms modules with shared functions
from . core import *


def get_unit_scaling(units, scaleby=1):
    """
    Get scaling for a given unit string

    Parameters
    -------
    units (str): units
    scaleby (float): scaling factor for unit

    Returns
    -------
    (float)
    """
    logging.debug("Getting unit scaling for {units}".format(units=units))
    misc = (
        'K', 'm/s', 'unitless', 'kg', 'm', 'm2', 'kg/m2/s', 'molec/cm2/s',
        'mol/cm3/s',  'kg/s', 'hPa', 'atoms C/cm2/s', 'kg S', 'mb', 'atoms C/cm2/s',
        'molec/cm3', 'v/v', 'cm/s', 's-1', 'molec/m3', 'W/m2', 'unitless',
        '$\mu$g m$^{-3}$',
    )
    # parts per trillion
    if any([(units == i) for i in ('pptv', 'pptC', 'ppt')]):
        scaleby = 1E12
    # parts per billion
    elif any([(units == i) for i in ('ppbv', 'ppbC', 'ppb')]):
        scaleby = 1E9
    elif any([units == i for i in misc]):
        scaleby = 1.
        logging.debug('WARNING: {} is not in unit lists: '.format(units))
    return scaleby


class species:
    """
    Class for holding infomation about chemical species

    Notes
    -----
     - the class is built from a csv file in the data folder of the repository
     - This file was built using the table of Species in GEOS-Chem on the wiki linked
     below. It was updated on
    http://wiki.seas.harvard.edu/geos-chem/index.php/Species_in_GEOS-Chem
    """

    def __repr__(self):
        rtn_str = "This is a class to hold chemical species information for {}"
        return rtn_str.format(self.name)

    def __str__(self):
        for key in self.__dict__.keys():
            print("{:<20}:".format(key, self.key))

    def __init__(self, name):
        self.name = name
        self.help = ("""This is a class to get information on a species from a CSV file
   It might contain the following information:
   self.RMM        = Molecular weight of the species in g mol-1
   self.latex      = The latex name of the species
   self.Smiles     = The smiles string of the species
   self.InChI      = The InChI string of the species
   self.Phase      = Denotes whether the species is in the gas or aerosol phase.
   self.Formula    = Chemical formula of the species
   self.long_name  = A longer, descriptive name for the species
   self.Chem       = Is the species contained in one of the pre-built KPP chemistry mechanisms used by GEOS-Chem?
   self.Advect     = Is the species subject to advection, cloud convection, + BL mixing?
   self.Drydep     = Is the species subject to dry deposition?
   self.Wetdep     = Is the species soluble and subject to wet deposition?
   self.Phot       = Is the species included in the FAST-JX photolysis mechanism?
   self.Mechanisms = the GEOS-Chem chemistry mechanisms to which the species belongs
   self.Ox         = Shows the number of molecules of the species that will be included in the computation of the P(Ox) and L(Ox) diagnostic families
   self.Version    = The version this species was added to GEOS-Chem or the latest version this species was updated (if available)
    self.Carbons   = number of carbon atoms in species
   """)
        # Set folder and filename to use, then check they are present
        # NOTE: "Python AC_tools/Scripts/get_data_files.py" retrieves data files
        folder = os.path.dirname(__file__) + '/../data/'
        filename = 'GEOS_ChemSpecies_fullchem_v0.1.0.csv'
        assert os.path.exists(folder+filename), "Error: Species csv not found!"
        # Open species csv file as dataframe
        dfM = pd.read_csv(folder+filename)
        # see if species in df
        df = dfM.loc[dfM['Species'] == str(self.name), :]
        # Add properties from csv file
        if df.shape[0] != 0:
            # - Now attributes for species
            self.formula = str(df['Formula'].values[0])
            self.long_name = str(df['Full name'].values[0])
            self.RMM = str(df['Molec wt\n(g/mol)'].values[0])
            self.Phase = str(df['Gas or Aer'].values[0])
            self.Chem = str(df['Chem'].values[0])
            self.Advect = str(df['Advect'].values[0])
            self.Drydep = str(df['Drydep'].values[0])
            self.Wetdep = str(df['Wetdep'].values[0])
            self.Phot = str(df['Phot'].values[0])
            self.Mechanisms = str(df['Mechanisms'].values[0])
            self.Ox = str(df['Ox?'].values[0])
            self.Version = str(df['Version\nadded/\nupdated'].values[0])
            # inc smiles, InChI, and latex add offline from MChem_tools file.
            # NOTE: smiles/InChI/latex need updating
            self.InChI = str(df['InChI'].values[0])
            self.smiles = str(df['smiles'].values[0])
            self.LaTeX = str(df['LaTeX'].values[0])

            # - Update the formating of columns of DataFrame
            # TODO: update to read a pre-processed file for speed.
            # Add the number of carbons in a species
            def add_carbon_column(x):
                try:
                    return float(x.split('(12, ')[-1][:-2])
                except:
                    return np.NaN
#            df['Carbons'] = df['Molec wt\n(g/mol)'].map(add_carbon_column)
#            val = df['Molec wt\n(g/mol)'].values[0]
#            df['Carbons'] = np.NaN
#            df.loc[:,'Carbons'] = add_carbon_column(val)
            self.Carbons = add_carbon_column(self.RMM)
            # Make sure mass is shown as RMM

            def mk_RMM_a_float(x):
                try:
                    return float(x.split('(12, ')[0].strip())
                except:
                    return float(x)
#            val = df['Molec wt\n(g/mol)'].values[0]
#            df.loc[:,'Molec wt\n(g/mol)'] = mk_RMM_a_float(val)
            self.RMM = mk_RMM_a_float(self.RMM)
            # Convert booleans from crosses to True or False

            def update_X_to_bool(x):
                if x == 'X':
                    return True
                else:
                    return False
            booleans = 'Chem', 'Advect', 'Drydep', 'Wetdep', 'Phot'
#            for col in booleans:
#                val = df[col].values[0]
#                df.loc[:,col] = update_X_to_bool(val)
            self.Chem = update_X_to_bool(self.Chem)
            self.Advect = update_X_to_bool(self.Advect)
            self.Drydep = update_X_to_bool(self.Drydep)
            self.Wetdep = update_X_to_bool(self.Wetdep)
            self.Phot = update_X_to_bool(self.Phot)

        else:
            print("Species not found in CSV file ({})".format(filename))
        # Remove the DataFrame from memory
        del dfM

    def help(self):
        '''
        Another way to get help for the class.
        '''
        help(self)
        return


def constants(input_x, rtn_dict=False):
    """
    Dictionary storing commonly used constants

    Parameters
    ----------
    input_x (str): name of contant of interest
    rtn_dict (bool): retrun complete dictionary instead of single value

    Returns
    -------
    value of constant (float) or dictionary on constants and values (dict)

    Notes
    -----
    """
    con_dict = {
        # Relative atomic mass of air (Just considering N2+O2)
        'RMM_air': (.78*(2.*14.)+.22*(2.*16.)),
        # Avogadro constant (Mol^-1)
        'AVG': 6.0221413E23,
        # Dobson unit - (molecules per meter squared)
        'mol2DU': 2.69E20,
        # Specific gas constant for dry air (J/(kg·K))
        'Rdry': 287.058,
    }
    if rtn_dict:
        return con_dict
    else:
        return con_dict[input_x]


def get_loc(loc=None, rtn_dict=False, debug=False):
    """
    Dictionary to store locations (lon., lat., alt.)

    Returns
    -------
    (tuple)

    Notes
    -----
     - Data arranged: LON, LAT, ALT
    ( LON in deg E, LAT in deg N, ALT in metres a.s.l. )
     - double up? ( with 5.02 ?? )
     - Now use Class of GEO_site in preference to this func?
     - UPDATE NEEDED: move this to func_vars4obs
    """
    loc_dict = {
        # - CAST/CONTRAST
        'GUAM':  (144.800, 13.500, 0),
        'CHUUK': (151.7833, 7.4167, 0),
        'PILAU': (134.4667, 7.3500, 0),
        'London': (-0.1275, 51.5072, 0),
        'Weybourne': (1.1380, 52.9420,  0),
        'WEY': (1.1380, 52.9420,  0),  # Weyboure ID
        'Cape Verde': (-24.871, 16.848, 0),
        'CVO': (-24.871, 16.848,  0),  # Cape Verde ID
        'CVO1': (-24.871, 16.848,  0),  # Cape Verde ID
        'CVO (N)': (-24.871, 16.848+4,  0),  # Cape Verde (N)
        'CVO (N) 2x2.5': (-24.871, 16.848+2,  0),  # Cape Verde (N)
        'CVO2': (-24.871, 16.848+4,  0),  # Cape Verde (N)
        'CVO (NNW)': (-24.871, 16.848+8.,  0),  # Cape Verde (NNW)
        'CVO3': (-24.871, 16.848+8.,  0),  # Cape Verde (NNW)
        'CVO (NW)': (-24.871-4, 16.848+4.,  0),  # Cape Verde (NW)
        'CVO (NW) 2x2.5': (-24.871-2, 16.848+2.,  0),  # Cape Verde (NW)
        'CVO4': (-24.871-4, 16.848+4.,  0),  # Cape Verde (NW)
        'CVO (W)': (-24.871-4, 16.848,  0),  # Cape Verde (W)
        'CVO (W) 2x2.5': (-24.871-2, 16.848,  0),  # Cape Verde (W)
        'CVO5': (-24.871-4, 16.848,  0),  # Cape Verde (W)
        'CVO (S)': (-24.871, 16.848-4,  0),  # Cape Verde (S)
        'CVO6': (-24.871, 16.848-4,  0),  # Cape Verde (S)
        'CVO (SW)': (-24.871-4, 16.848-4,  0),  # Cape Verde (SW)
        'CVO7': (-24.871-4, 16.848-4,  0),  # Cape Verde (SW)
        # - ClearFlo
        'North Ken':  (-0.214174, 51.520718, 0),
        'KEN':  (-0.214174, 51.520718, 0),
        'BT tower': (-0.139055, 51.521556, 190),
        'BTT': (-0.139055, 51.521556, 190),
        # - ClNO2 sites
        'HOU': (-95.22, 29.45, 0),
        'BOL': (-105.27, 40.0, 1655 + 150),
        'LAC': (-118.23, 34.05, 	0),
        'HES': (8.45, 50.22, 	825),
        'SCH': (114.25, 22.22, 60),
        'TEX': (-95.425000, 30.350278,  60),
        'CAL': (-114.12950, 51.07933,  1100),
        'PAS':  (-118.20, 34.23, 246),
        # - ClNO2 (UK) sites
        'PEN':  (-4.1858, 50.3214, 0.),
        'LEI_AUG':  (-1.127311, 52.619823, 0.),
        'LEI_MAR':  (-1.127311, 52.619823, 0.),
        'LEI':  (-1.127311, 52.619823, 0.),
        'Leicester':  (-1.127311, 52.619823, 0.),
        'Mace_head_M3': (-10.846408, 53.209003, 0.),
        'Penlee':  (-4.1858, 50.3214, 0.),
        'Penlee_M2': (-2.0229414, 49.7795272, 0.),
        'Penlee_M3': (-5.3652425, 49.8370764, 0.),
        'Penlee_M4': (-4.15,  50.25, 0.),
        'Penlee_M5': (-0.85, 50.25, 0.),
        'Penlee_M6': (-7.05, 50.25, 0.),
        'Penlee_M7': (-4.1858, 50.1, 0.),
        # - Europe sites
        'DZK':  (4.5000, 52.299999237, 4),
        # - sites with preindustrial ozone observations
        'MON':  (2.338333, 48.822222,  75+5),
        #    'MON' : (2.3, 48.8, 80), # Monsoursis
        # Pavelin  et al. (1999) / Mickely  et al. (2001)
        # 0 m. a. l. assumed following ( "<500m") in Mickely  et al. (2001)
        'ADE': (138.0, -35.0, 0),  # Adelaide
        'COI': (-8.0, 40.0, 0),  # Coimbra
        'HIR': (132.0, 34.0, 0),  # Hiroshima
        'HOB': (147.0, -43.0, 0),  # Hobart
        'HOK': (114.0, 22.0, 0),  # Hong Kong
        'LUA': (14.0, -9.0, 0),  # Luanda
        'MAU': (57.0, -20.0, 0),  # Mauritius
        'MOV': (-56.0, -35.0, 0),  # Montevideo
        'MVT': (4.0, 44.0, 1900),  # Mont-Ventoux
        'NEM': (145.0, 43.0, 0),  # Nemuro
        'TOK': (139.0, 35.0, 0),  # Tokyo
        'VIE': (16.0, 48.0, 0),  # Vienna
        'PDM': (0.0, 43.0, 1000),  # Pic du midi
        # - Miscellaneous
        #    'MAC' : ( -10.846408, 53.209003, 0 ) # Mace Head.
        'MAC': (-9.9039169999999999, 53.326443999999995, 0),  # Mace Head.
        'Mace Head': (-9.9039169999999999, 53.326443999999995, 0),  # .
        'Brittany': (-4.0, 48.7, 0),  # Brittany, France
        'Ria de Arousa': (-8.87, 42.50, 0),  # Ria de Arousa, Spain
        'Mweenish Bay': (-9.83, 53.31, 0),  # Ireland
        'Harestua': (10.7098608, 60.2008617, 0),  # Norway
        'Cartagena': (-1.0060599, 37.6174104, 0),  # Spain
        'Malasapina - final day': (-8.338, 35.179, 0),  # final day of cruise
        'Dagebull': (8.69, 54.73, 0),
        'Lilia': (-4.55, 48.62, 0),
        'Heraklion': (25.1, 35.3, 0),  # Heraklion, Crete
        'Sylt': (8.1033406, 54.8988164, 0),
        'Sicily': (14.2371407,  38.5519809, 0),  # Sicily
        #    'Frankfurt' : ( 8.45,50.22, )
        # - Global GAW sites (from GAWSIS)
        'Barrow': (-156.6114654541, 71.3230133057,  11),
        'Ascension Island': (-14.3999996185, -7.9699997902, 91),
        'Neumayer': (-8.265999794, -70.6660003662, 42),
        'Hilo': (-155.0700073242, 19.5799999237,  11),
        'Samoa': (-170.5645141602, -14.2474746704, 77),
        'Assekrem': (5.6333332062, 23.2666664124,  2710),
        # - Misc
        'UoM_Chem': (-2.2302418, 53.4659844, 38),
        'CDD': (6.83333333, 45.8333333, 4250),
        'NEEM': (-51.12, 77.75, 2484),
        'Welgegund': (26.939311,  -26.570146, 1480),
        'WEL': (26.939311,  -26.570146, 1480),  # abrev. Welgegund
        'WEL-W': (26.939311-1.5,  -26.570146, 1480),  # abrev. Welgegund
        'WEL-SW': (26.939311-1.5,  -26.570146-1.5, 1480),  # abrev. Welgegund
        'Botsalano': (25.75, -25.54, 1420),
        'BOT': (25.75, -25.54, 1420),  # abrev. Botsalano
        'Marikana': (27.48, -25.70, 1170),
        'MAR': (27.48, -25.70, 1170),  # abrev. Marikana
        'Elandsfontein': (29.42, -26.25, 1750),
        'ELA': (29.42, -26.25, 1750),  # abrev. Elandsfontein
        # - Global GAW sites
        'ASK': (5.63, 23.27, 2710.0000000000005),
        'BRW': (-156.6, 71.32, 10.999999999999746),
        'CGO': (144.68, -40.68, 93.99999999999973),
        'CMN': (10.7, 44.18, 2165.0),
        'CPT': (18.48, -34.35, 229.99999999999997),
        #        'CVO': (-24.871, 16.848, 10.000000000000103), # Already present.
        'JFJ': (7.987, 46.548, 3580.0),
        'LAU': (169.67, -45.03, 369.99999999999983),
        'MHD': (-9.9, 53.33, 4.999999999999905),
        'MLO': (-155.578, 19.539, 3397.0),
        'MNM': (153.981, 24.285, 7.999999999999767),
        'NMY': (-8.25, -70.65, 41.99999999999969),
        'SMO': (-170.565, -14.247, 77.00000000000001),
        'SPO': (-24.8, -89.98, 2810.0),
        'THD': (-124.15, 41.05, 119.99999999999997),
        # - NOAA sites
        # https://www.esrl.noaa.gov/gmd/grad/antuv/Palmer.jsp
        'Palmer Station': (64.05, -64.767, 21.),
        'PSA': (64.05, -64.767, 21.),
        # https://www.esrl.noaa.gov/gmd/dv/site/LEF.html
        'Park Falls Wisconsin': (-90.2732, 45.9451, 472.00),
        'LEF': (-90.2732, 45.9451, 472.00),
        # https://www.esrl.noaa.gov/gmd/obop/mlo/aboutus/siteInformation/kumukahi.html
        'Cape Kumukahi': (-154.82, 19.54, 15.0),
        'KUM': (-154.82, 19.54, 15.0),
        # https://www.esrl.noaa.gov/gmd/dv/site/NWR.html
        # NOTE: altitude in the GAW NetCDF is differrent (680.7339159020077m)
        'Niwot Ridge': (-105.5864, 40.0531, 3523.00),
        'NWR': (-105.5864, 40.0531, 3523.00),
        # https://gawsis.meteoswiss.ch/GAWSIS/#/search/station/stationReportDetails/487
        'Alert': (-62.3415260315, 82.4991455078, 210.),
        'ALT': (-62.3415260315, 82.4991455078, 210.),
        # https://gawsis.meteoswiss.ch/GAWSIS/#/search/station/stationReportDetails/312
        'Summit': (-38.4799995422, 72.5800018311, 3238.),
        'SUM': (-38.4799995422, 72.5800018311, 3238.),
        # https://www.esrl.noaa.gov/gmd/hats/stations/hfm.html
        # https://gawsis.meteoswiss.ch/GAWSIS/#/search/station/stationReportDetails/173
        # https://www.esrl.noaa.gov/gmd/dv/site/HFM.html
        'Havard Forest':  (-72.3000030518, 42.9000015259, 340.),
        'HFM': (-72.3000030518, 42.9000015259, 340.),
        # - ARNA locations
        'Dakar': (-17.467686, 14.716677, 22),
        'DSS': (-17.467686, 14.716677, 22),  # Dakar airport code (as above)
        'Sao Vicente Airport': (-25.0569, 16.8331, 20),
        'VXE': (-25.0569, 16.8331, 20),  # Sao Vincite code (as above)
        'Praia Airport': (-23.4939, 14.9242, 70),
        'RAI': (-23.4939, 14.9242, 70),  # Praia airport code (as above)
        # Other "nearby" airports
        'Gran Canaria Airport': (-15.386667, 27.931944, 24),
        # Gran Canaria airport code (as above)
        'LPA': (-15.386667, 27.931944, 24),
        'Lisbon Airport': (-9.134167, 38.774167, 114),
        'LIS': (-9.134167, 38.774167, 114),  # Lisbon airport code (as above)
        'Paris (Charles de Gaulle) Airport': (-2.547778, 49.009722, 119),
        'CDG': (-2.547778, 49.009722, 119),  # Paris airport code (as above)
    }
    if rtn_dict:
        return loc_dict
    else:
        return loc_dict[loc]


def site_code2name(code):
    """
    Get the full site name from a given code (e.g. GAW ID)
    """
    d = {
        'CMN': 'Monte Cimone',
        'CGO': 'Cape Grim',
        'BRW': 'Barrow',
        'HFM': 'Havard Forest',
        'SUM': 'Summit',
        'NWR': 'Niwot Ridge',
        'KUM': 'Cape Kumukahi',
        'LAU': 'Lauder',
        'ASK': 'Assekrem',
        'JFJ': 'Jungfraujoch',
        'MHD': 'Mace Head',
        'MLO': 'Mauna Loa',
        'MNM': 'Minamitorishima',
        'NMY': 'Neumayer',
        'SMO': 'Samoa',
        'SPO': 'South Pole',
        'THD': 'Trinidad Head',
        'ALT': 'Alert',
        'CPT': 'Cape Point',
        'LEF': 'Park Falls Wisconsin',
        'PSA': 'Palmer Station',
    }
    return d[code]


def sort_locs_by_lat(sites):
    """
    Order given list of sties by their latitudes
    """
    # Get info
    vars = [get_loc(s) for s in sites]  # lon, lat, alt,
    # Sort by lat, index orginal sites list and return
    lats = [i[1] for i in vars]
    slats = sorted(lats)[::-1]
    return [sites[i] for i in [lats.index(ii) for ii in slats]]


def latex_spec_name(input_x, debug=False):
    """
    Formatted (Latex) strings for species and analysis names


    Returns
    -------
    (tuple)

    Notes
    -----
     - Redundant? Can use class structure ( see species instance )
    """
    spec_dict = {
        'OIO': 'OIO', 'C3H7I': 'C$_{3}$H$_{7}$I', 'IO': 'IO', 'I': 'I',
        'I2': 'I$_{2}$', 'CH2ICl': 'CH$_{2}$ICl', 'HOI': 'HOI',
        'CH2IBr': 'CH$_{2}$IBr', 'C2H5I': 'C$_{2}$H$_{5}$I',
        'CH2I2': 'CH$_{2}$I$_{2}$', 'CH3IT': 'CH$_{3}$I',
        'IONO': 'INO$_{2}$', 'HIO3': 'HIO$_{3}$', 'ICl': 'ICl',
        'I2O3': 'I$_{2}$O$_{3}$', 'I2O4': 'I$_{2}$O$_{4}$',
        'I2O5': 'I$_{2}$O$_{5}$', 'INO': 'INO', 'I2O': 'I$_{2}$O',
        'IBr': 'IBr', 'I2O2': 'I$_{2}$O$_{2}$', 'IONO2': 'INO$_{3}$', 'HI': 'HI',
        'BrO': 'BrO', 'Br': 'Br', 'HOBr': 'HOBr', 'Br2': 'Br$_{2}$',
        'CH3Br': 'CH$_{3}$Br', 'CH2Br2': 'CH$_{2}$Br$_{2}$',
        'CHBr3': 'CHBr$_{3}$', 'O3': 'O$_{3}$', 'CO': 'CO', 'DMS': 'DMS',
        'NO': 'NO', 'NO2': 'NO$_{2}$',
        'NO3': 'NO$_{3}$', 'HNO3': 'HNO$_{3}$', 'HNO4': 'HNO$_{4}$',
        'PAN': 'PAN', 'HNO2': 'HONO', 'N2O5': 'N$_{2}$O$_{5}$',
        'ALK4': '$\geq$C4 alkanes', 'ISOP': 'Isoprene', 'H2O2': 'H$_{2}$O$_{2}$',
        'ACET': 'CH$_{3}$C(O)CH$_{3}$', 'MEK': '>C3 ketones',
        'RCHO': 'CH$_{3}$CH$_{2}$CHO',
        'MVK': 'CH$_{2}$=CHC(O)CH$_{3}$', 'MACR': 'Methacrolein',
        'PMN': 'PMN', 'PPN': 'PPN',
        'R4N2': '$\geq$C4 alkylnitrates', 'PRPE': '$\geq$C3 alkenes',
        'C3H8': 'C$_{3}$H$_{8}$', 'CH2O': 'CH$_{2}$O',
        'C2H6': 'C$_{2}$H$_{6}$', 'MP': 'CH$_{3}$OOH', 'SO2': 'SO$_{2}$',
        'SO4': 'SO${_4}{^{2-}}$', 'SO4s': 'SO${_4}{^{2-}}$ on SSA',
        'MSA': 'CH$_{4}$SO$_{3}$', 'NH3': 'NH$_{3}$', 'NH4': 'NH${_4}{^+}$',
        'NIT': 'NO${_3}{^-}$', 'NITs': 'NO${_3}{^-}$ on SSA', 'BCPI': 'BCPI',
        'OCPI': 'OCPI', 'BCPO': 'BCPO', 'OCPO': 'OCPO', 'DST1': 'DST1',
        'DST2': 'DST2', 'DST3': 'DST3', 'DST4': 'DST4', 'SALA': 'SALA',
        'SALC': 'SALC',  'HBr': 'HBr', 'BrNO2': 'BrNO$_{2}$',
        'BrNO3': 'BrNO$_{3}$', 'MPN': 'CH$_{3}$O$_{2}$NO$_{2}$',
        'ISOPN': 'ISOPN', 'MOBA': 'MOBA', 'PROPNN': 'PROPNN',
        'HAC': 'HAC', 'GLYC': 'GLYC', 'MMN': 'MMN', 'RIP': 'RIP',
        'IEPOX': 'IEPOX', 'MAP': 'MAP', 'AERI': 'Aerosol Iodine', 'Cl2': 'Cl$_{2}$',
        'Cl': 'Cl', 'HOCl': 'HOCl', 'ClO': 'ClO', 'OClO': 'OClO', 'BrCl': 'BrCl',
        'HI+OIO+IONO+INO': 'HI+OIO+INO$_{2}$+INO',
        'CH2IX': 'CH$_{2}$IX (X=Cl, Br, I)',
        'IxOy': 'I$_{2}$O$_{X}$ ($_{X}$=2,3,4)',
        'CH3I': 'CH$_{3}$I', 'OH': 'OH', 'HO2': 'HO$_{2}$', 'MO2': 'MO$_{2}$',
        'RO2': 'RO$_{2}$', 'ISALA': 'Iodine on SALA',
        'ISALC': 'Iodine on SALC', 'CH4': 'CH$_{4}$', 'MOH': 'Methanol',
        'RD01': r'I + O$_{3}$ $\rightarrow$ IO + O$_{2}$',
        # Adjusted names
        'ALD2': 'Acetaldehyde',
        # Analysis names
        'iodine_all': 'All Iodine', 'Iy': 'I$_{\\rm y}$',\
        'IOy': 'IO$_{\\rm y}$', \
        'IyOx': 'I$_{y}$O$_{x}$',
        'IOx': 'IO$_{\\rm x}$', \
        'iodine_all_A': 'All Iodine (Inc. AERI)',  \
        'I2Ox': 'I$_{2}$O$_{\\rm X}$', 'AERI/SO4': 'AERI/SO4', \
        'EOH': 'Ethanol', 'OH reactivity / s-1': 'OH reactivity / s$^{-1}$', \
        'PSURF': 'Pressure at the bottom of level', \
        'GMAO_TEMP': 'Temperature', 'TSKIN': 'Temperature at 2m', \
        'GMAO_UWND': 'Zonal Wind', 'GMAO_VWND': 'Meridional Wind', \
        'U10M': '10m Meridional Wind', 'V10M': '10m Zonal Wind', \
        'CH2OO': 'CH$_{2}$OO', 'Sulfate': 'Sulfate', 'VOCs': 'VOCs', \
        'GMAO_ABSH': 'Absolute humidity', 'GMAO_SURF': 'Aerosol surface area', \
        'GMAO_PSFC': 'Surface pressure',
        # Family/group species/tracer Names
        'N_specs': 'NO$_{\\rm y}$', 'NOy': 'NO$_{\\rm y}$',
        'Bry': 'Br$_{\\rm y}$', 'Cly': 'Cl$_{\\rm y}$', 'NIT+NITs': 'NIT+NITs',  \
        'N_specs_no_I': 'NO$_{\\rm y}$ exc. iodine', 'TSO4': 'TSO$_4$',
        'NOx': 'NO$_{\\rm x}$', 'HOx': 'HO$_{\\rm x}$', 'TNO3': 'TNO$_3$', \
        'SOx': 'SO$_{\\rm x}$', 'PM2.5': 'PM$_{2.5}$', 'VOC': 'VOC', \
        'NIT+NH4+SO4': 'NO${_3}{^-}$+NH${_4}{^+}$+SO${_4}{^{2-}}$',
        'NIT_ALL': 'NIT (all)', 'PM10': 'PM$_{10}$', 'BC': 'BC',
        # typos
        'CH2BR2': 'CH$_{2}$Br$_{2}$',\
        # Cly names
        'ClOO': 'ClOO', 'Cl2': 'Cl$_{2}$', \
        'BrCl': 'BrCl', 'ICl': 'ICl', 'HOCl': 'HOCl', 'ClO': 'ClO', 'ClOO': 'ClOO', \
        'OClO': 'OClO', 'Cl2O2': 'Cl$_{2}$O$_{2}$', 'HCl': 'HCl', \
        'ClNO2': 'ClNO$_{2}$', 'ClNO3': 'ClNO$_{3}$', 'Cl': 'Cl',\
        'CH3Cl': 'CH$_{3}$Cl',  'CH2Cl2': 'CH$_{2}$Cl$_{2}$', \
        'CHCl3': 'CHCl$_{3}$',
        # Bry names
        'BrSALC': 'Br- on SALC', 'BrSALA': 'Br- on SALA',
        # add planeflight variabels  for ease of processing
        'LON': 'Lon.', 'LAT': 'Lat.', 'PRESS': 'Press.',
        # add combined species for easy of processing
        'HOCl+Cl2': 'HOCl+Cl$_2$', 'HOBr+Br2': 'HOBr+Br$_2$',
        'HNO3/NOx': 'HNO$_3$/NO$_{\\rm x}$',
        'HNO3+NIT': 'HNO$_3$+NIT', 'HNO3+NO3': 'HNO$_3$+NO$_3$',
        'NIT/NOx': 'NIT/NO$_{\\rm x}$', 'HNO3/NIT': 'HNO$_3$/NIT',
        # Add pseudo species
        'Cl-': 'Cl$^{-}$',
        # Extra sub species from GEOS-CF
        'PM2.5(dust)': 'PM$_{2.5}$(dust)',
        'PM2.5(SO4)': 'PM$_{2.5}$(SO${_4}{^{2-}}$)',
        'PM2.5(NIT)': 'PM$_{2.5}$(NO${_3}{^-}$)',
        'PM2.5(SOA)': 'PM$_{2.5}$(SOA)',
        'PM2.5(SSA)': 'PM$_{2.5}$(SSA)',
        'PM2.5(BC)': 'PM$_{2.5}$(BC)',
        'PM2.5(OC))': 'PM$_{2.5}$(OC)',
        # Extra GEOS-chem advected tracers - in standard as of v12.9.1
        # TODO - complete expanding species
        # http://wiki.seas.harvard.edu/geos-chem/index.php/Species_in_GEOS-Chem
        'ACTA': 'ACTA', 'ATOOH': 'ATOOH', 'BENZ': 'Benzene',
        'CCl4': 'CCl4', 'CFC11': 'CFC11', 'CFC113': 'CFC113',
        'CFC114': 'CFC114', 'CFC115': 'CFC115', 'CFC12': 'CFC12',
        'CH3CCl3': 'CH3CCl3', 'ETHLN': 'ETHLN', 'ETNO3': 'ETNO3',
        'ETP': 'ETP', 'GLYX': 'GLYX', 'H1211': 'H1211',
        'H1301': 'H1301', 'H2402': 'H2402', 'H2O': 'H2O',
        'HC5A': 'HC5A', 'HCFC123': 'HCFC123', 'HCFC141b': 'HCFC141b',
        'HCFC142b': 'HCFC142b', 'HCFC22': 'HCFC22', 'HCOOH': 'HCOOH',
        'HMHP': 'HMHP', 'HMML': 'HMML', 'HONIT': 'HONIT',
        'HPALD1': 'HPALD1', 'HPALD2': 'HPALD2', 'HPALD3': 'HPALD3',
        'HPALD4': 'HPALD4', 'HPETHNL': 'HPETHNL', 'ICHE': 'ICHE',
        'ICN': 'ICN', 'ICPDH': 'ICPDH', 'IDC': 'IDC',
        'IDCHP': 'IDCHP', 'IDHDP': 'IDHDP', 'IDHPE': 'IDHPE',
        'IDN': 'IDN', 'IEPOXA': 'IEPOXA', 'IEPOXB': 'IEPOXB',
        'IEPOXD': 'IEPOXD', 'IHN1': 'IHN1', 'IHN2': 'IHN2',
        'IHN3': 'IHN3', 'IHN4': 'IHN4', 'INDIOL': 'INDIOL',
        'INPB': 'INPB', 'INPD': 'INPD', 'IONITA': 'IONITA',
        'IPRNO3': 'IPRNO3', 'ITCN': 'ITCN', 'ITHN': 'ITHN',
        'LIMO': 'LIMO', 'LVOC': 'LVOC', 'LVOCOA': 'LVOCOA',
        'MACR1OOH': 'MACR1OOH', 'MCRDH': 'MCRDH', 'MCRENOL': 'MCRENOL',
        'MCRHN': 'MCRHN', 'MCRHNB': 'MCRHNB', 'MCRHP': 'MCRHP',
        'MENO3': 'MENO3', 'MGLY': 'MGLY', 'MONITA': 'MONITA',
        'MONITS': 'MONITS', 'MONITU': 'MONITU', 'MPAN': 'MPAN',
        'MTPA': 'MTPA', 'MTPO': 'MTPO', 'MVKDH': 'MVKDH',
        'MVKHC': 'MVKHC', 'MVKHCB': 'MVKHCB', 'MVKHP': 'MVKHP',
        'MVKN': 'MVKN', 'MVKPC': 'MVKPC', 'N2O': 'N2O',
        'NPRNO3': 'NPRNO3', 'OCS': 'OCS', 'pFe': 'pFe',
        'PIP': 'PIP', 'PP': 'PP', 'PRPN': 'PRPN',
        'PYAC': 'PYAC', 'R4P': 'R4P', 'RA3P': 'RA3P',
        'RB3P': 'RB3P', 'RIPA': 'RIPA', 'RIPB': 'RIPB',
        'RIPC': 'RIPC', 'RIPD': 'RIPD', 'RP': 'RP',
        'SALAAL': 'SALAAL', 'SALACL': 'SALACL', 'SALCAL': 'SALCAL',
        'SALCCL': 'SALCCL', 'SOAGX': 'SOAGX', 'SOAIE': 'SOAIE',
        'SOAP': 'SOAP', 'SOAS': 'SOAS', 'TOLU': 'TOLU',
        'XYLE': 'Xylene',
        # Extra GEOS-chem species - in standard as of v12.9.1
        'O1D': 'O($^{1}$D)', 'O': 'O', 'hv': '$h\\nu$',
    }
    return spec_dict[input_x]


def species_mass(spec):
    """
    Function to get species relative molecular mass (RMM) in g/mol

    Parameters
    ----------
    spec (str): species/tracer/variable name

    Returns
    -------
    (float)

    Notes
    -----
     - C3H5I == C2H5I (this is a vestigle typo, left in to allow for
    use of older model run data  )
    """
    d = {
        'HIO3': 176.0, 'Br2': 160.0,  'O3': 48.0,
        'PAN': 121.0, 'RIP': 118.0, 'BrNO3': 142.0, 'Br': 80.0,
        'HBr': 81.0, 'HAC': 74.0,  'HNO3': 63.0, 'HNO2': 47.0,
        'C2H5I': 168.0, 'HNO4': 79.0, 'OIO': 159.0, 'MAP': 76.0,
        'CH2I2': 268.0, 'IONO2': 189.0, 'NIT': 62.0, 'CH3Br': 95.0,
        'C3H7I': 170.0, 'DMS': 62.0, 'CH2O': 30.0, 'CH3IT': 142.0,
        'NO2': 46.0, 'NO3': 62.0, 'N2O5': 105.0, 'H2O2': 34.0, 'DST4': 29.0,
        'DST3': 29.0, 'DST2': 29.0, 'DST1': 29.0, 'MMN': 149.0, 'HOCl': 52.0,
        'NITs': 62.0, 'RCHO': 58.0,  'MPN': 93.0, 'INO': 157.0,
        'MP': 48.0, 'CH2Br2': 174.0, 'SALC': 31.4, 'NH3': 17.0, 'CH2ICl': 167.0,
        'IEPOX': 118.0, 'ClO': 51.0, 'NO': 30.0, 'SALA': 31.4, 'MOBA': 114.0,
        'R4N2': 119.0, 'BrCl': 115.0, 'OClO': 67.0, 'PMN': 147.0, 'CO': 28.0,
        'MVK': 70.0, 'BrNO2': 126.0,
        'IONO': 173.0, 'Cl2': 71.0, 'HOBr': 97.0, 'PROPNN': 109.0, 'Cl': 35.0,
        'I2O2': 286.0, 'I2O3': 302.0, 'I2O4': 318.0, 'I2O5': 334.0,
        'HI': 128.0, 'ISOPN': 147.0, 'SO4s': 96.0, 'I2O': 270.0,
        'MSA': 96.0, 'I2': 254.0, 'PPN': 135.0, 'IBr': 207.0, 'MACR': 70.0,
        'I': 127.0, 'AERI': 127.0, 'HOI': 144.0, 'BrO': 96.0, 'NH4': 18.0,
        'SO2': 64.0, 'SO4': 96.0, 'IO': 143.0, 'CHBr3': 253.0, 'CH2IBr': 221.0,
        'ICl': 162.0, 'GLYC': 60.0, \
        # Carbon/VOC species - WARNING these are considered in units cf C equiv.
        # (following GEOS-Chem approach)
        'ALD2': 12.0, 'ACET': 12.0, 'PRPE': 12.0, 'OCPO': 12.0,  'OCPI': 12.0, \
        'C3H8': 12.0, 'C2H6': 12.0, 'BCPI': 12.0, 'ISOP': 12.0, 'BCPO': 12.0,\
        'ALK4': 12.0, 'MEK': 12.0, \
        # species, not in GEOS-Chem tracer list
        'HO2': 33.0, 'OH': 17.0, 'CH4': 16.0, 'N': 14.0, 'CH3I': 142.0, \
        'CH2OO': 46.0, 'S': 32.0, \
        # Carbon species not in GEOS-Chem
        'C2H4': 12.0,
        # Additional 2.0 species
        'HCl': 36.5, 'HOCl': 52.5, 'ClNO2': 81.5, 'ClNO3': 97.5, 'ClOO': 67.5, \
        'Cl2O2': 103.0,  'CH3Cl':  50.5, 'CH2Cl2': 85.0, 'CHCl3': 119.5, \
        'BrSALA': 80., 'BrSALC': 80., 'ISALA': 127.,  'ISALC': 127., \
        # Additional "species" to allow for ease of  processing
        'AERI_AVG': ((286.0+302.0+318.0)/3)/2, 'SO4S': 96.0,
        'IO3': 127.+(3.*16.), 'SSBr2': 160.0, 'C': 12.0,
        # Add families for ease of processing
        'Iodine': 127.0, 'Iy': 127., 'Bromine': 80.0, 'Bry': 80.0, 'Chlorine': 35.0,
        'Cly': 35.0, 'NOy': 14.0, 'NOx': 14.0, 'SOx': 32.0,\
        'Sulfate': 32.0, 'sulfur': 32.0, 'VOCs': 12.0,
        # v11-01 standard extra tracers...
        'ASOA1': 150.0, 'ASOA3': 150.0, 'ASOA2': 150.0, 'ASOG3': 150.0, \
        'ASOG2': 150.0, 'ASOG1': 150.0, 'TSOA0': 150.0, 'TSOA1': 150.0, \
        'TSOA2': 150.0, 'TSOA3': 150.0, 'TSOG2': 150.0, 'TSOG3': 150.0, \
        'TSOG0': 150.0, 'TSOG1': 150.0, 'MVKN': 149.0, 'MACRN': 149.0, \
        'MTPO': 136.0, 'ISOPND': 147.0, 'LIMO': 136.0, 'ISOPNB': 147.0, \
        'MTPA': 136.0, 'NITS': 31.0, 'ISOG3': 150.0, 'ISOG2': 150.0, \
        'ISOG1': 150.0, 'ISOA1': 150.0, 'ISOA3': 150.0, 'ISOA2': 150.0, \
        'ASOAN': 150.0,
        # more v11-01 advected tracers...
        'H2O': 18.0, 'N2O': 44.0, 'CFC11': 137.0, 'CFC12': 121.0, \
        'H1211': 165.0, 'BENZ': 78.11, 'H1301': 149.0, 'CFC114': 187.0, \
        'TOLU': 92.14, 'CH3CCl3': 133.0, 'CCl4': 152.0, 'HCFC22': 86.0, \
        'CFC113': 187.0, 'HCFC141b': 117.0, 'CFC115': 187.0, 'OCS': 60.0, \
        'XYLE': 106.16, 'H2402': 260.0, 'HCFC142b': 117.0, 'HCFC123': 117.0, \
        # Extra species in v12.x
        'GLYX': 58.0, 'MGLY': 72.0, 'SOAP': 150.0, 'SOAS': 150.0, 'NPMN': 147.0, \
        u'RIPB': 118.0, u'LVOCOA': 154.0, u'IEPOXD': 118.0, u'IEPOXB': 118.0, \
        u'IEPOXA': 118.0, u'RIPD': 118.0, u'LVOC': 154.0, u'INDIOL': 102.0, \
        u'RIPA': 118.0, u'IPMN': 147.0, u'DHDN': 226.0, u'HPALD': 116.0, \
        u'SOAGX': 58.0, u'MGLY': 72.0, u'IONITA': 14.0, u'NPMN': 147.0, \
        u'MONITS': 215.0, u'MONITU': 215.0, u'MONITA': 14.0, u'HC187': 187.0, \
        u'ISN1OG': 226.0, u'ISN1OA': 226.0, u'IMAE': 102.0, u'ETHLN': 105.0, \
        u'SOAIE': 118.0, u'HONIT': 215.0, u'GLYX': 58.0, u'SOAME': 102.0, \
        u'SOAMG': 72.0, u'HCOOH': 46.0, u'ISN1': 147.0, u'ACTA': 60.0, \
        u'SOAP': 150.0, u'SOAS': 150.0,
        # Temporary species or values where numbers not known for certain.
        'pFe': 55.85, 'EOH': 46.07,
        # Dust species
        'NITD1': 62.0, 'NITD2': 62.0, 'NITD3': 62.0, 'NITD4': 62.0,
        'SO4D1': 96.0, 'SO4D2': 96.0, 'SO4D3': 96.0, 'SO4D4': 96.0,
    }

    return d[spec]


def get_spec_properties():
    """
    Get the species properties using the GEOS-Chem json files in GCPy
    """

    pass


def spec_stoich(spec, IO=False, I=False, NO=False, OH=False, N=False,
                C=False, Br=False, Cl=False, S=False, ref_spec=None,
                debug=False):
    """
    Returns unit equivalent of X ( e.g. I ) for a given species

    Parameters
    ----------
    spec (str): species/tracer/variable name
    ref_spec (str): species which number of spec equiv. in is being sought
    wd (str): Specify the wd to get the results from a run.
    res (str): the resolution if wd not given (e.g. '4x5' )
    debug (bool): legacy debug option, replaced by python logging
    IO, I, NO, OH, N, C, Br, Cl, S (bool): reference species to use (default=I)

    Returns
    -------
    (float) number equivlent units of ref_spec in spec.

    Notes
    -----
     - This can be automatically set by providing a reference species or by
     setting boolean input parametiers.
     - Update Needed: re-write to take stioch species
     (e.g. OH, I instead of booleans )
     - asssume I == True as default
     - C3H5I == C2H5I
     (this is a vestigle typo, left in to allow for use of older model runs)
     - aerosol cycling specs
    # 'LO3_36' : (2.0/3.0) , 'LO3_37' : (2.0/4.0),  # aersol loss rxns... 'LO3_37' isn't true loss, as I2O4 is regen. temp
     - Aerosol loss rxns ( corrected stoich. for Ox, adjsutment need for I )
    """
    # If reference species provided automatically select family
    if not isinstance(ref_spec, type(None)):
        if any([(ref_spec == i) for i in ('I', 'Iy', 'Iodine')]):
            I = True
        if any([(ref_spec == i) for i in ('Br', 'Bry', 'Bromine')]):
            Br = True
        if any([(ref_spec == i) for i in ('Cl', 'Cly', 'Chlorine')]):
            Cl = True
        if any([(ref_spec == i) for i in ('C', 'VOC')]):
            C = True
        if any([(ref_spec == i) for i in ('N', 'NOy', 'NOx')]):
            N = True
        if any([(ref_spec == i) for i in ('OH', 'HO2')]):
            OH = True
        if ref_spec == 'IO':
            IO = True
        if ref_spec == 'NO':
            NO = True
        if any([(ref_spec == i) for i in ('S', 'SOx', 'Sulfate')]):
            S = True

    if debug:
        vars = ref_spec, IO, I, NO, OH, N, C, Br, Cl
        varsn = 'ref_spec', 'IO', 'I', 'N', 'OH', 'N', 'C', 'Br', 'Cl'
        print(("'spec_stoich'  called for: ", list(zip(varsn, vars))))

    # Select dictionary ( I=True is the default... )
    if IO:
        d = {
            'RD11': 2.0, 'RD10': 1.0, 'RD12': 2.0, 'LO3_36': 1./3.,
            'RD09': 1.0,
            'RD66': 1.0, 'RD23': 1.0, 'RD37': 1.0, 'LO3_24': 1.0/2.0,
            'RD56': 1.0,
            'RD01': 1.0, 'RD08': 1.0, 'RD46': 2.0, 'RD30': 1.0, 'RD25': 1.0,
            'RD27': 1.0, 'RD97': 1.0
        }
    elif NO:
        d = {
            'NO2': 1.0, 'NO3': 1.0, 'N2O5': 2.0, 'NO': 1.0, 'PPN': 1.0,
            'R4N2': 1.0,
            'BrNO3': 1.0, 'INO': 1.0, 'PAN': 1.0, 'PMN': 1.0, 'HNO3': 1.0,
            'HNO2': 1.0, 'NH3': 1.0, 'HNO4': 1.0, 'BrNO2': 1.0,
            'IONO': 1.0, 'PROPNN': 1.0, 'NH4': 1.0, 'MPN': 1.0, 'MMN': 1.0,
            'ISOPN': 1.0, 'IONO2': 1.0
        }
    elif OH:
        d = {
            'LO3_18': 2.0, 'LO3_03': 1.0,  'PO3_14': 1.0, 'RD65': 1.0,
            'LR25': 1.0,
            'LOH': 1.0, 'POH': 1.0, 'LO3_86': 1.0, 'RD98': 1.0, \
            # Redundant: 'RD95': 1.0,
            # also include HO2 and OH for HOx calculations
            'OH': 1.0, 'HO2': 1.0
        }
    elif S:
        d = {
            'S': 1.0, 'SO4': 1.0, 'SO4s': 1.0, 'SO4S': 1.0, 'SO2': 1.0,
            'DMS': 1.0,
            'SO4D1': 1.0, 'SO4D2': 1.0, 'SO4D3': 1.0, 'SO4D4': 1.0,
        }
    elif N:
        d = {
            'RD10': 1.0, 'LR26': 1.0, 'LR27': 1.0, 'LR20': 1.0, 'RD17': 1.0,
            'RD16': 1.0, 'RD19': 1.0, 'RD18': 2.0, 'LR28': 1.0, 'LO3_30': 1.0,
            'RD75': 1.0, 'LR7': 1.0, 'LR8': 1.0, 'RD56': 1.0, 'RD24': 1.0,
            'LO3_39': 1.0, 'RD25': 1.0, 'RD81': 1.0, 'LR35': 1.0, 'LR18': 1.0,
            'LR17': 1.0, 'LR11': 1.0, 'LR39': 1.0, 'RD20': 1.0, 'RD21': 2.0,
            'RD22': 1.0, 'RD23': 1.0, 'RD68': 1.0, 'RD69': 1.0, \
            # NOy ( N in 'NOy')
            'NO2': 1.0, 'NO3': 1.0, 'N2O5': 2.0, 'NO': 1.0, 'PPN': 1.0, \
            'R4N2': 2.0, 'BrNO3': 1.0, 'INO': 1.0, 'PAN': 1.0, 'PMN': 1.0, \
            'HNO3': 1.0, 'HNO2': 1.0, 'NH3': 1.0, 'HNO4': 1.0, 'BrNO2': 1.0, \
            'IONO': 1.0, 'PROPNN': 1.0, 'NH4': 1.0, 'MPN': 1.0, 'MMN': 1.0, \
            'ISOPN': 1.0, 'IONO2': 1.0, 'ClNO2': 1.0, 'ClNO3': 1.0,
            'NIT': 1.0, 'NITs': 1.0, 'NITS': 1.0, \
            #
            'NITD1': 1.0, 'NITD2': 1.0, 'NITD3': 1.0, 'NITD4': 1.0,
        }
    elif C:
        d = {
            'ACET': 3.0, 'ALD2': 2.0, 'C2H6': 2.0, 'C3H8': 3.0, 'ISOP': 5.0,
            'PRPE': 3.0, 'ALK4': 4.0, 'MEK': 4.0,
            'APINE': 10.0, 'BPINE': 10.0, 'LIMON': 10.0, 'SABIN': 10.0,
            'MYRCN': 10.0,
            'CAREN': 10.0, 'OCIMN': 10.0, 'XYLE': 8.0,
        }
    elif Br:
        d = {
            'CH3Br': 1.0, 'HOBr': 1.0, 'BrO': 1.0, 'CHBr3': 3.0, 'Br2': 2.0,
            'BrSALC': 1.0, 'CH2IBr': 1.0, 'BrCl': 1.0, 'Br': 1.0,
            'CH2Br2': 2.0,
            'IBr': 1.0, 'BrSALA': 1.0, 'BrNO2': 1.0, 'BrNO3': 1.0, 'HBr': 1.0,
            # for ease of processing also include Seasalt Br2
            'SSBr2': 2.0,
            # Also have reaction tracers
            'LR73': 1.0,
            # Note: stoichometry is for **GAS** phase Br (aka not SSA )
            # ( Aka JT03s == Br2 ( ==2 ), but one is BrSALA/BrSALC therefore =1)
            'JT03s': 1.0, 'JT04s': 1.0, 'JT05s': 1.0,
            # BrCl from HOBr or hv
            'JT02s': 1.0, 'JT08': 1.0,
            # v11 KPP Tags
            'T149': 3.0, 'T127': 0.680+1.360, 'T126': 0.440+0.560, 'T071': 3.0,
            'T198': 0.150, 'T199': 0.150, 'T200': 0.150, 'T082': 1.0
        }
    elif Cl:
        d = {
            'ClO': 1.0, 'Cl': 1.0, 'ClOO': 1.0, 'ClNO3': 1.0, 'ClNO2': 1.0,
            'Cl2': 2.0, 'OClO': 1.0, 'HOCl': 1.0, 'HCl': 1.0, 'Cl2O2': 2.0,
            'BrCl': 1.0, 'ICl': 1.0, 'CH2Cl2': 2.0, 'CHCl3': 3.0,
            'CH2ICl': 1.0,
            'CH3Cl': 1.0,
            # Also have reaction tracers
            'LR62': 3.0, 'LR107': 3.0,
            'LR74': 1.0, 'LR106': 1.0, 'LR103': 1.0,
            'LR75': 2.0, 'LR105': 2.0, 'LR104': 2.0,
            # BrCl from HOBr or hv
            'JT02s': 1.0, 'JT08': 1.0,
            # ICl  (assuming 0.85:0.15 )
            'RD59': 0.15, 'RD92': 0.15, 'RD63': 0.15,
            # N2O5+SSA=>ClNO2
            'LR114': 1.0,
            # v11 KPP Tags
            'T174': 3.0, 'T203': 3.0,
            'T173': 2.0, 'T201': 2.0, 'T202': 2.0,
            'T172': 1.0, 'T171': 1.0, 'T143': 1.0,
            'T155': 1.0, 'T135': 1.0, 'T212': 1.0,
            'T198': 0.850, 'T199': 0.850, 'T200': 0.850,
            'PT213': 1.0, 'PT214': 1.0,
        }
    else:  # ( I=True is the default... )
        d = {
            'RD11': 1.0, 'RD10': 1.0, 'HIO3': 1.0, 'RD15': 1.0, 'RD62': 2.0,
            'RD17': 1.0, 'RD16': 1.0, 'RD19': 1.0, 'LO3_37': 0.5, 'CH2I2': 2.0,
            'AERII': 1.0, 'CH2ICl': 1.0, 'PIOx': 1.0, 'C3H7I': 1.0,
            'RD73': 1.0,
            'RD72': 2.0, 'RD71': 1.0, 'RD70': 1.0, 'C3H5I': 1.0, 'RD57': 1.0,
            'CH3IT': 1.0, 'IO': 1.0, 'LO3_38': 1.0, 'RD61': 1.0, 'RD68': 1.0,
            'I2': 2.0, 'IONO': 1.0, 'LO3_36': 0.6666666666666666, 'INO': 1.0,
            'RD88': 1.0, 'RD89': 1.0, 'LOx': 1.0, 'RD06': 1.0, 'RD07': 1.0,
            'RD02': 1.0, 'RD01': 1.0, 'I': 1.0,  'LO3_24': 0.5, 'AERI': 1.0,
            'HOI': 1.0, 'RD64': 2.0, 'RD65': 1.0, 'RD66': 1.0, 'RD67': 1.0,
            'RD60': 1.0, 'RD47': 1.0, 'C2H5I': 1.0, 'RD63': 1.0, 'RD20': 1.0,
            'RD22': 1.0, 'RD24': 1.0, 'RD69': 1.0, 'RD27': 1.0, 'OIO': 1.0,
            'CH2IBr': 1.0, 'LIOx': 1.0, 'L_Iy': 1.0, 'ICl': 1.0, 'IBr': 1.0,
            'RD95': 2.0, 'I2O2': 2.0, 'I2O3': 2.0, 'I2O4': 2.0, 'I2O5': 2.0,
            'HI': 1.0, 'I2O': 2.0, 'RD59': 1.0, 'RD93': 2.0, 'RD92': 1.0,
            'IONO2': 1.0, 'RD58': 1.0, 'ISALA': 1.0, 'ISALC': 1.0, 'CH3I': 1.0, \
            # p/l for: IO, I
            'RD15': 1.0, 'RD17': 1.0, 'RD75': 1.0, 'RD72': 2.0, 'RD71': 1.0, \
            'RD70': 1.0, 'RD56': 1.0, 'RD69': 1.0, 'RD88': 1.0, 'RD89': 1.0, \
            'RD06': 1.0, 'RD07': 1.0, 'RD08': 1.0, 'RD64': 2.0, 'RD65': 1.0, \
            'RD67': 1.0, 'RD46': 2.0, 'RD47': 1.0, 'RD20': 1.0, 'RD22': 1.0, \
            'RD68': 1.0, 'RD25': 1.0, 'RD96': 1.0, 'RD11': 1.0, 'RD12': 2.0, \
            'RD02': 1.0, 'RD16': 1.0, 'RD19': 1.0, 'RD24': 1.0, 'RD09': 1.0, \
            'RD23': 1.0, 'RD37': 1.0, 'RD97': 1.0, \
            # kludge for test analysis (HEMCO emissions )
            'ACET': 1.0, 'ISOP': 1.0, 'CH2Br2': 1.0, 'CHBr3': 1.0,
            'CH3Br': 1.0, \
            # Iodine in het loss/cycling reactions
            # loss to SSA/other aerosols
            # HOI
            'LR44': 1.0, 'LR45': 1.0, 'LR32': 1.0,   \
            # HI other
            'LR34': 1.0, \
            # IONO2
            'LR42': 1.0, 'LR43': 1.0, 'LR35': 1.0, \
            # IONO
            'LR46': 1.0, 'LR47': 1.0, 'LR39': 1.0,
            # --- KPP tags
            # Iy cycling sinks...
            'T217': 1.0, 'T216': 1.0, 'T198': 1.0, 'T199': 1.0, 'T196': 1.0,
            'T183': 1.0, 'T195': 1.0, 'T184': 1.0,  'T215': 1.0, 'T197': 1.0,
            # I2Oy
            'T190': 2.0, 'T193': 2.0, 'T187': 2.0,
            'T186': 2.0, 'T189': 2.0, 'T192': 2.0,
            'T185': 2.0, 'T188': 2.0, 'T191': 2.0,
        }

    # Kludge for testing. Allow values to equal 1.0 if not defined.
    try:
        if debug:
            prt_str = '{} (ref_spec: {}) stoichiometry : {}'
            print((prt_str.format(spec, ref_spec,  d[spec])))
        return d[spec]

    except:
        prt_str = '!!!!!!! WARNING - Kludge assumming stoichiometry = 1.0, for'
        prt_str += ' {} (ref_spec given as: {})'
        print((prt_str.format(spec, ref_spec)))
        return 1.0


def tra_unit(x, scale=False, adjustment=False, adjust=True, global_unit=False,
             ClearFlo_unit=False, IUPAC_unit=False, use_pf_species_units=False,
             debug=False):
    """
    Get appropirate unit for Tracer (and scaling if requested)

    Parameters
    ----------
    x (str): species/tracer/variable name
    adjustment (float): adjustment to give unit (+,- value etc )
    scale (float): scaling factor for unit
    adjust (bool): set==True to adjust input.geos unit values to adjusted values
    global_unit (bool): set units to globally relevent ones
    IUPAC_unit (bool): set units to IUPAC uints
    ClearFlo_unit (bool): set units to those used in the ClearFlo campaign
    debug (bool): legacy debug option, replaced by python logging

    Returns
    -------
    units (str), adjustment to give units (float), and scaling for units (float)

    Notes
    -----
     - Is this redundant now with the species class?
     - "Appropirate" unit is taken from GEOS-Chem input.geos
     - Option to use IUPAC unit. ( set IUPAC_unit==True )
    """
    tra_unit = {
        'OCPI': 'ppbv', 'OCPO': 'ppbv', 'PPN': 'ppbv', 'HIO3': 'pptv',
        'O3': 'ppbv', 'PAN': 'ppbv', 'ACET': 'ppbC', 'RIP': 'ppbv',
        'BrNO3': 'pptv', 'Br': 'pptv', 'HBr': 'pptv', 'HAC': 'ppbv',
        'ALD2': 'ppbC', 'HNO3': 'ppbv', 'HNO2': 'ppbv', 'C2H5I': 'pptv',
        'HNO4': 'ppbv', 'OIO': 'pptv', 'MAP': 'ppbv', 'PRPE': 'ppbC',
        'HI': 'pptv', 'CH2I2': 'pptv', 'IONO2': 'pptv', 'NIT': 'ppbv',
        'CH3Br': 'pptv', 'C3H7I': 'pptv', 'C3H8': 'ppbC', 'DMS': 'ppbv',
        'CH2O': 'ppbv', 'CH3IT': 'pptv', 'NO2': 'ppbv', 'NO3': 'ppbv',
        'N2O5': 'ppbv', 'CHBr3': 'pptv', 'DST4': 'ppbv', 'DST3': 'ppbv',
        'DST2': 'ppbv', 'DST1': 'ppbv', 'HOCl': 'ppbv', 'NITs': 'ppbv',
        'RCHO': 'ppbv', 'C2H6': 'ppbC', 'MPN': 'ppbv', 'INO': 'pptv',
        'MP': 'ppbv', 'CH2Br2': 'pptv', 'SALC': 'ppbv', 'NH3': 'ppbv',
        'CH2ICl': 'pptv', 'IEPOX': 'ppbv', 'ClO': 'ppbv', 'NO': 'pptv',
        'SALA': 'ppbv', 'MOBA': 'ppbv', 'R4N2': 'ppbv', 'BrCl': 'pptv',
        'OClO': 'ppbv', 'PMN': 'ppbv', 'CO': 'ppbv', 'CH2IBr': 'pptv',
        'ISOP': 'ppbC', 'BCPO': 'ppbv', 'MVK': 'ppbv', 'BrNO2': 'pptv',
        'IONO': 'pptv', 'Cl2': 'ppbv', 'HOBr': 'pptv', 'PROPNN': 'ppbv',
        'Cl': 'ppbv', 'I2O2': 'pptv', 'I2O3': 'pptv', 'I2O4': 'pptv',
        'I2O5': 'pptv', 'MEK': 'ppbC', 'MMN': 'ppbv', 'ISOPN': 'ppbv',
        'SO4s': 'ppbv', 'I2O': 'pptv', 'ALK4': 'ppbC', 'MSA': 'ppbv',
        'I2': 'pptv', 'Br2': 'pptv', 'IBr': 'pptv', 'MACR': 'ppbv', 'I': 'pptv',
        'AERI': 'pptv', 'HOI': 'pptv', 'BrO': 'pptv', 'NH4': 'ppbv',
        'SO2': 'ppbv', 'SO4': 'ppbv', 'IO': 'pptv', 'H2O2': 'ppbv',
        'BCPI': 'ppbv', 'ICl': 'pptv', 'GLYC': 'ppbv', 'ISALA': 'pptv',
        'ISALC': 'pptv',
        # Extra diagnostics to allow for simplified processing
        'CH3I': 'pptv', 'Iy': 'pptv', 'PSURF': 'hPa', 'OH': 'pptv', 'HO2': 'pptv', \
        'MO2': 'pptv', 'NOy': 'ppbv', 'EOH': 'ppbv', 'CO': 'ppbv', 'CH4': 'ppbv', \
        'TSKIN': 'K', 'GMAO_TEMP': 'K', 'GMAO_VWND': 'm/s',\
        'GMAO_UWND': 'm/s', 'RO2': 'pptv', 'U10M': 'm/s', 'V10M': 'm/s',\
        'PRESS': 'hPa', 'CH2OO': 'pptv', 'Bry': 'ppbv', 'NOx': 'ppbv', 'HOx': 'HOx',
        'VOC': 'ppbC', 'TNO3': 'ppbv', 'GLYX': 'pptv',
        'GMAO_SURF': 'surface area',  # cm2/cm3?
        'GMAO_ABSH': 'frac.',
        'GMAO_PSFC': 'hPa',
        # Extra ClearFlo compounds
        'acetylene': 'pptv', 'propene': 'pptv', 'Napthalene': 'pptv', \
        'Styrene': 'pptv', '1,3-butadiene': 'pptv', '1,2-butadiene': 'pptv', \
        'iso-butene': 'pptv', 'm+p-xylene': 'pptv', '1-butene': 'pptv', \
        't-2 pentene': 'pptv', 'cis-2-butene': 'pptv', '1  pentene': 'pptv', \
        'Trans-2-butene': 'pptv', 'o-xylene': 'pptv',\
        'iso-pentane': 'pptv', 'n-hexane': 'pptv',  \
        'iso-butane': 'pptv', 'Nonane, 2-methyl-': 'pptv', \
        'Butane, 2,2,3-trimethyl-': 'pptv', 'Dodecane': 'pptv', \
        'Pentane, 2,2,4-trimethyl-': 'pptv', '2,3methylpentane': 'pptv', \
        'Nonane': 'pptv', 'cyclopentane': 'pptv', 'n- heptane': 'pptv', \
        'n-butane': 'pptv', 'n-pentane': 'pptv', 'Undecane': 'pptv', \
        'Decane': 'pptv', 'Octane': 'pptv', 'n-octane': 'pptv',\
        # Extra Cly species
        'ClNO2': 'pptv', 'ClNO3': 'pptv', 'HCl': 'pptv', 'ClOO': 'pptv', \
        'Cl2O2': 'pptv', 'CH2Cl2': 'pptv', 'CHCl3': 'pptv', 'CH3Cl': 'pptv', \
        'BrSALA': 'pptv', 'BrSALC': 'pptv', 'Cly': 'pptv', \
        # extra tag "species" for easy of processing
        'PD421': 'molec cm$^{-3}$ s$^{-1}$',
        # add planeflight variabels for ease of processing
        'LON': '$^{\circ}$E', 'LAT': '$^{\circ}$N', 'PRESS': 'hPa',
        # add combined species for easy of processing
        'HOCl+Cl2': 'pptv', 'HOBr+Br2': 'pptv',
        # add derivative species for easy of processing
        'HNO3/NOx': 'pptv', 'HNO3+NIT': 'pptv', 'HNO3+NO3': 'pptv',
        'NIT/NOx': 'pptv', 'HNO3/NIT': 'pptv',
        #
        'Cl-': 'pptv', 'pFe': 'pptv',
        # PM
        'PM10': '$\mu$g m$^{-3}$', 'PM2.5': '$\mu$g m$^{-3}$',
        'PM2.5(dust)': '$\mu$g m$^{-3}$',
        'PM2.5(SO4)': '$\mu$g m$^{-3}$',
        'PM2.5(NIT)': '$\mu$g m$^{-3}$',
        'PM2.5(SOA)': '$\mu$g m$^{-3}$',
        'PM2.5(SSA)': '$\mu$g m$^{-3}$',
        'PM2.5(BC)': '$\mu$g m$^{-3}$',
        'PM2.5(OC)': '$\mu$g m$^{-3}$',
        'PM': '$\mu$g m$^{-3}$',
    }
    try:
        units = tra_unit[x]
    except KeyError:
        LogStr = 'provided species/tracer ({}) not in unit dictionary (assuming {})'
        units = 'pptv'
        logging.info(LogStr.format(x, units))

    # Adjust to appropriate scale for pf analysis
    if adjust:
        spec_2_pptv = GC_var('spec_2_pptv')
        spec_2_pptC = GC_var('spec_2_pptC')
        if (x in spec_2_pptv):
            if debug:
                print(('adjusting {} ({}) to {}'.format(x, units, 'pptv')))
            units = 'pptv'
        if (x in spec_2_pptC):
            if debug:
                print(('adjusting {} ({}) to {}'.format(x, units, 'pptC')))
            units = 'pptC'

    # Over ride adjustments for globally appro. units
    if global_unit:
        spec_2_ppbv = GC_var('spec_2_ppbv')
        spec_2_ppbC = GC_var('spec_2_ppbC')
        if (x in spec_2_ppbv):
            if debug:
                print(('adjusting {} ({}) to {}'.format(x, units, 'ppbv')))
            units = 'ppbv'
        if (x in spec_2_ppbC):
            if debug:
                print(('adjusting {} ({}) to {}'.format(x, units, 'ppbC')))
            units = 'ppbC'

    if ClearFlo_unit:
        units2ppbv = ['NO', 'MACR', 'MVK', 'PRPE', 'ALK4', 'ALD2']
        if any([x == i for i in units2ppbv]):
            units = 'ppbv'
        if any([x == i for i in ['PAN', ]]):
            units = 'pptv'
        if any([x == i for i in ['ISOP']]):
            units = 'ppbC'

    if use_pf_species_units:
        TRA_v10_species = [
            'A3O2', 'ATO2', 'B3O2', 'EOH', 'ETO2', 'ETP', 'GLYX', 'HO2', 'IAP', 'INO2', 'INPN', 'ISN1', 'ISNOOA', 'ISNOOB', 'ISNOHOO', 'ISNP', 'KO2', 'MAN2', 'MAO3', 'MAOP', 'MAOPO2', 'MCO3', 'MGLY', 'MO2', 'MRO2', 'MRP', 'OH', 'PO2', 'PP', 'PRN1', 'PRPN', 'R4N1', 'R4O2', 'R4P', 'RA3P', 'RB3P', 'RCO3', 'RIO2', 'ROH', 'RP', 'VRO2', 'VRP', 'LISOPOH', 'ISOPND', 'ISOPNB', 'HC5', 'DIBOO', 'HC5OO', 'DHMOB', 'MOBAOO', 'ISOPNBO2', 'ISOPNDO2', 'ETHLN', 'MACRN', 'MVKN', 'PYAC', 'IEPOXOO', 'ATOOH', 'PMNN', 'MACRNO2', 'PMNO2'
        ]
        if (x in TRA_v10_species):
            units = 'molec/cm3'

    if scale:
        scaleby = get_unit_scaling(units)

    if adjustment:
        if units == 'K':
            units = 'Deg. Celcuis'
            adjustby = -273.15
        else:
            adjustby = 0

    if IUPAC_unit:
        if units == 'ppbv':
            units = 'nmol mol$^{-1}$'
        if units == 'ppbC':
            units = 'nmol (C) mol$^{-1}$'
        if units == 'pptv':
            units = 'pmol mol$^{-1}$'
        if units == 'pptC':
            units = 'pmol (C) mol$^{-1}$'

    if scale and (not adjustment):
        return units, scaleby
    elif (scale and adjustment):
        return units, scaleby, adjustby
    else:
        return units


def get_ref_spec(spec='LIOx'):
    """
    Store of reference species for families

    Parameters
    ----------
    spec (str): species/tracer/variable name

    Returns
    -------
    ref_spec (str) reference species for a given family

    Notes
    -----
    This is for use in conbination  with functions that calculate relative values
    (e.g. in units of Ox, I, etc)
    """
    d = {
        'Cly': 'Cl',
        'Cl': 'Cl',
        'LOx': 'O3',
        'POx': 'O3',
        'LOX': 'O3',
        'POX': 'O3',
        'LIOx': 'I',
        'PIOx': 'I',
        'PClOx': 'Cl',
        'LClOx': 'Cl',
        'PClOxI': 'Cl',
        'LClOxI': 'Cl',
        'PClOxII': 'Cl',
        'LClOxII': 'Cl',
        'PClOxI': 'Cl',
        'LCI': 'Cl',
        'LCII': 'Cl',
        'PBrOx': 'Br',
        'LBrOx': 'Br',
        'Br': 'Br',
        'Bry': 'Br',
        'I': 'I',
        'Iy': 'I',
        'IxOy': 'I',
        # core species
        'SO4': 'S',
        'NIT': 'N',
        'NITs': 'N',
        'NH4': 'N',
        'ISOP': 'C',
        'NO': 'N',
        'NO2': 'N',
        'N2O5': 'N',
        'O3': 'O3',
        'SO2': 'S',
        # Other VOCs
        'ACET': 'C',
        'ALD2': 'C',
        'DMS': 'S',
        # include halogens
        'HOI': 'I',
        'I2': 'I',
        'CH3I': 'I',
        'CH3IT': 'I',  # Vestigle spec from v10 (is CH3I)...
        'CH2I2': 'I',
        'CH2IBr': 'I',
        'CH2ICl': 'I',
        'CHBr3': 'Br',
        'CH2Br2': 'Br',
        'CH3Br': 'Br',
        'CH2Cl2': 'Cl',
        'CHCl3': 'Cl',
        'CH3Cl': 'Cl',
        'HCl': 'Cl',
        'HBr': 'Br',
    }
    try:
        return d[spec]
    except KeyError:
        pstr = "WARNING: Just returning provided species ('{}') as ref_spec"
        print(pstr.format(spec))
        return spec


def GC_var(input_x=None, rtn_dict=False, debug=False):
    """
    General Dictionary to manage common variables used by GC
    analysis programmes.

    Parameters
    ----------
    input_x (str): species/tracer/variable/etc name

    Returns
    -------
    values (e.g. list) from dictionary store

    Notes
    -----
     - A lot of this dictionary is vestigial. consider removing entirely?
        or moving to redundant section
     - Variables includes:
    f_var = GC flux (EW, NS , UP) variables
    Ox = 'Ox', 'POX', 'LOX' + list of drydep species
    ( # not inc. 'NO3df', 'HNO4df', 'BrOdf' , 'BrNO2', 'IO', 'IONO', 'OIO', )
    Ox_p = Ox prod list
    Ox-l = Ox loss list
    d_dep  = dry dep (category, name = species)
    w_dep  = wet dep ( 3x categories
    ( WETDCV = rain out loss in convective updrafts (kg/s),
    WETDLS = rainout in large scale precip (kg/s),
    CV-FLX = Mass change due to cloud convection (kg/s); name = species)
    BL_m = UPWARD MASS FLUX FROM BOUNDARY-LAYER MIXING,
    (category, name = species)
    f_strat  = strat flux (to tropsosphere) (category, name = species)
    """
    if debug:
        print('GC_var called for {}'.format(input_x))
    GC_var_dict = {
        # --- Ox budget analysis
        'f_var': ['EW-FLX-$', 'NS-FLX-$', 'UP-FLX-$'],
        'r_t': ['Photolysis', 'HOx', 'Bromine', 'Iodine'],
        'r_tn': ['Photolysis', 'HOx', 'Bromine', 'Iodine'],
        'r_tn_lc': ['photolysis', 'HOx', 'bromine', 'iodine'],
        # Ox loss families inc. Cly
        'r_tn_Cly': ['Photolysis', 'HOx', 'Chlorine', 'Bromine', 'Iodine'],
        'r_tn_lc_Cly': ['photolysis', 'HOx', 'chlorine', 'bromine', 'iodine'],
        'fams': ['I2', 'HOI', 'IO', 'I', 'HI+OIO+IONO+INO', 'IONO2', 'IxOy', \
                 'CH3I', 'CH2IX'],
        # Iy families + AERI
        'fams_A':  ['I2', 'HOI', 'IO', 'I', 'HI+OIO+IONO+INO', 'IONO2', \
                    'IxOy', 'CH3I', 'CH2IX', 'AERI'],
        # List slices
        'fam_slice': [(0, 1), (1, 2), (2, 3), (3, 4), (4, 8), (8, 9), (9, 12), \
                      (12, 13), (13, None)],
        'fam_slice_A': [(0, 1), (1, 2), (2, 3), (3, 4), (4, 8), (8, 9), (9, 12), \
                        (12, 13), (13, 16), (16, None)],
        # POx lists - redundant?
        #   'POx_l_fp' : ['PO3_01', 'PO3_03', 'PO3_02', 'PO3_05','PO3_14',\
        #     'PO3_15', 'PO3_18', 'PO3_19', 'PO3_20', 'PO3_21', 'PO3_22', \
        #     'PO3_24', 'PO3_25', 'PO3_26', 'PO3_27', 'PO3_30', 'PO3_31', \
        #     'PO3_32', 'PO3_33', 'PO3_34', 'PO3_35', 'PO3_37', 'PO3_38', 'PO3_39', \
        #     'PO3_40', 'PO3_41', 'PO3_43'],
        'Ox_key': ['POX', 'PO3_14', 'PO3_15',   'LOX'],
        # , 'LO3_18', 'LO3_03', 'LO3_02','LR25', 'LR21', 'LR5','LR6','LO3_34', 'LO3_33','LO3_24', 'LO3_35'  ],
        'POxLOx': ['POX', 'LOX'],
        'iPOxiLOx': ['POX', 'LOX', 'iPOX', 'iLOX'],
        # --- Iy/ Iodine budget analysis
        'BL_FT_UT': [(0, 6), (6, 26), (26, 38)],
        'n_order': ['CH2IX', 'CH3I', 'I2', 'HOI', 'IO', 'I', 'IONO2', \
                    'HI+OIO+IONO+INO', 'IxOy'],
        'n_order_A': ['CH2IX', 'CH3I', 'I2', 'HOI', 'IO', 'I', 'IONO2', \
                      'HI+OIO+IONO+INO', 'IxOy', 'AERI'],
        'I_l': ['RD01', 'RD02', 'RD16', 'RD19', 'RD24', 'RD27'],
        # LO37 swaped for RD97 as LO37 assigned to loss point of I2O3 uptake
        'IO_l': ['RD09', 'RD10', 'RD11', 'RD12', 'RD23', 'LO3_24', 'RD37', \
                 'RD97', 'RD66'],
        'I_p': [ \
            'RD06', 'RD07', 'RD10', 'RD11', 'RD47', 'RD15', 'RD17', 'RD20', 'RD22',\
            'LO3_24', 'RD64', 'RD65', 'RD66', 'RD67', 'RD68', 'RD69', 'RD70', \
            'RD71', 'RD72', 'RD73', 'RD88', 'RD89'],
        'IO_p': ['RD01', 'RD08', 'RD46', 'RD25', 'RD27', 'RD56'],
        'sOH': ['LO3_18'],
        'd_dep': ['DRYD-FLX'],
        'w_dep': ['WETDCV-$', 'WETDLS-$'],
        'BL_m': ['TURBMC-$'],
        'f_strat': ['STRT-FL'],
        'p_l': ['PORL-L=$'],
        'Cld_flx': ['CV-FLX-$'],
        'I_Br_O3': [ \
            'IO', 'OIO', 'HOI', 'I2', 'I', 'CH3IT', 'CH2I2', 'CH2ICl', \
            'CH2IBr', 'C3H7I', 'C2H5I', 'BrO', 'Br', 'HOBr', 'Br2',\
            'CH3Br', 'CH2Br2', 'CHBr3', 'O3', 'CO', ],
        'IOrg_RIS': [ \
            'CH3IT', 'CH2ICl', 'CH2I2', 'CH2IBr', 'I2', 'HOI', 'I', 'IO', \
            'OIO', 'HI', 'IONO', 'IONO2'],
        'I_specs': [ \
            'I2', 'HOI', 'IO', 'OIO', 'HI', 'IONO', 'IONO2', 'I2O2', \
            'I2O3', 'I2O4''CH3IT', 'CH2I2', 'I', 'INO'],
        'Iy': [ \
            'I2', 'HOI', 'IO', 'OIO', 'HI', 'INO', 'IONO', 'IONO2', 'I2O2', \
            'I2O3', 'I2O4', 'I', ]+['ICl', 'IBr'],
        'IxOy': ['IO', 'OIO',  'I2O2', 'I2O3', 'I2O4'],
        'Iy+AERO': [ \
            'I2', 'HOI', 'IO', 'OIO', 'HI', 'INO', 'IONO', 'IONO2', 'I2O2', \
            'I2O3', 'I2O4', 'I', ]+['ICl', 'IBr']+['AERI', 'ISALA', 'ISALC'],
        'Iy1.1': [ \
            'I2', 'HOI', 'IO', 'OIO', 'HI', 'IONO', 'IONO2', 'I2O2', \
            'I2O4', 'I', 'INO'],
        'IOy': [ \
            'HOI', 'IO', 'OIO', 'IONO', 'IONO2', 'INO', 'I2O2', \
            'I2O4', 'I2O3'],
        'IOy1.1': [\
            'HOI', 'IO', 'OIO', 'IONO', 'IONO2', 'INO', 'I2O2', 'I2O4'],
        'I2Ox': ['I2O2', 'I2O4', 'I2O3'],
        'IyOx1.1': ['I2O2', 'I2O4'],
        'Iy_no_i2o4': [ \
            'I2', 'HOI', 'IO', 'OIO', 'HI', 'IONO', 'IONO2', 'I2O2', 'I', 'INO', \
            'I2O3'],
        'Iy_no_i2o41.1': [ \
            'I2', 'HOI', 'IO', 'OIO', 'HI', 'IONO', 'IONO2', 'I2O2', 'I', 'INO'],
        'Phot_s_Iy': ['CH3IT', 'CH2ICl', 'CH2I2', 'CH2IBr'],
        #['RD89', 'RD88', 'RD71', 'RD72'],
        'HOI': ['HOI'],
        'IOx': ['IO', 'I', ],
        'IO': ['IO'],
        'I': ['I', ],
        'OIO': ['OIO'],
        # LOx is p/l tracer name, for Loss of IOx
        'LIOx': ['LIOx'],
        # LOx is p/l tracer name, for Loss of IOx
        'PIOx': ['PIOx'],
        'iodine_all': ['I2', 'HOI', 'IO', 'I', 'HI', 'OIO', 'INO', \
                       'IONO', 'IONO2', 'I2O2', 'I2O4', 'I2O3', 'I2O5', 'CH3IT',\
                       'CH2I2', 'CH2ICl', 'CH2IBr', 'C3H7I', 'C2H5I', 'ICl', 'I2O', \
                       'IBr', 'HIO3', ],
        'iodine_all_A': ['I2', 'HOI', 'IO', 'I', 'HI', 'OIO', 'INO', \
                         'IONO', 'IONO2', 'I2O2', 'I2O4', 'I2O3', 'I2O5', 'CH3IT', \
                         'CH2I2', 'CH2ICl', 'CH2IBr', 'C3H7I', 'C2H5I', 'ICl', 'I2O', \
                         'IBr', 'HIO3', 'AERI'],
        'iodine_all_A_v2': [
            'I2', 'HOI', 'IO', 'I', 'HI', 'OIO', 'INO',  'IONO', \
            'IONO2', 'I2O2', 'I2O4', 'I2O3', 'CH3IT', 'CH2I2', \
            'CH2ICl', 'CH2IBr', 'ICl', 'IBr', 'AERI', 'ISALA', 'ISALC'],
        # Misc analysis
        'LHOI': ['RD65', 'RD63', 'RD08'],
        'LHOBr': ['LR25', 'LR30', 'LR21'],
        'LI2': ['RD64', 'RD06', 'RD22'],
        'LCH2I2': ['RD72'],
        'LCH2Cl': ['RD88'],
        'LCH2Br': ['RD89'],
        'LCH3IT': ['RD15', 'RD71'],
        'sHOX': ['HOI', 'HOBr'],
        'HO2_loss': [\
            'PO3_14', 'RD09', 'RD02', 'LR2', 'LR3', 'PO3_46', 'PO3_02', 'PO3_03', \
            'PO3_05'],
        'CAST_int': [ \
            'IO', 'OIO', 'HOI', 'I2', 'I', 'HOI', 'CH3I', 'CH2I2', 'CH2ICl', 'CH2IBr',\
            'C3H7I', 'C3H5I', 'BrO', 'Br', 'HOBr', 'Br2', 'CH3Br', 'CH2Br2', \
            'CHBr3', 'O3', 'CO', 'OH', 'HO2', 'NO', 'NO2'],
        'CAST_intn': [\
            'IO', 'OIO', 'HOI', ' I2', 'I', 'HOI', 'CH3IT', 'CH2I2', 'CH2ICl', \
            'CH2IBr', 'C3H7I', 'C2H5I', 'BrO', 'Br', 'HOBr', 'Br2', 'CH3Br', \
            'CH2Br2', 'CHBr3', 'O3', 'CO', 'DMS', 'NO', 'HNO3', 'HNO4', \
            'NO2', 'NO3', 'PAN', 'HNO2', 'N2O5'],
        'CAST_int_n': [\
            'IO', 'OIO', 'HOI', 'I2', 'I', 'HOI', 'CH3I', 'CH2I2', 'CH2ICl', 'CH2IBr',\
            'C3H7I', 'C2H5I', 'BrO', 'Br', 'HOBr', 'Br2', 'CH3Br', 'CH2Br2', \
            'CHBr3', 'O3', 'CO', 'OH', 'HO2', 'NO', 'NO2'],
        'diurnal_sp': ['IO', 'I2', 'CH2I2', 'BrO'],
        'obs_comp': [\
            'CH3IT', 'CH2I2', 'CH2ICl', 'CH2IBr', 'C2H5I', 'C3H7I', 'I2', 'IO'],
        'emiss_specs': ['CH3IT', 'CH2I2', 'CH2ICl', 'CH2IBr', 'I2', 'HOI'],
        'w_dep_specs': [\
            'I2', 'HI', 'HOI', 'IONO', 'IONO2', 'I2O2', 'I2O4', 'I2O3',\
            'AERI'],  # , 'IBr', 'ICl']
        'd_dep_specsl1.1': [\
            'I2', 'HI', 'HOI', 'IONO', 'IONO2',  'I2O2', 'I2O4', 'AERI'],  # , 'IO', 'OIO'] ,
        'd_dep_specs': [ \
            'I2df', 'HIdf', 'HOIdf', 'IONOdf', 'IONO2df',  'I2O2df', 'I2O4df', \
            'I2O3df', 'AERIdf', ],  # , 'IOdf', 'OIOdf'], #
        'd_dep_specs_3.0': [
            'I2df', 'HIdf', 'HOIdf', 'IONOdf', 'IONO2df',  'I2O2df', 'I2O4df', \
            'I2O3df', 'ICldf', 'IBrdf', 'AERIdf', ],  # , 'IOdf', 'OIOdf'], #
        'Bry_d_dep_specs': [ \
            'HBr', 'HOBr',  'BrCl', 'Br2', 'IBr', 'BrNO3', ], \
        'Bry_w_dep_specs': [ \
            'HBr', 'HOBr',  'BrCl', 'Br2', 'IBr'], \
        'Cly_d_dep_specs': [ \
            'HCl', 'HOCl', 'ClNO3', 'BrCl', 'ICl'], \
        'I2_het_cyc': ['RD59', 'RD92', 'RD63'],
        # HI, I2O2, I2O4, I2O3 uptake (prev: 2OIO excuded as I2Ox formaed, IO+OIO included as I2O3 not treated )
        'I_het_loss': ['RD58', 'RD62', 'RD93', 'RD95'],
        # ['RD60','RD61','RD62','RD52','RD53','RD54','RD55','RD13'],  # RD13 = OIO + OH => HIO3  86 => AERI loss
        # -- Het ( v3.0+)
        'I2_het_cyc_v3': ['RD59', 'RD92', 'RD63'],
        'I_het_loss_v3': [  \
            # I2O2 all ( RD62), HI ssa (RD58),
            'RD58', 'RD62', 'RD93', 'RD95', \
            # loss to SSA/other aerosols
            'LR44', 'LR45', 'LR32',   # HOI
            'LR34',  # HI other
            'LR42', 'LR43', 'LR35',  # IONO2
            'LR46', 'LR47', 'LR39'],  # IONO
        'NOx': ['NO', 'NO2'],
        'HOx': ['OH', 'HO2'],
        'SOx': ['SO2', 'SO4', 'SO4s'],
        'N_specs': [
            'NO', 'NO2', 'PAN', 'HNO3', 'PMN', 'PPN', 'R4N2', 'N2O5', 'HNO4',\
            'NH3', 'NH4', 'BrNO2', 'BrNO3', 'MPN', 'ISOPN', 'PROPNN', 'MMN',\
            'NO3', 'HNO2', 'IONO', 'IONO2', 'INO'],
        'NOy': [
            'NO', 'NO2', 'PAN', 'HNO3', 'PMN', 'PPN', 'R4N2', 'N2O5', 'HNO4',\
            #    'NH3', 'NH4',
            'BrNO2', 'BrNO3', 'MPN', 'ISOPN', 'PROPNN', 'MMN',\
            'NO3', 'HNO2', 'IONO', 'IONO2', 'INO', 'ClNO2', 'ClNO3'],
        'N_specs_no_I':  [
            'NO', 'NO2', 'PAN', 'HNO3', 'PMN', 'PPN', 'R4N2', 'N2O5', 'HNO4', \
            'NH3', 'NH4', 'BrNO2', 'BrNO3', 'MPN', 'ISOPN', 'PROPNN', 'MMN',\
            'NO3', 'HNO2'],
        'Bry': [\
            'Br2', 'BrCl', 'IBr', 'HOBr', 'BrO', 'HBr', 'BrNO2', 'BrNO3', 'Br'],\
        'Cly': [ \
            'ClOO', 'OClO', 'ClO', 'Cl2O2', 'ICl', 'Cl2', 'Cl', 'BrCl', 'ClNO3',
            'ClNO2', 'HOCl', 'HCl'],
        'Cl_specs': [ \
            'Cl2', 'BrCl', 'ICl', 'HOCl', 'ClO', 'ClOO', 'OClO', 'Cl2O2', 'HCl',  \
            'ClNO2', 'ClNO3', 'Cl', 'CH2Cl2', 'CHCl3', 'CH2ICl', 'CH3Cl'],
        'Br_specs': ['Br2', 'BrNO3', 'Br', 'HBr', 'CH2IBr', \
                     'CH3Br', 'CH2Br2', 'BrCl', 'BrNO2', 'BrSALC', 'BrSALA', \
                     'HOBr', 'IBr', 'BrO', 'CHBr3'],
        'Br_emiss': ['CH2Br2', 'CHBr3', 'SSBr2'],  # 'CH3Br'
        'johan_GRL_TRAs': [ \
            'BrCl', 'Cl2', 'Cl', 'ClO', 'HCl', 'HOCl', 'ClNO2', 'ClNO3', \
            'ClOO', 'OClO', 'Cl2O2', 'CH3Cl', 'CH2Cl2', 'CHCl3', 'BrSALA', \
            'BrSALC'],
        'I_N_tags': ['RD10', 'RD23', 'RD19', 'RD16', 'RD22', \
                     'RD56', 'RD24', 'LO3_30', 'RD69', 'RD68', 'RD20', 'RD21', 'RD25', \
                     'LO3_39', 'RD17', 'RD18', 'RD75'],
        'Br_N_tags': ['LR7', 'LR18', 'LR17', 'LR11', 'LR8', \
                      'LR20', 'LR26', 'LR28', 'LR27'],
        'inactive_I': [ \
            'BrCl', 'OClO', 'ClO', 'HOCl', 'Cl', 'Cl2', 'I2O5', 'I2O', 'HIO3', \
            'IBr', 'ICl', 'C2H5I', 'C3H7I'],  # I2O3 now active.
        'active_I': [ \
            'I2', 'HOI', 'IO', 'I', 'HI', 'OIO', 'INO', 'IONO', 'IONO2', 'I2O2',
            'I2O4', 'I2O3', 'CH3IT', 'CH2I2', 'CH2ICl', 'CH2IBr'],
        'surface_specs': [\
            'O3', 'NO', 'NO2', 'NO3', 'N2O5', 'IO', 'IONO2'],
        # --- Model run title dictionaries
        'run_name_dict': {
            'run': 'Br-I', \
            'Br_2ppt': 'Halogens (I+,Br+) + fixed 2 pptv BrO', \
            'just_I': 'IODINE', 'no_hal': 'NOHAL', 'just_Br': \
            'BROMINE', \
            'Br_1ppt': 'Halogens (I+,Br+) + fixed 1 pptv BrO', \
            'obs': 'Observations'},
        'latex_run_names': {
            'I2Ox_half': 'I$_{2}$O$_{X}$ loss ($\\gamma$) /2',
            'run': 'Br-I',
            'MacDonald_iodide': 'Ocean iodide',
            'Sulfate_up': 'Sulfate uptake',
            'I2Ox_phot_exp': 'I$_{2}$O$_{X}$ exp. X-sections',
            'het_double': 'het. cycle ($\\gamma$) x2',
            'I2Ox_phot_x2': 'I$_{2}$O$_{X}$ X-sections x2',
            'no_het': 'no het. cycle ',
            'I2Ox_double': 'I$_{2}$O$_{X}$ loss ($\\gamma$) x2',
            'just_I': 'IODINE',
            'BrO1pptv': 'MBL BrO 1 pmol mol$^{-1}$',
            'het_half': 'het. cycle ($\\gamma$) /2',
            'Just_I_org': 'Just org. I',
            'no_I2Ox': 'No I$_{2}$O$_{X}$ Photolysis',
            'BrO1pptv_ALL': 'BrO 1 pptv in Trop.',
            'BrO2pptv': 'MBL BrO 2 pmol mol$^{-1}$',
            # adjust from GBC to ACP names
            #        'no_hal': '(I-,Br-)', 'Just_Br': '(I-,Br+)',
            'no_hal': 'NOHAL', 'Just_Br': 'BROMINE',
            # Add for v10 ( 2.0 Cl/Br/I code )
            'run.Cl.Br.I.aerosol':  'GEOS-Chem (v10 Cl.Br.I)', \
            # kludge for diurnal plot
            'Iodine simulation.': 'Br-I.', '(I+,Br+)': 'Br-I.', '(I+,Br-)': 'IODINE',\
            '(I-,Br+)': 'BROMINE', '(I-,Br-)': 'NOHAL'},
        # --- Tracer unit handling
        'spec_2_pptv': [ \
            'I2', 'HOI', 'IO', 'OIO', 'HI', 'IONO', 'IONO2', 'I2O2', 'CH3IT', \
            'CH2I2', 'IBr', 'ICl', 'I', 'HIO3', 'I2O', 'INO', 'I2O3', 'I2O4', \
            'I2O5', 'AERI', 'Cl2', 'Cl', 'HOCl', 'ClO', 'OClO', 'BrCl', 'CH2ICl', \
            'CH2IBr', 'C3H7I', 'C2H5I', 'Br2', 'Br', 'BrO', 'HOBr', 'HBr', 'BrNO2',\
            'BrNO3', 'CHBr3', 'CH2Br2', 'CH3Br', 'RCHO', 'MVK', 'MACR', \
            'PMN', 'PPN', 'R4N2', 'DMS', 'SO4s', 'MSA', 'NITs', 'BCPO', 'DST4', \
            'ISOPN', 'MOBA', 'PROPNN', 'HAC', 'GLYC', 'MMN', 'RIP', 'IEPOX', \
            'MAP', 'N2O5', 'NO3'],  # 'HNO4',  'HNO2'],
        'spec_2_pptC': ['PRPE', 'ISOP'],
        # global
        'spec_2_ppbv': [ \
            'NO', 'DMS',  'RIP', 'IEPOX', 'BCPO', 'DST4', 'HAC', 'GLYC', \
            'MACR', 'ISOP'],
        'spec_2_ppbC': ['ALK4'],
        # --- PF dictionaries
        # WARNING - remove non forwards combatible dicts:
        # (GCFP_TRA_d ... GCFP_d2TRA  ... GCFP_d2TRA_justTRA . etc)
        # GCFP_TRA_d is in use by CVO plotters -  use what_species_am_i instead!
        'GCFP_TRA_d': {'TRA_17': 'R4N2', 'TRA_16': 'PPN', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'TRA_96': 'C2H5I', 'TRA_95': 'C3H7I', 'TRA_94': 'CH2IBr', 'TRA_93': 'CH2ICl', 'TRA_92': 'BrCl', 'TRA_91': 'OClO', 'TRA_90': 'ClO', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_66': 'HNO2', 'TRA_67': 'I2', 'TRA_64': 'NO2', 'TRA_65': 'NO3', 'TRA_68': 'HOI', 'TRA_69': 'IO', 'TRA_71': 'HI', 'TRA_70': 'OIO', 'TRA_73': 'IONO2', 'TRA_72': 'IONO', 'TRA_75': 'CH3IT', 'TRA_74': 'I2O2', 'TRA_77': 'IBr', 'TRA_76': 'CH2I2', 'TRA_79': 'I', 'TRA_78': 'ICl', 'TRA_48': 'HBr', 'TRA_49': 'BrNO2', 'TRA_44': 'Br2', 'TRA_45': 'Br', 'TRA_46': 'BrO', 'TRA_47': 'HOBr', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'TRA_59': 'GLYC', 'TRA_58': 'HAC', 'TRA_53': 'CH3Br', 'TRA_52': 'CH2Br2', 'TRA_51': 'CHBr3', 'TRA_50': 'BrNO3', 'TRA_57': 'PROPNN', 'TRA_56': 'MOBA', 'TRA_55': 'ISOPN', 'TRA_54': 'MPN', 'TRA_28': 'SO4s', 'TRA_29': 'MSA', 'TRA_26': 'SO2', 'TRA_27': 'SO4', 'TRA_24': 'MP', 'TRA_25': 'DMS', 'TRA_22': 'N2O5', 'TRA_23': 'HNO4', 'TRA_20': 'CH2O', 'TRA_21': 'C2H6', 'TRA_39': 'DST2', 'TRA_38': 'DST1', 'TRA_35': 'OCPI', 'TRA_34': 'BCPI', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'TRA_32': 'NIT', 'TRA_08': 'H2O2', 'TRA_09': 'ACET', 'TRA_01': 'NO', 'TRA_02': 'O3', 'TRA_03': 'PAN', 'TRA_04': 'CO', 'TRA_05': 'ALK4', 'TRA_06': 'ISOP', 'TRA_07': 'HNO3', 'TRA_80': 'HIO3', 'TRA_81': 'I2O', 'TRA_82': 'INO', 'TRA_83': 'I2O3', 'TRA_84': 'I2O4', 'TRA_85': 'I2O5', 'TRA_86': 'AERI', 'TRA_87': 'Cl2', 'TRA_88': 'Cl', 'TRA_89': 'HOCl', 'O3': 'O3', 'CO': 'CO'},
        # GCFP_d2TRA is in use by IO plotters -  use what_species_am_i instead!
        'GCFP_d2TRA': {'HIO3': 'TRA_80', 'OCPO': 'TRA_37', 'PPN': 'TRA_16', 'OCPI': 'TRA_35', 'O3': 'TRA_2', 'PAN': 'TRA_3', 'ACET': 'TRA_9', 'IEPOX': 'TRA_62', 'BrNO3': 'TRA_50', 'Br': 'TRA_45', 'HBr': 'TRA_48', 'HAC': 'TRA_58', 'ALD2': 'TRA_11', 'HNO3': 'TRA_7', 'HNO2': 'TRA_66', 'C2H5I': 'TRA_96', 'HNO4': 'TRA_23', 'OIO': 'TRA_70', 'MAP': 'TRA_63', 'PRPE': 'TRA_18', 'HI': 'TRA_71', 'CH2I2': 'TRA_76', 'IONO2': 'TRA_73', 'NIT': 'TRA_32', 'CH3Br': 'TRA_53', 'C3H7I': 'TRA_95', 'C3H8': 'TRA_19', 'DMS': 'TRA_25', 'CH2O': 'TRA_20', 'CH3IT': 'TRA_75', 'CH3I': 'TRA_75', 'NO2': 'TRA_64', 'NO3': 'TRA_65', 'N2O5': 'TRA_22', 'CHBr3': 'TRA_51', 'DST4': 'TRA_41', 'DST3': 'TRA_40', 'DST2': 'TRA_39', 'DST1': 'TRA_38', 'HOCl': 'TRA_89', 'NITs': 'TRA_33', 'RCHO': 'TRA_12', 'C2H6': 'TRA_21', 'MPN': 'TRA_54', 'INO': 'TRA_82', 'MP': 'TRA_24', 'CH2Br2': 'TRA_52', 'SALC': 'TRA_43', 'NH3': 'TRA_30', 'CH2ICl': 'TRA_93', 'RIP': 'TRA_61', 'ClO': 'TRA_90', 'NO': 'TRA_1', 'SALA': 'TRA_42', 'MOBA': 'TRA_56', 'R4N2': 'TRA_17', 'BrCl': 'TRA_92', 'OClO': 'TRA_91', 'PMN': 'TRA_15', 'CO': 'TRA_4', 'CH2IBr': 'TRA_94', 'ISOP': 'TRA_6', 'BCPO': 'TRA_36', 'MVK': 'TRA_13', 'BrNO2': 'TRA_49', 'IONO': 'TRA_72', 'Cl2': 'TRA_87', 'HOBr': 'TRA_47', 'PROPNN': 'TRA_57', 'Cl': 'TRA_88', 'I2O2': 'TRA_74', 'I2O3': 'TRA_83', 'I2O4': 'TRA_84', 'I2O5': 'TRA_85', 'MEK': 'TRA_10', 'MMN': 'TRA_60', 'ISOPN': 'TRA_55', 'SO4s': 'TRA_28', 'I2O': 'TRA_81', 'ALK4': 'TRA_5', 'MSA': 'TRA_29', 'I2': 'TRA_67', 'Br2': 'TRA_44', 'IBr': 'TRA_77', 'MACR': 'TRA_14', 'I': 'TRA_79', 'AERI': 'TRA_86', 'HOI': 'TRA_68', 'BrO': 'TRA_46', 'NH4': 'TRA_31', 'SO2': 'TRA_26', 'SO4': 'TRA_27', 'IO': 'TRA_69', 'H2O2': 'TRA_8', 'BCPI': 'TRA_34', 'ICl': 'TRA_78', 'GLYC': 'TRA_59', 'ALK4': 'ALK4', 'MSA': 'MSA', 'MO2': 'MO2', 'C3H8': 'C3H8', 'ISOP': 'ISOP', 'DMS': 'DMS', 'CH2O': 'CH2O', 'O3': 'O3', 'PAN': 'PAN', 'NO3': 'NO3', 'N2O5': 'N2O5', 'H2O2': 'H2O2', 'NO': 'NO', 'PPN': 'PPN', 'R4N2': 'R4N2', 'HO2': 'HO2', 'NO2': 'NO2', 'PMN': 'PMN', 'ACET': 'ACET', 'CO': 'CO', 'ALD2': 'ALD2', 'RCHO': 'RCHO', 'HNO3': 'HNO3', 'HNO2': 'HNO2', 'SO2': 'SO2', 'SO4': 'SO4', 'HNO4': 'HNO4', 'C2H6': 'C2H6', 'RO2': 'RO2', 'MVK': 'MVK', 'PRPE': 'PRPE', 'OH': 'OH', 'ETO2': 'ETO2', 'MEK': 'MEK', 'MP': 'MP', 'GMAO_TEMP': 'GMAO_TEMP'},
        'GCFP_d2TRA_all_1.6': {'HIO3': 'TRA_80', 'TRA_17': 'TRA_17', 'TRA_16': 'TRA_16', 'TRA_15': 'TRA_15', 'TRA_14': 'TRA_14', 'TRA_13': 'TRA_13', 'TRA_12': 'TRA_12', 'TRA_11': 'TRA_11', 'TRA_19': 'TRA_19', 'ACET': 'ACET', 'RIP': 'TRA_61', 'BrNO3': 'TRA_50', 'HAC': 'TRA_58', 'ALD2': 'ALD2', 'HNO3': 'HNO3', 'HNO2': 'HNO2', 'HNO4': 'HNO4', 'OIO': 'TRA_70', 'MAP': 'TRA_63', 'PRPE': 'PRPE', 'TRA_29': 'TRA_29', 'CH2I2': 'TRA_76', 'I2O2': 'TRA_74', 'NIT': 'TRA_32', 'CH3Br': 'TRA_53', 'C3H7I': 'TRA_95', 'MO2': 'MO2', 'C3H8': 'C3H8', 'I2O5': 'TRA_85', 'TRA_71': 'TRA_71', 'TRA_70': 'TRA_70', 'TRA_73': 'TRA_73', 'DMS': 'DMS', 'TRA_75': 'TRA_75', 'TRA_74': 'TRA_74', 'TRA_77': 'TRA_77', 'TRA_76': 'TRA_76', 'CH2O': 'CH2O', 'TRA_78': 'TRA_78', 'CH3IT': 'TRA_75', 'NO2': 'NO2', 'NO3': 'NO3', 'N2O5': 'N2O5', 'H2O2': 'H2O2', 'PAN': 'PAN', 'HOCl': 'TRA_89', 'TRA_18': 'TRA_18', 'GMAO_TEMP': 'GMAO_TEMP', 'RCHO': 'RCHO', 'C2H6': 'C2H6', 'INO': 'TRA_82', 'MP': 'MP', 'CH2Br2': 'TRA_52', 'CH2ICl': 'TRA_93', 'TRA_59': 'TRA_59', 'TRA_58': 'TRA_58', 'IEPOX': 'TRA_62', 'TRA_53': 'TRA_53', 'TRA_52': 'TRA_52', 'TRA_51': 'TRA_51', 'TRA_50': 'TRA_50', 'TRA_57': 'TRA_57', 'TRA_56': 'TRA_56', 'TRA_55': 'TRA_55', 'TRA_54': 'TRA_54', 'MOBA': 'TRA_56', 'CH3I': 'TRA_75', 'BrCl': 'TRA_92', 'OClO': 'TRA_91', 'CO': 'CO', 'BCPI': 'TRA_34', 'ISOP': 'ISOP', 'BCPO': 'TRA_36', 'MVK': 'MVK', 'TRA_28': 'TRA_28', 'Cl': 'TRA_88', 'TRA_26': 'TRA_26', 'TRA_27': 'TRA_27', 'TRA_24': 'TRA_24', 'I2O3': 'TRA_83', 'I2O4': 'TRA_84', 'TRA_23': 'TRA_23', 'TRA_20': 'TRA_20', 'TRA_21': 'TRA_21', 'MMN': 'TRA_60', 'I2O': 'TRA_81', 'HBr': 'TRA_48', 'ALK4': 'ALK4', 'I2': 'TRA_67', 'PPN': 'PPN', 'IBr': 'TRA_77', 'I': 'TRA_79', 'AERI': 'TRA_86', 'NH4': 'TRA_31', 'SO2': 'SO2', 'SO4': 'SO4', 'NH3': 'TRA_30', 'TRA_08': 'TRA_08', 'TRA_09': 'TRA_09', 'TRA_01': 'TRA_01', 'TRA_02': 'TRA_02', 'TRA_03': 'TRA_03', 'TRA_04': 'TRA_04', 'TRA_05': 'TRA_05', 'TRA_06': 'TRA_06', 'TRA_07': 'TRA_07', 'OCPI': 'TRA_35', 'OCPO': 'TRA_37', 'Br2': 'TRA_44', 'O3': 'O3', 'Br': 'TRA_45', 'TRA_96': 'TRA_96', 'TRA_95': 'TRA_95', 'TRA_94': 'TRA_94', 'TRA_93': 'TRA_93', 'TRA_92': 'TRA_92', 'TRA_91': 'TRA_91', 'TRA_90': 'TRA_90', 'TRA_62': 'TRA_62', 'TRA_63': 'TRA_63', 'TRA_60': 'TRA_60', 'TRA_61': 'TRA_61', 'TRA_66': 'TRA_66', 'TRA_67': 'TRA_67', 'C2H5I': 'TRA_96', 'TRA_65': 'TRA_65', 'TRA_68': 'TRA_68', 'TRA_69': 'TRA_69', 'OH': 'OH', 'IONO2': 'TRA_73', 'HI': 'TRA_71', 'CHBr3': 'TRA_51', 'TRA_46': 'TRA_46', 'DST4': 'TRA_41', 'DST3': 'TRA_40', 'DST2': 'TRA_39', 'DST1': 'TRA_38', 'NITs': 'TRA_33', 'TRA_48': 'TRA_48', 'TRA_49': 'TRA_49', 'TRA_44': 'TRA_44', 'TRA_45': 'TRA_45', 'RO2': 'RO2', 'TRA_47': 'TRA_47', 'TRA_40': 'TRA_40', 'TRA_41': 'TRA_41', 'TRA_42': 'TRA_42', 'TRA_43': 'TRA_43', 'MPN': 'TRA_54', 'ETO2': 'ETO2', 'IO': 'TRA_69', 'TRA_64': 'TRA_64', 'ClO': 'TRA_90', 'NO': 'NO', 'SALA': 'TRA_42', 'SALC': 'TRA_43', 'R4N2': 'R4N2', 'PMN': 'PMN', 'TRA_25': 'TRA_25', 'CH2IBr': 'TRA_94', 'TRA_22': 'TRA_22', 'BrNO2': 'TRA_49', 'IONO': 'TRA_72', 'Cl2': 'TRA_87', 'HOBr': 'TRA_47', 'PROPNN': 'TRA_57', 'MEK': 'MEK', 'TRA_72': 'TRA_72', 'ISOPN': 'TRA_55', 'SO4s': 'TRA_28', 'TRA_79': 'TRA_79', 'MSA': 'MSA', 'TRA_39': 'TRA_39', 'TRA_38': 'TRA_38', 'GLYC': 'TRA_59', 'TRA_35': 'TRA_35', 'TRA_34': 'TRA_34', 'TRA_37': 'TRA_37', 'TRA_36': 'TRA_36', 'TRA_31': 'TRA_31', 'TRA_30': 'TRA_30', 'TRA_33': 'TRA_33', 'TRA_32': 'TRA_32', 'HO2': 'HO2', 'MACR': 'TRA_14', 'HOI': 'TRA_68', 'BrO': 'TRA_46', 'ICl': 'TRA_78', 'TRA_80': 'TRA_80', 'TRA_81': 'TRA_81', 'TRA_82': 'TRA_82', 'TRA_83': 'TRA_83', 'TRA_84': 'TRA_84', 'TRA_85': 'TRA_85', 'TRA_86': 'TRA_86', 'TRA_87': 'TRA_87', 'TRA_88': 'TRA_88', 'TRA_89': 'TRA_89', 'GMAO_TEMP': 'GMAO_TEMP', 'GMAO_UWND': 'GMAO_UWND', 'GMAO_VWND': 'GMAO_VWND'},
        'GCFP_d2TRA_all_1.6.3': {'HIO3': 'TRA_80', 'OCPO': 'TRA_37', 'TRA_65': 'TRA_65', 'PPN': 'PPN', 'TRA_17': 'TRA_17', 'TRA_16': 'TRA_16', 'TRA_15': 'TRA_15', 'OCPI': 'TRA_35', 'TRA_13': 'TRA_13', 'TRA_12': 'TRA_12', 'TRA_11': 'TRA_11', 'O3': 'O3', 'PAN': 'PAN', 'ACET': 'ACET', 'IEPOX': 'TRA_62', 'BrNO3': 'TRA_50', 'Br': 'TRA_45', 'TRA_98': 'TRA_98', 'GMAO_UWND': 'GMAO_UWND', 'TRA_96': 'TRA_96', 'TRA_95': 'TRA_95', 'TRA_94': 'TRA_94', 'TRA_93': 'TRA_93', 'TRA_92': 'TRA_92', 'TRA_91': 'TRA_91', 'HBr': 'TRA_48', 'TRA_72': 'TRA_72', 'HAC': 'TRA_58', 'ALD2': 'ALD2', 'HNO3': 'HNO3', 'HNO2': 'HNO2', 'TRA_60': 'TRA_60', 'TRA_61': 'TRA_61', 'TRA_66': 'TRA_66', 'TRA_67': 'TRA_67', 'C2H5I': 'TRA_96', 'HNO4': 'HNO4', 'TRA_62': 'TRA_62', 'TRA_68': 'TRA_68', 'TRA_69': 'TRA_69', 'OIO': 'TRA_70', 'MAP': 'TRA_63', 'PRPE': 'PRPE', 'OH': 'OH', 'TRA_29': 'TRA_29', 'TRA_14': 'TRA_14', 'HI': 'TRA_71', 'TRA_63': 'TRA_63', 'CH2I2': 'TRA_76', 'IONO2': 'TRA_73', 'TRA_24': 'TRA_24', 'NIT': 'TRA_32', 'CH3Br': 'TRA_53', 'C3H7I': 'TRA_95', 'MO2': 'MO2', 'C3H8': 'C3H8', 'TRA_23': 'TRA_23', 'TRA_71': 'TRA_71', 'TRA_70': 'TRA_70', 'TRA_73': 'TRA_73', 'DMS': 'DMS', 'TRA_75': 'TRA_75', 'TRA_20': 'TRA_20', 'TRA_77': 'TRA_77', 'TRA_76': 'TRA_76', 'CH2O': 'CH2O', 'TRA_78': 'TRA_78', 'CH3IT': 'TRA_75', 'NO2': 'NO2', 'NO3': 'NO3', 'N2O5': 'N2O5', 'CHBr3': 'TRA_51', 'TRA_46': 'TRA_46', 'DST4': 'TRA_41', 'DST3': 'TRA_40', 'DST2': 'TRA_39', 'DST1': 'TRA_38', 'TRA_56': 'TRA_56', 'TRA_19': 'TRA_19', 'HOCl': 'TRA_89', 'TRA_18': 'TRA_18', 'NITs': 'TRA_33', 'GMAO_TEMP': 'GMAO_TEMP', 'TRA_36': 'TRA_36', 'RCHO': 'RCHO', 'TRA_48': 'TRA_48', 'TRA_49': 'TRA_49', 'TRA_44': 'TRA_44', 'C2H6': 'C2H6', 'RO2': 'RO2', 'TRA_47': 'TRA_47', 'TRA_40': 'TRA_40', 'CH3I': 'TRA_75', 'TRA_42': 'TRA_42', 'TRA_43': 'TRA_43', 'TRA_97': 'TRA_97', 'MPN': 'TRA_54', 'ETO2': 'ETO2', 'INO': 'TRA_82', 'MP': 'MP', 'CH2Br2': 'TRA_52', 'SALC': 'TRA_43', 'NH3': 'TRA_30', 'TRA_30': 'TRA_30', 'TRA_64': 'TRA_64', 'CH2ICl': 'TRA_93', 'TRA_59': 'TRA_59', 'TRA_58': 'TRA_58', 'RIP': 'TRA_61', 'TRA_45': 'TRA_45', 'TRA_53': 'TRA_53', 'TRA_52': 'TRA_52', 'TRA_51': 'TRA_51', 'TRA_50': 'TRA_50', 'TRA_57': 'TRA_57', 'GMAO_VWND': 'GMAO_VWND', 'TRA_55': 'TRA_55', 'TRA_54': 'TRA_54', 'ClO': 'TRA_90', 'NO': 'NO', 'SALA': 'TRA_42', 'MOBA': 'TRA_56', 'R4N2': 'R4N2', 'TRA_41': 'TRA_41', 'BrCl': 'TRA_92', 'OClO': 'TRA_91', 'PMN': 'PMN', 'TRA_25': 'TRA_25', 'CO': 'CO', 'TRA_09': 'TRA_09', 'ISALA': 'TRA_97', 'BCPI': 'TRA_34', 'ISOP': 'ISOP', 'ISALC': 'TRA_98', 'BCPO': 'TRA_36', 'TRA_22': 'TRA_22', 'MVK': 'MVK', 'BrNO2': 'TRA_49', 'IONO': 'TRA_72', 'Cl2': 'TRA_87', 'HOBr': 'TRA_47', 'PROPNN': 'TRA_57', 'TRA_28': 'TRA_28', 'Cl': 'TRA_88', 'TRA_26': 'TRA_26', 'TRA_27': 'TRA_27', 'I2O2': 'TRA_74', 'I2O3': 'TRA_83', 'I2O4': 'TRA_84', 'I2O5': 'TRA_85', 'MEK': 'MEK', 'TRA_21': 'TRA_21', 'MMN': 'TRA_60', 'ISOPN': 'TRA_55', 'SO4s': 'TRA_28', 'I2O': 'TRA_81', 'TRA_90': 'TRA_90', 'TRA_74': 'TRA_74', 'ALK4': 'ALK4', 'TRA_79': 'TRA_79', 'MSA': 'MSA', 'TRA_39': 'TRA_39', 'TRA_38': 'TRA_38', 'TRA_81': 'TRA_81', 'TRA_35': 'TRA_35', 'TRA_34': 'TRA_34', 'TRA_37': 'TRA_37', 'I2': 'TRA_67', 'TRA_31': 'TRA_31', 'Br2': 'TRA_44', 'TRA_33': 'TRA_33', 'TRA_32': 'TRA_32', 'HO2': 'HO2', 'IBr': 'TRA_77', 'MACR': 'TRA_14', 'I': 'TRA_79', 'AERI': 'TRA_86', 'HOI': 'TRA_68', 'BrO': 'TRA_46', 'NH4': 'TRA_31', 'SO2': 'SO2', 'SO4': 'SO4', 'IO': 'TRA_69', 'H2O2': 'H2O2', 'TRA_08': 'TRA_08', 'CH2IBr': 'TRA_94', 'ICl': 'TRA_78', 'TRA_01': 'TRA_01', 'TRA_02': 'TRA_02', 'TRA_03': 'TRA_03', 'TRA_04': 'TRA_04', 'TRA_05': 'TRA_05', 'TRA_06': 'TRA_06', 'TRA_07': 'TRA_07', 'TRA_80': 'TRA_80', 'GLYC': 'TRA_59', 'TRA_82': 'TRA_82', 'TRA_83': 'TRA_83', 'TRA_84': 'TRA_84', 'TRA_85': 'TRA_85', 'TRA_86': 'TRA_86', 'TRA_87': 'TRA_87', 'TRA_88': 'TRA_88', 'TRA_89': 'TRA_89'},
        'GCFP_d2TRA_justTRA_1.6': {'TRA_17': 'R4N2', 'TRA_16': 'PPN', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_10': 'MEK', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'TRA_96': 'C2H5I', 'TRA_95': 'C3H7I', 'TRA_94': 'CH2IBr', 'TRA_93': 'CH2ICl', 'TRA_92': 'BrCl', 'TRA_91': 'OClO', 'TRA_90': 'ClO', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_66': 'HNO2', 'TRA_67': 'I2', 'TRA_64': 'NO2', 'TRA_65': 'NO3', 'TRA_68': 'HOI', 'TRA_69': 'IO', 'TRA_71': 'HI', 'TRA_70': 'OIO', 'TRA_73': 'IONO2', 'TRA_72': 'IONO', 'TRA_75': 'CH3IT', 'TRA_74': 'I2O2', 'TRA_77': 'IBr', 'TRA_76': 'CH2I2', 'TRA_79': 'I', 'TRA_78': 'ICl', 'TRA_48': 'HBr', 'TRA_49': 'BrNO2', 'TRA_44': 'Br2', 'TRA_45': 'Br', 'TRA_46': 'BrO', 'TRA_47': 'HOBr', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'TRA_59': 'GLYC', 'TRA_58': 'HAC', 'TRA_53': 'CH3Br', 'TRA_52': 'CH2Br2', 'TRA_51': 'CHBr3', 'TRA_50': 'BrNO3', 'TRA_57': 'PROPNN', 'TRA_56': 'MOBA', 'TRA_55': 'ISOPN', 'TRA_54': 'MPN', 'TRA_28': 'SO4s', 'TRA_29': 'MSA', 'TRA_26': 'SO2', 'TRA_27': 'SO4', 'TRA_24': 'MP', 'TRA_25': 'DMS', 'TRA_22': 'N2O5', 'TRA_23': 'HNO4', 'TRA_20': 'CH2O', 'TRA_21': 'C2H6', 'TRA_39': 'DST2', 'TRA_38': 'DST1', 'TRA_35': 'OCPI', 'TRA_34': 'BCPI', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'TRA_32': 'NIT', 'TRA_9': 'ACET', 'TRA_8': 'H2O2', 'TRA_7': 'HNO3', 'TRA_6': 'ISOP', 'TRA_5': 'ALK4', 'TRA_4': 'CO', 'TRA_3': 'PAN', 'TRA_2': 'O3', 'TRA_1': 'NO', 'TRA_80': 'HIO3', 'TRA_81': 'I2O', 'TRA_82': 'INO', 'TRA_83': 'I2O3', 'TRA_84': 'I2O4', 'TRA_85': 'I2O5', 'TRA_86': 'AERI', 'TRA_87': 'Cl2', 'TRA_88': 'Cl', 'TRA_89': 'HOCl'},
        'GCFP_d2TRA_justTRA_1.6.3': {'TRA_17': 'R4N2', 'TRA_16': 'PPN', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_10': 'MEK', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'TRA_96': 'C2H5I', 'TRA_95': 'C3H7I', 'TRA_94': 'CH2IBr', 'TRA_93': 'CH2ICl', 'TRA_92': 'BrCl', 'TRA_91': 'OClO', 'TRA_90': 'ClO', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_66': 'HNO2', 'TRA_67': 'I2', 'TRA_64': 'NO2', 'TRA_65': 'NO3', 'TRA_68': 'HOI', 'TRA_69': 'IO', 'TRA_71': 'HI', 'TRA_70': 'OIO', 'TRA_73': 'IONO2', 'TRA_72': 'IONO', 'TRA_75': 'CH3IT', 'TRA_74': 'I2O2', 'TRA_77': 'IBr', 'TRA_76': 'CH2I2', 'TRA_79': 'I', 'TRA_78': 'ICl', 'TRA_48': 'HBr', 'TRA_49': 'BrNO2', 'TRA_44': 'Br2', 'TRA_45': 'Br', 'TRA_46': 'BrO', 'TRA_47': 'HOBr', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'TRA_59': 'GLYC', 'TRA_58': 'HAC', 'TRA_53': 'CH3Br', 'TRA_52': 'CH2Br2', 'TRA_51': 'CHBr3', 'TRA_50': 'BrNO3', 'TRA_57': 'PROPNN', 'TRA_56': 'MOBA', 'TRA_55': 'ISOPN', 'TRA_54': 'MPN', 'TRA_28': 'SO4s', 'TRA_29': 'MSA', 'TRA_26': 'SO2', 'TRA_27': 'SO4', 'TRA_24': 'MP', 'TRA_25': 'DMS', 'TRA_22': 'N2O5', 'TRA_23': 'HNO4', 'TRA_20': 'CH2O', 'TRA_21': 'C2H6', 'TRA_39': 'DST2', 'TRA_38': 'DST1', 'TRA_35': 'OCPI', 'TRA_34': 'BCPI', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'TRA_32': 'NIT', 'TRA_9': 'ACET', 'TRA_8': 'H2O2', 'TRA_7': 'HNO3', 'TRA_6': 'ISOP', 'TRA_5': 'ALK4', 'TRA_4': 'CO', 'TRA_3': 'PAN', 'TRA_2': 'O3', 'TRA_1': 'NO', 'TRA_80': 'HIO3', 'TRA_81': 'I2O', 'TRA_82': 'INO', 'TRA_83': 'I2O3', 'TRA_84': 'I2O4', 'TRA_85': 'I2O5', 'TRA_86': 'AERI', 'TRA_87': 'Cl2', 'TRA_88': 'Cl', 'TRA_89': 'HOCl',  'TRA_98': 'ISALC', 'TRA_97': 'ISALA'},
        #                    'GCFP_d2TRA_all_1.7' : {'TRA_74': 'ICl', 'TRA_25': 'DMS', 'TRA_68': 'CH2I2', 'TRA_44': 'Br2', 'TRA_70': 'CH2IBr', 'TRA_22': 'N2O5', 'TRA_76': 'IO', 'TRA_79': 'INO', 'TRA_23': 'HNO4', 'TRA_17': 'R4N2', 'TRA_16': 'PPN', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_10': 'MEK', 'TRA_53': 'CH3Br', 'TRA_52': 'CH2Br2', 'TRA_51': 'CHBr3', 'TRA_21': 'C2H6', 'TRA_57': 'PROPNN', 'TRA_56': 'MOBA', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'TRA_69': 'CH2ICl', 'TRA_50': 'BrNO3', 'TRA_39': 'DST2', 'TRA_38': 'DST1', 'TRA_73': 'IBr', 'TRA_35': 'OCPI', 'TRA_34': 'BCPI', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'TRA_32': 'NIT', 'TRA_77': 'HI', 'TRA_83': 'I2O3', 'TRA_55': 'ISOPN', 'TRA_54': 'MPN', 'TRA_72': 'I2', 'TRA_59': 'GLYC', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_48': 'HBr', 'TRA_49': 'BrNO2', 'TRA_64': 'NO2', 'TRA_65': 'NO3', 'TRA_20': 'CH2O', 'TRA_45': 'Br', 'TRA_46': 'BrO', 'TRA_47': 'HOBr', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'TRA_08': 'H2O2', 'TRA_09': 'ACET', 'TRA_75': 'I', 'TRA_28': 'SO4s', 'TRA_29': 'MSA', 'TRA_26': 'SO2', 'TRA_01': 'NO', 'TRA_02': 'O3', 'TRA_03': 'PAN', 'TRA_04': 'CO', 'TRA_05': 'ALK4', 'TRA_06': 'ISOP', 'TRA_07': 'HNO3', 'TRA_80': 'IONO', 'TRA_81': 'IONO2', 'TRA_82': 'I2O2', 'TRA_58': 'HAC', 'TRA_84': 'I2O4', 'TRA_85': 'AERI', 'TRA_27': 'SO4', 'TRA_78': 'OIO', 'TRA_66': 'HNO2', 'TRA_71': 'HOI', 'TRA_24': 'MP', 'TRA_67': 'CH3IT', 'TRA_9': 'ACET', 'TRA_8': 'H2O2', 'TRA_7': 'HNO3', 'TRA_6': 'ISOP', 'TRA_5': 'ALK4', 'TRA_4': 'CO', 'TRA_3': 'PAN', 'TRA_2': 'O3', 'TRA_1': 'NO'},
        'GCFP_d2TRA_all_1.7': {'TRA_25': 'DMS', 'TRA_77': 'HI', 'TRA_76': 'IO', 'TRA_23': 'HNO4', 'TRA_71': 'HOI', 'TRA_70': 'CH2IBr', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_10': 'MEK', 'TRA_79': 'INO', 'TRA_78': 'OIO', 'TRA_51': 'CHBr3', 'TRA_50': 'BrNO3', 'TRA_52': 'CH2Br2', 'TRA_46': 'BrO', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'TRA_47': 'HOBr', 'TRA_39': 'DST2', 'TRA_38': 'DST1', 'TRA_81': 'IONO2', 'TRA_35': 'OCPI', 'TRA_57': 'PROPNN', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'TRA_56': 'MOBA', 'TRA_83': 'I2O3', 'TRA_55': 'ISOPN', 'TRA_84': 'I2O4', 'TRA_54': 'MPN', 'TRA_5': 'ALK4', 'TRA_49': 'BrNO2', 'TRA_32': 'NIT', 'TRA_9': 'ACET', 'TRA_8': 'H2O2', 'TRA_7': 'HNO3', 'TRA_6': 'ISOP', 'TRA_59': 'GLYC', 'TRA_4': 'CO', 'TRA_3': 'PAN', 'TRA_2': 'O3', 'TRA_1': 'NO', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_66': 'HNO2', 'TRA_67': 'CH3IT', 'TRA_64': 'NO2', 'TRA_65': 'NO3', 'TRA_44': 'Br2', 'TRA_45': 'Br', 'TRA_68': 'CH2I2', 'TRA_69': 'CH2ICl', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'TRA_17': 'R4N2', 'TRA_28': 'SO4s', 'TRA_16': 'PPN', 'TRA_58': 'HAC', 'TRA_27': 'SO4', 'TRA_24': 'MP', 'TRA_29': 'MSA', 'TRA_22': 'N2O5', 'TRA_73': 'IBr', 'TRA_20': 'CH2O', 'TRA_21': 'C2H6', 'TRA_80': 'IONO', 'TRA_26': 'SO2', 'TRA_82': 'I2O2', 'TRA_72': 'I2', 'TRA_48': 'HBr', 'TRA_85': 'AERI', 'TRA_34': 'BCPI', 'TRA_75': 'I', 'TRA_53': 'CH3Br', 'TRA_74': 'ICl'},
        'GCFP_d2TRA_all_2.0': {'TRA_17': 'R4N2', 'TRA_16': 'PPN', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_10': 'MEK', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'TRA_99': 'I2O3', 'TRA_98': 'I2O2', 'TRA_97': 'IONO2', 'TRA_96': 'IONO', 'TRA_95': 'INO', 'TRA_94': 'OIO', 'TRA_93': 'HI', 'TRA_92': 'IO', 'TRA_91': 'I', 'TRA_90': 'ICl', 'TRA_100': 'I2O4', 'TRA_101': 'ISALA', 'TRA_102': 'ISALC', 'TRA_103': 'AERI', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_66': 'HNO2', 'TRA_67': 'BrCl', 'TRA_64': 'NO2', 'TRA_65': 'NO3', 'TRA_68': 'Cl2', 'TRA_69': 'Cl', 'TRA_71': 'HOCl', 'TRA_70': 'ClO', 'TRA_73': 'ClNO2', 'TRA_72': 'HCl', 'TRA_75': 'ClOO', 'TRA_74': 'ClNO3', 'TRA_77': 'Cl2O2', 'TRA_76': 'OClO', 'TRA_79': 'CH2Cl2', 'TRA_78': 'CH3Cl', 'TRA_48': 'HBr', 'TRA_49': 'BrNO2', 'TRA_44': 'Br2', 'TRA_45': 'Br', 'TRA_46': 'BrO', 'TRA_47': 'HOBr', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'TRA_59': 'GLYC', 'TRA_58': 'HAC', 'TRA_53': 'CH3Br', 'TRA_52': 'CH2Br2', 'TRA_51': 'CHBr3', 'TRA_50': 'BrNO3', 'TRA_57': 'PROPNN', 'TRA_56': 'MOBA', 'TRA_55': 'ISOPN', 'TRA_54': 'MPN', 'TRA_28': 'SO4s', 'TRA_29': 'MSA', 'TRA_26': 'SO2', 'TRA_27': 'SO4', 'TRA_24': 'MP', 'TRA_25': 'DMS', 'TRA_22': 'N2O5', 'TRA_23': 'HNO4', 'TRA_20': 'CH2O', 'TRA_21': 'C2H6', 'TRA_39': 'DST2', 'TRA_38': 'DST1', 'TRA_35': 'OCPI', 'TRA_34': 'BCPI', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'TRA_32': 'NIT', 'TRA_9': 'ACET', 'TRA_8': 'H2O2', 'TRA_7': 'HNO3', 'TRA_6': 'ISOP', 'TRA_5': 'ALK4', 'TRA_4': 'CO', 'TRA_3': 'PAN', 'TRA_2': 'O3', 'TRA_1': 'NO', 'TRA_80': 'CHCl3', 'TRA_81': 'BrSALA', 'TRA_82': 'BrSALC', 'TRA_83': 'CH3IT', 'TRA_84': 'CH2I2', 'TRA_85': 'CH2ICl', 'TRA_86': 'CH2IBr', 'TRA_87': 'HOI', 'TRA_88': 'I2', 'TRA_89': 'IBr'},
        'GCFP_d2TRA_all_1.7_EOH_actual_names': {'HNO4': 'HNO4', 'PPN': 'PPN', 'TRA_17': 'R4N2', 'TRA_16': 'PPN', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_10': 'MEK', 'O3': 'O3', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'GMAO_UWND': 'GMAO_UWND', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_66': 'HNO2', 'TRA_67': 'CH3IT', 'TRA_65': 'NO3', 'TRA_68': 'CH2I2', 'TRA_69': 'CH2ICl', 'OH': 'OH', 'LAT': 'LAT', 'TRA_71': 'HOI', 'TRA_70': 'CH2IBr', 'TRA_73': 'IBr', 'TRA_72': 'I2', 'TRA_75': 'I', 'TRA_74': 'ICl', 'TRA_77': 'HI', 'TRA_76': 'IO', 'TRA_79': 'INO', 'TRA_78': 'OIO', 'NO2': 'NO2', 'NO3': 'NO3', 'N2O5': 'N2O5', 'H2O2': 'H2O2', 'GMAO_VWND': 'GMAO_VWND', 'PAN': 'PAN', 'GMAO_TEMP': 'GMAO_TEMP', 'TRA_48': 'HBr', 'TRA_49': 'BrNO2', 'TRA_44': 'Br2', 'TRA_45': 'Br', 'TRA_46': 'BrO', 'TRA_47': 'HOBr', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'TRA_59': 'GLYC', 'TRA_58': 'HAC', 'TRA_53': 'CH3Br', 'TRA_52': 'CH2Br2', 'TRA_51': 'CHBr3', 'TRA_50': 'BrNO3', 'TRA_57': 'PROPNN', 'TRA_56': 'MOBA', 'TRA_55': 'ISOPN', 'TRA_54': 'MPN', 'NO': 'NO', 'PMN': 'PMN', 'HNO3': 'HNO3', 'TRA_28': 'SO4s', 'TRA_29': 'MSA', 'TRA_26': 'SO2', 'TRA_27': 'SO4', 'TRA_24': 'MP', 'TRA_25': 'DMS', 'TRA_22': 'N2O5', 'TRA_23': 'HNO4', 'TRA_20': 'CH2O', 'TRA_21': 'C2H6', 'RO2': 'RO2', 'LON': 'LON', 'TRA_39': 'DST2', 'TRA_38': 'DST1', 'TRA_35': 'OCPI', 'TRA_34': 'BCPI', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'TRA_32': 'NIT', 'HO2': 'HO2', 'SO2': 'SO2', 'SO4': 'SO4', 'TRA_08': 'H2O2', 'TRA_09': 'ACET', 'HNO2': 'HNO2', 'TRA_03': 'PAN', 'TRA_04': 'CO', 'TRA_05': 'ALK4', 'TRA_06': 'ISOP', 'TRA_07': 'HNO3', 'TRA_80': 'IONO', 'TRA_81': 'IONO2', 'TRA_82': 'I2O2', 'TRA_83': 'I2O3', 'TRA_84': 'I2O4', 'TRA_85': 'AERI', 'TRA_86': 'EOH'},
        'TRA_spec_met_all_1.7_EOH': {'MAO3': 'MAO3', 'DHMOB': 'DHMOB', 'ETP': 'ETP', 'RCO3': 'RCO3', 'MO2': 'MO2', 'EOH': 'EOH', 'MVKN': 'MVKN', 'R4P': 'R4P', 'ISNP': 'ISNP', 'RB3P': 'RB3P', 'MGLY': 'MGLY', 'MAOPO2': 'MAOPO2', 'RIO2': 'RIO2', 'PMNN': 'PMNN', 'PP': 'PP', 'VRP': 'VRP', 'RP': 'RP', 'MRO2': 'MRO2', 'HC5': 'HC5', 'ATO2': 'ATO2', 'PYAC': 'PYAC', 'R4N1': 'R4N1', 'DIBOO': 'DIBOO', 'LISOPOH': 'LISOPOH', 'HO2': 'HO2', 'ETHLN': 'ETHLN', 'ISNOOB': 'ISNOOB', 'ISNOOA': 'ISNOOA', 'ROH': 'ROH', 'MAN2': 'MAN2', 'B3O2': 'B3O2', 'INPN': 'INPN', 'MACRN': 'MACRN', 'PO2': 'PO2', 'VRO2': 'VRO2', 'MRP': 'MRP', 'PRN1': 'PRN1', 'ISNOHOO': 'ISNOHOO', 'MOBAOO': 'MOBAOO', 'MACRNO2': 'MACRNO2', 'ISOPND': 'ISOPND', 'HC5OO': 'HC5OO', 'ISOPNBO2': 'ISOPNBO2', 'RA3P': 'RA3P', 'ISOPNB': 'ISOPNB', 'ISOPNDO2': 'ISOPNDO2', 'PMNO2': 'PMNO2', 'IAP': 'IAP', 'MCO3': 'MCO3', 'IEPOXOO': 'IEPOXOO', 'MAOP': 'MAOP', 'INO2': 'INO2', 'OH': 'OH', 'PRPN': 'PRPN', 'GLYX': 'GLYX', 'A3O2': 'A3O2', 'ETO2': 'ETO2', 'R4O2': 'R4O2', 'ISN1': 'ISN1', 'KO2': 'KO2', 'ATOOH': 'ATOOH', 'GMAO_PSFC': 'GMAO_PSFC', 'GMAO_SURF': 'GMAO_SURF', 'GMAO_TEMP': 'GMAO_TEMP', 'GMAO_ABSH': 'GMAO_ABSH', 'GMAO_UWND': 'GMAO_UWND', 'GMAO_VWND': 'GMAO_VWND', 'TRA_9': 'ACET', 'TRA_8': 'H2O2', 'TRA_7': 'HNO3', 'TRA_6': 'ISOP', 'TRA_5': 'ALK4', 'TRA_4': 'CO', 'TRA_3': 'PAN', 'TRA_2': 'O3', 'TRA_1': 'NO', 'TRA_74': 'ICl', 'TRA_25': 'DMS', 'TRA_68': 'CH2I2', 'TRA_44': 'Br2', 'TRA_70': 'CH2IBr', 'TRA_22': 'N2O5', 'TRA_76': 'IO', 'TRA_79': 'INO', 'TRA_23': 'HNO4', 'TRA_17': 'R4N2', 'TRA_16': 'PPN', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_10': 'MEK', 'TRA_53': 'CH3Br', 'TRA_52': 'CH2Br2', 'TRA_51': 'CHBr3', 'TRA_21': 'C2H6', 'TRA_57': 'PROPNN', 'TRA_56': 'MOBA', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'TRA_69': 'CH2ICl', 'TRA_50': 'BrNO3', 'TRA_39': 'DST2', 'TRA_38': 'DST1', 'TRA_73': 'IBr', 'TRA_35': 'OCPI', 'TRA_34': 'BCPI', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'TRA_32': 'NIT', 'TRA_77': 'HI', 'TRA_83': 'I2O3', 'TRA_55': 'ISOPN', 'TRA_54': 'MPN', 'TRA_72': 'I2', 'TRA_59': 'GLYC', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_48': 'HBr', 'TRA_49': 'BrNO2', 'TRA_64': 'NO2', 'TRA_65': 'NO3', 'TRA_20': 'CH2O', 'TRA_45': 'Br', 'TRA_46': 'BrO', 'TRA_47': 'HOBr', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'TRA_08': 'H2O2', 'TRA_09': 'ACET', 'TRA_75': 'I', 'TRA_28': 'SO4s', 'TRA_29': 'MSA', 'TRA_26': 'SO2', 'TRA_01': 'NO', 'TRA_02': 'O3', 'TRA_03': 'PAN', 'TRA_04': 'CO', 'TRA_05': 'ALK4', 'TRA_06': 'ISOP', 'TRA_07': 'HNO3', 'TRA_80': 'IONO', 'TRA_81': 'IONO2', 'TRA_82': 'I2O2', 'TRA_58': 'HAC', 'TRA_84': 'I2O4', 'TRA_85': 'AERI', 'TRA_27': 'SO4', 'TRA_78': 'OIO', 'TRA_66': 'HNO2', 'TRA_71': 'HOI', 'TRA_24': 'MP', 'TRA_67': 'CH3IT'},
        'TRA_spec_met_all_1.7_EOH_no_trailing_zeroes':  {'MVKN': 'MVKN', 'ETP': 'ETP', 'MGLY': 'MGLY', 'EOH': 'EOH', 'TRA_17': 'R4N2', 'TRA_16': 'PPN', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_10': 'MEK', 'TRA_53': 'CH3Br', 'TRA_52': 'CH2Br2', 'TRA_51': 'CHBr3', 'TRA_50': 'BrNO3', 'TRA_57': 'PROPNN', 'TRA_56': 'MOBA', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'RIO2': 'RIO2', 'PYAC': 'PYAC', 'DHMOB': 'DHMOB', 'RP': 'RP', 'HC5OO': 'HC5OO', 'U10M': 'U10M', 'R4N1': 'R4N1', 'ISNOOB': 'ISNOOB', 'ETHLN': 'ETHLN', 'TRA_8': 'H2O2', 'GMAO_UWND': 'GMAO_UWND', 'GMAO_PSFC': 'GMAO_PSFC', 'MAN2': 'MAN2', 'TRA_32': 'NIT', 'B3O2': 'B3O2', 'TRA_59': 'GLYC', 'VRO2': 'VRO2', 'MRP': 'MRP', 'PRN1': 'PRN1', 'ISNOHOO': 'ISNOHOO', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_66': 'HNO2', 'TRA_67': 'CH3IT', 'TRA_64': 'NO2', 'TRA_65': 'NO3', 'TRA_68': 'CH2I2', 'TRA_69': 'CH2ICl', 'IAP': 'IAP', 'MCO3': 'MCO3', 'TRA_3': 'PAN', 'TRA_28': 'SO4s', 'GMAO_SURF': 'GMAO_SURF', 'OH': 'OH', 'PRPN': 'PRPN', 'TRA_27': 'SO4', 'TRA_24': 'MP', 'TRA_29': 'MSA', 'TRA_22': 'N2O5', 'TRA_23': 'HNO4', 'TRA_20': 'CH2O', 'TRA_21': 'C2H6', 'TRA_26': 'SO2', 'TRA_58': 'HAC', 'TRA_81': 'IONO2', 'GLYX': 'GLYX', 'R4P': 'R4P', 'MAO3': 'MAO3', 'TRA_25': 'DMS', 'TRA_77': 'HI', 'KO2': 'KO2', 'RCO3': 'RCO3', 'MO2': 'MO2', 'TRA2': 'O3', 'MACRNO2': 'MACRNO2', 'R4O2': 'R4O2', 'TRA_71': 'HOI', 'TRA_70': 'CH2IBr', 'TRA_73': 'IBr', 'TRA_72': 'I2', 'TRA_75': 'I', 'TRA_74': 'ICl', 'ISNP': 'ISNP', 'TRA_76': 'IO', 'TRA_79': 'INO', 'RB3P': 'RB3P', 'TRA_80': 'IONO', 'MAOPO2': 'MAOPO2', 'ROH': 'ROH', 'PMNN': 'PMNN', 'PP': 'PP', 'ISOPNDO2': 'ISOPNDO2', 'MRO2': 'MRO2', 'HC5': 'HC5', 'TRA_35': 'OCPI', 'TRA_34': 'BCPI', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'GMAO_VWND': 'GMAO_VWND', 'MACRN': 'MACRN', 'DIBOO': 'DIBOO', 'LISOPOH': 'LISOPOH', 'HO2': 'HO2', 'TRA_55': 'ISOPN', 'GMAO_ABSH': 'GMAO_ABSH', 'PRESS': 'PRESS', 'ATOOH': 'ATOOH', 'TRA8': 'H2O2', 'TRA_54': 'MPN', 'GMAO_TEMP': 'GMAO_TEMP', 'ISNOOA': 'ISNOOA', 'TRA_9': 'ACET', 'INPN': 'INPN', 'TRA_7': 'HNO3', 'TRA_6': 'ISOP', 'TRA_5': 'ALK4', 'TRA_4': 'CO', 'PO2': 'PO2', 'TRA_2': 'O3', 'TRA_1': 'NO', 'MOBAOO': 'MOBAOO', 'ISOPND': 'ISOPND', 'VRP': 'VRP', 'TRA_48': 'HBr', 'TRA_49': 'BrNO2', 'RA3P': 'RA3P', 'ISOPNB': 'ISOPNB', 'TRA_44': 'Br2', 'TRA_45': 'Br', 'TRA_46': 'BrO', 'TRA_47': 'HOBr', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'IEPOXOO': 'IEPOXOO', 'MAOP': 'MAOP', 'INO2': 'INO2', 'TRA_38': 'DST1', 'A3O2': 'A3O2', 'ETO2': 'ETO2', 'ISOPNBO2': 'ISOPNBO2', 'ATO2': 'ATO2', 'TRA_82': 'I2O2', 'TRA_83': 'I2O3', 'TRA_84': 'I2O4', 'TRA_85': 'AERI', 'ISN1': 'ISN1', 'TRA_78': 'OIO', 'TRA_39': 'DST2', 'PMNO2': 'PMNO2'},
        # Reduced output for EU grid
        'red_specs_f_name': [ \
            'O3', 'NO2', 'NO', 'NO3', 'N2O5', 'HNO4', 'HNO3', 'HNO2', 'PAN', \
            'PPN', 'PMN', 'H2O2', 'HO2', 'OH', 'RO2', 'SO2', 'SO4', \
            'GMAO_TEMP', 'GMAO_UWND', 'GMAO_VWND', 'I2', 'HOI', \
            'IO', 'I', 'HI', 'OIO', 'INO', 'IONO', 'IONO2', 'I2O2', 'I2O4', 'I2O3',\
            'CH3IT', 'CH2I2', 'CH2ICl', 'CH2IBr'],
        # Photolysis/Fast-J
        'FastJ_lower': [ \
            289.0, 298.25, 307.45, 312.45, 320.3, 345.0, 412.45],
        'FastJ_upper': [\
            298.25, 307.45, 312.45, 320.3, 345.0, 412.45, 850.0],
        'FastJ_mids':  [294, 303, 310, 316, 333, 380, 574],
        # ---  OH loss reactions
        'OH_loss_rxns_1.6': [ \
            'LO3_02', 'LR86', \
            'LR96', 'LR89', 'LR87', 'LR88', 'LR84', 'LR79', 'LR94',\
            'PO3_91', 'LR41', 'LR81', 'LR10', 'LR76', 'LR91', 'LR93', \
            'LR92', 'LR40', 'LR77', 'LR85', 'LR82', 'PO3_86', 'LR74',\
            'LR4', 'LO3_78', 'LR78', 'PO3_67', 'PO3_92', 'RD08', 'LR75', \
            'PO3_01', 'RD07', 'LR9', 'LR62', 'LR37', 'LR73', 'LR19', 'LO3_79', \
            'RD15', 'PO3_68', 'RD06', 'LO3_80', 'LR83', 'LR80', 'LR99', \
        ],
        'OH_loss_rxns': [ \
            'LR100', 'LR101', 'LR97', 'LR102', 'LO3_02', 'LR86', \
            'LR96', 'LR89', 'LR87', 'LR88', 'LR84', 'LR79', 'LR94',\
            'PO3_91', 'LR41', 'LR81', 'LR10', 'LR76', 'LR91', 'LR93', \
            'LR92', 'LR40', 'LR77', 'LR85', 'LR82', 'PO3_86', 'LR74',\
            'LR4', 'LO3_78', 'LR78', 'PO3_67', 'PO3_92', 'RD08', 'LR75', \
            'PO3_01', 'RD07', 'LR9', 'LR62', 'LR37', 'LR73', 'LR19', 'LO3_79', \
            'RD15', 'PO3_68', 'RD06', 'LO3_80', 'LR83', 'LR80', 'LR99', \
            # LR125 is the tag for ALD2 (hash out for runs without this tag)
            #    'LR125'
        ],
        # not outputted by p/l ( but should be) : 'PO3_103', 'PO3_104', 'PO3_105',
        # 'PO3_10'
        'Br_ox_org_rxns':  ['LR12', 'LR13', 'LR14', 'LR15', 'LR16'],
        'ClO_ox_org_rxns': ['LO3_83'],
        'OH_loss_rxns4cl_comp': [
        ],
        'Cl_ox_org_rxns': [
            'LR63', 'LR51', 'LR54', 'LR59', 'LR52', 'LR64', 'LR58', 'LR57', 'LR50', \
            'LR60', 'LR53', 'LR55', 'LR49', 'LR56', 'LR123', 'LR122'],
        'ClO_ox': [
            'LR68', 'LR61', 'LR69', 'LR74', 'LR48', 'LR73', 'LR70',
        ],
        'ClHOx': ['LR67',  'LR66', 'LR61',  'PO3_106', 'LR65'],
        'ClNOx': ['LR68', 'LR69', 'LR48'],
    }

    if rtn_dict:
        return GC_var_dict
    else:
        return GC_var_dict[input_x]


def get_conversion_factor_kgX2kgREF(spec=None, ref_spec=None, stioch=None,
                                    debug=False):
    """
    Return conversion factor for mass (e.g. kg) X to mass ref_spec
    """
    # Get the reference species if not provided and calculate the mass ratio
    if isinstance(ref_spec, type(None)):
        ref_spec = get_ref_spec(spec)
        if debug:
            print("ref_spec for '{}': {}".format(spec, ref_spec))
    factor = 1/species_mass(spec)*species_mass(ref_spec)
    # Consider if there is a stoichiometry between ref_spec and species
    if isinstance(stioch, type(None)):
        stioch = spec_stoich(spec, ref_spec=ref_spec)
        if debug:
            print("stoich for '{}': {}".format(spec, stioch))
    if stioch != 1.0:
        factor = factor * stioch
    return factor
