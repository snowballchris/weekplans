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

## Prerequisites

- Python 3.x
- poppler-utils (for PDF conversion)
- Node.js and npm (for frontend development)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/snowballchris/weekplans.git
   cd weekplans
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

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

1. Start the Flask backend:
   ```bash
   python app.py
   ```
   The server will start on `http://localhost:5001`

2. Access the dashboard:
   - Main dashboard: `http://localhost:5001/`
   - Admin panel: `http://localhost:5001/admin`

## Raspberry Pi – One‑command install (recommended)

For a simple, reliable two‑process setup (Flask API via Gunicorn, frontend via Nginx), run this on a fresh Raspberry Pi OS:

```bash
curl -fsSL https://raw.githubusercontent.com/snowballchris/weekplans/main/scripts/install.sh | sudo bash
```

After it finishes:
- Open: `http://<pi-ip>/`
- API health: `http://<pi-ip>/mode`

To update later:
```bash
curl -fsSL https://raw.githubusercontent.com/snowballchris/weekplans/main/scripts/update.sh | sudo bash
```

### What the installer does
- Installs system packages: Python, venv, pip, poppler-utils, Nginx, Node.js, npm, git
- Clones/updates this repo into `/opt/weekplans`
- Creates a Python venv and installs backend deps + Gunicorn
- Builds the React frontend (`frontend/dist`)
- Sets up a systemd service `weekplans` (Gunicorn on 127.0.0.1:5001)
- Configures Nginx to serve the frontend and proxy API routes to 5001
- Enables services to start on boot

### Scripts (for reference)

`scripts/install.sh` (used by the one‑liner)
```bash
#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/weekplans
REPO_URL=${REPO_URL:-https://github.com/snowballchris/weekplans.git}
BRANCH=${BRANCH:-main}
API_BIND=127.0.0.1:5001
SYSTEM_USER=${SYSTEM_USER:-pi}
SYSTEM_GROUP=${SYSTEM_GROUP:-pi}

apt update
apt install -y python3 python3-venv python3-pip poppler-utils nginx nodejs npm git

mkdir -p "$APP_DIR"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch --all
  git -C "$APP_DIR" checkout "$BRANCH"
  git -C "$APP_DIR" pull --ff-only
else
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt gunicorn

cd "$APP_DIR/frontend"
npm ci
npm run build

cat >/etc/systemd/system/weekplans.service <<EOF
[Unit]
Description=Weekplans Flask API
After=network-online.target
Wants=network-online.target
[Service]
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn -w 2 -b $API_BIND app:app
Environment=PYTHONUNBUFFERED=1
Restart=always
User=$SYSTEM_USER
Group=$SYSTEM_GROUP
[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now weekplans

cat >/etc/nginx/sites-available/weekplans <<EOF
server {
  listen 80;
  server_name _;
  root $APP_DIR/frontend/dist;
  index index.html;
  location ~ ^/(api|mode|screensaver_image|admin) {
    proxy_pass http://$API_BIND;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
  location / {
    try_files $uri /index.html;
  }
}
EOF

ln -sf /etc/nginx/sites-available/weekplans /etc/nginx/sites-enabled/weekplans
nginx -t
systemctl reload nginx

echo "Done. Open: http://<pi-ip>/"
```

`scripts/update.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
APP_DIR=/opt/weekplans
cd "$APP_DIR"
if [ -d .git ]; then git pull --ff-only; fi
./venv/bin/pip install -r requirements.txt
cd frontend && npm ci && npm run build
systemctl restart weekplans
systemctl reload nginx
echo "Updated."
```

### Configuration on Pi
- Edit `/opt/weekplans/config.json` to adjust settings (names/icons, MQTT, duration).
- Restart API after edits:
```bash
sudo systemctl restart weekplans
```

### Troubleshooting
- API logs: `sudo journalctl -u weekplans -f`
- Nginx test/reload: `sudo nginx -t && sudo systemctl reload nginx`
- Health: `curl http://localhost/mode` should return JSON 200

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
weekplans2/
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
