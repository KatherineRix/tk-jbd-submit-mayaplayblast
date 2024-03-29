"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------

Code for a maya playblast creator app that runs in maya
This is not a shotgun supported app_store application.
"""
import os, sys, shutil
import logging
logger = logging.getLogger(__name__)
from functools import partial
import time
###################################
## Maya Imports                  ##
import maya.cmds as cmds
###################################
## Shotgun Imports               ##
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import tank.templatekey
try:
    from shotgun_api3 import Shotgun
except ImportError:
    logger.warning('You are missing the api3 dependency! Please install it now or make sure it is on the sys.path or python path!')
###################################
### tk-jbd-baseconfig imports    ##
try:
    import configCONST as configCONST
except ImportError:
    logger.warning('No configCONST avail... using python/lib CONST instead, please make sure your application CONST is set correctly for the config name.')

## TODO Set all previous versions to viewed, or na so latest status is valid.


class PlayBlastGenerator(Application):
    def init_app(self):
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the PlayBlastGenerator application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")
        getDisplayName = self.get_setting('display_name')
        self.engine.register_command(getDisplayName, self.run_app)
        self.lib = self.import_module("lib")
        logger.info('%s Loaded...' % getDisplayName)

    def run_app(self):
        getDisplayName = self.get_setting('display_name')
        self.engine.show_dialog(getDisplayName, self, MainUI, self)


class MainUI(QtGui.QWidget):
    def __init__(self, app):
        """
        main UI for the playblast options
        NOTE: This currenlty playblasts directly into the publish folder.. it'd be great to avoid this and do the move of the file on register...
        """
        QtGui.QWidget.__init__(self)
        ## The app for the UI to use...
        self.app = app
        self.EXISTSWARNING = 'UPLOAD ABORTED! A VERSION WITH THIS FiLE NAME ALREADY EXISTS ON DISK! Either delete the version and try again, or  save a new version of your scene and try again!'

        ## Grab the library python stuff from lib
        self.lib = self.app.import_module("lib")
        logger.info('self.lib loaded sucessfully...')

        ## Check to make sure there is a valid context set
        if self.app.context.entity is None:
            logger.info("Cannot load the PlayBlast application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")
        else:
            ## Grab the application settings now...
            self.upload_to_shotgun  = self.app.get_setting("upload_to_shotgun")
            logger.info('upload_to_shotgun: %s' % self.upload_to_shotgun)
            self.renderWidth        = self.app.get_setting('movie_width')
            logger.info('renderWidth: %s' % self.renderWidth)
            self.renderHeight       = self.app.get_setting('movie_height')
            logger.info('renderHeight: %s' % self.renderHeight)
            ## The current model editor is...
            self.currentEditor = self._getEditor()
            logger.info('currentEditor: %s' % self.currentEditor)

            ## These two are used for the os module when doing a os.rename for windows
            self.osPathToWorkFile       = ''
            logger.info('osPathToWorkFile: %s' % self.osPathToWorkFile)
            self.osPathToPublishFile    = ''
            logger.info('osPathToPublishFile: %s' % self.osPathToPublishFile)
            ## Now build the main UI
            self._buildUI()
            logger.info('_buildUI: %s' % self._buildUI)

            ## Resize the UI
            self.resize(self.sizeHint())

    def _buildUI(self):
        """
        MainUI builder
        """
        logger.info('ValidContextFound.. building UI')
        ############################################################################################
        ## Setup the main UI
        self.setStyleSheet("QGroupBox{background-color: #4B4B4B}")
        self.mainLayout = QtGui.QVBoxLayout(self)
        ############################################################################################
        ############################################################################################
        ## TOP INFO BOX
        ############################################################################################
        self.infoGroupBox       = QtGui.QGroupBox(self)
        self.infoGroupBox.setTitle('Info')
        self.infoGroupBox.setFlat(True)
        self.hLayout            = QtGui.QHBoxLayout(self.infoGroupBox)
        self.renderWidthLabel   = QtGui.QLabel('Width: %s' % self.renderWidth)
        self.renderHeightLabel  = QtGui.QLabel('Height: %s' % self.renderHeight)
        self.codecLabel         = QtGui.QLabel('Codec: MPEG-4 Video')
        self.formatLabel        = QtGui.QLabel('Format: mov')
        self.hLayout.addWidget(self.renderWidthLabel)
        self.hLayout.addWidget(self.renderHeightLabel)
        self.hLayout.addWidget(self.codecLabel)
        self.hLayout.addWidget(self.formatLabel)

        ############################################################################################
        ## CAMERA SETTINGS GROUPBOX
        ############################################################################################
        logger.info('Building cameraSettings')
        self.cameraSettingsGroupBox     = QtGui.QGroupBox(self)
        self.cameraSettingsGroupBox.setTitle('Camera Settings')
        self.cameraSettingsGroupBox.setFlat(True)
        self.camGridLayout              = QtGui.QGridLayout(self.cameraSettingsGroupBox)
        self.maxColumns                 = 4
        ## Process all the stupid maya options for the camera settings for the playblast.
        self.optionsList                = self.lib.CAM_SETTINGS_OPTIONS
        self.defaultOn                  = self.lib.CAM_SETTINGS_DEFAULT_ON
        self.camRadioButtons            = []
        self.row                        = 0
        self.col                        = 0

        ## Now build the columnLayout for these options to be displayed.
        for eachRButton in self.optionsList:
            self.myButton = QtGui.QRadioButton(eachRButton)
            self.myButton.setAutoExclusive(False)
            self.camRadioButtons.append(self.myButton)

            ## Now add the radio button to the layout
            self.camGridLayout.addWidget(self.myButton, self.row, self.col)

            ## Set the button to checked if it is in the CONST default on list
            if eachRButton in self.defaultOn:
                self.myButton.setChecked(True)

            ## Now increase column by 1
            self.col = self.col + 1

            ## Check to see if at last column, if so reset columns and add one to row.
            if self.col == self.maxColumns:
                self.row = self.row + 1
                self.col = 0

            ## Connect signal slots
            self.myButton.toggled.connect(self._processRadioButtons)

        ############################################################################################
        ## VIEWPORT SETTINGS GROUPBOX
        ############################################################################################
        logger.info('Building viewportSettings')
        self.viewportSettingsGroupBox   = QtGui.QGroupBox(self)
        self.viewportSettingsGroupBox.setFlat(True)
        self.viewportSettingsGroupBox.setTitle('Viewport Settings')
        self.viewportGridLayout         = QtGui.QGridLayout(self.viewportSettingsGroupBox)
        ## Process all the viewport settings for the playblast.
        self.viewportOptions            = self.lib.VIEWPORT_SETTINGS_OPTIONS
        self.defaultOn                  = self.lib.VIEWPORT_SETTINGS_DEFAULT_ON
        self.viewportRadioButtons       = []
        self.row                        = 0
        self.col                        = 0

        ## Now build the columnLayout for these options to be displayed.
        for eachRButton in self.viewportOptions:
            self.myButton = QtGui.QRadioButton(eachRButton)
            if eachRButton == 'WireFrame' or eachRButton == 'SmoothShade All' or eachRButton == 'Bounding Box':
                self.myButton.setAutoExclusive(True)
            else:
                self.myButton.setAutoExclusive(False)
            self.viewportRadioButtons.append(self.myButton)

            ## Now add the radio button to the layout
            self.viewportGridLayout.addWidget(self.myButton, self.row, self.col)

            ## Set the button to checked if it is in the CONST default on list
            if eachRButton in self.defaultOn:
                self.myButton.setChecked(True)

            ## Now increase column by 1
            self.col = self.col + 1

            ## Check to see if at last column, if so reset columns and add one to row.
            if self.col == self.maxColumns:
                self.row = self.row + 1
                self.col = 0

            ## Connect signal slots
            self.myButton.toggled.connect(self._processRadioButtons)

        ############################################################################################
        ## RENDERER SETTINGS GROUPBOX
        ############################################################################################
        logger.info('Building renderSettings')
        self.rendererSettingsGroupBox   = QtGui.QGroupBox(self)
        self.rendererSettingsGroupBox.setFlat(True)
        self.rendererSettingsGroupBox.setTitle('Renderer Settings')
        self.rendererGridLayout         = QtGui.QGridLayout(self.rendererSettingsGroupBox)
        ## Process all the renderer settings for the playblast.
        self.rendererOptions            = self.lib.RENDERER_SETTINGS_OPTIONS
        self.defaultOn                  = self.lib.RENDERER_SETTINGS_DEFAULT_ON
        self.rendererRadioButtons       = []
        self.row                        = 0
        self.col                        = 0

        ## Now build the columnLayout for these options to be displayed.
        for eachRButton in self.rendererOptions:
            self.myButton = QtGui.QRadioButton(eachRButton)
            self.myButton.setAutoExclusive(True)
            self.rendererRadioButtons.append(self.myButton)

            ## Now add the radio button to the layout
            self.rendererGridLayout.addWidget(self.myButton, self.row, self.col)

            ## Set the button to on if it is in the CONST default on list
            if eachRButton in self.defaultOn:
                self.myButton.setChecked(True)

            ## Now increase column by 1
            self.col = self.col + 1

            ## Check to see if at last column, if so reset columns and add one to row.
            if self.col == self.maxColumns:
                self.row = self.row + 1
                self.col = 0

            ## Connect signal slots
            self.myButton.toggled.connect(self._processRadioButtons)

        self.rendererGridLayout.setColumnStretch(self.maxColumns + 1,1)

        ############################################################################################
        ## BUILD ASSET TURN TABLE UI IF THIS IS AN ASSET
        ############################################################################################
        if self.app.get_setting('isAsset') and self.app.get_setting('allowAssetTurnTableBuild'):
            logger.info('Showing Asset UI')
            self._buildAssetTurntableUI()

        ############################################################################################
        ## COMMENT GROUP BOX
        ############################################################################################
        logger.info('Building Comment Layout')
        ## Now the comment layout
        self.commentGroupBox        = QtGui.QGroupBox(self)
        self.commentGroupBox.setFlat(True)
        self.commentGroupBox.setTitle('Comment -- required!')

        self.hLayout                = QtGui.QHBoxLayout(self.commentGroupBox)
        self.commentLabel           = QtGui.QLabel('Set Comment:')
        self.comment                = QtGui.QLineEdit(self)
        self.comment.setToolTip('You MUST set a comment if you are publishing to shotgun. Please set a sensible version note here.')
        self.hLayout.addWidget(self.commentLabel)
        self.hLayout.addWidget(self.comment)

        ##################################################################1##########################
        ## SUBMISSION GROUP BOX
        ############################################################################################
        ## Now the submission area
        logger.info('Building Submission Layout')
        self.submissionGroupBox     = QtGui.QGroupBox(self)
        self.submissionGroupBox.setFlat(True)
        self.submissionGroupBox.setTitle('Submission to Shotgun')
        self.submissionlayout       = QtGui.QHBoxLayout(self.submissionGroupBox)
        ##################
        ## Quality Spinbox
        self.qualityPercentage      = 75
        self.qualityLabel           = QtGui.QLabel('Quality:')
        self.qualityPercent         = QtGui.QSpinBox(self)
        self.qualityPercent.setRange(0, 100)
        self.qualityPercent.setValue(75)
        #####################
        ## Percentage Spinbox
        self.sizePercentage         = 75
        self.sizeLabel              = QtGui.QLabel('Scale:')
        self.sizePercent            = QtGui.QSpinBox(self)
        self.sizePercent.setRange(0, 100)
        self.sizePercent.setValue(75)
        #####################
        ## Build the statusList Combobox
        self.statusLabel            = QtGui.QLabel('Status')
        self.statusList             = QtGui.QComboBox(self)
        for each in self.lib.STATUS_LIST:
            self.statusList.addItem(each)
        status                      = self.app.get_setting('new_version_status')
        index                       = self.statusList.findText(status)
        self.statusList.setCurrentIndex(index)
        #####################
        ## Build the upload button
        self.upload                 = QtGui.QRadioButton('Submit to shotgun?')
        self.upload.setStyleSheet('QRadioButton:indicator{background-color: #088A08}')
        self.upload.setAutoExclusive(False)
        self.upload.setChecked(False)
        self.upload.toggled.connect(self._uploadToggle)
        #####################
        ## Build the main go button
        self.goButton               = QtGui.QPushButton('Playblast...')
        self.goButton.setStyleSheet("QPushButton { background-color: #088A08}")
        self.goButton.setMinimumWidth(350)
        self.goButton.released.connect(self.doPlayblast)
        #####################
        ## Add to layout
        self.submissionlayout.addWidget(self.qualityLabel)
        self.submissionlayout.addWidget(self.qualityPercent)
        self.submissionlayout.addWidget(self.sizeLabel)
        self.submissionlayout.addWidget(self.sizePercent)

        self.submissionlayout.addWidget(self.statusLabel)
        self.submissionlayout.addWidget(self.statusList)

        ## Check to see if the attr in the _step.yml is looking to upload to shotgun or not.
        ## If it is show the upload options and set the button to true
        if self.upload_to_shotgun:
            self.submissionlayout.addWidget(self.upload)
            self.upload.setChecked(True)
        else:
            self.upload.hide()
            self.commentGroupBox.hide()
            self.submissionGroupBox.setTitle('Local Playblast')
        ## Check if we are an asset or a shot, and show the option to delete the turnTable group after playblasting
        if self.app.get_setting('isAsset') and self.app.get_setting('allowAssetTurnTableBuild'):
            self.deleteHrcGrp = QtGui.QRadioButton('Delete Turntable Grp?')
            self.deleteHrcGrp.setAutoExclusive(False)
            self.submissionlayout.addWidget(self.deleteHrcGrp)

        #########################################################
        ## Now add the go button regardless of shot or asset step
        self.submissionlayout.addWidget(self.goButton)
        self.submissionlayout.addStretch(1)

        ############################################
        ## Now add the groupboxes to the main layout.
        logger.info('Building final Layout')
        self.mainLayout.addWidget(self.infoGroupBox)
        self.mainLayout.addWidget(self.cameraSettingsGroupBox)
        self.mainLayout.addWidget(self.viewportSettingsGroupBox)
        self.mainLayout.addWidget(self.rendererSettingsGroupBox)
        logger.info('Building final Layout step 2')
        if self.app.get_setting('isAsset'):
            if self.app.get_setting('allowAssetTurnTableBuild'):
                self.mainLayout.addWidget(self.turnTableGroupBox)
            else:
                pass
        else:
            logger.info('Building final Layout step 2.5')
            self._setupShotCamera()
        logger.info('Building final Layout step 3')
        self.mainLayout.addWidget(self.submissionGroupBox)
        self.mainLayout.addWidget(self.commentGroupBox)
        self.mainLayout.addStretch(1)
        logger.info('Building final Layout complete..')

        ###############################################################################
        ## Now show or hide the options if the showOptions is turned on else hide these
        if not self.app.get_setting('showOptions'):
            self.groupBoxes = [self.infoGroupBox, self.cameraSettingsGroupBox, self.viewportSettingsGroupBox, self.rendererSettingsGroupBox]
            for each in self.groupBoxes:
                each.hide()

        #######################################
        ## Process all the radio button options
        self._processRadioButtons()
        logger.info('_processRadioButtons successful...')

        #############################
        ## Now set the default render globals
        self._setupRenderGlobals()

        logger.info('UI Built Successfully...')

    def _buildAssetTurntableUI(self):
        """
        Builds the turnTable UI if needed
        """
        self.turnTableGroupBox      = QtGui.QGroupBox(self)
        self.turnTableGroupBox.setFlat(True)
        self.turnTableGroupBox.setTitle('Turn Table Setup')

        self.turnTableGridLayout    = QtGui.QGridLayout(self.turnTableGroupBox)
        self.inputPromptUI          = self.lib.InputPrompt(self, label = 'TurnTableGroup', defaultText = '', getSelected = True)

        self.frameRangeLayout       = QtGui.QHBoxLayout(self)
        self.startFrameLabel        = QtGui.QLabel('Start Frame:')
        ## Start Frame
        self.startFrame             = QtGui.QSpinBox(self)
        self.startFrame.setToolTip('The start frame for the turntable animation')
        self.startFrame.setRange(-10000000, 100000000)
        self.startFrame.setValue(1)
        ## Frame count
        self.totalFramesLabel       = QtGui.QLabel('Total # of Frames:')
        self.totalFrames            = QtGui.QSpinBox(self)
        self.totalFrames.setToolTip('The duration of the turn table.\nNote turn tables rotate in two planes and these full rotations are split across the total duration assigned.\nIf 100frames 50 frames for the first spin, 50frames for the 2nd.')
        self.totalFrames.setRange(0, 100000000)
        self.totalFrames.setValue(100)
        self.frameRangeLayout.addWidget(self.startFrameLabel)
        self.frameRangeLayout.addWidget(self.startFrame)
        self.frameRangeLayout.addWidget(self.totalFramesLabel)
        self.frameRangeLayout.addWidget(self.totalFrames)
        ## Now the go button
        self.buildTurnTableButton   = QtGui.QPushButton('Setup Turn Table')
        self.buildTurnTableButton.setStyleSheet("QPushButton { background-color: #6C8B87}")
        self.buildTurnTableButton.setToolTip('Setup the turntable animation for the group specified.')
        self.buildTurnTableButton.pressed.connect(partial(self._setupTurnTable, self.inputPromptUI, self.startFrame, self.totalFrames))
        ## Now add the ui elements back to the layout
        self.turnTableGridLayout.addWidget(self.inputPromptUI, 0,0)
        self.turnTableGridLayout.addLayout(self.frameRangeLayout, 1,0)
        self.turnTableGridLayout.addWidget(self.buildTurnTableButton, 2,0)
        self.frameRangeLayout.stretch(1)

    def _uploadToggle(self):
        """
        Shows and hides the comment groupBox if the upload radio button is true or false.
        """
        if self.upload.isChecked():
            self.commentGroupBox.show()
            self.upload.setStyleSheet('QRadioButton:indicator{background-color: #088A08}')
            self.submissionGroupBox.setTitle('Submission to Shotgun')

        else:
            self.commentGroupBox.hide()
            self.upload.setStyleSheet('QRadioButton:indicator{background-color: #B40404}')
            self.submissionGroupBox.setTitle('Local Playblast')

    def _getEditor(self):
        currentPanel = cmds.getPanel(withFocus = True)
        logger.info('currentPanel: %s' % currentPanel)

        if 'modelPanel' not in currentPanel:
            QtGui.QMessageBox.information(None, "Aborted...", 'You must have active a current 3D viewport! \nRight click the viewport you wish to playblast from.')
            return -1
        else:
            currentEditor = cmds.modelPanel(currentPanel, q = True, modelEditor = True)
            logger.info('Current Editor is: %s' % currentEditor)
            self.currentEditor = currentEditor
            return currentEditor

    def _setupShotCamera(self):
        """
        Shot camera setup
        """
        camera = self.lib._findShotCamera()
        if camera:
            logger.info('camera: %s' % camera)
            ## Set the current modelEditors cam to this camera
            cmds.modelEditor(self.currentEditor, edit = True, camera = camera)

            ## Now get the parent of the shape to send through to setup the camera Defaults.
            getCamTransform = cmds.listRelatives(camera, parent = True)[0] ## need to send the camera transform to this function

            ## Setup the camearDefaults.
            self.lib._setCameraDefaults(getCamTransform)

    def _setupTurnTable(self, geoGroup = '', start = '', frames = ''):
        """
        Builds a camera for turn table
        """
        logger.info('_setupTurnTable run...')
        geoGroup    = geoGroup.getText()
        start       = start.value()
        frames      = frames.value()

        ## Now check for existing and delete it.
        if cmds.objExists('turnTable_hrc'):
            logger.info('Removed existing turnTable...')
            cmds.delete('turnTable_hrc')

        ## Build the camera for the turnTable
        cameraName  = 'turnTable_shotCam'
        cmds.camera()
        cmds.rename('camera1', cameraName)
        ## Now change the settings of the camera to the default settings
        self.lib._setCameraDefaults(cameraName)

        ## Setup the group
        cmds.group(cameraName, n = 'turnTable_hrc')
        cmds.pointConstraint(geoGroup, 'turnTable_hrc', mo = False, n = 'tmpPoint')
        cmds.orientConstraint(geoGroup, 'turnTable_hrc', mo = False, n = 'tmpOrient')
        cmds.delete(['tmpPoint', 'tmpOrient'])

        ## Now set the camera into the modelEditor that was selected by the artist
        cmds.modelEditor(self.currentEditor, e = True, camera = cameraName)
        cmds.viewFit(cameraName, allObjects = False, animate = False,  f=0.80)
        #cmds.xform(cameraName, translation = [0,0,25])

        ## Now keyframe the turntable group
        cmds.currentTime(start)
        getStartRotY = cmds.getAttr('turnTable_hrc.rotateY')
        cmds.setKeyframe('turnTable_hrc', at = 'rotateY')
        cmds.currentTime(start + frames/2)
        cmds.playbackOptions(animationStartTime = start, animationEndTime = start + frames, minTime = start, maxTime = start + frames)
        cmds.setAttr('turnTable_hrc.rotateY', 360 + getStartRotY)
        cmds.setKeyframe('turnTable_hrc', at = 'rotateY')
        cmds.setKeyframe('turnTable_hrc', at = 'rotateX')

        cmds.currentTime(start + frames)
        cmds.setAttr('turnTable_hrc.rotateX', -360)
        cmds.setKeyframe('turnTable_hrc', at = 'rotateX')

        cmds.select(clear = True)

    def _processRadioButtons(self):
        self.editor = self.currentEditor
        radioButtons = [self.camRadioButtons, self.viewportRadioButtons, self.rendererRadioButtons]
        logger.info('Processing the radioButtonStates')
        logger.info('CurrentEditor is: %s' % self.currentEditor)
        for eachSettingList in radioButtons:
            for eachSetting in eachSettingList:
                if eachSetting.text() == 'NURBS Curves':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, nc = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, nc = False)
                if eachSetting.text() == 'NURBS Surfaces':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, ns = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, ns = False)
                if eachSetting.text() == 'Polygons':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, polymeshes = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, polymeshes = False)
                if eachSetting.text() == 'Subdiv Surfaces':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, subdivSurfaces = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, subdivSurfaces = False)
                if eachSetting.text() == 'Planes':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, planes = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, planes = False)
                if eachSetting.text() == 'Lights':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, lights = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, lights = False)
                if eachSetting.text() == 'Cameras':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, cameras = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, cameras = False)
                if eachSetting.text() == 'Joints':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, joints = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, joints = False)
                if eachSetting.text() == 'IK Handles':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, ikHandles = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, ikHandles = False)
                if eachSetting.text() == 'Deformers':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, deformers = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, deformers = False)
                if eachSetting.text() == 'Dynamics':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, dynamics = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, dynamics = False)
                if eachSetting.text() == 'Fluids':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, fluids = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, fluids = False)
                if eachSetting.text() == 'Hair Systems':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, hairSystems = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, hairSystems = False)
                if eachSetting.text() == 'Follicles':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, follicles = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, follicles = False)
                if eachSetting.text() == 'nCloths':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, nCloths = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, nCloths = False)
                if eachSetting.text() == 'nParticles':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, nParticles = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, nParticles = False)
                if eachSetting.text() == 'nRigids':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, nRigids = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, nRigids = False)
                if eachSetting.text() == 'Dynamic Constraints':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, dynamicConstraints = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, dynamicConstraints = False)
                if eachSetting.text() == 'Locators':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, locators = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, locators = False)
                if eachSetting.text() == 'Dimensions':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, dimensions = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, dimensions = False)
                if eachSetting.text() == 'Pivots':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, pivots = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, pivots = False)
                if eachSetting.text() == 'Handles':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, handles = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, handles = False)
                if eachSetting.text() == 'Textures':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, textures = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, textures = False)
                if eachSetting.text() == 'Strokes':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, strokes = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, strokes = False)
                if eachSetting.text() == 'Motion Trails':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, motionTrails = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, motionTrails = False)
                if eachSetting.text() == 'Manipulators':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, manipulators = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, manipulators = False)
                if eachSetting.text() == 'Clip Ghosts':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, clipGhosts = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, clipGhosts = False)
                if eachSetting.text() == "NURBS CV's":
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, controlVertices = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, controlVertices = False)
                if eachSetting.text() == 'NURBS Hulls':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, hulls = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, hulls = False)
                if eachSetting.text() == 'Grid':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, grid = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, grid = False)
                if eachSetting.text() == 'HUD':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, headsUpDisplay = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, headsUpDisplay = False)
                if eachSetting.text() == 'Image Planes':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, imagePlane = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, imagePlane = False)
                if eachSetting.text() == 'Selection Highlighting':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, selectionHiliteDisplay = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, selectionHiliteDisplay = False)
                if eachSetting.text() == 'Texture Placements':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, textures = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, textures = False)
                if eachSetting.text() == 'Plugin Shapes':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, pluginShapes = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, pluginShapes = False)
                if eachSetting.text() == 'GPU Caches':
                    try:## Extension only
                        if eachSetting.isChecked():
                            cmds.modelEditor(self.editor, edit = True,  pluginObjects = ['gpuCacheDisplayFilter', True])
                        else:
                            cmds.modelEditor(self.editor, edit = True, pluginObjects = ['gpuCacheDisplayFilter', False])
                    except:
                        pass
                if eachSetting.text() == 'Nurbs CVs':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, cv = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, cv = False)
                if eachSetting.text() == 'Nurbs CVs':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, cv = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, cv = False)
                if eachSetting.text() == 'Use Default Mat':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, useDefaultMaterial = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, useDefaultMaterial = False)
                if eachSetting.text() == 'X-Ray':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, xray = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, xray = False)
                if eachSetting.text() == 'X-Ray Joints':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, jointXray = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, jointXray = False)
                if eachSetting.text() == 'Hardware Texturing':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, displayTextures = True, displayAppearance='smoothShaded', displayLights = "default")
                        for eachSetting in self.viewportRadioButtons:
                            if eachSetting.text() == 'SmoothShade All':
                                eachSetting.setChecked(True)
                            if eachSetting.text()  == 'WireFrame':
                                eachSetting.setEnabled(False)
                            if eachSetting.text()  == 'Bounding Box':
                                eachSetting.setEnabled(False)

                    else:
                        cmds.modelEditor(self.editor, edit = True, displayTextures = False)
                        for eachSetting in self.viewportRadioButtons:
                            if eachSetting.text()  == 'WireFrame':
                                eachSetting.setEnabled(True)
                            if eachSetting.text()  == 'Bounding Box':
                                eachSetting.setEnabled(True)

                if eachSetting.text() == 'WireFrame':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, displayAppearance = "wireframe")
                if eachSetting.text() == 'SmoothShade All':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, displayAppearance = "smoothShaded")
                if eachSetting.text() == 'Bounding Box':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, displayAppearance = "boundingBox")
                if eachSetting.text() == 'Wireframe on Shaded':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, displayAppearance = "smoothShaded", activeOnly = False, wireframeOnShaded = True)
                        for eachSetting in self.viewportRadioButtons:
                            if eachSetting.text() == 'SmoothShade All':
                                eachSetting.setChecked(True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, wireframeOnShaded = False)
                if eachSetting.text() == 'Default Renderer':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, rendererName =  'base_OpenGL_Renderer')
                if eachSetting.text() == 'Viewport 2.0':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, rendererName = 'ogsRenderer')

        logger.info('Done processing each radio setting')

    def doPlayblast(self):
        """
        Double check the comment. Then grab some settings and do the main thread.
        """
        comment = self.comment.text()
        if self.upload.isChecked():
            if comment == '':
                logger.info('You must set a valid comment for review!')
                QtGui.QMessageBox.information(None, "Aborted...", 'Please put a valid comment.')
                return -1

        work_template   = self.app.get_template('template_work')
        width           = self.app.get_setting("movie_width")
        height          = self.app.get_setting("movie_height")
        isAsset         = self.app.get_setting("isAsset")
        user            = tank.util.get_current_user(self.app.tank)

        self._setupPlayblast(work_template, width, height, comment, isAsset, user)

    def _setupPlayblast(self, work_template, width, height, comment, isAsset, user):
        """
        This is the main method to processs the playblast
        """
        # Is the app configured to do anything?
        store_on_disk = self.app.get_setting("store_on_disk")
        if not self.upload_to_shotgun and not store_on_disk:
            logger.info("App is not configured to store playblast on disk nor upload to shotgun! Check the shot_step.yml to fix this.")
            return None

        ## Double check the artist wants to playblast.
        self.reply = QtGui.QMessageBox.question(None, 'Continue with playblast?', "Do you wish to playblast now? \nNow is a good time to save a new vers scene if you haven't already...", QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)
        if self.reply == QtGui.QMessageBox.Ok:
            ## Check the playblast ranged against shotguns cut in and out.
            logger.info('_setupPlayblast')
            self._setFrameRanges(isAsset)
            logger.info('_setupPlayblast')

            ## Now setup the output path for the mov
            scene_path = os.path.abspath(cmds.file(query=True, sn= True))
            try:
                fields = work_template.get_fields(scene_path)
            except:
                QtGui.QMessageBox.information(None, "Aborted...", 'Please save your scene first before continuing. And relaunch the playblast tool...')
                return -1

            logger.info('fields: %s' % fields)
            publish_path_template   = self.app.get_template("movie_path_template")
            publish_path            = publish_path_template.apply_fields(fields)
            work_path_template      = self.app.get_template("movie_workpath_template")
            work_path               = work_path_template.apply_fields(fields)

            logger.info('publish_path_template: %s' % publish_path_template)
            logger.info('publish_path: %s' % publish_path)
            logger.info('work_path_template: %s' % work_path_template)
            logger.info('work_path: %s' % work_path)

            if sys.platform == 'win32':
                self.osPathToWorkFile = r'%s' % work_path
                self.osPathToPublishFile = r'%s' % publish_path

            ## Now query the first and last frames of the animation
            getFirstFrame = cmds.playbackOptions(query = True, animationStartTime = True)
            getLastFrame = cmds.playbackOptions(query = True, animationEndTime = True)

            ## logging Info
            logger.info('Width: \t\t%s' % width)
            logger.info('Height: \t%s' % height)
            logger.info('Comment: \t%s' % comment)
            logger.info('isAsset: \t%s' % isAsset)
            logger.info('UserName: \t%s' % user)
            logger.info('scene_path: \t%s' % scene_path)
            logger.info('fields: \t%s' % fields)
            logger.info('WorkTemplate: \t%s' %  work_template)
            logger.info('publish_path_template: \t%s' % publish_path_template)
            logger.info('publish_path: \t%s' % publish_path)
            logger.info('work_path_template: \t%s' % work_path_template)
            logger.info('work_path: \t%s' % work_path)
            logger.info('osPathToWorkFile: \t%s' % self.osPathToWorkFile.replace('\\', '/'))
            logger.info('osPathToPublishFile: \t%s' % self.osPathToPublishFile.replace('\\', '/'))

            ## Now check for existing playblast. We check the publish folder because the working file gets moved into publish on upload.
            ## The playblast tool overwrites any playblasts it does with the same version name in the working directory.
            if self._checkVersionExists(name = os.path.splitext(os.path.basename(publish_path))[0]):
                cmds.warning(self.EXISTSWARNING)
                return -1
            else:
                self._finishPlayblast(publish_path, width, height, store_on_disk, getFirstFrame, getLastFrame, comment, user, work_path)

    def setProgress(self, progress):
        self.progressBar.setValue(progress)

    def _finishPlayblast(self, publish_path, width, height, store_on_disk, getFirstFrame, getLastFrame, comment, user, work_path):
        ## Now do the playblast if the user selected okay or there wasn't a duplicate found.
        logger.info('Duplicate check passed. Playblasting...')

        ## Now render the playblast
        self._render_pb_in_maya(getFirstFrame, getLastFrame, publish_path, work_path, width, height)
        logger.info('PlayBlast finished..')

        ## Check if uploading is enabled in the UI and do the uploading if it is, else we will finish up here.
        if self.upload.isChecked():
            logger.info('Upload is turned on.. processing version to sg now..')

            ## Move the working file to the publish path
            try:
                logger.info('RENAMING: osPathToWorkFile to osPathToPublishFile')
                os.rename(self.osPathToWorkFile.replace('\\', '/'), self.osPathToPublishFile.replace('\\', '/'))
            except:
                logger.info('FAILED: \tTo rename osPathToWorkFile to osPathToPublishFile')
                ## This could fail because the process is in use, and not the fact a freaking published file exists, due to maya trying to open the playblast once it's done!
                ## So a quick check here to make sure it doesn't exist.. if it doesn't and it failed COPY it instead. FU maya...
                if not os.path.exists(publish_path):
                    logger.info('FAILED: \tTo rename because file is IN USE. Using shutil to copy instead.')
                    shutil.copyfile(self.osPathToWorkFile.replace('\\', '/'), self.osPathToPublishFile.replace('\\', '/'))
                else:
                    logger.info('FAILED: \tTo rename because file already exists.. how the heck the remove previously failed.. who knows.. but try again now..')
                    os.remove(self.osPathToPublishFile.replace('\\', '/'))
                    os.rename(self.osPathToWorkFile.replace('\\', '/'), self.osPathToPublishFile.replace('\\', '/'))

            ## Now submit the version to shotgun
            logger.info('Submitting vesion info to shotgun...')

            ## Doing a double check here for existing version in shotgun just to be on the safe side.
            if not self._checkVersionExists(name = os.path.splitext(os.path.basename(publish_path))[0]):
                sg_version = self._submit_version(
                                                  path_to_movie     = publish_path,
                                                  store_on_disk     = store_on_disk,
                                                  first_frame       = getFirstFrame,
                                                  last_frame        = getLastFrame,
                                                  comment           = comment,
                                                  user              = user
                                                  )
                logger.info('Version Submitted to shotgun successfully')

                ## Uploading...
                ## Now upload in a new thread and make our own event loop to wait for the thread to finish.
                self.progressBar        = self.lib.ProgressBarUI()
                self.progressBar.show()

                logger.info('Uploading mov to shotgun for review.')

                ######################################
                ##### THE EVENT LOOP THREAD TO UPLOAD
                event_loop = QtCore.QEventLoop()
                logger.info('event_loop set...')

                fileSize            = os.stat('%s' % publish_path)
                fileInMB            = float(fileSize.st_size/1000000)
                ##speed : 100 KBs 6mb per 60seconds approx
                timeToUploadSecs    = (fileInMB/6)*100
                step                = timeToUploadSecs/100
                logger.info('step: %s' % step)

                thread              = self.lib.UploaderThread(self.app, sg_version, publish_path, self.upload_to_shotgun)
                logger.info('thread set...')
                thread.finished.connect(self.progressBar.hide)
                thread.finished.connect(event_loop.quit)
                thread.start()
                x = 1
                i = 0
                while (x > 0):
                    threadRunning = thread.isRunning()
                    if threadRunning:
                        self.progressBar.updateProgress(i, os.path.splitext(os.path.basename(publish_path))[0])
                        i = i + 1
                        time.sleep(step)
                    else:
                        x = 0
                logger.info('thread started...')
                event_loop.exec_()

                logger.info('event_loop.exec_...')
                ######################################
                ### THREAD FNISHED....

                ## log any errors generated in the thread
                for e in thread.get_errors():
                    self.app.log_error(e)
                    print e

                ## Remove from file system if required
                if not store_on_disk and os.path.exists(publish_path):
                    os.unlink(publish_path)

                ## Remove turntable if option is selected
                if self.app.get_setting('isAsset'):
                    if self.deleteHrcGrp.isChecked():
                        cmds.delete('turnTable_hrc')

                logger.info('Upload to shotgun finished.')
                cmds.warning('UPLOAD COMPLETE!')

            else:
                cmds.warning(self.EXISTSWARNING)

    def _setFrameRanges(self, isAsset):
        """
        STOLEN FROM tk-multi-setframerange v0.1.7
        Sets the in and out according to shotgun
        Requires a valid cut in and cut out to be set in the shotgun db
        """
        if isAsset:
                getFirstFrame   = cmds.playbackOptions(query = True, animationStartTime = True)
                getLastFrame    = cmds.playbackOptions(query = True, animationEndTime = True)
                self.set_frame_range(self.app.engine.name, getFirstFrame, getLastFrame)
        else:
            (new_in, new_out)           = self.get_frame_range_from_shotgun()
            (current_in, current_out)   = self.get_current_frame_range(self.app.engine.name)
            if new_in is None or new_out is None:
                # lazy import so that this script still loads in batch mode
                message =  "Shotgun has not yet been populated with \n"
                message += "in and out frame data for this Shot."
                # present a pyside dialog
                QtGui.QMessageBox.information(None, "ERROR", message)
            elif int(new_in) != int(current_in) or int(new_out) != int(current_out):
                # change!
                message = "Your scene has been updated with the \n"
                message += "latest frame ranges from shotgun.\n\n"
                message += "Previous start frame: %d\n" % current_in
                message += "New start frame: %d\n\n" % new_in
                message += "Previous end frame: %d\n" % current_out
                message += "New end frame: %d\n\n" % new_out
                print message## Print the message so we can continue without user prompting....
                self.set_frame_range(self.app.engine.name, new_in, new_out)
                return
            else:
                pass

    def get_frame_range_from_shotgun(self):
        """
        STOLEN FROM tk-multi-setframerange v0.1.7
        Returns (in, out) frames from shotgun.
        """
        # we know that this exists now (checked in init)
        entity          = self.app.context.entity

        sg_entity_type  = self.app.context.entity["type"]
        sg_filters      = [["id", "is", entity["id"]]]

        sg_in_field     = self.app.get_setting("sg_in_frame_field")
        sg_out_field    = self.app.get_setting("sg_out_frame_field")
        fields          = [sg_in_field, sg_out_field]

        data            = self.app.shotgun.find_one(sg_entity_type, filters=sg_filters, fields=fields)

        # check if fields exist!
        if sg_in_field not in data:
            raise tank.TankError("Configuration error: Your current context is connected to a Shotgun "
                                 "%s. This entity type does not have a "
                                 "field %s.%s!" % (sg_entity_type, sg_entity_type, sg_in_field))

        if sg_out_field not in data:
            raise tank.TankError("Configuration error: Your current context is connected to a Shotgun "
                                 "%s. This entity type does not have a "
                                 "field %s.%s!" % (sg_entity_type, sg_entity_type, sg_out_field))

        return ( data[sg_in_field], data[sg_out_field] )

    def get_current_frame_range(self, engine):
        """
        STOLEN FROM tk-multi-setframerange v0.1.7
        """
        if engine == "tk-maya":
            current_in = cmds.playbackOptions(query=True, minTime= True)
            current_out = cmds.playbackOptions(query=True, maxTime= True)
        else:
            raise tank.TankError("Don't know how to get current frame range for engine %s!" % engine)
        return (current_in, current_out)

    def set_frame_range(self, engine, in_frame, out_frame):
        """
        STOLEN FROM tk-multi-setframerange v0.1.7
        """
        if engine == "tk-maya":
            import pymel.core as pm
            # set frame ranges for plackback
            pm.playbackOptions(minTime=in_frame,
                               maxTime=out_frame,
                               animationStartTime=in_frame,
                               animationEndTime=out_frame)
            # set frame ranges for rendering
            defaultRenderGlobals = pm.PyNode('defaultRenderGlobals')
            defaultRenderGlobals.startFrame.set(in_frame)
            defaultRenderGlobals.endFrame.set(out_frame)
        else:
            raise tank.TankError("Don't know how to set current frame range for engine %s!" % engine)

    def _checkVersionExists(self, name):
        ## Instance the api for talking directly to shotgun.
        try:
            ## Try getting it from the default config CONST first
            base_url        = configCONST.SHOTGUN_URL
            script_name     = configCONST.SHOTGUN_TOOLKIT_NAME
            api_key         = configCONST.SHOTGUN_TOOLKIT_API_KEY
        except:
            ## Else get from the lib CONST
            base_url       = self.lib.SHOTGUN_URL
            script_name    = self.lib.SHOTGUN_TOOLKIT_NAME
            api_key        = self.lib.SHOTGUN_TOOLKIT_API_KEY

        logger.info('base_url: %s' % base_url)
        logger.info('script_name: %s' % script_name)
        logger.info('api_key: %s' % api_key)

        self.sgsrv      = Shotgun(base_url = base_url, script_name = script_name, api_key = api_key, ensure_ascii=True, connect=True)
        logger.info('self.sgsrv%s' % self.sgsrv)

        exists = self.sgsrv.find_one('Version', filters = [["code", "is", name]], fields = ['code'])
        if exists:
            return True
        else:
            return False

    def _submit_version(self, path_to_movie, store_on_disk, first_frame, last_frame, comment, user):
        """
        Create a version in Shotgun for this path and linked to this publish.
        """
        # get current shotgun user
        current_user    = user
        name            = os.path.splitext(os.path.basename(path_to_movie))[0]
        # create a name for the version based on the file name grab the file name, strip off extension
        # do some replacements
        name            = name.replace("_", " ")
        # and capitalize
        name            = name.capitalize()
        data = {
            "code":         name,
            "entity":       self.app.context.entity,
            "sg_task":      self.app.context.task,
            "user":         current_user,
            "created_by":   current_user,
            "project":      self.app.context.project,
            "description":  comment,
            "sg_status_list": self.statusList.currentText()
        }
        if store_on_disk:
            data["sg_path_to_movie"] = path_to_movie

        sg_version = self.app.tank.shotgun.create("Version", data)
        return sg_version

    def _render_pb_in_maya(self, first_frame, last_frame, publish_path, work_path, width, height):
        """
        Method to handle the playblast in maya
        NOTE: May need to add an active viewport update here in case the operator had a different window selected.
        """
        logger.info('self.qualityPercent.value: %s' % self.qualityPercent.value())
        ## Clear selection in case the operator had something selected.
        cmds.select(clear = True)

        ## Now set the current editor to be the currently active view
        cmds.modelEditor(self.currentEditor, e = True, activeView = True)

        ## Find sound files and use the first found if there are more than one.
        soundFiles = cmds.ls(type = 'audio')
        if soundFiles:
            sound = soundFiles[0]
            if len(soundFiles) > 1:
                cmds.warning('More than one audio track in scene, using the first found in the list: \n\t\AUDIO: %s' % soundFiles[0])
        else:
            cmds.warning('No sound files found...')
            sound  = None

        logger.info('sound: %s' % sound)

        ############################
        ## Now do the main playblast
        if self.upload_to_shotgun:
            viewer = False
        else:
            viewer = self.lib.PB_VIEWER

        logger.info('Playblasing to work_path: %s' % work_path)
        cmds.playblast(
                        filename        = work_path,
                        activeEditor    = self.lib.PB_ACTIVEEDITOR,
                        clearCache      = self.lib.PB_CLEARCACHE,
                        combineSound    = self.lib.PB_COMBINESOUND,
                        compression     = self.lib.PB_COMPRESSION,
                        startTime       = first_frame,
                        endTime         = last_frame + 1,
                        forceOverwrite  = self.lib.PB_FORCEOVERWRITE,
                        format          = self.lib.PB_FORMAT,
                        framePadding    = self.lib.PB_FRAMEPADDING,
                        offScreen       = self.lib.PB_OFFSCREEN,
                        options         = self.lib.PB_OPTIONS,
                        percent         = self.sizePercent.value(),
                        quality         = self.qualityPercent.value(),
                        sequenceTime    = self.lib.PB_SEQUENCETIME,
                        showOrnaments   = self.lib.PB_SHOWORNAMENTS,
                        viewer          = viewer,
                        widthHeight     = [width, height],
                        sound           = sound
                        )

    def _setupRenderGlobals(self):
        """
        Used to setup your renderGlobals.
        We set the start and end times and the default widths and then call the external for studio customisation.
        """
        # Set globals default resolution
        cmds.setAttr('defaultResolution.width', self.renderWidth)
        cmds.setAttr('defaultResolution.height', self.renderHeight)
        cmds.setAttr('defaultResolution.pixelAspect', 1)
        cmds.setAttr('defaultResolution.deviceAspectRatio', 1.7778)

        ## Setup any custom globals from the users lib file.
        self.lib.setRenderGlobals()

        ## Setup the viewport 2.0 HW globals
        self._setupVP2()
        print 'Default render settings initialized.'

    def _setupVP2(self):
        #cmds.optionMenuGrp('VP20multisampleMenu', e = True,  value = 16)
        #cmds.attrFieldSliderGrp('attrFieldSliderGrp21', e = True, en = True)
        #cmds.setAttr("hardwareRenderingGlobals.textureMaxResolution", 128)
        cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", self.lib.HW_MULTI_SAMPLE_ENABLE)
        cmds.setAttr("hardwareRenderingGlobals.ssaoEnable", self.lib.HW_SSAC_ENABLE)
        cmds.setAttr("hardwareRenderingGlobals.ssaoAmount", self.lib.HW_SSAC_AMOUNT)
        cmds.setAttr("hardwareRenderingGlobals.ssaoRadius", self.lib.HW_SSAC_RADIUS)
        cmds.setAttr("hardwareRenderingGlobals.ssaoFilterRadius", self.lib.HW_FILTER_RADIUS)
        cmds.setAttr("hardwareRenderingGlobals.ssaoSamples", self.lib.HW_SSAO_SAMPLES)
        cmds.setAttr("hardwareRenderingGlobals.consolidateWorld", self.lib.HW_CONSOLODATEWORLD)