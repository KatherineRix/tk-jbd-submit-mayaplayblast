"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------

Code for a maya playblast creator app that runs in maya
"""

from tank.platform.qt import QtCore, QtGui
import maya.cmds as cmds


class InputPrompt(QtGui.QWidget):
    """
    QInputDialog with a custom input that will try to use the currently selected item to populate the textValue
    """
    def __init__(self, parent = None, label = '', defaultText = '', getSelected = True):
        QtGui.QWidget.__init__(self, parent)
        self.parent         = parent
        self.mainLayout     = QtGui.QVBoxLayout(self)
        self.hLayout        = QtGui.QHBoxLayout(self)
        self.inputLabel     = QtGui.QLabel('Turn Table Group:')
        self.selInput       = QtGui.QLineEdit(self)
        self.selInput.setToolTip('You can type the name of the group you want to spin the camera around in here or use the button to the left to assign the group.')
        self.getSelButton   = QtGui.QPushButton('Update From Selected')
        self.getSelButton.setToolTip('Update the text field with the name of the selected group you want to spin the camera around. \nThis is generally the highest level grp for the geo to be reviewed.')
        self.getSelButton.pressed.connect(self.updateTextFromSelected)
        self.hLayout.addWidget(self.inputLabel)
        self.hLayout.addWidget(self.selInput)
        self.hLayout.addWidget(self.getSelButton)
        
        try:
            self.selInput.setText('%s' % cmds.ls(sl= True)[0])
        except IndexError:
            pass
        self.mainLayout.addLayout(self.hLayout)
                   
    def updateTextFromSelected(self):
        try:
            self.selInput.setText('%s' % cmds.ls(sl= True)[0])
        except IndexError:
            self.selInput.setText('Select something first and try again')
            
    def getText(self):
        return str(self.selInput.text())                    