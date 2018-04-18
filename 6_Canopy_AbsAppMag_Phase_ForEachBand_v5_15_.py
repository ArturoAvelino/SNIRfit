
# coding: utf-8

# # Create text files of:
# # - (phase, absolute mag, error mag) and
# # - (phase, apparent mag, error mag)

# ### Notes
#
# - The section of the code more pulished is for J band:  use it as template for any other band.
# - So far, the only case that apply (z_min, z_max) are the bands: J
# - So far, the only case that apply (z_min) are the bands: B, J

# # User interface

# In[ ]:

# USER

import sys # To read arguments in command line

# For command line
bandName = '%s'%sys.argv[1]
Sample = '%s'%sys.argv[2]

# For notebook:
# bandName = 'J'

# Sample = 'CfA'
# Sample = 'CSP'
# Sample = 'Others'
# Sample = 'CfA_CSP'


#----------------

HoFix = 73.24 # 72 # Hubble constant (km/(s Mpc))
# HoFix = 72.78  # TEMPORAL: value reported by Dhawan et al 2017.

OmMFix = 0.28
OmLFix = 0.72
wFix = -1


# -----

# # Automatic

# In[ ]:

from snpy import *
# from numpy import *
import numpy as np
from matplotlib import pyplot as plt
import json
import glob # To read the name of the files in a given directory

# %pylab qt
# For CANOPY python: to show the plots in a separated Windows instead of inline.
# If used, then I don't have to put the instruction "plt.close()" at
# the end of the plot because it will show the figure and instantaneously
# close the windows too.

5+6


# In[ ]:




# In[ ]:


#-------- BAND --------------------

if bandName == 'J':
    filterNames = ['J2m', 'JANDI', 'J', 'Jrc1', 'Jrc2', 'Jdw']

if bandName == 'Y':
    filterNames = ['Y', 'Ydw']

if bandName == 'H':
    filterNames = ['H2m', 'HANDI', 'H', 'Hdw']

if bandName == 'K':
    filterNames = ['Ks2m', 'KANDI', 'K', 'Kd']

#--------------------

DataType = 'OpticalNIR' # OpticalNIR, Optical

# The kcorr uncertainties were computed during the snoopy fitting
# of the light curves?
error_kcorr = False

# Comment the CfA photometric observations flagged by Andrew Friedmann?
CommentFlaggedCfAData = True


######## (usually fixed) ########
#   Filter system
FilterSyst = 'Std_filters/'
# FilterSyst = 'CSP_filters/'


# In[ ]:


# Range of redshift data to be considered
zMinCuttoff = 0.
zMaxCuttoff = 0.1

#-----------------------------------------

# In CfA sample, remove the photometric data with the following error bars.
flag1 = 0.175; flag2 = 0.25 # OK

#-----------------------------------------

#-- Consider the light curves with -at least- the following number of data:
MinNumberOfDataInLCs=3

#-- Consider the LC that contains data in the following range -at least- only:
# phase_min = 3
# phase_max = 10

phase_min = 50
phase_max = -15

#-----------------------------------------

#   Some fixed constants

cc = 299792.458  # Speed of light (km/s)

# Peculiar velocity
# old. vpecFix = 150 # km/s. # Not used anymore

##################################3

# MainDir = '/Users/arturo/Dropbox/Research/SoftwareResearch/Snoopy/AndyLCComp_2018_02/'


# In[ ]:




# ## Metadata: (zhel, zcmb)

# In[ ]:

DirMetadata = '/Users/arturo/Dropbox/Research/SoftwareResearch/Snoopy/AndyLCComp_2018_02/'

# Reading the metadata file
infoSNe_data = np.genfromtxt(DirMetadata+
                             'carrick_Flow_corrections_snnames_v1.txt',
                            dtype=['S17', float,float, 'S40',float,float,
                                   float,float,float,float,'S16', int ])

# Create a dictionary:
# {snname: ra, dec, zhelio, e_zhel, zcmb, e_zcmb, zcmbFlow, e_zcmbFlow, code}

infoSNe_dict = {infoSNe_data['f0'][i]: np.array( [ infoSNe_data['f1'][i],
                infoSNe_data['f2'][i],
                infoSNe_data['f4'][i]/cc, infoSNe_data['f5'][i]/cc,
                infoSNe_data['f6'][i]/cc, infoSNe_data['f7'][i]/cc,
                infoSNe_data['f8'][i]/cc, infoSNe_data['f9'][i]/cc,
                infoSNe_data['f11'][i]] )
                for i in range(len(infoSNe_data)) }

