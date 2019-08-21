#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Functions for use with the GEOS-Chem chemical transport model (CTM).

Use help(<name of function>) to get details on a particular function.

"""
# - Required modules:
# I/O / Low level
import os
import sys
#import csv
import glob
import pandas as pd
import xarray as xr
import re
from netCDF4 import Dataset
# try:
#    import iris
# except ImportError:
#    print('WARNING iris not imported')
import logging
# Math/Analysis
import numpy as np
#from time import mktime
#import scipy.stats as stats
#import math
# Time
import time
#import calendar
#import datetime as datetime
#from datetime import datetime as datetime_
# The below imports need to be updated,
# imports should be specific and in individual functions
# import tms modules with shared functions
from .core import *
from .generic import *
from .AC_time import *
from .planeflight import *
from .variables import *
#from .Scripts.bpch2netCDF import convert_to_netCDF


def get_GEOSChem_files_as_ds(file_str='GEOSChem.SpeciesConc.*.nc4', wd=None,
                              debug=False):
    """
    Extract GEOS-Chem NetCDF files that match file string format to a xr.dataset

    Parameters
    ----------
    wd (str): Specify the wd to get the results from a run.
    StateMet (dataset): Dataset object containing time in troposphere

    Returns
    -------
    (dataset)

    Notes
    """
    import glob
    # Check input
    assert type(wd) == str, 'Working directory (wd) provided must be a string!'
    # Get files
    files = glob.glob(wd+file_str)
    assert len(files) >= 1, 'No files found matching-{}'.format(wd+file_str)
    # Sort the files based on their name (which contains a regular datastring)
    files = list(sorted(files))
    # open all of these files as single Dataset
    ds = xr.open_mfdataset(files)
    return ds


def get_Gg_trop_burden(ds=None, spec=None, spec_var=None, StateMet=None, wd=None,
                      trop_level_var='Met_TropLev', air_mass_var='Met_AD',
                      avg_over_time=False,
                      sum_patially=True, rm_trop=True, use_time_in_trop=False,
                      trop_mask=None, spec_conc_prefix='SpeciesConc_',
                      time_in_trop_var='N/A',
                      ):
    """
    Get Tropospheric burden for a/all species in dataset

    Parameters
    ----------
    wd (str): Specify the wd to get the results from a run.
    StateMet (dataset): Dataset object containing time in troposphere
    trop_mask (nd.array): 3D or 4D boolean array where stratosphere is False
    rm_trop (bool): remove the troposphere
    spec (str): Name of the species (optional)
    spec_var (str):  Name of the species inc. Diagnostic prefix (optional)
    spec_conc_prefix (str): the diagnostic prefix for concentration

    Returns
    -------
    (xr.dataset or pandas.DataFrame)

    Notes
    -----
     - A pandas dataframe is returned if values are requested to be summed spatially
     (e.g. sum_patially=True), otherwise a dataset xr.dataset is returned.
    """
    # Only setup to take xarray datasets etc currently...
    assert type(StateMet) != None, 'Func. just setup to take StateMet currently'
    assert type(
        ds) == xr.Dataset, 'Func. just setup to take a xr.dataset currently'
    # Setup a dataset to process and return
    dsL = ds.copy()
    # Extract local variables
    AirMass = StateMet[air_mass_var]
#    TropLevel = StateMet[trop_level_var]
    # Define spec_var as the diga. prefix + "spec" if "spec" provided
    if not isinstance(spec, type(None)):
        if isinstance(spec_var, type(None)):
            spec_var = spec_conc_prefix+spec
    # Create mask for stratosphere if not provided
    if isinstance(trop_mask, type(None)):
        trop_mask = create4Dmask4trop_level(StateMet=StateMet)
    # only allow "SpeciesConc" species
    Specs2Convert = [i for i in dsL.data_vars if 'SpeciesConc' in i]
    dsL = dsL[Specs2Convert]
    MXUnits = 'mol mol-1 dry'
    # Covert all species into burdens (Gg)
    if isinstance(spec_var, type(None)) and isinstance(spec, type(None)):
        # Loop by spec
        for spec_var in Specs2Convert:
            # Remove diagnostic prefix from chemical species
            spec = spec_var.replace(spec_conc_prefix, '')
            # Check units
            SpecUnits = dsL[spec_var].units
            MixingRatioUnits = MXUnits == SpecUnits
            assert_str = "Units must be in '{}' terms! (They are: '{}')"
            assert MixingRatioUnits, assert_str.format(MXUnits, SpecUnits)
            # v/v * (mass total of air (kg)/ 1E3 (converted kg to g)) = moles of tracer
            dsL[spec_var] = dsL[spec_var] * (AirMass*1E3 / constants('RMM_air'))
            # Convert moles to mass (* RMM) , then to Gg
            dsL[spec_var] = dsL[spec_var] * float(species_mass(spec)) / 1E9
        # Return values averaged over time if requested
        if avg_over_time:
            dsL = dsL.mean(dim='time')
        # Remove the tropospheric values?
        if rm_trop:
            # Loop by spec
            for spec_var in Specs2Convert:
                dsL[spec_var] = dsL[spec_var].where(trop_mask)
    else:
        # Just consifer the species of interest
        dsL = dsL[[spec_var]]
        # Remove diagnostic prefix from chemical species
        spec = spec_var.replace(spec_conc_prefix, '')
        # Check units
        SpecUnits = dsL[spec_var].units
        MixingRatioUnits = MXUnits == SpecUnits
        assert_str = "Units must be in '{}' terms! (They are: '{}')"
        assert MixingRatioUnits, assert_str.format(MXUnits, SpecUnits)
        # v/v * (mass total of air (kg)/ 1E3 (converted kg to g)) = moles of tracer
        dsL[spec_var] = dsL[spec_var] * (AirMass*1E3 / constants('RMM_air'))
        # Convert moles to mass (* RMM) , then to Gg
        dsL[spec_var] = dsL[spec_var] * float(species_mass(spec)) / 1E9
        # Return values averaged over time if requested
        if avg_over_time:
            dsL = dsL.mean(dim='time')
        # remove the tropospheric values?
        if rm_trop:
            dsL[spec_var] = dsL[spec_var].where(trop_mask)
    # Sum the values spatially?
    if sum_patially:
        dsL = dsL.sum()
        return dsL.to_array().to_pandas()
    else:
        return dsL

def plot_up_surface_changes_between2runs( ds_dict=None, levs=[1], specs=[],
        BASE='', NEW='', prefix='IJ_AVG_S__', update_PyGChem_format2COARDS=False ):
    """
    Compare BASE and NEW datasets for given species using GCPy

    Parameters
    ----------
    wd (str): Specify the wd to get the results from a run.
    BASE (str): name of the dataset (key) in ds_dict to have as the reference for changes
    NEW (str): name of the dataset (key) in ds_dict to compare against BASE
    specs (list): list of the names of the species to plot
    ds_dict (dict): dictionary of xr.datasets objects
    update_PyGChem_format2COARDS (bool): update the dataset names to be COARDS?
    prefix (str): category string that proceeds all variable names of specs
    levs (list): levels to plot spatial changes for

    Returns
    -------
    (xr.dataset or pandas.DataFrame)

    Notes
    -----

    """
    import gcpy
    # Species to plot
    vars2use = [prefix+i for i in specs]
    unit=None
    PDFfilenameStr = 'Oi_surface_change_{}_vs_{}_lev_{:0>2}'
    # Set datasets to use and  Just include the variables to plot in the dataset
    title1 = BASE
    title2 = NEW
    ds1 = ds_dict[ BASE ][ vars2use ].copy()
    ds2 = ds_dict[ NEW ][ vars2use ].copy()
    # Average over time
    print( ds1, ds2 )
    ds1 = ds1.mean(dim='time')
    ds2 = ds2.mean(dim='time')
    # Remove vestigial coordinates.
    # (e.g. the time_0 coord... what is this?)
    vars2drop = ['time_0']
    dsL = [ds1,ds2]
    for var2drop in vars2drop:
        for n, ds in enumerate(dsL):
            CoordVars = [ i for i in ds.coords ]
            if var2drop in CoordVars:
                ds = ds.drop(var2drop)
                dsL[n] = ds
    ds1, ds2 = dsL
    # Update dimension names
    if update_PyGChem_format2COARDS:
        ds1 = convert_pyGChem_iris_ds2COARDS_ds(ds=ds1)
        ds2 = convert_pyGChem_iris_ds2COARDS_ds(ds=ds2)
    # Now plot this using the compare_single_level script
    for lev in levs:
        # Just select surface (default) or lev in list provided
        ds1 = ds1.isel(lev=lev)
        ds2 = ds2.isel(lev=lev)
        # Make sure the units are present (xarray loses these after some actions)
        for var_ in vars2use:
            ds1[var_].attrs = ds_dict[title1][var_].attrs
            ds2[var_].attrs = ds_dict[title2][var_].attrs
        # Plot and save through GCPy
        PDFfilename = PDFfilenameStr.format( BASE, NEW, lev )
        gcpy.compare_single_level( ds1, title1, ds2, title2, varlist=vars2use,
                 ilev=0, pdfname=PDFfilename+'.pdf',)


def create4Dmask4trop_level(StateMet=None,
                           trop_level_var='Met_TropLev',
                           dyn_trop_press_var='Met_TropP',
                           pmid_press='Met_PMID',
                           use_time_in_trop=False,
                           ):
    """
    Create a mask to remove the stratosphere from GEOSChem output
    """
    # Extract local variables
#    TropLevel = StateMet[trop_level_var]
    DynTropPress = StateMet[dyn_trop_press_var]
    # PMID: Pressure at average pressure level
    pmid_press = StateMet[pmid_press]
    # Just use an integer value for this for now
#    TropLevel = TropLevel.astype(int)
#    MASK = (StateMet['Met_PMID'] > )
    # Just mask as middle pressures values above dynamic troposphere for now
    # this can then be used like ds[VarName].where( MASK )
    # and summed via np.nansum( ds[VarName].where(MASK).values )
    MASK = pmid_press > DynTropPress
    return MASK


def read_inst_files_save_only_surface(wd=None, file_str='GEOSChem.inst1hr.*',
                                         file_extension='.nc4', save_new_NetCDF=True,
                                         delete_existing_NetCDF=True):
    """
    Extract just surface values and save as NetCDF (& DELETE old NetCDF)
    """
    import glob
    # Check input
    assert type(wd) == str, 'Working directory (wd) provided must be a string!'
    # Get files
    files = glob.glob(wd+file_str)
    assert len(files) >= 1, 'No files found matching-{}'.format(wd+file_str)
    for FullFileRoot in sorted(files):
        print(FullFileRoot)
        ds = xr.open_dataset(FullFileRoot)
        ds = ds.sel(lev=ds['lev'][0].values)
        # Create new file name
        Suffix = '_Just_surface'+file_extension
        file_strNew = FullFileRoot.replace(file_extension, Suffix)
        print(file_strNew)
        # Save and close file
        if save_new_NetCDF:
            ds.to_netcdf(file_strNew, engine='scipy')
        ds.close()
        # Delele old file?
        if delete_existing_NetCDF:
            os.remove(FullFileRoot)


def GetSpeciesConcDataset(file_str='GEOSChem.SpeciesConc.*.nc4', wd=None):
    """
    Wrapper to retrive GEOSChem SpeciesConc NetCDFs as a xr.dataset

    Parameters
    ----------
    wd (str): Specify the wd to get the results from a run.
    file_str (str): a str for file format with wildcards (?, *)

    Returns
    -------
    (dataset)
    """
    return get_GEOSChem_files_as_ds(file_str=file_str, wd=wd)


def get_Inst1hr_ds(file_str='GEOSChem.inst1hr.*', wd=None):
    """
    Wrapper to get NetCDF 1hr instantaneous (Inst1hr) output as a Dataset

    Parameters
    ----------
    wd (str): Specify the wd to get the results from a run.
    file_str (str): a str for file format with wildcards (?, *)

    Returns
    -------
    (dataset)
    """
    return get_GEOSChem_files_as_ds(file_str=file_str, wd=wd)


def get_StateMet_ds(file_str='GEOSChem.StateMet.*', wd=None):
    """
    Wrapper to get NetCDF StateMet output as a Dataset

    Parameters
    ----------
    wd (str): Specify the wd to get the results from a run.
    file_str (str): a str for file format with wildcards (?, *)

    Returns
    -------
    (dataset)
    """
    return get_GEOSChem_files_as_ds(file_str=file_str, wd=wd)


def get_ProdLoss_ds(file_str='GEOSChem.ProdLoss.*', wd=None):
    """
    Wrapper to get NetCDF ProdLoss output as a Dataset

    Parameters
    ----------
    wd (str): Specify the wd to get the results from a run.
    file_str (str): a str for file format with wildcards (?, *)

    Returns
    -------
    (dataset)
    """
    return get_GEOSChem_files_as_ds(file_str=file_str, wd=wd)


def GetJValuesDataset(file_str='GEOSChem.JValues.*', wd=None):
    """
    Wrapper to get NetCDF photolysis rates (Jvalues) output as a Dataset

    Parameters
    ----------
    wd (str): Specify the wd to get the results from a run.
    file_str (str): a str for file format with wildcards (?, *)

    Returns
    -------
    (dataset)
    """
    return get_GEOSChem_files_as_ds(file_str=file_str, wd=wd)


def get_HEMCO_diags_as_ds(file_str='HEMCO_diagnostics.*', wd=None):
    """
    Wrapper to get HEMCO diagnostics NetCDF output as a Dataset

    Parameters
    ----------
    wd (str): Specify the wd to get the results from a run.
    file_str (str): a str for file format with wildcards (?, *)

    Returns
    -------
    (dataset)
    """
    return get_GEOSChem_files_as_ds(file_str=file_str, wd=wd)


def convert_pyGChem_iris_ds2COARDS_ds(ds=None, transpose_dims=True):
    """
    Convert a PyChem/Iris dataset into a COARDS compliant xr.dataset/NetCDF

    Parameters
    ----------
    ds (dataset): input Dataset object
    transpose_dims (bool): transpose the dimension order?

    Returns
    -------
    (dataset)
    """
    # PyGChem NetCDF (via iris backend ordering)
    PyGChem_Iris_order = ('time', 'longitude', 'latitude', 'dim3')
    # Make sure the Datasets are using the correct names
    rename_dims = {
    'dim3': 'lev', 'latitude': 'lat', 'longitude': 'lon',
    'model_level_number':'lev'
    }
    for CoordVar in ds.coords:
        try:
            ds = ds.rename(name_dict={CoordVar: rename_dims[CoordVar]})
        except KeyError:
            print('Not renamed {} as not in Dataset'.format(CoordVar))
    # Update the ordering to follow COARDS
    if transpose_dims:
        CoordVars = [ i for i in ds.coords ]
        if 'time' in CoordVars:
            COARDS_order = ('time', 'lev', 'lat', 'lon')
        else:
            COARDS_order = ('lev', 'lat', 'lon')
        # Transpose to ordering
        ds = ds.transpose(*COARDS_order)
    return ds


def convert_HEMCO_ds2Gg_per_yr( ds, vars2convert=None, var_species_dict=None,
                          output_freq='End', verbose=False, debug=False):
    """
    Convert emissions in HEMCO dataset to mass/unit time

    vars2convert (list), NetCDF vairable names to convert
    var_species_dict (dict), dictionary to map variables names to chemical species
    output_freq (str), output frequency dataset made from HEMCO NetCDF file output

    """
    # Get chemical species for each variable name
    var_species = {}
    for var in vars2convert:
        try:
            var_species[var] = var_species_dict[var]
        except:
#            if verbose:
            PrtStr = "WARNING - using variable name '{}' as chemical species!"
            print( PrtStr.format( var) )
            var_species[var] = var
    # Print assumption about end units.
    if output_freq == 'End':
        print( "WARNING - Assuming Output frequnecy ('End') is monthly")

    # Get equivalent unit for chemical species (e.g. I, Br, Cl, N, et c)
    ref_specs = {}
    for var in vars2convert:
        try:
            ref_specs[var] = get_ref_spec( var_species[var] )
        except KeyError:
            print("WARNING: Using '{}' as reference species for '{}'".format(var, var))
    # Loop dataset by variable
    for var_n, var_ in enumerate(vars2convert):
        if debug:
            print('{:<2} {} '.format(var_n, var_))
        # Extract the variable array
        try:
            arr = ds[var_].values
        except KeyError:
            print("WARNING: skipping variable '({})' as not in dataset".format(var_ ))
            continue

        # --- Adjust units to be in kg/gridbox
        # remove area units
        if ds[var_].units == 'kg/m2/':
            arr = arr * ds['AREA']
        elif ds[var_].units == 'kg/m2/s':
            arr = arr * ds['AREA']
            # now remove seconds
            if output_freq == 'Hourly':
                arr = arr*60.*60.
            elif output_freq == 'Daily':
                arr = arr*60.*60.*24.
            elif output_freq == 'Weekly':
                arr = arr*60.*60.*24.*(365./52.)
            elif (output_freq == 'Monthly') or (output_freq == 'End'):
                arr = arr*60.*60.*24.*(365./12.)
            else:
                print('WARNING: ({}) output convert. unknown'.format(
                    output_freq))
                sys.exit()
        elif ds[var_].units  == 'kg':
            pass # units are already in kg .
        else:
            print('WARNING: unit convert. ({}) unknown'.format(ds[var_].units))
            sys.exit()
        # --- convert to Gg species
        # get spec name for output variable
        spec = var_species[var_]
        # Get equivalent unit for species (e.g. I, Br, Cl, N, et c)
        ref_spec = ref_specs[var_]
        # get stiochiometry of ref_spec in species
        stioch = spec_stoich(spec, ref_spec=ref_spec)
        RMM_spec = species_mass(spec)
        RMM_ref_spec = species_mass(ref_spec)
        # update values in array
        arr = arr / RMM_spec * RMM_ref_spec * stioch
        # (from kg=>g (*1E3) to g=>Gg (/1E9))
        arr = arr*1E3 / 1E9
        if set(ref_specs) == 1:
            units = '(Gg {})'.format(ref_spec)
        else:
            units = '(Gg X)'
        if debug:
            print(arr.shape)
        # reassign arrary
        ds[var_].values = arr
        # Update units too
        attrs = ds[var_].attrs
        attrs['units'] = units
        ds[var_].attrs = attrs
    return ds


def get_HEMCO_ds_summary_stats_Gg_yr( ds, vars2use=None ):
    """
    Get summary statistics on dataframe of data
    """
    # master list to hold values
    master_l = []

    # loop by species
    for var_n, var_ in enumerate(vars2use):

        # sub list to hold calculated values
        sub_l = []
        headers = []

        # --- process data to summary statistics
        sum_over_lat_lon = arr.sum(axis=-1).sum(axis=-1).copy()

        # If monthly... process useful summary stats...
        Monthly_output_freqs = 'Monthly', 'End'
        if output_freq in Monthly_output_freqs:
            if output_freq == 'End':
                print(('!'*100, 'WARNING: End output assumed to monthly!'))

            # Add a monthly total
            sub_l += [sum_over_lat_lon.mean(axis=0)]
            headers += ['Mon. avg {}'.format(units)]

            # Add a monthly max
            sub_l += [sum_over_lat_lon.max(axis=0)]
            headers += ['Mon. max {}'.format(units)]

            # Add a monthly min
            sub_l += [sum_over_lat_lon.min(axis=0)]
            headers += ['Mon. max {}'.format(units)]

            # Annual equi.
            sub_l += [arr.sum() / len(arr[:, 0, 0])*12]
            headers += ['Ann. equiv. {}'.format(units)]

            # Annual equi.
            sub_l += [arr.sum() / len(arr[:, 0, 0])*12/1E3]
            header_ = 'Ann. equiv. (Tg {})'.format(ref_spec)
            if len(set(ref_specs)) > 1:
                header_ = 'Ann. equiv. (Tg X)'.format(ref_spec)
            headers += [header_]

        # If daily?!
        elif output_freq == 'Daily':

            # Add a monthly total
            sub_l += [sum_over_lat_lon.mean(axis=0)]
            headers += ['Daily avg {}'.format(units)]

            # Annual equi.
            sub_l += [arr.sum() / len(arr[:, 0, 0])*365.]
            headers += ['Ann. equiv. {}'.format(units)]

            # Annual equi.
            sub_l += [arr.sum() / len(arr[:, 0, 0])*365./1E3]
            header_ = ['Ann. equiv. (Tg {})'.format(ref_spec)]
            if len(set(ref_specs)) > 1:
                header_ = 'Ann. equiv. (Tg X)'.format(ref_spec)
            headers += [header_]

        else:
            prt_str = 'WARNING: no processing setup for {} output'
            print(prt_str.format(output_freq))
            sys.exit()

        # save to master list
        master_l += [sub_l]

    # Make into a DataFrame
    df = pd.DataFrame(master_l)
    df.columns = headers
    df.index = variables
    if verbose:
        print(df)
    return df

