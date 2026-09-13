import sys

from PyQt5 import QtCore, QtWidgets

from backend.login_be import LoginBE
from lyt_realestate import Ui_Dialog
from appointments_controller import AppointmentsWindow

# Must be set before QApplication is constructed so Qt scales the UI to
# match Windows display scaling (otherwise everything renders at its raw
# pixel size and looks tiny on a high-DPI / scaled display).
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


def main():
    app = QtWidgets.QApplication(sys.argv)

    login_dialog = QtWidgets.QDialog()
    login_ui = Ui_Dialog()
    login_ui.setupUi(login_dialog)

    login_backend = LoginBE()

    # Built up front and kept referenced for the life of main() so the window
    # survives once control returns to the Qt event loop.
    appointments_window = AppointmentsWindow()

    def handle_login():
        username = login_ui.username_txt.text().strip()
        password = login_ui.password_txt.text().strip()

        if login_backend.check_credentials(username, password):
            login_dialog.accept()
            appointments_window.show()
        else:
            QtWidgets.QMessageBox.warning(
                login_dialog,
                "Login failed",
                "Incorrect username or password.",
            )

    login_ui.login_btn.clicked.connect(handle_login)

    login_dialog.show()
    sys.exit(app.exec_())

    


if __name__ == "__main__":
    main()
