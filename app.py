import os
import errno
import locale
import json
import random
import subprocess
import uuid
import requests
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify
from pdf2image import convert_from_path
from urllib.parse import urlparse
from typing import Optional, Dict, List
from werkzeug.utils import secure_filename
from icalendar import Calendar
import pytz
import recurring_ical_events

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Always log to console
    ]
)
logger = logging.getLogger(__name__)

# --- Configuration ---
# Base directory and folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
STATIC_IMAGE_FOLDER = os.path.join(STATIC_FOLDER, 'images')
SCREENSAVER_FOLDER = os.path.join(STATIC_FOLDER, 'screensaver')

# Create necessary folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_IMAGE_FOLDER, exist_ok=True)
os.makedirs(SCREENSAVER_FOLDER, exist_ok=True)
os.makedirs(os.path.join(STATIC_FOLDER, 'js'), exist_ok=True)

# Files for persistent settings and dynamic state
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')
UPDATE_FILE = os.path.join(BASE_DIR, 'last_updates.json')
DASHBOARD_MODE_FILE = os.path.join(BASE_DIR, 'dashboard_mode.json')

# Allowed file extensions for security
ALLOWED_PDF_EXTENSIONS = {'pdf'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'avif'}

# --- Helper Functions ---
def allowed_file(filename, allowed_extensions):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_system_stats():
    """Get container-friendly system statistics for the Controls tab."""
    stats = {
        "uptime": "Unknown",
        "start_time": "Unknown",
        "memory_usage": "Unknown",
        "memory_limit": "Unknown",
        "container_id": "Unknown"
    }

    def read_first_line(path: str) -> Optional[str]:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return handle.readline().strip()
        except Exception:
            return None

    def format_bytes(value_bytes: int) -> str:
        if value_bytes < 1024:
            return f"{value_bytes} B"
        if value_bytes < 1024 ** 2:
            return f"{value_bytes / 1024:.1f} KB"
        if value_bytes < 1024 ** 3:
            return f"{value_bytes / (1024 ** 2):.1f} MB"
        return f"{value_bytes / (1024 ** 3):.1f} GB"

    try:
        uptime_line = read_first_line("/proc/uptime")
        if uptime_line:
            uptime_seconds = int(float(uptime_line.split()[0]))
            delta = timedelta(seconds=uptime_seconds)
            stats["uptime"] = str(delta)
            stats["start_time"] = (datetime.now() - delta).strftime("%Y-%m-%d %H:%M:%S")

        try:
            with open("/proc/self/status", "r", encoding="utf-8") as handle:
                status_content = handle.read()
        except Exception:
            status_content = ""
        for line in status_content.splitlines():
            if line.startswith("VmRSS:"):
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    stats["memory_usage"] = format_bytes(int(parts[1]) * 1024)
                break

        memory_max = read_first_line("/sys/fs/cgroup/memory.max")
        if memory_max:
            if memory_max == "max":
                stats["memory_limit"] = "Unlimited"
            elif memory_max.isdigit():
                stats["memory_limit"] = format_bytes(int(memory_max))

        container_id = read_first_line("/etc/hostname")
        if container_id:
            stats["container_id"] = container_id
    except Exception as e:
        logger.error(f"Could not retrieve all system stats: {e}")

    return stats

