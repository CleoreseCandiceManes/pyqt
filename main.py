import sys

from PyQt5 import QtCore, QtWidgets

from backend.login_be import LoginBE
from lyt_realestate import Ui_Dialog
from appointments_controller import AppointmentsWindow

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


def main():
    app = QtWidgets.QApplication(sys.argv)

    login_dialog = QtWidgets.QDialog()
    login_ui = Ui_Dialog()
    login_ui.setupUi(login_dialog)

    login_backend = LoginBE()

    appointments_window = AppointmentsWindow()

    def handle_login():
        # load the enterted values into code and remove spaces before or after the text
        username = login_ui.username_txt.text().strip()
        password = login_ui.password_txt.text().strip()

        # Run the function that will check the crendtials, 
        #   if it returns true then dirrect user to the application or else display error message
        if login_backend.check_credentials(username, password):
            login_dialog.accept()
            appointments_window.show()
        else:
            QtWidgets.QMessageBox.warning(
                login_dialog,
                "Login failed",
                "Incorrect username or password.",
            )

    #If the user presses the cancel button close the application
    def handle_cancel():
        login_dialog.reject()
        app.quit()

    login_ui.login_btn.clicked.connect(handle_login)
    login_ui.cancel_btn.clicked.connect(handle_cancel)

    login_dialog.show()
    sys.exit(app.exec_())

    


if __name__ == "__main__":
    main()
