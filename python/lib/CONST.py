"""
Created by James Dunlop
This is if you are using your own config and wish to add this application to it.
It is mainly used for the api to set the base paths from and the debugging for the tool.
"""
## Import base python stuff
import sys, getpass

#############################################
## CONFIG CONSTANTS
#############################################
## SOME CUSTOM FLAGS FOR THINGS TO DO OR USE
DEBUGGING                       = True

## SETUP BASE CONSTANTS FOR THE CONFIG
USER_NAME                       = '%s' % getpass.getuser()
## SHOT GUN BASE CONSTANTS
SHOTGUN_CONFIG_NAME             = 'genericconfig'
SHOTGUN_URL                     = 'https://mystudio.shotgunstudio.com'
SHOTGUN_TOOLKIT_NAME            = 'Toolkit'
SHOTGUN_TOOLKIT_API_KEY         = 'APIKEY'

## Shotguns default task short names
RIG_SHORTNAME                   = 'Rig'
MODEL_SHORTNAME                 = 'Model'
SURFACE_SHORTNAME               = 'Surface'
ART_SHORTNAME                   = 'Art'

## Define some maya prefixes for use in checks and apps across the config.
BUILDING_SUFFIX                 = 'BLD'
ENVIRONMENT_SUFFIX              = 'ENV'
CHAR_SUFFIX                     = 'CHAR'
LND_SUFFIX                      = 'LND'
PROP_SUFFIX                     = 'PROP'
CPROP_SUFFIX                    = 'CPROP'
LIB_SUFFIX                      = 'LIB'
VEH_SUFFIX                      = 'VEH'
SURFVAR_PREFIX                  = 'SRFVar'

###################################################################################################################
## NOTE!!! If you change these you MUST MANUALLY CHANGE THEM IN THE asset_step.yml and the shot_step.yml as well!!!
ASSEMBLYDEF_SUFFIX              = 'ADEF'
BUILDINGS_AS_AREF               = True ## TURNS ON OR OFF REFERENCING OR ASSEMBLY REFERENCING OF BUILDING RIGS!
###################################################################################################################
## MAYA NAMING CONVENTIONS
GROUP_SUFFIX                    = 'hrc'
GEO_SUFFIX                      = 'geo'
NURBSCRV_SUFFIX                 = 'crv'
IMPORT_SUFFIX                   = 'importDELME'
SHOTCAM_SUFFIX                  = 'shotCam'

## Set platform dependant config constants
if sys.platform == 'win32':
    ## OS specific
    TEMP_FOLDER                 = 'C:/Temp'
    OSTYPE                      = 'win'

    ## Shotgun specific
    SHOTGUN_SOFTWARE_ROOT       = 'T:/software'
    SHOTGUN_PRIMARY_DRIVE       = 'I:'
    SHOTGUN_SECONDARY_DRIVE     = 'K:'
    SHOTGUN_CONFIG_PATH         = '%s/%s' % (SHOTGUN_SOFTWARE_ROOT, SHOTGUN_CONFIG_NAME)
    SHOTGUN_ICON_PATH           = '%s/%s/config/icons' % (SHOTGUN_SOFTWARE_ROOT, SHOTGUN_CONFIG_NAME)
    TANKCORE_PYTHON_PATH        = '%s/studio/install/core/python' % SHOTGUN_SOFTWARE_ROOT
    SGTK_PYTHON_PATH            = '%s/python-api' % SHOTGUN_SOFTWARE_ROOT
    SHOTGUN_LIBRARY_PATH        = '%s/defaultShotgunLibrary' % SHOTGUN_SOFTWARE_ROOT
    SHOTGUN_DEVAPPS_PATH        = '%s/install/apps' % SHOTGUN_CONFIG_PATH

## OSX
elif sys.platform == 'darwin':
    ## OS specific
    TEMP_FOLDER                 = '/tmp'
    OSTYPE                      = 'osx'

    ## Shotgun specific
    SHOTGUN_SOFTWARE_ROOT       = '/volumes/development/software'
    SHOTGUN_PRIMARY_DRIVE       = '/volumes/projects'
    SHOTGUN_SECONDARY_DRIVE     = '/volumes/renders'
    SHOTGUN_CONFIG_PATH         = '%s/%s' % (SHOTGUN_SOFTWARE_ROOT, SHOTGUN_CONFIG_NAME)
    SHOTGUN_ICON_PATH           = '%s/%s/config/icons' % (SHOTGUN_SOFTWARE_ROOT, SHOTGUN_CONFIG_NAME)
    TANKCORE_PYTHON_PATH        = '%s/studio/install/core/python' % SHOTGUN_SOFTWARE_ROOT
    SGTK_PYTHON_PATH            = '%s/python-api' % SHOTGUN_SOFTWARE_ROOT
    SHOTGUN_LIBRARY_PATH        = '%s/defaultShotgunLibrary' % SHOTGUN_SOFTWARE_ROOT
    SHOTGUN_DEVAPPS_PATH        = '%s/install/apps' % SHOTGUN_CONFIG_PATH

## LINUX
else:
    ## OS specific
    TEMP_FOLDER                 = '/tmp'
    OSTYPE                      = 'linux'

    ## Shotgun specific
    SHOTGUN_SOFTWARE_ROOT       = '/development'
    SHOTGUN_PRIMARY_DRIVE       = '/projects'
    SHOTGUN_SECONDARY_DRIVE     = '/renders'
    SHOTGUN_CONFIG_PATH         = '%s/%s' % (SHOTGUN_SOFTWARE_ROOT, SHOTGUN_CONFIG_NAME)
    SHOTGUN_ICON_PATH           = '%s/%s/config/icons' % (SHOTGUN_SOFTWARE_ROOT, SHOTGUN_CONFIG_NAME)
    TANKCORE_PYTHON_PATH        = '%s/studio/install/core/python' % SHOTGUN_SOFTWARE_ROOT
    SGTK_PYTHON_PATH            = '%s/python-api' % SHOTGUN_SOFTWARE_ROOT
    SHOTGUN_LIBRARY_PATH        = '%s/defaultShotgunLibrary' % SHOTGUN_SOFTWARE_ROOT
    SHOTGUN_DEVAPPS_PATH        = '%s/install/apps' % SHOTGUN_CONFIG_PATH