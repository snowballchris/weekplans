# <img src="icon.png" alt="" height="1em" style="vertical-align: middle; margin-right: 8px;"> WeekPlans - Home Assistant App

Digital weekly schedule display for home automation. Perfect for information radiators, tablet dashboards, or any display showing weekly plans.

## Features

- Display PDF schedules as images (auto-converted, supports two pages)
- Multiple weekplan support with custom names and icons
- Screensaver mode with image rotation
- Configurable screensaver buttons (show plan1/plan2/all, or custom URL) with position and colors
- Calendar integration (iCal/Google Calendar) with per-plan assignments and upcoming events
- Display page selection (page 1 or 2) per plan for the "all" view
- Dashboard language (English, Norwegian Bokmål)
- Optional MQTT integration with Home Assistant discovery
- Controls tab: display on/off, brightness, browser URL, refresh, system restart
- Keyboard shortcuts: Arrow Left/Right/Up to switch views
- Responsive design for various display sizes

## Standalone Docker

You can also run WeekPlans as a standalone Docker container without Home Assistant. See the main [WeekPlans repository](https://github.com/snowballchris/weekplans) for full Docker documentation.

## Installation

1. Add this repository to Home Assistant:
   - Go to **Settings** → **Apps** → **App repositories**
   - Add: `https://github.com/snowballchris/weekplans`
   - Or add the repository as a local path if using a custom setup

2. Install the WeekPlans app from the Apps store

3. Configure the app (optional):
   - **MQTT**: Enable if you want to control displays via MQTT and use Home Assistant discovery
   - **Broker**: Use `core-mosquitto` if you have the Mosquitto broker add-on, or your MQTT broker hostname
   - MQTT is optional—the app works without it

4. Start the app and access it:
   - **Open Web UI** button in the Apps view opens the admin panel directly
   - Or open `http://<your-ha-ip>:8080` (dashboard: `/`, admin: `/admin`)

## Configuration

Configure via the app settings in Home Assistant, or use the admin panel at `/admin` after starting the app. Settings configured in the Home Assistant app (MQTT broker, etc.) take precedence and will be shown as read-only in the admin panel.

## Documentation

See the main [WeekPlans repository](https://github.com/snowballchris/weekplans) for full documentation.
