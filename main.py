import sys

from PyQt5.QtWidgets import QApplication, QDialog

from login import Login
from window import Window


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = Login()

    if login.exec_() == QDialog.Accepted:
        window = Window()
        window.show()
        sys.exit(app.exec_())
