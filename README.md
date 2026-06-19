<!-- markdownlint-disable first-line-heading -->
<!-- markdownlint-disable no-inline-html -->
<img src="custom_components/look_keo_blade_power/brand/icon.png" width="12%" align="left" style="float: left; margin: 30px 0px 20px 20px;" />

[![GitHub Release](https://img.shields.io/github/v/release/neznein9/Keo-Blade-Power-Integration-for-Home-Assistant)](https://github.com/neznein9/Keo-Blade-Power-Integration-for-Home-Assistant/releases/latest)
[![GitHub License](https://img.shields.io/github/license/neznein9/Keo-Blade-Power-Integration-for-Home-Assistant?cacheSeconds=60)](./LICENSE)
[![hacs](https://img.shields.io/badge/HACS-default-green.svg)](https://hacs.xyz)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-blue.svg)](https://github.com/neznein9/Keo-Blade-Power-Integration-for-Home-Assistant/pulls)

<!-- https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.dvla.total -->

---


# Keo Blade Power Integration for Home-Assistant

## Integration for Home Assistant
This is a community integration for [Home Assistant](https://www.home-assistant.io/) that adds support for [LOOK Keo Blade Power](https://www.lookcycle.com/us-en/products/pedals/powermeter/keo-blade-power-single) power meter pedals.


## Features

- [x] Passively read device advertisements over BLE
- [x] Connect and poll battery charge percent
- [x] Connect and read device configuration details
- [ ] ~~Connect and read cycling power data~~

## A Note about Bluetooth
The Keo Blade Power pedals are very conservative with energy usage. They do not appear to send BLE advertisements unless physically woken up.

The pedals only allow one Bluetooth connection at a time. If the pedals are connected to a cycling computer or smart phone, they become invisible to Home Assistant (and vice versa). Because of this limitation, Home Assistant will only attempt to read the battery level of the pedals when a Bluetooth advertisement packet is received, by connecting for about 1 second and then releasing the connection. (Up to one time per hour maximum.)


## Requirements
- [Bluetooth](https://www.home-assistant.io/integrations/bluetooth/) integration with Home Assistant
- An active Bluetooth antenna in range of the LOOK bike pedal

## Installation

### HACS

Click the button to install via [HACS](https://hacs.xyz/):

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=neznein9&repository=Keo-Blade-Power-Integration-for-Home-Assistant&category=device)

Or manually:

1. Open HACS
2. Go to **Integrations**
3. Open the **⋮** three-dot menu
4. Select **Custom repositories**
5. Paste this repository URL
6. Set category to **Integration**
7. Install **LOOK Keo Blade Power**
8. Restart Home Assistant

### Manual Installation

Copy the `custom_components/look_keo_blade_power` directory from this repo into your `custom_components` config directory.

## Usage

#### 1. Find the MAC address of your pedal
Use the Bluetooth integration, or a scanner such as [nRF Connect](https://apps.apple.com/us/app/nrf-connect-for-mobile/id1054362403) to find your pedal's MAC address.
- Make sure the pedals are within close range of the scanning device
- Make sure pedals are "awake" by spinning the cranks once or twice until the charge LED blinks
- Attaching to the charger helps the pedals broadcast more reliably
- Pedals tend to advertise immediately when awoken, then again about 2 minutes later. After two minutes, the pedals usually go back to sleep.

#### 2. Create a new device in Home Assistant
In Home Assistant, in Settings > Devices & Services, click `+ Add Integration` and choose **LOOK Keo Blade Power**.

#### 3. Connect by MAC address
Paste in the MAC address of your pedal and click `Submit`. You will then see the device page. Wake up your pedals again and watch for the RSSI signal to become visible.

Home Assistant will automatically attempt to read the battery and device data.


## Tested Devices
- [x] [Keo Blade Power Single](https://www.lookcycle.com/us-en/products/pedals/powermeter/keo-blade-power-single)
- [ ] [Keo Blade Power Dual](https://www.lookcycle.com/us-en/products/pedals/powermeter/keo-blade-power-dual)
- [ ] [Keo Blade Power Dual<sup>VISION</sup>](https://www.lookcycle.com/us-en/products/pedals/powermeter/keo-blade-power-dual-vision)
- [ ] [X-Track Power Single](https://www.lookcycle.com/us-en/products/pedals/powermeter/x-track-power-single)
- [ ] [X-Track Power Dual](https://www.lookcycle.com/us-en/products/pedals/powermeter/x-track-power-dual)


## Contributing

The LOOK pedals expose standard Bluetooth Battery Service,
Device Information Service, and Cycling Power Service
characteristics.

Contributions are welcome, especially around:
- Additional LOOK power meter models
- BT Cycling Power Service decoding
