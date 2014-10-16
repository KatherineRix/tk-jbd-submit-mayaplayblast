from tank.platform.qt import QtCore, QtGui


class ProgressBarUI(QtGui.QWidget):
    """
    Main class for the base progress bar used in applications to show users a progress..
    """
    def __init__(self, parent = None, title = 'Approx Progress:'):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle(title)
        self.layout         = QtGui.QVBoxLayout(self)

        # Create a progress bar and a button and add them to the main layout
        self.labelLayout    = QtGui.QHBoxLayout(self)
        self.mainLabel      = QtGui.QLabel(title)
        self.doingLabel     = QtGui.QLabel('')

        self.progressBar    = QtGui.QProgressBar(self)
        self.progressBar.setRange(0,100)
        self.progressBar.setValue(0)
        self.progressBarGeo = self.progressBar.rect()
        self.progressBar.setTextVisible(True)
        
        self.labelLayout.addWidget(self.mainLabel)
        self.labelLayout.addWidget(self.doingLabel)
        
        self.layout.addLayout(self.labelLayout)
        self.layout.addWidget(self.progressBar)
        #self.setWindowFlags(Qt.SplashScreen)
        self.layout.addStretch(1)

    def updateProgress(self, percent = 0, doingWhat = ''):
        self.progressBar.setValue(percent)
        self.doingLabel.setText(doingWhat)
        self.repaint()
        
    def showEvent(self, e):
        QtGui.QWidget.showEvent(self, e)
        self.resize(400, 50)        
        self.move(QtCore.QApplication.desktop().screen().rect().center()- self.rect().center())