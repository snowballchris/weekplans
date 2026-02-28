# WeekPlans - Digital Weekly Schedule Display System

A Flask-based web application designed to display and manage weekly schedules in a digital format. Perfect for home automation displays, information radiators, or any scenario where you need to show and manage weekly plans digitally.

## Features

- 📅 Digital weekly schedule display with multiple plan support
- 🖼️ Customizable screensaver mode with image rotation
- 🔄 PDF to image conversion for easy schedule updates
- ⚙️ Admin panel for system management
- 🌐 MQTT integration for home automation (optional)
- 📱 Responsive design for various display sizes
- ⏱️ Configurable display duration
- 🔆 Brightness control (via MQTT)
- 🎯 URL control for browser integration

## Docker

WeekPlans is designed to run as a single Docker container that serves the frontend (Nginx) and API (Gunicorn).

1. Pull the prebuilt image:
   ```bash
   docker pull ghcr.io/snowballchris/weekplans:latest
   ```

2. Run the container:
   ```bash
   mkdir -p data/static data/uploads
   cp example/config.example.json data/config.json

   docker run --rm -p 8080:80 \
     -v "$(pwd)/data:/data" \
     ghcr.io/snowballchris/weekplans:latest
   ```

3. Build locally (optional):
   ```bash
   git clone https://github.com/snowballchris/weekplans.git
   cd weekplans
   docker build -t weekplans .
   ```

4. Run the locally built image:
   ```bash
   mkdir -p data/static data/uploads
   cp example/config.example.json data/config.json

   docker run --rm -p 8080:80 \
     -v "$(pwd)/data:/data" \
     weekplans
   ```

Then open:
- `http://localhost:8080/` (dashboard)
- `http://localhost:8080/admin` (admin)

Notes:
- `poppler-utils` is included in the image for PDF conversion.
- The `/data` volume holds `config.json`, uploads, and generated images.

### Environment variables (optional)

You can override MQTT settings via environment variables. When set, these take precedence over `config.json` and the admin panel will show them as read-only:

| Variable | Description |
|----------|-------------|
| `WEEKPLANS_ENABLE_MQTT` | Enable MQTT (`1`, `true`, or `yes`) |
| `WEEKPLANS_MQTT_BROKER` | MQTT broker hostname |
| `WEEKPLANS_MQTT_PORT` | MQTT port (default 1883) |
| `WEEKPLANS_MQTT_USER` | MQTT username |
| `WEEKPLANS_MQTT_PASS` | MQTT password |

Example with env vars:
```bash
docker run --rm -p 8080:80 \
  -v "$(pwd)/data:/data" \
  -e WEEKPLANS_ENABLE_MQTT=true \
  -e WEEKPLANS_MQTT_BROKER=homeassistant.local \
  ghcr.io/snowballchris/weekplans:latest
```

## Home Assistant App

WeekPlans can run as a Home Assistant app (formerly add-on). Add this repository in Home Assistant:

1. Go to **Settings** → **Apps** → **App repositories**
2. Add: `https://github.com/snowballchris/weekplans`
3. Install the WeekPlans app from the Apps store
4. Configure MQTT (optional) in the app settings
5. Open `http://<your-ha-ip>:8080` for the dashboard and admin

The same Docker image works for both standalone Docker and Home Assistant. MQTT is optional in both modes.

## Configuration

The application uses several configuration files:

- `config.json`: Main configuration file (copy from `example/config.example.json` for first run)
  - Dashboard duration
  - Screensaver settings
  - MQTT configuration
  - Weekplan settings

Example configuration:
```json
{
  "dashboard_duration": 10,
  "screensaver_config": [],
  "enable_mqtt": false,
  "mqtt_broker": "homeassistant.local",
  "mqtt_port": 1883,
  "mqtt_user": "",
  "mqtt_pass": "",
  "weekplans": [
    {"key": "plan1", "name": "Weekplan 1", "icon": "1"},
    {"key": "plan2", "name": "Weekplan 2", "icon": "2"}
  ]
}
```

## Usage

The Docker container serves the dashboard and admin interface:
- Main dashboard: `http://localhost:8080/`
- Admin panel: `http://localhost:8080/admin`

## Features in Detail

### Weekly Plans
- Upload PDF schedules that are automatically converted to images
- Support for multiple plans with custom names and icons
- Timestamp tracking for last updates

### Screensaver Mode
- Upload images directly or via URLs
- Random rotation of active images
- Enable/disable individual images

### MQTT Integration
- Optional integration with home automation systems
- Control display brightness
- Monitor system status
- URL control for browser-based displays

### Admin Panel
- System statistics monitoring
- Configuration management
- Schedule uploads
- Screensaver management
- MQTT settings
- Display controls

## Directory Structure

```
weekplans/
├── app.py              # Main Flask application
├── example/
│   └── config.example.json  # Example configuration (copy to data/config.json)
├── requirements.txt    # Python dependencies
├── frontend/          # React frontend
├── static/
│   ├── images/        # Converted schedule images
│   ├── screensaver/   # Screensaver images
│   └── js/           # JavaScript files
├── templates/         # HTML templates
└── uploads/          # Temporary PDF storage
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask for the web framework
- pdf2image for PDF conversion
- Pillow for image processing
- paho-mqtt for MQTT integration
