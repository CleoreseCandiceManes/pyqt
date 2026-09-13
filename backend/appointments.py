from PyQt5.QtCore import QObject, pyqtSlot
from datetime import datetime

class AppointmentsBE(QObject):
    def __init__(self):
        super().__init__()

        self.client_meetings = {
            "20260903_gay": {"name": "Wru Gay", "appointment_time": "12:00", "appointment_date": "03-09-2026" },
            "20260914_lord": {"name": "Bob Lord", "appointment_time": "12:00", "appointment_date": "14-09-2026"},
            "20260920_focker": {"name": "Frilly Focker", "appointment_time": "12:00", "appointment_date": "20-09-2026"}
        }

    def get_meetings(self):
        """Return the scheduled meetings as a list of dicts, each including
        its id (so callers can cancel/restore a specific meeting) and a
        cancelled flag (defaulting to False for older entries)."""
        meetings = []
        for meeting_id, meeting in self.client_meetings.items():
            entry = dict(meeting)
            entry["id"] = meeting_id
            entry.setdefault("cancelled", False)
            meetings.append(entry)
        return meetings

    def cancel_meeting(self, meeting_id):
        """Mark a meeting as cancelled (kept in the list, shown struck-through)."""
        if meeting_id in self.client_meetings:
            self.client_meetings[meeting_id]["cancelled"] = True

    def restore_meeting(self, meeting_id):
        """Undo a cancellation."""
        if meeting_id in self.client_meetings:
            self.client_meetings[meeting_id]["cancelled"] = False

    def add_meeting(self, last_name, name, date_str, time_str):
        """
        Dynamically adds a meeting using the exact format you established.
        Expects date_str as 'DD-MM-YYYY' and time_str as 'HH:MM'
        """
        # Parse date to build the YYYYMMDD prefix for the unique key
        date_obj = datetime.strptime(date_str, "%d-%m-%Y")
        key_prefix = date_obj.strftime("%Y%m%d")
        
        # Build the dictionary key (e.g., '20260914_lord')
        unique_key = f"{key_prefix}_{last_name.lower()}"
        
        # Insert the meeting data
        self.client_meetings[unique_key] = {
            "name": name,
            "appointment_time": time_str,
            "appointment_date": date_str
        }
        return unique_key

    def get_upcoming_meetings(self):
        """Filters out past meetings based on the current date."""
        today = datetime.today()
        upcoming = {}
        
        for key, details in self.client_meetings.items():
            meeting_date = datetime.strptime(details["appointment_date"], "%d-%m-%Y")
            if meeting_date >= today:
                upcoming[key] = details
                
        return upcoming
