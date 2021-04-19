import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox, QLabel, QMainWindow, QMenuBar
from PyQt5.QtWidgets import QMenu, QAction, qApp
from PyQt5 import QtCore, Qt


class Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reeves Lab - DBA")
        self.resize(400, 400)
        self.centralWidget = QLabel("Hello, Lab!")
        self.centralWidget.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.setCentralWidget(self.centralWidget)
        self._createMenuBar()

    def _createMenuBar(self):
        menuBar = self.menuBar()
        menuBar.setNativeMenuBar(False)
        # Creating file menu
        fileMenu = menuBar.addMenu("File")
        openAct = QAction("Load DB", self)
        openAct.setStatusTip("Load the Publication DB")
        openAct.triggered.connect(self.load_db)
        fileMenu.addAction(openAct)
        # Create a menu item to exit the application
        exitAct = QAction("&Exit", self)
        exitAct.setShortcut("Ctrl+Q")
        exitAct.setStatusTip("Exit application | Ctrl (⌘) + Q")
        exitAct.triggered.connect(qApp.quit)

        # Start a status bar at the bottom of the application
        self.statusBar()
        menuBar.addAction(exitAct)

    def load_db(self):
        self.centralWidget.setText("Loading DB...")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())
