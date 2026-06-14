from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry


class LookPedal:
    def __init__(self, address: str, name: str):
        self.address = address
        self.name = name
        self.entry_id = None
        self.advertisement_count = 0
        self.last_seen = None
        self.last_service_info = None
        self.rssi = None


    @classmethod
    def from_config_entry(cls, entry: ConfigEntry) -> "LookPedal":
        pedal = cls(
            address=entry.data["address"],
            name=entry.title,
        )
        pedal.entry_id = entry.entry_id
        return pedal


    def update_from_advertisement(self, service_info: bluetooth.BluetoothServiceInfoBleak) -> None:
        self.advertisement_count += 1
        self.last_seen = service_info.time
        self.last_service_info = service_info
        self.rssi = service_info.rssi

        if service_info.name:
            self.name = service_info.name
