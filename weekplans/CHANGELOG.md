# Changelog

## 2026.02.28b

- Fix ingress: add ingress_port 80 and ingress_entry /admin so Open Web UI button works
- Fix port mapping: container 80 -> host 8080 (was incorrectly 8080->8080)
- Add panel icon and title for Apps view

## 1.0.0

- Initial Home Assistant app release
- Same image as standalone Docker
- MQTT configuration via app options (optional)
- Reads options from Home Assistant options.json