def fetch_calendar_events(ical_url: str, days_ahead: int = 14) -> List[Dict]:
    """Fetch and parse iCal events from a URL, returning events for the next N days including recurring events.
    Default N is 14 (2 weeks)."""
    # Normalize webcal:// URLs to https:// (webcal is just a protocol hint, not a real protocol)
    normalized_url = ical_url.replace('webcal://', 'https://', 1) if ical_url.startswith('webcal://') else ical_url
    
    try:
        logger.info(f"Fetching calendar from: {normalized_url}")
        
        # Fetch the iCal data
        response = requests.get(normalized_url, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Calendar data fetched, size: {len(response.content)} bytes")
        
        # Get current date and window end
        now = datetime.now()
        window_end = now + timedelta(days=days_ahead)
        
        logger.info(f"Date range: {now.strftime('%Y-%m-%d %H:%M')} to {window_end.strftime('%Y-%m-%d %H:%M')}")
        
        # Parse the calendar first
        cal = Calendar.from_ical(response.content)
        
        # Use recurring_ical_events to get all events (including recurring) within the date range
        # The library expects dates, not datetimes for the between() method
        start_date = now.date()
        end_date = window_end.date()
        
        logger.info(f"Using date range for recurring events: {start_date} to {end_date}")
        
        events_in_range = recurring_ical_events.of(cal).between(start_date, end_date)
        
        logger.info(f"Found {len(events_in_range)} events in range")
        
        events = []
        local_tz = pytz.timezone('Europe/Oslo')  # Adjust timezone as needed
        
        for i, event in enumerate(events_in_range):
            try:
                # Get event details
                summary = str(event.get('summary', 'No Title'))
                location = str(event.get('location', ''))
                dtstart = event.get('dtstart')
                
                logger.debug(f"Processing event {i+1}: {summary}")
                
                if dtstart:
                    # Handle different datetime formats
                    if hasattr(dtstart.dt, 'astimezone'):
                        # It's a datetime object with timezone
                        event_start = dtstart.dt
                        if event_start.tzinfo is None:
                            event_start = event_start.replace(tzinfo=pytz.UTC)
                        local_start = event_start.astimezone(local_tz)
                    elif hasattr(dtstart.dt, 'year'):
                        # It's a date object (all-day event), convert to datetime
                        event_start = datetime.combine(dtstart.dt, datetime.min.time())
                        event_start = event_start.replace(tzinfo=local_tz)
                        local_start = event_start
                    else:
                        continue
                    
                    # Check if it's an all-day event
                    is_all_day = not hasattr(dtstart.dt, 'hour') or (
                        hasattr(dtstart.dt, 'hour') and dtstart.dt.hour == 0 and dtstart.dt.minute == 0
                    )
                    
                    event_data = {
                        'summary': summary,
                        'location': location,
                        'start_datetime': local_start.isoformat(),
                        'start_date': local_start.strftime('%Y-%m-%d'),
                        'start_time': 'All day' if is_all_day else local_start.strftime('%H:%M'),
                        'weekday': local_start.strftime('%A'),
                        'is_all_day': is_all_day
                    }
                    events.append(event_data)
                    
            except Exception as e:
                logger.warning(f"Error parsing event: {e}")
                continue
        
        # Sort events by start time
        events.sort(key=lambda x: x['start_datetime'])
        
        logger.info(f"Returning {len(events)} processed events")
        for event in events[:3]:  # Log first 3 events for debugging
            logger.info(f"Event: {event['summary']} at {event['start_date']} {event['start_time']}")
        
        return events
        
    except Exception as e:
        logger.error(f"Error fetching calendar from {ical_url} (normalized to {normalized_url}): {e}")
        return []

# --- Configuration Management ---
def load_config():
    """Load the main configuration from config.json."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading config file: {e}")
    # Default configuration
    return {
        "dashboard_duration": 10,
        "screensaver_config": [],
        "enable_mqtt": False,
        "mqtt_broker": "homeassistant.local",
        "mqtt_port": 1883,
        "mqtt_user": "",
        "mqtt_pass": "",
        "weekplans": [
            {"key": "plan1", "name": "Weekplan 1", "icon": "1"},
            {"key": "plan2", "name": "Weekplan 2", "icon": "2"}
        ],
        "calendar_urls": [],
        "calendar_assignments": {},
        "dashboard_language": "en-GB"
    }

def save_config(config_data):
    """Save the configuration to config.json."""
    tmp_path = f"{CONFIG_FILE}.tmp"
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
        os.replace(tmp_path, CONFIG_FILE)
    except OSError as e:
        if e.errno in (errno.EBUSY, errno.EXDEV):
            try:
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2)
                logger.warning("Atomic config replace failed; wrote directly to config.json.")
            except OSError as inner:
                logger.error(f"Error saving config file: {inner}")
        else:
            logger.error(f"Error saving config file: {e}")
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass

# Load initial configuration
config = load_config()

# --- Dynamic State (Last Updates) ---
def load_last_updates() -> Dict[str, Optional[datetime]]:
    """Load the last update timestamps for weekplans."""
    if os.path.exists(UPDATE_FILE):
        try:
            with open(UPDATE_FILE, 'r') as f:
                data = json.load(f)
            for key, value in data.items():
                try:
                    data[key] = datetime.fromisoformat(value) if value else None
                except (ValueError, TypeError):
                    data[key] = None
            return data
        except (json.JSONDecodeError, IOError):
            pass
    return {plan['key']: None for plan in config.get("weekplans", [])}

def save_last_updates(updates_data):
    """Save the last update timestamps."""
    data_to_save = {key: dt.isoformat() if dt else "" for key, dt in updates_data.items()}
    with open(UPDATE_FILE, 'w') as f:
        json.dump(data_to_save, f, indent=2)

last_updates = load_last_updates()

# --- Dashboard Mode State ---
def set_forced_dashboard_until(dt: Optional[datetime], view: str = "all"):
    """Set the forced dashboard mode until a specific time and view (all|plan1|plan2)."""
    if view not in ["all", "plan1", "plan2"]:
        view = "all"
    data = {"until": dt.isoformat() if dt else "", "view": view}
    with open(DASHBOARD_MODE_FILE, 'w') as f:
        json.dump(data, f)

def get_forced_dashboard_until() -> Optional[datetime]:
    """Get the time until which the dashboard is forced."""
    if not os.path.exists(DASHBOARD_MODE_FILE):
        return None
    try:
        with open(DASHBOARD_MODE_FILE, 'r') as f:
            data = json.load(f)
        until = data.get("until")
        return datetime.fromisoformat(until) if until else None
    except (json.JSONDecodeError, ValueError, IOError):
        return None

def get_forced_dashboard_view(default_view: str = "all") -> str:
    if not os.path.exists(DASHBOARD_MODE_FILE):
        return default_view
    try:
        with open(DASHBOARD_MODE_FILE, 'r') as f:
            data = json.load(f)
        view = data.get("view", default_view)
        return view if view in ["all", "plan1", "plan2"] else default_view
    except (json.JSONDecodeError, IOError):
        return default_view

app = Flask(__name__)

# Configure Flask for large file uploads (50MB max)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

@app.before_request
def refresh_config():
    """Reload config per request to avoid stale worker state."""
    global config
    if request.endpoint == 'static':
        return
    config = load_config()

# --- MQTT Setup (optional) ---
mqtt_client = None
if config.get("enable_mqtt"):
    try:
        import paho.mqtt.client as mqtt
        import socket
        logger.info("MQTT is enabled.")
        # Initialize MQTT client
        client_id = f"weekplans-{socket.gethostname()}-{uuid.uuid4().hex[:6]}"
        try:
            # Try paho-mqtt v2 style constructor first
            from paho.mqtt.client import Client, CallbackAPIVersion
            mqtt_client = Client(CallbackAPIVersion.VERSION1, client_id=client_id)
        except Exception:
            # Fallback to v1 style
            mqtt_client = mqtt.Client(client_id=client_id)

        # Set credentials if provided
        if config.get("mqtt_user"):
            mqtt_client.username_pw_set(config.get("mqtt_user", ""), config.get("mqtt_pass", ""))

        # Local state holder for connection
        _mqtt_connected_flag = {"val": False}

        def _publish_ha_discovery(client):
            """Publish Home Assistant MQTT Discovery messages for weekplan buttons."""
            try:
                import socket
                device_name = f"Weekplans {socket.gethostname()}"
                device_id = f"weekplans_{socket.gethostname()}".replace("-", "_")
                
                # Device info
                device_info = {
                    "identifiers": [device_id],
                    "name": device_name,
                    "manufacturer": "Weekplans App",
                    "model": "Weekplans Dashboard",
                    "sw_version": "1.0"
                }
                
                # Button configurations for each weekplan view
                buttons = [
                    {
                        "name": "Show All Weekplans",
                        "command_topic": "pi/weekplan/command",
                        "payload_press": "all",
                        "unique_id": f"{device_id}_show_all"
                    },
                    {
                        "name": "Show Julie's Weekplan",
                        "command_topic": "pi/weekplan/command", 
                        "payload_press": "plan1",
                        "unique_id": f"{device_id}_show_plan1"
                    },
                    {
                        "name": "Show Emil's Weekplan",
                        "command_topic": "pi/weekplan/command",
                        "payload_press": "plan2", 
                        "unique_id": f"{device_id}_show_plan2"
                    }
                ]
                
                # Publish discovery messages for each button
                for button in buttons:
                    discovery_topic = f"homeassistant/button/{button['unique_id']}/config"
                    discovery_payload = {
                        "name": button["name"],
                        "command_topic": button["command_topic"],
                        "payload_press": button["payload_press"],
                        "unique_id": button["unique_id"],
                        "device": device_info,
                        "icon": "mdi:calendar-week"
                    }
                    
                    client.publish(discovery_topic, json.dumps(discovery_payload), qos=1, retain=True)
                    logger.info(f"Published HA discovery for button: {button['name']}")
                
                logger.info("Home Assistant MQTT Discovery messages published successfully")
                
            except Exception as e:
                logger.error(f"Error publishing HA discovery messages: {e}")

        def _on_connect(client, userdata, flags, rc):
            try:
                logger.info(f"Connected to MQTT broker with result code {rc}")
                _mqtt_connected_flag["val"] = True
                # Subscribe to state topics (read-only)
                client.subscribe("pi/display/state")
                client.subscribe("pi/browser/current_url")
                client.subscribe("pi/brightness/state")
                # Subscribe to weekplan command topics
                client.subscribe("pi/weekplan/command")
                
                # Publish Home Assistant MQTT Discovery messages
                _publish_ha_discovery(client)
            except Exception as e:
                logger.error(f"Error in MQTT on_connect: {e}")

        def _on_disconnect(client, userdata, rc):
            _mqtt_connected_flag["val"] = False
            logger.warning(f"Disconnected from MQTT broker (rc={rc})")

        def _on_message(client, userdata, msg):
            try:
                payload = msg.payload.decode(errors="ignore") if isinstance(msg.payload, (bytes, bytearray)) else str(msg.payload)
                topic = msg.topic
                # Update in-memory state to reflect current values
                if topic in ["pi/display/state", "pi/browser/current_url", "pi/brightness/state"]:
                    mqtt_stats[topic] = payload
                    logger.debug(f"MQTT state updated: {topic} = {payload}")
                # Handle weekplan commands
                elif topic == "pi/weekplan/command":
                    logger.info(f"Received weekplan command: {payload}")
                    duration = config.get("dashboard_duration", 10)
                    view = payload.strip().lower()
                    if view not in ['all', 'plan1', 'plan2']:
                        view = 'all'
                    set_forced_dashboard_until(datetime.now() + timedelta(seconds=duration), view=view)
                    logger.info(f"Set dashboard mode: {view} for {duration} seconds")
            except Exception as e:
                logger.error(f"Error processing MQTT message: {e}")

        mqtt_client.on_connect = _on_connect
        mqtt_client.on_disconnect = _on_disconnect
        mqtt_client.on_message = _on_message

        # Connect and start background loop
        try:
            mqtt_client.connect(config.get("mqtt_broker", "localhost"), int(config.get("mqtt_port", 1883)))
            mqtt_client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
    except ImportError:
        logger.warning("paho-mqtt library not found. MQTT is disabled.")
        config["enable_mqtt"] = False

# Mock MQTT stats for demonstration if MQTT is disabled
mqtt_stats = {
    "pi/browser/current_url": "http://example.com",
    "pi/brightness/state": "0.75",
    "pi/display/state": "off"
}

# --- Routes ---
@app.route('/')
def root():
    """Renders the main dashboard page."""
    now = datetime.now()
    try:
        locale.setlocale(locale.LC_TIME, "en_GB.UTF-8")
    except locale.Error:
        locale.setlocale(locale.LC_TIME, "")

    date_str = now.strftime("%A %-d %B").capitalize()
    time_str = now.strftime("%H:%M:%S")
    
    plan_updates = []
    user_views = {}
    for plan in config.get("weekplans", []):
        key = plan['key']
        dt = last_updates.get(key)
        update_str = dt.strftime("%-d %B %Y, at %H:%M") if dt else "—"
        ts = int(dt.timestamp()) if dt else 0
        page1_url = url_for('static', filename=f'images/{key}-ukeplan.png') + f'?v={ts}'
        page2_path = os.path.join(STATIC_IMAGE_FOLDER, f"{key}-ukeplan-2.png")
        page2_url = url_for('static', filename=f'images/{key}-ukeplan-2.png') + f'?v={ts}' if os.path.exists(page2_path) else ""
        display_page = int(plan.get('display_page', 1))
        selected_img = page1_url if display_page != 2 or not page2_url else page2_url
        plan_updates.append({
            'key': key,
            'name': plan.get('name', key),
            'icon': plan.get('icon', ''),
            'img_url': selected_img,
            'last_update': update_str
        })
        user_views[key] = {
            'name': plan.get('name', key),
            'icon': plan.get('icon', ''),
            'img_page1_url': page1_url,
            'img_page2_url': page2_url
        }
        
    active_screensaver_images = [item["filename"] for item in config.get("screensaver_config", []) if item.get("active", True)]
    screensaver_image_url = ""
    if active_screensaver_images:
        chosen_image = random.choice(active_screensaver_images)
        screensaver_image_url = url_for('static', filename=f'screensaver/{chosen_image}')
        
    return render_template(
        "dashboard.html",
        date_str=date_str,
        time_str=time_str,
        weekplans=plan_updates,
        screensaver_image_url=screensaver_image_url,
        user_views=user_views
    )

@app.route("/mode")
def mode():
    """API endpoint to check if the dashboard should be displayed."""
    until = get_forced_dashboard_until()
    mode_active = until is not None and datetime.now() < until
    view = get_forced_dashboard_view("all") if mode_active else "all"
    return jsonify({
        "dashboard": mode_active,
        "view": view,
        "language": config.get("dashboard_language", "en-GB")
    })

@app.route("/screensaver_image")
def screensaver_image():
    """API endpoint to get a random screensaver image URL."""
    active_images = [item["filename"] for item in config.get("screensaver_config", []) if item.get("active", True)]
    if not active_images:
        return jsonify({"image_url": ""})
    
    chosen = random.choice(active_images)
    image_url = url_for('static', filename=f'screensaver/{chosen}')
    return jsonify({"image_url": image_url})

# --- API: Weekplans for React frontend ---
@app.route("/api/weekplans", methods=["GET"])
def api_weekplans():
    """Return list of weekplans with selected image (all view) and explicit page1/page2 URLs."""
    result = []
    for plan in config.get("weekplans", []):
        key = plan['key']
        dt = last_updates.get(key)
        ts = int(dt.timestamp()) if dt else 0
        page1_url = url_for('static', filename=f'images/{key}-ukeplan.png') + f'?v={ts}'
        img2_path = os.path.join(STATIC_IMAGE_FOLDER, f"{key}-ukeplan-2.png")
        page2_url = url_for('static', filename=f'images/{key}-ukeplan-2.png') + f'?v={ts}' if os.path.exists(img2_path) else ""
        display_page = int(plan.get('display_page', 1))
        img_url = page1_url if display_page != 2 or not page2_url else page2_url
        result.append({
            "key": key,
            "name": plan.get('name', key),
            "icon": plan.get('icon', ''),
            "last_update_iso": dt.isoformat() if dt else "",
            "img_url": img_url,
            "img_url2": page2_url,
            "page1_url": page1_url,
            "page2_url": page2_url
        })
    return jsonify(result)

@app.route("/api/calendar/events", methods=["GET"])
def api_calendar_events():
    """Return calendar events from all configured URLs for the next 2 weeks."""
    all_events = []
    calendar_urls = config.get("calendar_urls", [])
    
    logger.info(f"Processing {len(calendar_urls)} calendar URLs")
    
    for calendar_config in calendar_urls:
        url = calendar_config.get('url', '')
        name = calendar_config.get('name', 'Calendar')
        color = calendar_config.get('color', '#3788d8')  # Default blue color
        if url:
            logger.info(f"Processing calendar: {name}")
            # Admin panel should show next 2 weeks
            events = fetch_calendar_events(url, days_ahead=14)
            for event in events:
                event['calendar_name'] = name
                event['calendar_color'] = color
            all_events.extend(events)
    
    # Sort all events by start time
    all_events.sort(key=lambda x: x['start_datetime'])
    
    logger.info(f"Returning {len(all_events)} total events")
    return jsonify(all_events)

@app.route("/api/calendar/events_for/<plan_key>", methods=["GET"])
def api_calendar_events_for(plan_key: str):
    """Return calendar events assigned to a specific plan (user) for today + next 3 days."""
    assignments_map = config.get("calendar_assignments", {}) or {}
    assigned_ids = set(assignments_map.get(plan_key, []))
    all_events: List[Dict] = []
    if not assigned_ids:
        return jsonify([])

    calendars = config.get("calendar_urls", [])
    for calendar in calendars:
        cal_id = calendar.get('id')
        if cal_id in assigned_ids:
            url = calendar.get('url', '')
            name = calendar.get('name', 'Calendar')
            color = calendar.get('color', '#3788d8')
            if not url:
                continue
            events = fetch_calendar_events(url, days_ahead=3)  # today + next 3 days
            for event in events:
                event['calendar_name'] = name
                event['calendar_color'] = color
            all_events.extend(events)

    all_events.sort(key=lambda x: x['start_datetime'])
    return jsonify(all_events)

@app.route("/api/calendar/debug/<path:calendar_url>", methods=["GET"])
def api_calendar_debug(calendar_url):
    """Debug endpoint to test a specific calendar URL."""
    import urllib.parse
    decoded_url = urllib.parse.unquote(calendar_url)
    logger.info(f"Debug testing calendar URL: {decoded_url}")
    events = fetch_calendar_events(decoded_url)
    return jsonify({
        'url': decoded_url,
        'event_count': len(events),
        'events': events[:10]  # Return first 10 events for debugging
    })

@app.route("/admin", methods=["GET", "POST"])
def admin():
    """Renders the admin panel and handles all admin actions."""
    global config, last_updates, mqtt_stats

    if request.args.get('refresh_status') == 'true':
        return jsonify(system_stats=get_system_stats())

    current_tab = request.args.get('tab', 'ukeplan')

    if request.method == 'POST':
        # Always reload to avoid stale worker state during writes.
        config = load_config()
        action = request.form.get('action')
        current_tab = request.form.get('current_tab', 'ukeplan') 

        if action == 'upload_pdf':
            file = request.files.get('pdf_file')
            target = request.form.get('target', 'plan1')
            if file and file.filename and allowed_file(file.filename, ALLOWED_PDF_EXTENSIONS):
                filename = secure_filename(f"{target}.pdf")
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                try:
                    images = convert_from_path(filepath, first_page=1, last_page=2)
                    if images:
                        image_path1 = os.path.join(STATIC_IMAGE_FOLDER, f"{target}-ukeplan.png")
                        images[0].save(image_path1, 'PNG')
                        if len(images) > 1:
                            image_path2 = os.path.join(STATIC_IMAGE_FOLDER, f"{target}-ukeplan-2.png")
                            images[1].save(image_path2, 'PNG')
                        last_updates[target] = datetime.now()
                        save_last_updates(last_updates)
                except Exception as e:
                    logger.error(f"Error converting PDF: {e}")
            
        elif action == 'upload_screensaver_file':
            file = request.files.get('screensaver_file')
            if file and file.filename and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                filename = secure_filename(file.filename)
                if not any(d.get('filename') == filename for d in config["screensaver_config"]):
                    file.save(os.path.join(SCREENSAVER_FOLDER, filename))
                    config["screensaver_config"].append({"filename": filename, "active": True})
                    save_config(config)
            
        elif action == 'upload_screensaver_url':
            url = request.form.get('screensaver_url')
            if url:
                try:
                    parsed_url = urlparse(url)
                    if not all([parsed_url.scheme, parsed_url.netloc]):
                        raise ValueError("Invalid URL provided")
                    response = requests.get(url, stream=True, timeout=10)
                    response.raise_for_status()
                    content_type = response.headers.get('content-type', '').split(';')[0]
                    if not content_type.startswith('image/'):
                         raise ValueError(f"Invalid content type: {content_type}")
                    filename = secure_filename(os.path.basename(parsed_url.path) or f"downloaded_{uuid.uuid4().hex[:8]}.jpg")
                    if not allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS):
                        ext = content_type.split('/')[-1]
                        valid_ext = ext if ext in ['jpeg', 'jpg', 'png', 'gif', 'webp'] else 'jpg'
                        filename = f"{os.path.splitext(filename)[0]}.{valid_ext}"
                    if not any(d.get('filename') == filename for d in config["screensaver_config"]):
                        filepath = os.path.join(SCREENSAVER_FOLDER, filename)
                        with open(filepath, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        config["screensaver_config"].append({"filename": filename, "active": True})
                        save_config(config)
                except (requests.RequestException, ValueError) as e:
                    logger.error(f"Error downloading from URL {url}: {e}")
            
        elif action == 'delete_screensaver':
            filename = request.form.get('filename')
            if filename:
                safe_filename = secure_filename(filename)
                filepath = os.path.join(SCREENSAVER_FOLDER, safe_filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                config["screensaver_config"] = [item for item in config["screensaver_config"] if item['filename'] != safe_filename]
                save_config(config)
            
        elif action == 'update_screensaver_activation':
            active_images = request.form.getlist('active_images')
            for item in config["screensaver_config"]:
                item['active'] = item['filename'] in active_images
            save_config(config)
            
        elif action == 'show_week_plan':
            duration = config.get("dashboard_duration", 10)
            view = request.form.get('view', 'all')
            if view not in ['all', 'plan1', 'plan2']:
                view = 'all'
            set_forced_dashboard_until(datetime.now() + timedelta(seconds=duration), view=view)
            
        elif action == 'set_display_pages':
            # Save which page to show in "All" view per plan
            for plan in config.get('weekplans', []):
                key = plan['key']
                val = request.form.get(f'display_page_{key}', str(plan.get('display_page', 1)))
                try:
                    page_num = int(val)
                    plan['display_page'] = 2 if page_num == 2 else 1
                except ValueError:
                    plan['display_page'] = 1
            save_config(config)
            
        elif action == 'set_duration':
            config['dashboard_duration'] = int(request.form.get('dashboard_duration', 10))
            # Also allow saving language in this general form
            lang = request.form.get('dashboard_language')
            if lang in ['en-GB', 'nb-NO']:
                config['dashboard_language'] = lang
            save_config(config)

        elif action == 'set_weekplan_details':
            for plan in config.get('weekplans', []):
                plan['name'] = request.form.get(f"name_{plan['key']}", plan['name'])
                plan['icon'] = request.form.get(f"icon_{plan['key']}", plan['icon'])
            save_config(config)
        
        elif action == 'set_mqtt_config':
            config['enable_mqtt'] = 'enable_mqtt' in request.form
            config['mqtt_broker'] = request.form.get('mqtt_broker', 'homeassistant.local')
            config['mqtt_port'] = int(request.form.get('mqtt_port', 1883))
            config['mqtt_user'] = request.form.get('mqtt_user', '')
            config['mqtt_pass'] = request.form.get('mqtt_pass', '')
            save_config(config)
            
        elif action == 'set_calendar_assignments':
            # For each plan, read selected calendar IDs
            assignments: Dict[str, List[str]] = {}
            calendar_ids = {cal.get('id') for cal in config.get('calendar_urls', []) if cal.get('id')}
            for plan in config.get('weekplans', []):
                key = plan['key']
                selected = [cid for cid in request.form.getlist(f'assign_{key}') if cid in calendar_ids]
                assignments[key] = selected
            config['calendar_assignments'] = assignments
            logger.info(f"Saved calendar assignments for {len(assignments)} plans")
            save_config(config)

        elif action == 'add_calendar':
            calendar_name = request.form.get('calendar_name', '').strip()
            calendar_url = request.form.get('calendar_url', '').strip()
            calendar_color = request.form.get('calendar_color', '#3788d8').strip()  # Default blue color
            if calendar_name and calendar_url:
                if 'calendar_urls' not in config:
                    config['calendar_urls'] = []
                # Check if URL already exists
                if not any(cal.get('url') == calendar_url for cal in config['calendar_urls']):
                    config['calendar_urls'].append({
                        'name': calendar_name,
                        'url': calendar_url,
                        'color': calendar_color,
                        'id': str(uuid.uuid4())
                    })
                    save_config(config)
                    logger.info(f"Added calendar: {calendar_name} ({calendar_url})")
                else:
                    logger.info(f"Calendar already exists for URL: {calendar_url}")
                    
        elif action == 'remove_calendar':
            calendar_id = request.form.get('calendar_id')
            calendar_url = request.form.get('calendar_url', '').strip()
            if calendar_id or calendar_url:
                before_count = len(config.get('calendar_urls', []))
                def _keep_calendar(cal):
                    if calendar_id and cal.get('id') == calendar_id:
                        return False
                    if calendar_url and not cal.get('id') and cal.get('url') == calendar_url:
                        return False
                    return True
                config['calendar_urls'] = [cal for cal in config.get('calendar_urls', []) if _keep_calendar(cal)]
                after_count = len(config.get('calendar_urls', []))
                # Remove from assignments too (only applies to calendars with ids)
                if calendar_id:
                    assignments = config.get('calendar_assignments', {}) or {}
                    for key, assigned in assignments.items():
                        assignments[key] = [cid for cid in assigned if cid != calendar_id]
                    config['calendar_assignments'] = assignments
                save_config(config)
                logger.info(f"Removed calendar (id={calendar_id or 'n/a'}, url={calendar_url or 'n/a'}) ({before_count} -> {after_count})")
            else:
                logger.warning("remove_calendar called without calendar_id or calendar_url")
            
        elif action == 'set_brightness':
            brightness_pct = request.form.get('brightness', '75')
            brightness_val = float(brightness_pct) / 100.0
            logger.info(f"COMMAND: Set Brightness to {brightness_val}")
            # Publish command if MQTT is available; do not mutate state directly
            try:
                if mqtt_client is not None and mqtt_client.is_connected():
                    mqtt_client.publish('pi/brightness/command', str(brightness_val), qos=0, retain=False)
                else:
                    logger.warning("MQTT not connected; brightness command not published")
            except Exception as e:
                logger.error(f"Error publishing brightness command: {e}")
        
        elif action == 'browser_url':
            url = request.form.get('url')
            if url:
                logger.info(f"COMMAND: Change URL to {url}")
                try:
                    if mqtt_client is not None and mqtt_client.is_connected():
                        mqtt_client.publish('pi/browser/command/url', url, qos=0, retain=False)
                    else:
                        logger.warning("MQTT not connected; browser URL command not published")
                except Exception as e:
                    logger.error(f"Error publishing browser URL command: {e}")

        elif action == 'browser_refresh':
            logger.info("COMMAND: Refresh Browser")
            try:
                if mqtt_client is not None and mqtt_client.is_connected():
                    mqtt_client.publish('pi/browser/command/refresh', '1', qos=0, retain=False)
                else:
                    logger.warning("MQTT not connected; browser refresh command not published")
            except Exception as e:
                logger.error(f"Error publishing browser refresh command: {e}")

        elif action in ['display_on', 'display_off', 'system_restart']:
            logger.info(f"Received command: {action}")
            try:
                if mqtt_client is None or not mqtt_client.is_connected():
                    logger.warning("MQTT not connected; command not published")
                else:
                    if action == 'display_on':
                        mqtt_client.publish('pi/display/command', 'on', qos=0, retain=False)
                    elif action == 'display_off':
                        mqtt_client.publish('pi/display/command', 'off', qos=0, retain=False)
                    elif action == 'system_restart':
                        mqtt_client.publish('pi/system/command/restart', '1', qos=0, retain=False)
            except Exception as e:
                logger.error(f"Error publishing command for {action}: {e}")

        return redirect(url_for('admin', tab=current_tab))

    system_stats = get_system_stats()
    mqtt_connected = config.get('enable_mqtt') and mqtt_client is not None and mqtt_client.is_connected()

    return render_template(
        'admin.html',
        config=config,
        last_updates=last_updates,
        system_stats=system_stats,
        mqtt_stats=mqtt_stats,
        mqtt_connected=mqtt_connected,
        current_tab=current_tab
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

