"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------

Code for a maya playblast creator app that runs in maya
"""
import os, sys, shutil
from functools import partial
###################################
## Maya Imports                  ##
import maya.cmds as cmds
###################################
## Shotgun Imports               ##
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import tank.templatekey


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
        ## Grab the library python stuff from lib
        self.lib = self.app.import_module("lib")
        self.lib.log(self.app, method = 'Main_UI', message = 'INIT PlayBlastGenerator UI', printToLog = False, verbose = self.lib.DEBUGGING)

        ## Check to make sure there is a valid context set
        if self.app.context.entity is None:
            self.lib.log(app = self.app, message = "Cannot load the PlayBlast application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.", printToLog = False, verbose = self.lib.DEBUGGING)
        else:
            ## Grab the application settings now...
            self.upload_to_shotgun  = self.app.get_setting("upload_to_shotgun")
            self.renderWidth        = self.app.get_setting('movie_width')
            self.renderHeight       = self.app.get_setting('movie_height')

            ## The current model editor is...
            self.currentEditor = self._getEditor()
            self.lib.log(app = self.app, method = 'MainUI', message = 'Active Editor: %s' % self.currentEditor, printToLog = False, verbose = self.lib.DEBUGGING)

            ## These two are used for the os module when doing a os.rename for windows
            self.osPathToWorkFile       = ''
            self.osPathToPublishFile    = ''

            ## Now build the main UI
            self._buildUI()

            ## Resize the UI
            self.resize(self.sizeHint())

    def _buildUI(self):
        self.lib.log(app = self.app, method = '_buildUI', message = 'ValidContextFound.. building UI', printToLog = False, verbose = self.lib.DEBUGGING)
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
        self.lib.log(app = self.app, method = '_buildUI', message = 'Building cameraSettings', printToLog = False, verbose = self.lib.DEBUGGING)
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
        self.lib.log(app = self.app, method = '_buildUI', message = 'Building viewportSettings', printToLog = False, verbose = self.lib.DEBUGGING)
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
        self.lib.log(app = self.app, method = '_buildUI', message = 'Building renderSettings', printToLog = False, verbose = self.lib.DEBUGGING)
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
            self.lib.log(app = self.app, method = '_buildUI', message = 'Showing Asset UI', printToLog = False, verbose = self.lib.DEBUGGING)
            self._buildAssetTurntableUI()

        ############################################################################################
        ## COMMENT GROUP BOX
        ############################################################################################
        self.lib.log(app = self.app, method = '_buildUI', message = 'Building Comment Layout', printToLog = False, verbose = self.lib.DEBUGGING)
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
        self.lib.log(app = self.app, method = '_buildUI', message = 'Building Submission Layout', printToLog = False, verbose = self.lib.DEBUGGING)
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
        self.lib.log(app = self.app, method = '_buildUI', message = 'Building final Layout', printToLog = False, verbose = self.lib.DEBUGGING)
        self.mainLayout.addWidget(self.infoGroupBox)
        self.mainLayout.addWidget(self.cameraSettingsGroupBox)
        self.mainLayout.addWidget(self.viewportSettingsGroupBox)
        self.mainLayout.addWidget(self.rendererSettingsGroupBox)
        if self.app.get_setting('isAsset'):
            if self.app.get_setting('allowAssetTurnTableBuild'):
                self.mainLayout.addWidget(self.turnTableGroupBox)
            else:
                pass
        else:
            self._setupShotCamera()
        self.mainLayout.addWidget(self.submissionGroupBox)
        self.mainLayout.addWidget(self.commentGroupBox)
        self.mainLayout.addStretch(1)

        ###############################################################################
        ## Now show or hide the options if the showOptions is turned on else hide these
        if not self.app.get_setting('showOptions'):
            self.groupBoxes = [self.infoGroupBox, self.cameraSettingsGroupBox, self.viewportSettingsGroupBox, self.rendererSettingsGroupBox]
            for each in self.groupBoxes:
                each.hide()

        #######################################
        ## Process all the radio button options
        self._processRadioButtons()
        self.lib.log(app = self.app, method = 'MainUI', message = '_processRadioButtons successful...', printToLog = False, verbose = self.lib.DEBUGGING)

        #############################
        ## Now set the render globals
        if self.app.get_setting('isAsset'):
            self._setRenderGlobals(animation = False)
        else:
            self._setRenderGlobals(animation = True)

        self.lib.log(app = self.app, method = 'MainUI', message = 'UI Built Successfully...', printToLog = False, verbose = self.lib.DEBUGGING)

    def _uploadToggle(self):
        if self.upload.isChecked():
             self.commentGroupBox.show()
             self.upload.setStyleSheet('QRadioButton:indicator{background-color: #088A08}')
        else:
            self.commentGroupBox.hide()
            self.upload.setStyleSheet('QRadioButton:indicator{background-color: #B40404}')

    def _getEditor(self):
        currentPanel = cmds.getPanel(withFocus = True)
        if 'modelPanel' not in currentPanel:
            QtGui.QMessageBox.information(None, "Aborted...", 'You must have active a current 3D viewport! \nRight click the viewport you wish to playblast from.')
            return -1
        else:
            currentEditor = cmds.modelPanel(currentPanel, q = True, modelEditor = True)
            self.lib.log(app = self.app, method = '_getEditor', message = 'Current Editor is: %s' % currentEditor, printToLog = False, verbose = self.lib.DEBUGGING)
            self.currentEditor = currentEditor
            return currentEditor

    def _setupShotCamera(self):
        """
        Shot camera setup
        """
        try:
            cameraSuffix = configCONST.SHOTCAM_SUFFIX
        except:
            camerSuffix = self.lib.SHOTCAM_SUFFIX
        camera = []
        self.lib.log(app = self.app, method = '_setupShotCamera', message = 'Finding camera..', printToLog = False, verbose = self.lib.DEBUGGING)
        for each in cmds.ls(type = 'camera'):
            getCamTransform = cmds.listRelatives(each, parent = True)[0]
            self.lib.log(app = self.app, method = '_setupShotCamera', message = 'getCamTransform.. %s' % getCamTransform, printToLog = False, verbose = self.lib.DEBUGGING)
            if cmds.objExists('%s.type' % getCamTransform):
                camera.append(each)

        self.lib.log(app = self.app, method = '_setupShotCamera', message = 'List of cameras found: %s' % camera, printToLog = False, verbose = self.lib.DEBUGGING)
        
        if not camera:
            self.lib.log(app = self.app, method = '_setupShotCamera',  message ="No shotCam found!", printToLog = False, verbose = self.lib.DEBUGGING)
            QtGui.QMessageBox.information(None, "Aborted...", 'No shotCam found!!')
            return -1
        else:
            if len(camera) > 1:
                self.lib.log(app = self.app, method = '_setupShotCamera',  message ="More than one camera found. Please make sure you only have one shot camera in your scene!", printToLog = False, verbose = self.lib.DEBUGGING)
                QtGui.QMessageBox.information(None, "Aborted...", 'Make sure you have only ONE shot camera in the scene!')
                return -1
            else:
                cam = camera[0]
                cmds.modelEditor(self.currentEditor, edit = True, camera = cam)
                getCamTransform = cmds.listRelatives(cam, parent = True)[0] ## need to send the camera transform to this function
                self.lib._setCameraDefaults(getCamTransform)

    def _buildAssetTurntableUI(self):
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

    def _setRenderGlobals(self, animation):
        self.lib.log(app = self.app, method = '_setRenderGlobals', message = 'Setting render globals now..', printToLog = False, verbose = self.lib.DEBUGGING)
        ## Now try to setup the renderglobals if using the default config
        try:
            self._setupRenderGlobals(width = self.renderWidth, height = self.renderHeight, animation = animation)
        except:
            pass
        self.lib.log(app = self.app, method = '_setRenderGlobals', message = 'DONE setting render globals..', printToLog = False, verbose = self.lib.DEBUGGING)

    def _setupTurnTable(self, geoGroup = '', start = '', frames = ''):
        """
        Builds a camera for turn table
        """
        self.lib.log(app = self.app, message = '_setupTurnTable run...', printToLog = False, verbose = self.lib.DEBUGGING)
        geoGroup    = geoGroup.getText()
        start       = start.value()
        frames      = frames.value()
        
        ## Now check for existing and delete it.
        if cmds.objExists('turnTable_hrc'):
            self.lib.log(app = self.app, message = 'Removed existing turnTable...', printToLog = False, verbose = self.lib.DEBUGGING)
            cmds.delete('turnTable_hrc')
        
        ## Build the camera for the turnTable
        cameraName  = 'turnTable%s' % self.app.get_setting('cameraSuffix')
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
        self.lib.log(app = self.app, method = '_processRadioButtons', message = 'Processing the radioButtonStates', printToLog = False, verbose = self.lib.DEBUGGING)
        self.lib.log(app = self.app, method = '_processRadioButtons', message = 'CurrentEditor is: %s' % self.currentEditor, printToLog = False, verbose = self.lib.DEBUGGING)
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
                if eachSetting.text() == 'Subdiv Surfaces' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, subdivSurfaces = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, subdivSurfaces = False)
                if eachSetting.text() == 'Planes' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, planes = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, planes = False)
                if eachSetting.text() == 'Lights' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, lights = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, lights = False)
                if eachSetting.text() == 'Cameras' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, cameras = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, cameras = False)
                if eachSetting.text() == 'Joints' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, joints = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, joints = False)
                if eachSetting.text() == 'IK Handles' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, ikHandles = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, ikHandles = False)
                if eachSetting.text() == 'Deformers' :
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
                if eachSetting.text() == 'Grid' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, grid = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, grid = False)
                if eachSetting.text() == 'HUD' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, headsUpDisplay = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, headsUpDisplay = False)
                if eachSetting.text() == 'Image Planes' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, imagePlane = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, imagePlane = False)
                if eachSetting.text() == 'Selection Highlighting' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, selectionHiliteDisplay = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, selectionHiliteDisplay = False)
                if eachSetting.text() ==  'Texture Placements' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, textures = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, textures = False)
                if eachSetting.text() ==  'Plugin Shapes' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, pluginShapes = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, pluginShapes = False)
                if eachSetting.text() ==  'GPU Caches' :
                    try:## Extension only
                        if eachSetting.isChecked():
                            cmds.modelEditor(self.editor, edit = True,  pluginObjects = ['gpuCacheDisplayFilter', True])
                        else:
                            cmds.modelEditor(self.editor, edit = True, pluginObjects = ['gpuCacheDisplayFilter', False])
                    except:
                        pass
                if eachSetting.text() ==  'Nurbs CVs' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, cv = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, cv = False)
                if eachSetting.text() ==  'Nurbs CVs' :
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
                            if eachSetting.text() ==  'SmoothShade All' :
                                eachSetting.setChecked(True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, displayTextures = False)
                if eachSetting.text() ==  'WireFrame' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, displayAppearance = "wireframe")
                if eachSetting.text() ==  'SmoothShade All' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, displayAppearance = "smoothShaded")
                if eachSetting.text() ==  'Bounding Box' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, displayAppearance = "boundingBox")
                if eachSetting.text() ==  'Wireframe on Shaded' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, displayAppearance = "smoothShaded", activeOnly = False, wireframeOnShaded = True)
                        for eachSetting in self.viewportRadioButtons:
                            if eachSetting.text() ==  'SmoothShade All' :
                                eachSetting.setChecked(True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, wireframeOnShaded = False)
                if eachSetting.text() ==  'Default Renderer' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, rendererName =  'base_OpenGL_Renderer')
                if eachSetting.text() == 'Viewport 2.0':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, rendererName = 'ogsRenderer')
                        cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)
                        #cmds.optionMenuGrp('VP20multisampleMenu', e = True,  value = 16)
                        #cmds.attrFieldSliderGrp('attrFieldSliderGrp21', e = True, en = True)
                        #cmds.setAttr("hardwareRenderingGlobals.textureMaxResolution", 128)
                        cmds.setAttr("hardwareRenderingGlobals.ssaoEnable", 1)
                        cmds.setAttr("hardwareRenderingGlobals.ssaoAmount", 1.5)
                        cmds.setAttr("hardwareRenderingGlobals.ssaoRadius", 10)
                        cmds.setAttr("hardwareRenderingGlobals.ssaoFilterRadius", 10)
                        cmds.setAttr("hardwareRenderingGlobals.ssaoSamples", 32)
                        cmds.setAttr("hardwareRenderingGlobals.consolidateWorld", 1)
        self.lib.log(app = self.app, method = '_processRadioButtons', message = 'Done processing each radio setting', printToLog = False, verbose = self.lib.DEBUGGING)
        
    def doPlayblast(self):
        """
        Double check the comment. Then grab some settings and do the main thread.
        """
        comment = self.comment.text() 
        if self.upload.isChecked():
            if comment == '':
                self.lib.log(app = self.app, message = 'You must set a valid comment for review!', printToLog = False, verbose = self.lib.DEBUGGING)
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
            self.lib.log(app = self.app, message ="App is not configured to store playblast on disk nor upload to shotgun! Check the shot_step.yml to fix this.", printToLog = False, verbose = self.lib.DEBUGGING)
            return None
        
        ## Double check the artist wants to playblast.
        self.reply = QtGui.QMessageBox.question(None, 'Continue with playblast?', "Do you wish to playblast now? \nNow is a good time to save a new vers scene if you haven't already...", QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)
        if self.reply == QtGui.QMessageBox.Ok:
            ## Check the playblast ranged against shotguns cut in and out.
            self.lib.log(app = self.app, method = '_setupPlayblast', message = 'QtGui.QMessageBox.Ok accepted', printToLog = False, verbose = self.lib.DEBUGGING)
            self._setFrameRanges(isAsset)
            self.lib.log(app = self.app, method = '_setupPlayblast', message = '_setFrameRanges finished', printToLog = False, verbose = self.lib.DEBUGGING)
            ## Now setup the output path for the mov
            scene_path = os.path.abspath(cmds.file(query=True, sn= True))
            try:
                fields = work_template.get_fields(scene_path)
            except:
                QtGui.QMessageBox.information(None, "Aborted...", 'Please save your scene first before continuing. And relaunch the playblast tool...')
                return -1
            publish_path_template = self.app.get_template("movie_path_template")
            publish_path = publish_path_template.apply_fields(fields)
            work_path_template = self.app.get_template("movie_workpath_template")
            work_path = work_path_template.apply_fields(fields)
            self.lib.log(app = self.app, message = 'work_path: %s' % work_path, printToLog = False, verbose = self.lib.DEBUGGING)
            
            if sys.platform == 'win32':
                self.osPathToWorkFile = r'%s' % work_path
                self.osPathToPublishFile = r'%s' % publish_path
                
            ## Now query the first and last frames of the animation
            getFirstFrame = cmds.playbackOptions(query = True, animationStartTime = True)
            getLastFrame = cmds.playbackOptions(query = True, animationEndTime = True)

            ## logging Info
            self.lib.log(app = self.app, method = '_setupPlayblast', message = 'Width: \t\t%s' % width, printToLog = False, verbose = self.lib.DEBUGGING)
            self.lib.log(app = self.app, method = '_setupPlayblast', message = 'Height: \t%s' % height, printToLog = False, verbose = self.lib.DEBUGGING)
            self.lib.log(app = self.app, method = '_setupPlayblast', message = 'Comment: \t%s' % comment, printToLog = False, verbose = self.lib.DEBUGGING)
            self.lib.log(app = self.app, method = '_setupPlayblast', message = 'isAsset: \t%s' % isAsset, printToLog = False, verbose = self.lib.DEBUGGING)
            self.lib.log(app = self.app, method = '_setupPlayblast', message = 'UserName: \t%s' % user, printToLog = False, verbose = self.lib.DEBUGGING)
            self.lib.log(app = self.app, method = '_setupPlayblast', message = 'scene_path: \t%s' % scene_path, printToLog = False, verbose = self.lib.DEBUGGING)
            self.lib.log(app = self.app, method = '_setupPlayblast', message = 'fields: \t%s' % fields, printToLog = False, verbose = self.lib.DEBUGGING)
            self.lib.log(app = self.app, method = '_setupPlayblast', message = 'WorkTemplate: \t%s' %  work_template, printToLog = False, verbose = self.lib.DEBUGGING)
            self.lib.log(app = self.app, method = '_setupPlayblast', message = 'publish_path_template: \t%s' % publish_path_template, printToLog = False, verbose = self.lib.DEBUGGING)
            self.lib.log(app = self.app, method = '_setupPlayblast', message = 'publish_path: \t%s' % publish_path, printToLog = False, verbose = self.lib.DEBUGGING)
            self.lib.log(app = self.app, method = '_setupPlayblast', message = 'work_path_template: \t%s' % work_path_template, printToLog = False, verbose = self.lib.DEBUGGING)
            self.lib.log(app = self.app, method = '_setupPlayblast', message = 'work_path: \t%s' % work_path, printToLog = False, verbose = self.lib.DEBUGGING)
            self.lib.log(app = self.app, method = '_setupPlayblast', message = 'osPathToWorkFile: \t%s' % self.osPathToWorkFile.replace('\\', '/'), printToLog = False, verbose = self.lib.DEBUGGING)
            self.lib.log(app = self.app, method = '_setupPlayblast', message = 'osPathToPublishFile: \t%s' % self.osPathToPublishFile.replace('\\', '/'), printToLog = False, verbose = self.lib.DEBUGGING)
            
            ## Now check for existing playblast. We check the publish folder because the working file gets moved into publish on upload.
            ## The playblast tool overwrites any playblasts it does with the same version name in the working directory.
            if os.path.exists(publish_path):
                self.lib.log(app = self.app, message = "Existing published playblast found with same version number....", printToLog = False, verbose = self.lib.DEBUGGING)
                self.reply = QtGui.QMessageBox.question(None, 'IMPORTANT!!!!!', "Existing published playblast found!!!!\nIf for some reason the previous blast didn't upload click okay to redo the playblast now.\nOtherwise CANCEL NOW and save a new version of your scene or you will end up with duplicates in shotgun!", QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)
                if self.reply == QtGui.QMessageBox.Ok:
                    ################################################
                    ## CHECK PERMS AT KL FOR THIS IT MIGHT NOT WORK !!
                    ################################################
                    try:
                        os.remove(self.osPathToPublishFile.replace('\\', '/'))
                        self._finishPlayblast(publish_path, width, height, store_on_disk, getFirstFrame, getLastFrame, comment, user, work_path)
                    except:
                        self.lib.log(app = self.app, method = '_setupPlayblast', message = 'FAILED: \tTo remove osPathToPublishFile', printToLog = False, verbose = self.lib.DEBUGGING)
                        return -1
                else:
                    return -1
            else:
                self._finishPlayblast(publish_path, width, height, store_on_disk, getFirstFrame, getLastFrame, comment, user, work_path)
                
    def _finishPlayblast(self, publish_path, width, height, store_on_disk, getFirstFrame, getLastFrame, comment, user, work_path):
        ## Now do the playblast if the user selected okay or there wasn't a duplicate found.
        self.lib.log(app = self.app, method = '_finishPlayblast', message = 'Duplicate check passed. Playblasting...', printToLog = False, verbose = self.lib.DEBUGGING)
        
        ## Now render the playblast
        self._render_pb_in_maya(getFirstFrame, getLastFrame, publish_path, work_path, width, height)
        self.lib.log(app = self.app, method = '_finishPlayblast', message = 'PlayBlast finished..', printToLog = False, verbose = self.lib.DEBUGGING)
        
        ## Check if uploading is enabled in the UI and do the uploading if it is, else we will finish up here.
        if self.upload.isChecked():
            self.lib.log(app = self.app, method = '_finishPlayblast', message = 'Upload is turned on.. processing version to sg now..', printToLog = False, verbose = self.lib.DEBUGGING)
            
            ## Move the working file to the publish path
            try:
                self.lib.log(app = self.app, method = '_finishPlayblast', message = 'RENAMING: osPathToWorkFile to osPathToPublishFile', printToLog = False, verbose = self.lib.DEBUGGING)
                os.rename(self.osPathToWorkFile.replace('\\', '/'), self.osPathToPublishFile.replace('\\', '/'))
            except:
                self.lib.log(app = self.app, method = '_setupPlayblast', message = 'FAILED: \tTo rename osPathToWorkFile to osPathToPublishFile', printToLog = False, verbose = self.lib.DEBUGGING)
                ## This could fail because the process is in use, and not the fact a freaking published file exists, due to maya trying to open the playblast once it's done!
                ## So a quick check here to make sure it doesn't exist.. if it doesn't and it failed COPY it instead. Fucking maya...
                if not os.path.exists(publish_path):
                    self.lib.log(app = self.app, method = '_setupPlayblast', message = 'FAILED: \tTo rename because file is IN USE. Using shutil to copy instead.', printToLog = False, verbose = self.lib.DEBUGGING)
                    shutil.copyfile(self.osPathToWorkFile.replace('\\', '/'), self.osPathToPublishFile.replace('\\', '/'))
                else:
                    self.lib.log(app = self.app, method = '_setupPlayblast', message = 'FAILED: \tTo rename because file already exists.. how the heck the remove previously failed.. who knows.. but try again now..', printToLog = False, verbose = self.lib.DEBUGGING)
                    os.remove(self.osPathToPublishFile.replace('\\', '/'))
                    os.rename(self.osPathToWorkFile.replace('\\', '/'), self.osPathToPublishFile.replace('\\', '/'))
            
            ## Now submit the version to shotgun
            self.lib.log(app = self.app, method = '_finishPlayblast', message = 'Submitting vesion info to shotgun...', printToLog = False, verbose = self.lib.DEBUGGING)
            sg_version = self._submit_version(
                                              path_to_movie = publish_path, 
                                              store_on_disk = store_on_disk,
                                              first_frame = getFirstFrame, 
                                              last_frame = getLastFrame,
                                              comment = comment,
                                              user = user
                                              )
            self.lib.log(app = self.app, method = '_finishPlayblast', message = 'Version Submitted to shotgun successfully', printToLog = False, verbose = self.lib.DEBUGGING)
            ## Uploading...
            ## Now upload in a new thread and make our own event loop to wait for the thread to finish.
            self.lib.log(app = self.app, method = '_finishPlayblast', message = 'Uploading mov to shotgun for review.', printToLog = False, verbose = self.lib.DEBUGGING)
            cmds.headsUpMessage("Uploading playblast to shotgun for review this may take some time! Be patient...", time = 2)
            event_loop = QtCore.QEventLoop()
            self.lib.log(app = self.app, method = '_finishPlayblast', message = 'event_loop set...', printToLog = False, verbose = self.lib.DEBUGGING)
            thread = self.lib.UploaderThread(self.app, sg_version, publish_path, self.upload_to_shotgun)
            self.lib.log(app = self.app, method = '_finishPlayblast', message = 'thread set...', printToLog = False, verbose = self.lib.DEBUGGING)
            thread.finished.connect(event_loop.quit)
            thread.start()
            self.lib.log(app = self.app, method = '_finishPlayblast', message = 'thread started set...', printToLog = False, verbose = self.lib.DEBUGGING)
            event_loop.exec_()
            self.lib.log(app = self.app, method = '_finishPlayblast', message = 'event_loop.exec_...', printToLog = False, verbose = self.lib.DEBUGGING)
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
            self.lib.log(app = self.app, method = '_finishPlayblast', message = 'Upload to shotgun finished.', printToLog = False, verbose = self.lib.DEBUGGING)
            cmds.headsUpMessage("Playblast upload to shotgun complete!", time = 2)
            cmds.warning('UPLOAD COMPLETE!')
                    
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
        entity = self.app.context.entity

        sg_entity_type = self.app.context.entity["type"]
        sg_filters = [["id", "is", entity["id"]]]

        sg_in_field = self.app.get_setting("sg_in_frame_field")
        sg_out_field = self.app.get_setting("sg_out_frame_field")
        fields = [sg_in_field, sg_out_field]

        #import time
        #start = time.time()
        data = self.app.shotgun.find_one(sg_entity_type, filters=sg_filters, fields=fields)
        #data = self.dbWrap.find_one(self.sg, sg_entity_type, sg_filters, fields)
        #print 'TIME: %s' % (time.time()-start)
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
            defaultRenderGlobals=pm.PyNode('defaultRenderGlobals')
            defaultRenderGlobals.startFrame.set(in_frame)
            defaultRenderGlobals.endFrame.set(out_frame)
        else:
            raise tank.TankError("Don't know how to set current frame range for engine %s!" % engine)

    def _submit_version(self, path_to_movie, store_on_disk, first_frame, last_frame, comment, user):
        """
        Create a version in Shotgun for this path and linked to this publish.
        """
        # get current shotgun user
        current_user = user
        name = os.path.splitext(os.path.basename(path_to_movie))[0]
        # create a name for the version based on the file name grab the file name, strip off extension
        # do some replacements
        name = name.replace("_", " ")
        # and capitalize
        name = name.capitalize()
        data = {
            "code": name,
            "entity": self.app.context.entity,
            "sg_task":  self.app.context.task,
            "user": current_user,
            "created_by": current_user,
            "project": self.app.context.project,
            "description": comment
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
        self.lib.log(self.app, method = '_render_pb_in_maya', message = 'self.qualityPercent.value: %s' % self.qualityPercent.value(), printToLog = False, verbose = self.lib.DEBUGGING)
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

        self.lib.log(self.app, method = '_render_pb_in_maya', message = 'sound: %s' % sound, printToLog = False, verbose = self.lib.DEBUGGING)

        ############################
        ## Now do the main playblast
        cmds.playblast(
        filename        = work_path,
        activeEditor    = self.lib.PB_ACTIVEEDITOR,
        clearCache      = self.lib.PB_CLEARCACHE,
        combineSound    = self.lib.PB_COMBINESOUND,
        compression     = self.lib.PB_COMPRESSION,
        startTime       = first_frame,
        endTime         = last_frame + 1,
        forceOverwrite  = self.lib.PB_FORCEOVERWRITE,
        format          = self.lib.PLAYBLAST_FORMAT,
        framePadding    = self.lib.PB_FRAMEPADDING,
        offScreen       = self.lib.PLAYBLAST_OFFSCREEN,
        options         = self.lib.PB_OPTIONS,
        percent         = self.sizePercent.value(),
        quality         = self.qualityPercent.value(),
        sequenceTime    = self.lib.PB_SEQUENCETIME,
        showOrnaments   = self.lib.PB_SHOWORNAMENTS,
        viewer          = self.lib.PB_VIEWER,
        widthHeight     = [width, height],
        sound           = sound
        )
        
    def _setupRenderGlobals(self, width = 1280, height = 720, animation = False):
        cmds.currentUnit(time='pal')
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'Set currentTime to pal', printToLog = False, verbose = self.lib.DEBUGGING)
        cmds.currentUnit(linear='cm')
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'Set units to cm', printToLog = False, verbose = self.lib.DEBUGGING)
    
        mel.eval('setAttr defaultResolution.width %s' % width)
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'Set defaultResolution width: %s' % width, printToLog = False, verbose = self.lib.DEBUGGING)
        mel.eval('setAttr defaultResolution.height %s' % height)
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'Set defaultResolution height: %s' % height, printToLog = False, verbose = self.lib.DEBUGGING)
        mel.eval('setAttr defaultResolution.deviceAspectRatio 1.777')
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'Set defaultResolution deviceAspectRatio: 1.777', printToLog = False, verbose = self.lib.DEBUGGING)
        mel.eval('setAttr defaultResolution.pixelAspect 1')
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'Set defaultResolution pixelAspect: 1', printToLog = False, verbose = self.lib.DEBUGGING)
    
        ## load mentalray
        if not cmds.pluginInfo( 'Mayatomr', query=True, loaded = True ):
            cmds.loadPlugin('Mayatomr')
            self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'Loaded Mayatomr plugin..', printToLog = False, verbose = self.lib.DEBUGGING)
    
        cmds.setAttr('defaultRenderGlobals.currentRenderer','mentalRay', type = 'string')
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'Set currentRenderer to mentalRay', printToLog = False, verbose = self.lib.DEBUGGING)
        mel.eval('unifiedRenderGlobalsWindow;')
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'unifiedRenderGlobalsWindow', printToLog = False, verbose = self.lib.DEBUGGING)
    
        # Default Render Globals
        # /////////////////////
        cmds.setAttr('defaultRenderGlobals.imageFormat', 51)
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.imageFormat: 51', printToLog = False, verbose = self.lib.DEBUGGING)
    
        cmds.setAttr('defaultRenderGlobals.imfkey','exr', type = 'string')
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.imfkey: exr', printToLog = False, verbose = self.lib.DEBUGGING)
    
        cmds.setAttr('defaultRenderGlobals.animation', 1)
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.animation: 1', printToLog = False, verbose = self.lib.DEBUGGING)
    
        cmds.setAttr('defaultRenderGlobals.extensionPadding', 3)
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.extensionPadding: 3', printToLog = False, verbose = self.lib.DEBUGGING)
    
        cmds.getAttr('defaultRenderGlobals.extensionPadding')
    
        cmds.setAttr('defaultRenderGlobals.periodInExt', 1)
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.periodInExt: 1', printToLog = False, verbose = self.lib.DEBUGGING)
    
        cmds.setAttr('defaultRenderGlobals.outFormatControl', 0)
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.outFormatControl: 0', printToLog = False, verbose = self.lib.DEBUGGING)
    
        cmds.setAttr('defaultRenderGlobals.putFrameBeforeExt', 1)
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.putFrameBeforeExt: 1', printToLog = False, verbose = self.lib.DEBUGGING)
    
        cmds.setAttr('defaultRenderGlobals.enableDefaultLight', 0)
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.enableDefaultLight: 0', printToLog = False, verbose = self.lib.DEBUGGING)
    
        cmds.setAttr('defaultResolution.aspectLock', 0)
        self.lib.log(app = self.app, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.aspectLock: 0', printToLog = False, verbose = self.lib.DEBUGGING)
    
        # MentalRay Globals
        # /////////////////////
        cmds.setAttr('mentalrayGlobals.imageCompression', 4)
        cmds.setAttr('mentalrayGlobals.exportPostEffects', 0)
        cmds.setAttr('mentalrayGlobals.accelerationMethod', 4)
        cmds.setAttr('mentalrayGlobals.exportVerbosity', 5)
        # miDefault Frame Buffer
        cmds.setAttr('miDefaultFramebuffer.datatype', 16)
        # miDefault sampling defaults
        cmds.setAttr('miDefaultOptions.filterWidth', 0.6666666667)
        cmds.setAttr('miDefaultOptions.filterHeight', 0.6666666667)
        cmds.setAttr('miDefaultOptions.filter', 2)
        cmds.setAttr('miDefaultOptions.sampleLock', 0)
        # enable raytracing, disable scanline
        cmds.setAttr('miDefaultOptions.scanline', 0)
        try:
            cmds.optionMenuGrp('miSampleModeCtrl', edit = True,  select = 2)
        except:
            pass
        cmds.setAttr('miDefaultOptions.minSamples', -2)
        cmds.setAttr('miDefaultOptions.maxSamples', 0)
    
        # set sampling quality for RGB channel to eliminate noise
        # costs a bit extra time because it will sample more in the
        # red / green channel but will be faster for blue.
        # using unified sampling
        cmds.setAttr('miDefaultOptions.contrastR', 0.04)
        cmds.setAttr('miDefaultOptions.contrastG', 0.03)
        cmds.setAttr('miDefaultOptions.contrastB', 0.06)
        cmds.setAttr('miDefaultOptions.contrastA', 0.03)
    
        cmds.setAttr('miDefaultOptions.maxReflectionRays', 3)
        cmds.setAttr('miDefaultOptions.maxRefractionRays', 3)
        cmds.setAttr('miDefaultOptions.maxRayDepth', 5)
        cmds.setAttr('miDefaultOptions.maxShadowRayDepth', 5)
    
        cmds.setAttr('miDefaultOptions.finalGatherRays', 20)
        cmds.setAttr('miDefaultOptions.finalGatherPresampleDensity', 0.2)
        cmds.setAttr('miDefaultOptions.finalGatherTraceDiffuse', 0)
        cmds.setAttr('miDefaultOptions.finalGatherPoints', 50)
    
        cmds.setAttr('miDefaultOptions.displacePresample', 0)
    
        playStart  = cmds.playbackOptions( query = True, minTime= True)
        playFinish = cmds.playbackOptions( query = True, maxTime= True)
        cmds.setAttr('defaultRenderGlobals.startFrame', playStart)
        cmds.setAttr('defaultRenderGlobals.endFrame', playFinish)
    
        # MentalCore
        # /////////////////////
        if not animation:
            try:
                mapi.enable(True)
                cmds.setAttr('mentalcoreGlobals.en_colour_management',1)
                mel.eval('unifiedRenderGlobalsWindow;')
    
                cmds.setAttr('mentalcoreGlobals.contrast_all_buffers', 1)
    
                cmds.setAttr('mentalcoreGlobals.output_mode', 0)
                cmds.setAttr('mentalcoreGlobals.unified_sampling', 1)
                cmds.setAttr('mentalcoreGlobals.samples_min', 1)
                cmds.setAttr('mentalcoreGlobals.samples_max', 80)
                cmds.setAttr('mentalcoreGlobals.samples_quality', 0.8)
                cmds.setAttr('mentalcoreGlobals.samples_error_cutoff', 0.02)
    
                cmds.setAttr('mentalcoreGlobals.en_envl', 1)
                cmds.setAttr('mentalcoreGlobals.envl_scale', 0.5)
                cmds.setAttr('mentalcoreGlobals.envl_blur_res', 0)
                cmds.setAttr('mentalcoreGlobals.envl_blur', 0)
                cmds.setAttr('mentalcoreGlobals.envl_en_flood_colour', 1)
                cmds.setAttr('mentalcoreGlobals.envl_flood_colour', 1, 1, 1, 1, type = 'double3')
                cmds.setAttr('mentalcoreGlobals.en_ao', 1)
                cmds.setAttr('mentalcoreGlobals.ao_samples', 24)
                cmds.setAttr('mentalcoreGlobals.ao_spread', 60)
                cmds.setAttr('mentalcoreGlobals.ao_near_clip', 1)
                cmds.setAttr('mentalcoreGlobals.ao_far_clip', 10)
                cmds.setAttr('mentalcoreGlobals.ao_opacity', 0)
                cmds.setAttr('mentalcoreGlobals.ao_vis_indirect', 0)
                cmds.setAttr('mentalcoreGlobals.ao_vis_refl', 0)
                cmds.setAttr('mentalcoreGlobals.ao_vis_refr', 1)
                cmds.setAttr('mentalcoreGlobals.ao_vis_trans', 1)
            except:
                cmds.warning('NO MENTAL CORE LOADED!!!')
                pass
    
            # Default Resolution
            cmds.setAttr('defaultResolution.width', 1280)
            cmds.setAttr('defaultResolution.height', 720)
            cmds.setAttr('defaultResolution.pixelAspect', 1)
            cmds.setAttr('defaultResolution.deviceAspectRatio', 1.7778)
            print 'Default render settings initialized.'