from PyQt5.QtCore import QObject, pyqtSlot


class AppointmentsBE(QObject):
    def __init__(self):
        super().__init__()

        self.client_meetings = {
            "20260903_gay": {"name": "Wru Gay", "appointment_time": "12:00", "appointment_date": "03-09-2026" },
            "20260914_lord": {"name": "Bob Lord", "appointment_time": "12:00", "appointment_date": "14-09-2026"},
            "20260920_focker": {"name": "Frilly Focker", "appointment_time": "12:00", "appointment_date": "20-09-2026"}
        }

    def get_meetings(self):
        """Return the scheduled meetings as a plain list of dicts."""
        return list(self.client_meetings.values())
