

MANUFACTURER_NAME_UUID = "00002A29-0000-1000-8000-00805f9b34fb"
MODEL_NUMBER_UUID = "00002A24-0000-1000-8000-00805f9b34fb"
SERIAL_NUMBER_UUID = "00002A25-0000-1000-8000-00805f9b34fb"
HARDWARE_REVISION_UUID = "00002A27-0000-1000-8000-00805f9b34fb"
FIRMWARE_REVISION_UUID = "00002A26-0000-1000-8000-00805f9b34fb"
SOFTWARE_REVISION_UUID = "00002A28-0000-1000-8000-00805f9b34fb"
SYSTEM_ID_UUID = "00002A23-0000-1000-8000-00805f9b34fb"
PNP_ID_UUID = "00002A50-0000-1000-8000-00805f9b34fb"
BATTERY_LEVEL_UUID = "00002A19-0000-1000-8000-00805f9b34fb"

BLUETOOTH_BASE_UUID = "-0000-1000-8000-00805f9b34fb"

GATT_UUIDS = {
    "1800": "Generic Access",
    "1801": "Generic Attribute",
    "180A": "Device Information",
    "2A29": "Manufacturer Name",
    "2A24": "Model Number",
    "2A25": "Serial Number",
    "2A26": "Firmware Revision",
    "2A27": "Hardware Revision",
    "2A28": "Software Revision",
    "2A23": "System ID",
    "2A2A": "IEEE 11073-20601 Regulatory Certification Data List", # Data type transcoding
    "2A50": "PnP ID",

    "1818": "Cycling Power Service",
    "2A63": "Cycling Power Measurement",
    "2A65": "Cycling Power Feature",
    "2A5D": "Sensor Location",
    "2A66": "Cycling Power Control Point",

    "180F": "Battery Service",
    "2A19": "Battery Level",
}


def short_uuid(uuid: str) -> str:
    uuid = uuid.lower()
    if uuid.endswith(BLUETOOTH_BASE_UUID):
        return uuid[4:8].upper()
    return uuid.upper()


# Convert UUID into a human readable name.
def gatt_name(uuid: str) -> str:
    short = short_uuid(uuid)
    return GATT_UUIDS.get(short, f"Unknown GATT ({short})")


def describe_uuid(uuid: str) -> str:
    short = short_uuid(uuid)
    name = gatt_name(uuid)
    return f"0x{short} ({name})"
