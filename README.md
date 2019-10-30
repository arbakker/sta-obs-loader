# README

CLI application to load sensor data from `mqtt.sensemakersams.org` MQTT stream into SensorThingsAPI server, such as [GOST](https://github.com/gost/server) or [FROST-Server](https://github.com/FraunhoferIOSB/FROST-Server) (only tested against GOST).

See the file [raw_observation.md](./raw_observation.md) for the input data format sta-obs-loader is capable of parsing.

## Dependencies

Requires Python version `>=3.6.8`.

Install dependencies with:

```bash
pip3 install -r requirements.txt
```

## Usage

Usage CLI:

```bash
./script.py --help
Usage: script.py [OPTIONS] STA_BASE_URL MQQT_HOST MQTT_PORT MQTT_OPIC

Options:
  -u, --mqtt_user TEXT
  -p, --mqtt_password TEXT
  --help                    Show this message and exit.
```

For example (credentials are obfuscated):

```
python3 script.py  sub mqtt.sensemakersams.org 9998 pipeline/mijnomgeving/# -u ***** -p *****
```

## Debug configuration in VS Code

Add the following configuration to `launch.json`:

```json
 {
    "name": "Launch ./script.py",
    "type": "python",
    "request": "launch",
    "program": "${workspaceFolder}/script.py",
    "console": "integratedTerminal",
    "args":[
        "http://localhost:32788/v1.0", "mqtt.sensemakersams.org", "9998", "pipeline/mijnomgeving/#", "-u", "public", "-p", "public1234"
    ]
}
```
