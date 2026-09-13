from PyQt5.QtCore import QObject, pyqtSlot


class LoginBE(QObject):
    def __init__(self):
        super().__init__()

        self.sys_users = {
            "admin": "000",
            "manes": "21543038"
        }

    @pyqtSlot(str, str, result=bool)
    def check_credentials(self, username, password):
        if username in self.sys_users:
            return self.sys_users[username] == password

        return False
