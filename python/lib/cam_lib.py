import maya.cmds as cmds
from tank.platform.qt import QtCore, QtGui

def _findShotCamera():
    """
    Shot camera setup. You can replace this entire func with your own code to return the correct cameraShape for the app to use.
    """
    camera = []
    for each in cmds.ls(type = 'camera'):
        getCamTransform = cmds.listRelatives(each, parent = True)[0]
        ## We don't care about any suffix used, we're looking for an attr called type on the camera here to find the shot cam.
        ## You can change this to find your shot camera as you need
        if cmds.objExists('%s.type' % getCamTransform):
            camera.append(each)

    if not camera:
        QtGui.QMessageBox.information(None, "Aborted...", 'No shotCam found!!')
        return -1
    else:
        if len(camera) > 1:
            QtGui.QMessageBox.information(None, "Aborted...", 'Make sure you have only ONE shot camera in the scene!')
            return -1
        else:
            ## Camera is the first in the list.
            cam = camera[0]

    return cam

def _setCameraDefaults(camera = ''):
    """
    Sets the base defaults for the camera
    @param camera: The name of the camera transform node NOT the shape node!
    @type camera: String
    """
    if not camera:
        camera = None

    if camera:
        camName = camera
        camShape = cmds.listRelatives(camera, shapes = True)[0]
        cmds.camera(camName, e = True,  displayFilmGate  = 0,  displayResolution = 1,  overscan = 1.19)
        cmds.setAttr("%s.displayGateMask" % camShape, 1)
        cmds.setAttr('%s.displayGateMaskOpacity' % camShape, 1)
        cmds.setAttr('%s.displayGateMaskColor' % camShape, 0, 0, 0, type = 'double3' )
        cmds.setAttr("%s.displayResolution" % camShape, 1)
        cmds.setAttr("%s.displaySafeAction" % camShape, 1)
        cmds.setAttr("%s.journalCommand" % camShape, 0)
        cmds.setAttr("%s.nearClipPlane" % camShape, 0.05)
        cmds.setAttr("%s.overscan" % camShape, 1)
    else:
        cmds.warning('No shotcam found!')

def _createCamGate(camera = '', pathToImage = ''):
    if not camera:
        camera = getShotCamera()

    if camera:
        if not cmds.objExists('camGate'):
            cmds.imagePlane(n = 'camGate')
            cmds.rename('camGate1', 'camGate')
            cmds.pointConstraint('%s' % camera, 'camGate', mo = False, n ='tmpPoint')
            cmds.orientConstraint('%s' % camera, 'camGate', mo = False, n ='tmpOrient')
            cmds.delete(['tmpPoint', 'tmpOrient'])
            cmds.parent('camGate', '%s' % camera)
            cmds.connectAttr('camGateShape.message', '%sShape.imagePlane[0]' % camera, f = True)
            cmds.setAttr('camGate.depth', 0.01)
            cmds.setAttr('camGate.sizeX', 1.710)
            cmds.setAttr('camGate.sizeY', 2)
            cmds.setAttr('camGate.offsetX', 0.004)
            cmds.setAttr('camGate.offsetY', 0.003)
            cmds.setAttr('camGateShape.imageName', pathToImage, type = 'string')
            cmds.setAttr('camGateShape.lockedToCamera', 1)
            cmds.setAttr('camGateShape.displayOnlyIfCurrent', 1)