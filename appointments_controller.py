from datetime import datetime

from PyQt5 import QtCore, QtWidgets

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

        self.load_appointments()

    def show_page(self, page):
        self.ui.contentStack.setCurrentWidget(page)

    def load_appointments(self):
        """Fetch meetings from the backend, sort them chronologically, and
        render them as HTML in the dashboard's Appointments_listed browser."""
        meetings = self.appointments_be.get_meetings()

        def sort_key(meeting):
            return datetime.strptime(
                f"{meeting['appointment_date']} {meeting['appointment_time']}",
                "%d-%m-%Y %H:%M",
            )

        meetings = sorted(meetings, key=sort_key)

        if not meetings:
            self.ui.Appointments_listed.setHtml(
                "<p style='color:#888;'>No upcoming appointments.</p>"
            )
            return

        rows = []
        for meeting in meetings:
            rows.append(
                "<p style='margin:4px 0;'>"
                "<b>{name}</b> &mdash; {date} at {time}"
                "</p>".format(
                    name=meeting["name"],
                    date=meeting["appointment_date"],
                    time=meeting["appointment_time"],
                )
            )

        self.ui.Appointments_listed.setHtml("".join(rows))

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
