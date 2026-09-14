import os
import xml.etree.ElementTree as ET
from datetime import datetime

from PyQt5.QtCore import QObject, pyqtSlot


class AppointmentsBE(QObject):
    XML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "appointments.xml")

    _DEFAULT_MEETINGS = {
        "20260903_gay": {
            "name": "Wru Gay",
            "appointment_time": "12:00",
            "appointment_date": "03-09-2026",
            "cancelled": False,
        },
        "20260914_lord": {
            "name": "Bob Lord",
            "appointment_time": "12:00",
            "appointment_date": "14-09-2026",
            "cancelled": False,
        },
        "20260920_focker": {
            "name": "Frilly Focker",
            "appointment_time": "12:00",
            "appointment_date": "20-09-2026",
            "cancelled": False,
        },
    }

    def __init__(self):
        super().__init__()
        self.client_meetings = self._load_from_xml()

    def _load_from_xml(self):
        if not os.path.exists(self.XML_PATH):
            meetings = {key: dict(value) for key, value in self._DEFAULT_MEETINGS.items()}
            self.client_meetings = meetings
            self._save_to_xml()
            return meetings

        meetings = {}
        tree = ET.parse(self.XML_PATH)
        for meeting_el in tree.getroot().findall("meeting"):
            meeting_id = meeting_el.get("id")
            if not meeting_id:
                continue
            meetings[meeting_id] = {
                "name": meeting_el.findtext("name", default=""),
                "appointment_date": meeting_el.findtext("appointment_date", default=""),
                "appointment_time": meeting_el.findtext("appointment_time", default=""),
                "cancelled": (meeting_el.findtext("cancelled", default="false") or "").strip().lower()
                == "true",
            }
        return meetings

    def _save_to_xml(self):
        root = ET.Element("appointments")
        for meeting_id, meeting in self.client_meetings.items():
            meeting_el = ET.SubElement(root, "meeting", {"id": meeting_id})
            ET.SubElement(meeting_el, "name").text = meeting.get("name", "")
            ET.SubElement(meeting_el, "appointment_date").text = meeting.get("appointment_date", "")
            ET.SubElement(meeting_el, "appointment_time").text = meeting.get("appointment_time", "")
            ET.SubElement(meeting_el, "cancelled").text = "true" if meeting.get("cancelled") else "false"

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(self.XML_PATH, encoding="utf-8", xml_declaration=True)

    def get_meetings(self):
        meetings = []
        for meeting_id, meeting in self.client_meetings.items():
            entry = dict(meeting)
            entry["id"] = meeting_id
            entry.setdefault("cancelled", False)
            meetings.append(entry)
        return meetings

    def cancel_meeting(self, meeting_id):
        if meeting_id in self.client_meetings:
            self.client_meetings[meeting_id]["cancelled"] = True
            self._save_to_xml()

    def restore_meeting(self, meeting_id):
        if meeting_id in self.client_meetings:
            self.client_meetings[meeting_id]["cancelled"] = False
            self._save_to_xml()

    def add_meeting(self, last_name, name, date_str, time_str):
        date_obj = datetime.strptime(date_str, "%d-%m-%Y")
        key_prefix = date_obj.strftime("%Y%m%d")

        unique_key = f"{key_prefix}_{last_name.lower()}"

        self.client_meetings[unique_key] = {
            "name": name,
            "appointment_time": time_str,
            "appointment_date": date_str,
            "cancelled": False,
        }
        self._save_to_xml()
        return unique_key

    def get_upcoming_meetings(self):
        today = datetime.today()
        upcoming = {}

        for key, details in self.client_meetings.items():
            meeting_date = datetime.strptime(details["appointment_date"], "%d-%m-%Y")
            if meeting_date >= today:
                upcoming[key] = details

        return upcoming
