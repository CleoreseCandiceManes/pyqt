import os
import xml.etree.ElementTree as ET

from PyQt5.QtCore import QObject


class ClientsBE(QObject):
    """Persists client records to clients.xml, next to this module - same
    approach as AppointmentsBE: every add writes the whole file back out
    immediately."""

    XML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clients.xml")

    # The fields every client record has, shared by the load and save
    # methods instead of listing the same field names in both.
    FIELDS = (
        "first_name",
        "last_name",
        "email_address",
        "phone_nr",
        "client_type",
        "owned_property",
        "interested_property",
        "notes",
    )

    def __init__(self):
        super().__init__()
        self.clients = self._load_from_xml()

    def _load_from_xml(self):
        """Load clients from clients.xml next to this file. Unlike
        appointments, there's no seed data - if the file doesn't exist yet,
        start with an empty client list (it's created on the first save)."""
        if not os.path.exists(self.XML_PATH):
            return {}

        clients = {}
        tree = ET.parse(self.XML_PATH)
        for client_el in tree.getroot().findall("client"):
            client_id = client_el.get("id")
            if not client_id:
                continue
            clients[client_id] = {
                field: client_el.findtext(field, default="") for field in self.FIELDS
            }
        return clients

    def _save_to_xml(self):
        """Write self.clients back out to clients.xml in full."""
        root = ET.Element("clients")
        for client_id, client in self.clients.items():
            client_el = ET.SubElement(root, "client", {"id": client_id})
            for field in self.FIELDS:
                ET.SubElement(client_el, field).text = client.get(field, "")

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(self.XML_PATH, encoding="utf-8", xml_declaration=True)

    def get_clients(self):
        """Return the saved clients as a list of dicts, each including its
        id."""
        clients = []
        for client_id, client in self.clients.items():
            entry = dict(client)
            entry["id"] = client_id
            clients.append(entry)
        return clients

    def remove_client(self, client_id):
        """Delete a client record and persist the change immediately."""
        if client_id in self.clients:
            del self.clients[client_id]
            self._save_to_xml()

    def _has_client(self, first_name, last_name):
        return any(
            client.get("first_name") == first_name and client.get("last_name") == last_name
            for client in self.clients.values()
        )

    def ensure_clients_from_names(self, full_names):
        """Given full names (e.g. from existing appointments), add a bare
        client record - just first/last name, everything else blank - for
        any name not already in the client list. Safe to call on every
        startup: names already known as clients are skipped, so nothing
        gets duplicated."""
        added = []
        for full_name in full_names:
            parts = full_name.split()
            if not parts:
                continue
            first_name = parts[0]
            last_name = parts[-1] if len(parts) > 1 else parts[0]
            if self._has_client(first_name, last_name):
                continue
            client_id = self.add_client(first_name, last_name, "", "", "", "", "", "")
            added.append(client_id)
        return added

    def _unique_key(self, first_name, last_name):
        base = f"{first_name}_{last_name}".strip("_").lower().replace(" ", "_") or "client"
        key = base
        suffix = 2
        while key in self.clients:
            key = f"{base}_{suffix}"
            suffix += 1
        return key

    def add_client(
        self,
        first_name,
        last_name,
        email_address,
        phone_nr,
        client_type,
        owned_property,
        interested_property,
        notes,
    ):
        """Add a new client record and persist it to clients.xml
        immediately. Returns the new client's id."""
        client_id = self._unique_key(first_name, last_name)
        self.clients[client_id] = {
            "first_name": first_name,
            "last_name": last_name,
            "email_address": email_address,
            "phone_nr": phone_nr,
            "client_type": client_type,
            "owned_property": owned_property,
            "interested_property": interested_property,
            "notes": notes,
        }
        self._save_to_xml()
        return client_id
