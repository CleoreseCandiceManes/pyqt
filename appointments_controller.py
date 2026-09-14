from datetime import datetime
from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from appointments_window import Ui_MainWindow
from backend.appointments import AppointmentsBE
from backend.clients import ClientsBE


class AppointmentsWindow(QtWidgets.QMainWindow):

    SIDEBAR_EXPANDED_WIDTH = 200
    SIDEBAR_COLLAPSED_WIDTH = 60
    ANIMATION_DURATION_MS = 250

    NAV_BUTTON_LABELS = {
        "dashboardButton": "Dashboard",
        "calendarButton": "Calendar",
        "propertiesButton": "Properties",
        "clientsButton": "Clients",
        "salesButton": "Sales",
        "settingsButton": "Settings",
    }

    NAV_BUTTON_PAGES = {
        "dashboardButton": "dashboardPage",
        "calendarButton": "calendarPage",
        "propertiesButton": "propertiesPage",
        "clientsButton": "clientsPage",
        "salesButton": "salesPage",
        "settingsButton": "settingsPage",
    }

    ALL_APPOINTMENTS_TABLE = "appointments_table"
    TODAY_APPOINTMENTS_TABLE = "todays_appointments_table"

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._sidebar_animation = None

        self.appointments_be = AppointmentsBE()
        self.clients_be = ClientsBE()

        self.clients_be.ensure_clients_from_names(
            meeting["name"] for meeting in self.appointments_be.get_meetings()
        )

        self.ui.menuButton.clicked.connect(self.toggle_sidebar)

        for button_name, page_name in self.NAV_BUTTON_PAGES.items():
            button = getattr(self.ui, button_name)
            page = getattr(self.ui, page_name)
            button.clicked.connect(lambda _checked=False, p=page: self.show_page(p))

        self.ui.add_appointment_btn.clicked.connect(self._on_add_appointment)

        self.ui.client_save_btn.clicked.connect(self._on_save_client)
        self.ui.client_cancel_btn.clicked.connect(self._on_clear_client_form)

        self._marked_dates = []
        self.ui.calendarWidget.clicked.connect(self._on_calendar_date_clicked)
        self.ui.add_appointment_on_date_btn.clicked.connect(self._on_add_appointment_on_date)

        self.load_appointments()
        self.load_clients()

    def show_page(self, page):
        self.ui.contentStack.setCurrentWidget(page)

    def _ui_widget(self, constant_name, object_name):
        widget = getattr(self.ui, object_name, None)
        if widget is None:
            raise RuntimeError(
                f"appointments_window.ui/py has no widget named {object_name!r} "
                f"(expected via {constant_name}). If it was renamed in Designer, "
                f"update {constant_name} in appointments_controller.py to match, "
                f"and make sure appointments_window.py was regenerated from the "
                f"latest .ui."
            )
        return widget

    @property
    def all_appointments_table(self):
        return self._ui_widget("ALL_APPOINTMENTS_TABLE", self.ALL_APPOINTMENTS_TABLE)

    @property
    def todays_appointments_table(self):
        return self._ui_widget("TODAY_APPOINTMENTS_TABLE", self.TODAY_APPOINTMENTS_TABLE)

    def load_appointments(self):
        meetings = self.appointments_be.get_meetings()

        def sort_key(meeting):
            return datetime.strptime(
                f"{meeting['appointment_date']} {meeting['appointment_time']}",
                "%d-%m-%Y %H:%M",
            )

        all_meetings = sorted(meetings, key=sort_key)

        today = datetime.today().date()
        todays_meetings = [
            meeting
            for meeting in all_meetings
            if datetime.strptime(meeting["appointment_date"], "%d-%m-%Y").date() == today
        ]

        self._render_table(self.todays_appointments_table, todays_meetings)
        self._render_table(self.all_appointments_table, all_meetings)

        self._refresh_calendar_marks()
        self._show_appointments_for_date(self.ui.calendarWidget.selectedDate())

    def _refresh_calendar_marks(self):
        calendar = self.ui.calendarWidget
        plain_format = QtGui.QTextCharFormat()

        for date in self._marked_dates:
            calendar.setDateTextFormat(date, plain_format)

        marked_format = QtGui.QTextCharFormat()
        marked_format.setFontWeight(QtGui.QFont.Bold)
        marked_format.setForeground(QtGui.QColor("#2E7D5E"))

        marked_dates = []
        seen = set()
        for meeting in self.appointments_be.get_meetings():
            if meeting.get("cancelled"):
                continue
            qdate = QtCore.QDate.fromString(meeting["appointment_date"], "dd-MM-yyyy")
            if qdate.isValid() and qdate not in seen:
                seen.add(qdate)
                marked_dates.append(qdate)
                calendar.setDateTextFormat(qdate, marked_format)

        self._marked_dates = marked_dates

    def _on_calendar_date_clicked(self, qdate):
        self._show_appointments_for_date(qdate)

    def _show_appointments_for_date(self, qdate):
        date_str = qdate.toString("dd-MM-yyyy")
        meetings = sorted(
            (m for m in self.appointments_be.get_meetings() if m["appointment_date"] == date_str),
            key=lambda m: m["appointment_time"],
        )

        self.ui.selected_date_label.setText(
            f"Appointments on {qdate.toString('d MMMM yyyy')}"
        )

        table = self.ui.day_appointments_table
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setStyleSheet(
            "QTableWidget {"
            " border: 1px solid #E8E3E0;"
            " border-radius: 10px;"
            " background-color: #FFFFFF;"
            "}"
            "QTableWidget::item {"
            " padding: 10px;"
            " border-bottom: 1px solid #F1EEEC;"
            "}"
            "QHeaderView::section {"
            " background-color: #FFFFFF;"
            " color: #888888;"
            " border: none;"
            " border-bottom: 1px solid #E8E3E0;"
            " padding: 8px;"
            " font-weight: 600;"
            "}"
        )
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Name", "Time"])
        table.setRowCount(len(meetings))

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)

        for row, meeting in enumerate(meetings):
            name_item = QtWidgets.QTableWidgetItem(meeting["name"])
            time_item = QtWidgets.QTableWidgetItem(meeting["appointment_time"])
            if meeting.get("cancelled"):
                font = QtGui.QFont(name_item.font())
                font.setStrikeOut(True)
                for item in (name_item, time_item):
                    item.setFont(font)
                    item.setForeground(QtGui.QColor("#A8A29D"))
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, time_item)

        self._selected_calendar_date = qdate

    def _on_add_appointment_on_date(self):
        qdate = getattr(self, "_selected_calendar_date", None) or self.ui.calendarWidget.selectedDate()
        current_time = self.ui.dateTimeEdit.time()
        self.ui.dateTimeEdit.setDate(qdate)
        self.ui.dateTimeEdit.setTime(current_time)
        self.show_page(self.ui.dashboardPage)

    def _render_table(self, table, meetings):
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setStyleSheet(
            "QTableWidget {"
            " border: 1px solid #E8E3E0;"
            " border-radius: 10px;"
            " background-color: #FFFFFF;"
            "}"
            "QTableWidget::item {"
            " padding: 10px;"
            " border-bottom: 1px solid #F1EEEC;"
            "}"
            "QHeaderView::section {"
            " background-color: #FFFFFF;"
            " color: #888888;"
            " border: none;"
            " border-bottom: 1px solid #E8E3E0;"
            " padding: 8px;"
            " font-weight: 600;"
            "}"
        )

        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Name", "Date", "Time", ""])
        table.setRowCount(len(meetings))

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Fixed)
        table.setColumnWidth(3, 70)

        for row, meeting in enumerate(meetings):
            cancelled = meeting.get("cancelled", False)

            name_item = QtWidgets.QTableWidgetItem(meeting["name"])
            date_item = QtWidgets.QTableWidgetItem(meeting["appointment_date"])
            time_item = QtWidgets.QTableWidgetItem(meeting["appointment_time"])

            if cancelled:
                font = QtGui.QFont(name_item.font())
                font.setStrikeOut(True)
                for item in (name_item, date_item, time_item):
                    item.setFont(font)
                    item.setForeground(QtGui.QColor("#A8A29D"))

            table.setItem(row, 0, name_item)
            table.setItem(row, 1, date_item)
            table.setItem(row, 2, time_item)

            button = QtWidgets.QPushButton("Undo" if cancelled else "Cancel")
            button.setCursor(QtCore.Qt.PointingHandCursor)
            button.setFlat(True)
            button.setStyleSheet(
                "QPushButton {{"
                " border: none;"
                " background: transparent;"
                " color: {color};"
                " font-weight: 600;"
                " font-size: 12px;"
                "}}"
                "QPushButton:hover {{ text-decoration: underline; }}".format(
                    color="#5B8A72" if cancelled else "#B23B3B"
                )
            )
            button.clicked.connect(
                partial(self._on_cancel_toggle, meeting["id"], cancelled)
            )
            table.setCellWidget(row, 3, button)

    def _on_cancel_toggle(self, meeting_id, currently_cancelled):
        if currently_cancelled:
            self.appointments_be.restore_meeting(meeting_id)
        else:
            self.appointments_be.cancel_meeting(meeting_id)
        QtCore.QTimer.singleShot(0, self.load_appointments)

    def _on_add_appointment(self):
        name = self.ui.client_name_combo.currentText().strip()
        if not name:
            QtWidgets.QMessageBox.warning(
                self, "Missing client", "Select a client before adding an appointment."
            )
            return

        appointment_dt = self.ui.dateTimeEdit.dateTime()
        date_str = appointment_dt.toString("dd-MM-yyyy")
        time_str = appointment_dt.toString("HH:mm")

        last_name = name.split()[-1] if name.split() else name

        self.appointments_be.add_meeting(last_name, name, date_str, time_str)

        self.load_appointments()

    def _on_save_client(self):
        first_name = self.ui.first_name.text().strip()
        last_name = self.ui.last_name.text().strip()
        if not first_name or not last_name:
            QtWidgets.QMessageBox.warning(
                self, "Missing name", "Enter both a first and last name before saving a client."
            )
            return

        self.clients_be.add_client(
            first_name,
            last_name,
            self.ui.email_address.text().strip(),
            self.ui.phone_nr.text().strip(),
            self.ui.client_type.currentText(),
            self.ui.owned_property.currentText(),
            self.ui.interested_propery.currentText(),
            self.ui.notes.toPlainText().strip(),
        )

        QtWidgets.QMessageBox.information(
            self, "Client saved", f"{first_name} {last_name} was added."
        )
        self._on_clear_client_form()
        self.load_clients()

    def load_clients(self):
        clients = self.clients_be.get_clients()
        self._render_client_table(clients)
        self._populate_client_combo(clients)

    def _render_client_table(self, clients):
        table = self.ui.client_list

        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setStyleSheet(
            "QTableWidget {"
            " border: 1px solid #E8E3E0;"
            " border-radius: 10px;"
            " background-color: #FFFFFF;"
            "}"
            "QTableWidget::item {"
            " padding: 10px;"
            " border-bottom: 1px solid #F1EEEC;"
            "}"
            "QHeaderView::section {"
            " background-color: #FFFFFF;"
            " color: #888888;"
            " border: none;"
            " border-bottom: 1px solid #E8E3E0;"
            " padding: 8px;"
            " font-weight: 600;"
            "}"
        )

        headers = ["Name", "Email", "Phone", "Type", "Owned", "Interested", "Notes", ""]
        column_widths = [150, 160, 100, 70, 80, 120]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(clients))

        header = table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        for col, width in enumerate(column_widths):
            table.setColumnWidth(col, width)
        notes_col = len(headers) - 2
        remove_col = len(headers) - 1
        header.setSectionResizeMode(notes_col, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(remove_col, QtWidgets.QHeaderView.Fixed)
        table.setColumnWidth(remove_col, 80)

        for row, client in enumerate(clients):
            full_name = f"{client.get('first_name', '')} {client.get('last_name', '')}".strip()
            values = [
                full_name,
                client.get("email_address", ""),
                client.get("phone_nr", ""),
                client.get("client_type", ""),
                client.get("owned_property", ""),
                client.get("interested_property", ""),
                client.get("notes", ""),
            ]
            for col, value in enumerate(values):
                table.setItem(row, col, QtWidgets.QTableWidgetItem(value))

            remove_btn = QtWidgets.QPushButton("Remove")
            remove_btn.setCursor(QtCore.Qt.PointingHandCursor)
            remove_btn.setFlat(True)
            remove_btn.setStyleSheet(
                "QPushButton {"
                " border: none;"
                " background: transparent;"
                " color: #B23B3B;"
                " font-weight: 600;"
                " font-size: 12px;"
                "}"
                "QPushButton:hover { text-decoration: underline; }"
            )
            remove_btn.clicked.connect(
                partial(self._on_remove_client, client["id"], full_name)
            )
            table.setCellWidget(row, remove_col, remove_btn)

    def _on_remove_client(self, client_id, full_name):
        confirmed = QtWidgets.QMessageBox.question(
            self,
            "Remove client",
            f"Remove {full_name} from your client list? This can't be undone.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if confirmed != QtWidgets.QMessageBox.Yes:
            return

        self.clients_be.remove_client(client_id)
        QtCore.QTimer.singleShot(0, self.load_clients)

    def _populate_client_combo(self, clients):
        combo = self.ui.client_name_combo
        previous_selection = combo.currentText()

        names = sorted(
            {f"{c.get('first_name', '')} {c.get('last_name', '')}".strip() for c in clients}
        )

        combo.blockSignals(True)
        combo.clear()
        combo.addItems(names)
        index = combo.findText(previous_selection)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    def _on_clear_client_form(self):
        self.ui.first_name.clear()
        self.ui.last_name.clear()
        self.ui.email_address.clear()
        self.ui.phone_nr.clear()
        self.ui.client_type.setCurrentIndex(0)
        self.ui.owned_property.setCurrentIndex(0)
        self.ui.interested_propery.setCurrentIndex(0)
        self.ui.notes.clear()

    def toggle_sidebar(self):
        is_expanded = self.ui.sidebar.width() > 100
        new_width = (
            self.SIDEBAR_COLLAPSED_WIDTH if is_expanded else self.SIDEBAR_EXPANDED_WIDTH
        )

        self._sidebar_animation = QtCore.QVariantAnimation(self)
        self._sidebar_animation.setDuration(self.ANIMATION_DURATION_MS)
        self._sidebar_animation.setStartValue(self.ui.sidebar.width())
        self._sidebar_animation.setEndValue(new_width)
        self._sidebar_animation.setEasingCurve(QtCore.QEasingCurve.InOutCubic)
        self._sidebar_animation.valueChanged.connect(
            lambda value: self.ui.sidebar.setFixedWidth(int(value))
        )
        self._sidebar_animation.start()

        collapsing = is_expanded
        for object_name, label in self.NAV_BUTTON_LABELS.items():
            getattr(self.ui, object_name).setText("" if collapsing else label)
