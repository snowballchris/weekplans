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

1. Clone the repository:
   ```bash
   git clone https://github.com/snowballchris/weekplans.git
   cd weekplans
   ```

2. Build the image:
   ```bash
   docker build -t weekplans .
   ```

3. Run the container:
   ```bash
   docker run --rm -p 8080:80 \
     -v "$(pwd)/config.json:/app/config.json" \
     -v "$(pwd)/static:/app/static" \
     -v "$(pwd)/uploads:/app/uploads" \
     weekplans
   ```

Then open:
- `http://localhost:8080/` (dashboard)
- `http://localhost:8080/admin` (admin)

Notes:
- `poppler-utils` is included in the image for PDF conversion.
- The volume mounts keep settings and uploads between restarts.

## Configuration

The application uses several configuration files:

- `config.json`: Main configuration file
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
├── config.json         # Configuration file
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