print infoSNe_dict['sn1991T']
# [  1.88542500e+02   2.66556000e+00   5.79067269e-03   3.33564095e-06
#    3.19220839e-03   2.00138457e-05   6.60456908e-03   5.00346143e-04
#    2.00000000e+00]


# In[ ]:




# ### Uploading the SED of Hsiao to compute the extinction

# In[ ]:

Ia_w, Ia_f = kcorr.get_SED(0,'H3')


# ### Cosmology theory for $\mu(z)$

# In[ ]:

from scipy.integrate import quad as intquad

# Inverse of the dimensionless Hubble parameter
def InvEHubblePar(z, OmM, wde):
    "Dimensionless Hubble parameter"
    InvEHubbleParInt = 1.0/(np.sqrt(OmM*(1.0+z)**3.0 + (1.0-OmM)*(1.+z)**(3.*(1.+wde))))
    return InvEHubbleParInt

# ---- The luminosity distance ----
def LumDistance(z, OmM, wde, Ho):
    "Luminosity distance"
    LumDistanceVecInt = 0.
    LumDistanceVecInt = cc*(1.+z)*intquad(InvEHubblePar, 0., z, args=(OmM, wde))[0]/Ho
    return LumDistanceVecInt


# ---- Distance modulus ----
def DistanceMu(z, OmM, wde, Ho):
    "Distance modulus"
    DistanceMuInt = 5.0*np.log10(LumDistance(z, OmM, wde, Ho)) + 25.0
    return DistanceMuInt

#--------------------------------------------------

ztest1 = 0.1
print DistanceMu(ztest1, OmMFix, wFix, HoFix)
# 38.2572823409
# 38.2202031449


# In[ ]:




# ### Generating a table of data (phase[TBmax], M, error_M) including the info of the SNe, from the "snpy" files
#
# The output data is already corrected by
# - k-correction
# - extinction by Milky Way dust
# - time dilation using the z_helio
#

# In[ ]:

#- Directory to save the data

DirSaveFiles = '/Users/arturo/Dropbox/Research/Articulos/10_AndyKaisey/10Compute/TheTemplates/'+bandName+'_band/'+FilterSyst+'1_AllData_InitialFit/AbsMag/'+Sample+'/'

#- Force the creation of the directory to save the outputs.
#- "If the subdirectory does not exist then create it"
if not os.path.exists(DirSaveFiles): os.makedirs(DirSaveFiles)
# if not os.path.exists(DirSavAppMag): os.makedirs(DirSavAppMag)

#- Directory where the ".snpy" files are located:
DirLocationData = '/Users/arturo/Dropbox/Research/SoftwareResearch/Snoopy/AndyLCComp_2018_02/all/snoopy/2_Combine_Fit/'+Sample+'/'+DataType+'/Fit/'

os.chdir(DirLocationData)

# Create a list of the the ".snpy" file names:
list_SN = glob.glob('*_StdFilt.snpy')
# tmp. list_SN = glob.glob('*_1stFit.snpy') # tmp

print len(list_SN),"SNe read with extension '_StdFilt.snpy.'"


# In[ ]:




# In[ ]:

# AUTOMATIC: THIS DOES NOT NEED USER INTERACTION

# Create a list of the the "kcorr_Mean_Std.json" file names:
# old. list_JSON = glob.glob('*_kcorr_Mean_Std.json')

log_text = open(DirSaveFiles+'Log_ListSNeWithData_in_'+bandName+'_band_'+Sample+'.log', 'w')
# log_tex2 = open(DirSavAppMag+'Log_ListSNeWithData_in_'+bandName+'_band_'+Sample+'.log', 'w')

log_text.write("# %s SNe read with extension '_StdFilt.snpy' \
in folder: \n"%len(list_SN))
log_text.write("# %s \n"%DirLocationData)
log_text.write("%s \n"%('-'*40))
log_text.write('# '+bandName+'_band in the following SNe: \n')
# log_tex2.write(bandName+'_band in the following SNe: \n')

print 'SNe with data in band '+bandName+':'

countSN_nir = 0 # Count SNe with data in a given NIR band
# count_nodata = 0 # Count SNe with no data in a given NIR band.
# SNe_nodata = [] # list of SNe with no data in a given NIR band.

