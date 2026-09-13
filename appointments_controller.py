from datetime import datetime
from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from appointments_window import Ui_MainWindow
from backend.appointments import AppointmentsBE


class AppointmentsWindow(QtWidgets.QMainWindow):
    """Main dashboard window: sidebar nav + content area.

    Wraps the Designer-generated Ui_MainWindow and adds:
    - the collapsible sidebar behaviour (burger-menu button animates the
      sidebar width and swaps the nav button labels for icon-only text
      while collapsed)
    - page switching: each nav button shows its matching page in the
      contentArea's QStackedWidget (contentStack)
    - populating the dashboard's two appointments tables from AppointmentsBE,
      and adding new appointments via the Client_name / dateTimeEdit / Add form
    """

    SIDEBAR_EXPANDED_WIDTH = 200
    SIDEBAR_COLLAPSED_WIDTH = 60
    ANIMATION_DURATION_MS = 250

    # objectName -> label shown when the sidebar is expanded. Cleared to ""
    # when collapsed. Update this if buttons are added/renamed in Designer.
    NAV_BUTTON_LABELS = {
        "dashboardButton": "Dashboard",
        "calendarButton": "Calendar",
        "propertiesButton": "Properties",
        "clientsButton": "Clients",
        "salesButton": "Sales",
        "settingsButton": "Settings",
    }

    # objectName of the nav button -> objectName of the page it shows in
    # contentStack. Update this if pages are added/renamed in Designer.
    NAV_BUTTON_PAGES = {
        "dashboardButton": "dashboardPage",
        "calendarButton": "calendarPage",
        "propertiesButton": "propertiesPage",
        "clientsButton": "clientsPage",
        "salesButton": "salesPage",
        "settingsButton": "settingsPage",
    }

    # objectNames of the two appointments tables in dashboardPage.
    ALL_APPOINTMENTS_TABLE = "appointments_table"
    TODAY_APPOINTMENTS_TABLE = "todays_appointments_table"

    # objectName of the client-name field in the "Add Appointment" form.
    CLIENT_NAME_FIELD = "Client_name"

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._sidebar_animation = None

        self.appointments_be = AppointmentsBE()

        self.ui.menuButton.clicked.connect(self.toggle_sidebar)

        for button_name, page_name in self.NAV_BUTTON_PAGES.items():
            button = getattr(self.ui, button_name)
            page = getattr(self.ui, page_name)
            button.clicked.connect(lambda _checked=False, p=page: self.show_page(p))

        self.ui.add_appointment_btn.clicked.connect(self._on_add_appointment)

        self.load_appointments()

    def show_page(self, page):
        self.ui.contentStack.setCurrentWidget(page)

    @property
    def all_appointments_table(self):
        return getattr(self.ui, self.ALL_APPOINTMENTS_TABLE)

    @property
    def todays_appointments_table(self):
        return getattr(self.ui, self.TODAY_APPOINTMENTS_TABLE)

    @property
    def client_name_field(self):
        return getattr(self.ui, self.CLIENT_NAME_FIELD)

    def load_appointments(self):
        """Fetch meetings from the backend and populate both dashboard
        tables: appointments_table gets everything, todays_appointments_table
        gets only meetings dated today. Both render Name / Date / Time / a
        Cancel-or-Undo button per row, and cancelled meetings stay in the
        list but render with strike-through text.
        """
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
        # Fixed rather than ResizeToContents: a cell *widget's* size hint
        # isn't always picked up in time, which left the Cancel/Undo button
        # clipped at the table's right edge.
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
        # Rebuilding the tables replaces (and deletes) the very button
        # that's still mid-click; deferring one tick lets that click event
        # finish first, which avoids a stale repaint of the old button
        # underneath the new one.
        QtCore.QTimer.singleShot(0, self.load_appointments)

    def _on_add_appointment(self):
        name = self.client_name_field.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(
                self, "Missing client name", "Enter a client name before adding an appointment."
            )
            return

        appointment_dt = self.ui.dateTimeEdit.dateTime()
        date_str = appointment_dt.toString("dd-MM-yyyy")
        time_str = appointment_dt.toString("HH:mm")

        # AppointmentsBE.add_meeting keys each meeting by date + last name;
        # derive a last name from whatever was typed (last word, or the
        # whole name if it's a single word) since the form only has one
        # name field.
        last_name = name.split()[-1] if name.split() else name

        self.appointments_be.add_meeting(last_name, name, date_str, time_str)

        self.client_name_field.clear()
        self.load_appointments()

    def toggle_sidebar(self):
        is_expanded = self.ui.sidebar.width() > 100
        new_width = (
            self.SIDEBAR_COLLAPSED_WIDTH if is_expanded else self.SIDEBAR_EXPANDED_WIDTH
        )

        # Kept as an instance attribute so it isn't garbage-collected mid-animation.
        self._sidebar_animation = QtCore.QVariantAnimation(self)
        self._sidebar_animation.setDuration(self.ANIMATION_DURATION_MS)
        self._sidebar_animation.setStartValue(self.ui.sidebar.width())
        self._sidebar_animation.setEndValue(new_width)
        self._sidebar_animation.setEasingCurve(QtCore.QEasingCurve.InOutCubic)
        # setFixedWidth pins both min and max together each frame, so the
        # frame actually resizes regardless of the fixed min/max Designer set.
        self._sidebar_animation.valueChanged.connect(
            lambda value: self.ui.sidebar.setFixedWidth(int(value))
        )
        self._sidebar_animation.start()

        collapsing = is_expanded
        for object_name, label in self.NAV_BUTTON_LABELS.items():
            getattr(self.ui, object_name).setText("" if collapsing else label)
