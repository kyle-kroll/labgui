from PyQt5.QtWidgets import QLineEdit, QPushButton, QVBoxLayout, QDialog, QMessageBox
import hashlib


class Login(QDialog):
    def __init__(self, parent=None):
        super(Login, self).__init__(parent)
        self.textName = QLineEdit(self)
        self.textPass = QLineEdit(self)
        self.textPass.setEchoMode(QLineEdit.Password)
        self.buttonLogin = QPushButton('Login', self)
        self.buttonLogin.clicked.connect(self.handleLogin)
        layout = QVBoxLayout(self)
        layout.addWidget(self.textName)
        layout.addWidget(self.textPass)
        layout.addWidget(self.buttonLogin)
        self.setWindowTitle("Reeves Lab Login")

    def handleLogin(self):
        with open("info", "rb") as f:
            # Getting the values back out
            data = f.read()
            salt = data[:32]  # 32 is the length of the salt
            key = data[32:]

        newkey = hashlib.pbkdf2_hmac('sha256', self.textPass.text().encode('utf-8'), salt, 100000)
        if (self.textName.text() == 'admin' and
                newkey == key):
            self.accept()
        else:
            QMessageBox.warning(
                self, 'Error', 'Bad user or password')
