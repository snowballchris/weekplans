# <img src="icon.png" alt="" height="1em" style="vertical-align: middle; margin-right: 8px;"> WeekPlans Beta - Home Assistant App

**Beta version** – for testing upcoming features. May be less stable than the [stable WeekPlans add-on](../weekplans).

Digital weekly schedule display for home automation. Perfect for information radiators, tablet dashboards, or any display showing weekly plans.

## Features

- Display PDF schedules as images (auto-converted)
- Multiple weekplan support
- Screensaver mode with image rotation
- Calendar integration (iCal/Google Calendar)
- Optional MQTT integration for Home Assistant control
- Responsive design for various display sizes

## Installation

1. Add this repository to Home Assistant:
   - Go to **Settings** → **Apps** → **App repositories**
   - Add: `https://github.com/snowballchris/weekplans`
   - Or add the repository as a local path if using a custom setup

2. Install **WeekPlans Beta** (not "WeekPlans") from the Apps store

3. Configure the app (optional):
   - **MQTT**: Enable if you want to control displays via MQTT and use Home Assistant discovery
   - **Broker**: Use `core-mosquitto` if you have the Mosquitto broker add-on, or your MQTT broker hostname
   - MQTT is optional—the app works without it

4. Start the app and access it:
   - **Open Web UI** button in the Apps view opens the admin panel directly
   - Or open `http://<your-ha-ip>:8080` (dashboard: `/`, admin: `/admin`)

## Note

WeekPlans Beta and WeekPlans (stable) use the same port. Install only one at a time, or use different ports if you need both for testing.

## Documentation

See the main [WeekPlans repository](https://github.com/snowballchris/weekplans) for full documentation.
