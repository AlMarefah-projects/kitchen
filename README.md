# Kitchen Safety Violation System
Advanced kitchen safety monitoring system comprehensive violation detection.

## Manual Installation

### Prerequisites Setup
```bash
# Install system dependencies
sudo apt update
sudo apt install cmake python3-dev python3-pip python3-venv

# Setup MQTT broker (if not already installed)
sudo apt-add-repository ppa:mosquitto-dev/mosquitto-ppa
sudo apt install mosquitto mosquitto-clients
sudo tee -a /etc/mosquitto/mosquitto.conf << EOF
listener 1883
protocol mqtt

listener 9001
protocol websockets

allow_anonymous true
EOF
sudo systemctl restart mosquitto
sudo systemctl enable mosquitto
```

### Application Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install requirements
pip install -U pip
pip install -r requirements.txt
```

### Configuration
```bash
# Interactive configuration (recommended)
python configure.py

# Or manually edit config.json
# Set local_video: true and local_video_source for local testing
# Configure RTSP streams for live camera feeds
```

### Running the Application
```bash
# Activate virtual environment
source venv/bin/activate

# Run with configuration file
python kitchen_safety.py config.json
```

## Configuration Options

### Stream Configuration
- **Demo Mode**: Uses local video files for testing
- **Live Mode**: Connects to RTSP camera streams
- **Multi-Stream**: Monitor multiple kitchen areas simultaneously

### Detection Parameters
- **IOU Threshold**: Intersection over Union threshold for detection filtering
- **Inference Interval**: Time between detection runs (seconds)
- **Cooldown Period**: Minimum time between violation reports (seconds)

### Integration Settings
- **Data Send URL**: Endpoint for violation reports
- **Heartbeat URL**: System health monitoring endpoint
- **MQTT Settings**: Real-time alert configuration

## Background Service Management





```bash
# Install as system service
sudo cp kitchen-system.service /etc/systemd/system/hajj-systems.service
sudo systemctl daemon-reload
sudo systemctl enable hajj-systems.service
sudo systemctl start hajj-systems.service

sudo systemctl status hajj-systems.service
```



## Project Structure
```
yolo11-kitchen-rknn-python/
├── kitchen_safety.py          # Main application script
├── config.json               # Configuration file
├── requirements.txt          # Python dependencies
├── kitchen-safety.service   # Systemd service file
├── models/                  # RKNN model files
│   ├── kitchen-detection-model_rknn_model
│   └── person-april21-yolo11n_rknn_model
├── demo/                    # Demo videos and test files
├── libraries/               # Supporting libraries
└── uploader_cached_files/   # Temporary upload cache
```

## Model Information
- **Kitchen Detection Model**: Specialized for kitchen safety violations
- **Person Detection Model**: YOLO11n optimized for person detection
- **Target Platform**: RK3588 (Rockchip Neural Processing Unit)
- **Format**: RKNN optimized models for edge inference

## API Integration
The system integrates with external APIs for comprehensive monitoring:
- **Violation Reporting**: Automated incident reporting
- **Health Monitoring**: System heartbeat and status
- **Authentication**: Secure API communication with secret keys

## Troubleshooting

### Common Issues
1. **RKNN Model Loading**: Ensure models are in the correct format and path
2. **MQTT Connection**: Verify mosquitto service is running
3. **Camera Access**: Check RTSP URLs and network connectivity
4. **Permission Issues**: Ensure proper file permissions for service files

### Debug Mode
Enable detailed logging by setting `logging_level: "debug"` in config.json

### Log Files
- **Application Logs**: Check console output or journal logs for services
- **System Logs**: Use `journalctl` for systemd service debugging

## Development
For development and testing:
```bash
# Test with demo video
python kitchen_safety.py config.json

# Monitor in debug mode
# Edit config.json and set: "logging_level": "debug", "show": true

```