for sn in list_SN: # Loop over the SNe.

    s=get_sn(sn) # upload .snpy info

    # The kcorr uncertainties were computed during the snoopy fitting
    # of the light curves?
    if error_kcorr == True:
        # upload the .json dictionary containing the k-corr uncertainties
        with open(sn[:-12]+'kcorr_Mean_Std.json','r') as outfile: s_errorKcorr = json.load(outfile)

    zhelio     = infoSNe_dict[s.name][2]
    err_zhelio = infoSNe_dict[s.name][3]

    # Flag to determine the appropiate z_cmb:
    flag_zcmb  = infoSNe_dict[s.name][8]
    if flag_zcmb > 0.1:
        zcmb       = infoSNe_dict[s.name][4]
        err_zcmb   = infoSNe_dict[s.name][5]
    else:
        zcmb       = infoSNe_dict[s.name][6]
        err_zcmb   = infoSNe_dict[s.name][7]

    if zhelio > zMinCuttoff and zhelio < zMaxCuttoff:

        # Count the number of similar bands in the same SNe (e.g., J, J2m)
        CountNumSimilarBands = 0

        # Loop over all the variants of filters names in a given band.
        for band in filterNames:
            if (band in s.data.keys() and
                (s.data[band].MJD[0] -s.Tmax)/(1+zhelio) <= phase_min and
                (s.data[band].MJD[-1]-s.Tmax)/(1+zhelio) >= phase_max and
                len(s.data[band].MJD) >= MinNumberOfDataInLCs):

                CountNumSimilarBands = CountNumSimilarBands + 1

                if CountNumSimilarBands == 1:
                    SN_txtfile = open(DirSaveFiles+sn[0:18]+'_'+Sample+'_'+
                                      bandName+'.txt', 'w')
                else:
                    SN_txtfile = open(DirSaveFiles+sn[0:18]+'_'+Sample+'_'+
                                      bandName+'.txt', 'a')
                    SN_txtfile.write("#------ %s ------\n"%band)

                #------- The extinction A_lambda --------
                R_F = fset[band].R(wave=Ia_w, flux=Ia_f, Rv=3.1)
                Alamb = R_F * s.EBVgal
                e_Alamb = R_F * s.e_EBVgal

                #------- distance modulus (LCDM)
                mu_LCDM = DistanceMu(zcmb, OmMFix, wFix, HoFix)

                #------------------------------------------------------------------------
                #   WRITTING THE HEADERS IN THE TEXT FILE

                if CountNumSimilarBands == 1:
                    SN_txtfile.write("# {0} \n".format(s.name))
                    # SN_txtfil2.write("# {0}    # SN name \n".format(s.name))

                    # SN_txtfile.write("# \n")
                    SN_txtfile.write("%-13.6f  %.6f  %.6f  %.6f  -1       -1  -1 # \
(zcmb, err_zcmb, zhelio, err_zhelio) \n"%(
                            zcmb, err_zcmb, zhelio, err_zhelio))
                    # SN_txtfil2.write("{0}  {1}  {2}  {3}  00.000  00.000 00.000 # \
    # (zcmb, err_zcmb, zhelio, err_zhelio) metadata file \n".format(zcmb, err_zcmb,
    #                                                              zhelio, err_zhelio ))
                    # SN_txtfile.write("# \n")
                    SN_txtfile.write("%-13.6f  %.6f  %.6f   -1       -1       -1  -1 # \
(dm15, err_dm15, stretch) \n"%(
                            s.dm15, s.e_dm15, s.ks_s))
    #                SN_txtfil2.write("{0}  {1}  {2}   00.000  00.000 00.000 00.000 # \
    # (dm15, err_dm15, stretch) \n".format(s.dm15, s.e_dm15, s.ks_s))

                    # SN_txtfile.write(" \n")
                    SN_txtfile.write("%-13.6f  %.6f  %.6f  -1       -1       -1  -1 # \
(mu_Snoopy, err_mu_Snoopy, mu_LCDM) \n"%(
                            s.DM, s.e_DM, mu_LCDM))
    #                 SN_txtfil2.write("{0}  {1}  {2}  00.000  00.000  00.000 00.000 # \
    # (mu_Snoopy, err_mu_Snoopy, mu_LCDM) \n".format(s.DM, s.e_DM, mu_LCDM))

                    # SN_txtfile.write(" \n")
                    SN_txtfile.write("%-13.6f  %.6f  %.6f  %.6f  %.6f -1  -1 # \
(E(B-V)_MW, err_E(B-V)_MW, Alamb, err_Alamb, R_F) \n"%(
                            s.EBVgal, s.e_EBVgal, Alamb, e_Alamb, R_F))
    #                SN_txtfil2.write("{0}  {1}  {2}  {3}  {4} 00.000  00.000 # \
    # (E(B-V)_MW, err_E(B-V)_MW, Alamb, err_Alamb, R_F) \n".format(s.EBVgal, s.e_EBVgal,
    #                                                              Alamb, e_Alamb, R_F))

                    # SN_txtfile.write(" \n")
                    SN_txtfile.write("%-13.6f  %.6f  -1        -1        -1       -1  -1 # \
(E(B-V)_host, err_E(B-V)_host) \n"%(
                            s.EBVhost, s.e_EBVhost))
    #                 SN_txtfil2.write("{0}  {1}  00.000  00.000 00.000 00.000 00.000 # \
    # (E(B-V)_host, err_E(B-V)_host) \n".format(s.EBVhost, s.e_EBVhost))

                    # SN_txtfile.write(" \n")
                    SN_txtfile.write("%-13.6f  %.6f  -1        -1        -1       -1  -1 # \
(T_Bmax, err_T_Bmax) \n"%(s.Tmax, s.e_Tmax))
    #                 SN_txtfil2.write("{0}  {1}  00.000  00.000 00.000 00.000 00.000 # \
    # (T_Bmax, err_T_Bmax) \n".format(s.Tmax, s.e_Tmax))

                    SN_txtfile.write("-1  -1  -1  -1  -1  -1  -1 # Free slot \n")


                    SN_txtfile.write("-1  -1  -1  -1  -1  -1  -1 # Free slot \n")


                    SN_txtfile.write("# Assuming flat LCDM with (Om={0}, OL={1}, w={2}, \
Ho={3}) \n".format(OmMFix, OmLFix, wFix, HoFix))

                    SN_txtfile.write('#------------------------------------------------- \n')
                    SN_txtfile.write("#  %s \n"%band)
                    SN_txtfile.write('#Phase(TBmax) Abs mag  Err_Absmag  App mag  \
Err_appmag   kcorr    err_kcorr  \n')

                #------------------------------------------------------------------------
                #   WRITTING THE PHOTOMETRY

                # Retriving the error in EBVgal
                # e_EBVgal = dust_getval.get_dust_sigma_RADEC(s.ra, s.decl, calibration='SF11')

                for i in range(len(s.data[band].MJD)): # Loop over MJD in a given band

                    #---------------------------------------------
                    # Remove bad photometric data points in CfA sample based on the flag
                    # in the error value:

                    if CommentFlaggedCfAData == False: CommentText = ''

                    elif CommentFlaggedCfAData == True:
                        if (Sample == 'CfA' and (s.data[band].e_mag[i] == flag1 or
                              s.data[band].e_mag[i] == flag2)):
                            CommentText = '##'
                        else: CommentText = ''

                    # Define the err_kcorr value:
                    if error_kcorr == True:
                            err_kcorr = s_errorKcorr[band]['%s'%s.data[band].MJD[i]][1]
                    else: err_kcorr = 0.

                    # Write in a text file: (phase, Absolute mag, error abs mag)
                    SN_txtfile.write("%s%-9.5f   %.6f  %.6f  %.6f  %.6f  %10.6f  %.6f\n"%(
                        CommentText,

                        # phase:
                        (s.data[band].MJD[i]-s.Tmax)/((1+zhelio)*s.ks_s),

                        # Abs mag: kcorrected, MWdust corrected, and distance
                        # modulus subtracted:
                        s.data[band].mag[i] - s.ks[band][i] - Alamb - mu_LCDM,

                       # Total uncertainty for abs mag =
                       # = (e_mag^2 + e_Alamb^2 + e_kcorr^2)^(-1/2)
                       np.sqrt((s.data[band].e_mag[i])**2 + e_Alamb**2 +
                       err_kcorr**2 ),

                       # Apparent magnitude: MWdust corrected
                       s.data[band].mag[i] - Alamb,

                       # Apparent magnitude error
                       np.sqrt((s.data[band].e_mag[i])**2 + e_Alamb**2),

                       # k-corr
                       s.ks[band][i],

                       # k-corr error
                       err_kcorr
                       ))

                log_text.write('%s \n'%sn)
                # log_tex2.write('%s \n'%sn)

                SN_txtfile.close()
                # SN_txtfil2.close()

                countSN_nir = countSN_nir + 1
                print '%r)'%countSN_nir, sn[0:36]

            #--------------

            # else:
                # SNe_nodata += [sn]
                # count_nodata += 1
                # print "No %s band in:"%bandName, sn
    else: print "SN with z <", zMinCuttoff,":", s.name

log_text.write("# %s SNe in this list. \n"%countSN_nir)
log_text.close()
# log_tex2.close()

print "   "
print "# -- %r SNe in subsample %s with data in %s band: done. -- "%(
        countSN_nir, Sample, bandName)
print len(list_SN),"# SNe read with extension '_StdFilt.snpy.'"
# print "# %s SNe with no data in %s band or less than %s observations."%(
#         count_nodata, bandName, MinNumberOfDataInLCs)
# print "# The SNe are:"



# In[ ]:

# -- 69 SNe in subsample CfA with data in J band: done --
# -- 84 SNe in subsample CSP with data in J band: done --


# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# -----

# # Scratch