# WORKFLOW 

Raw observation from MQTT sensemakersams service:
```json
{
    "app_id": "mijnomgeving",
    "dev_id": "357518080166580",
    "payload_fields": {
        "imei": 357518080166580,
        "timestamp": 1572364002,
        "batteryVoltage": 4.15,
        "boardTemperature": 18,
        "waterEC": 927,
        "waterTemperature": 13.86,
        "Lat": 52.3602022,
        "Lon": 4.8153333,
        "altitude": 36,
        "speed": 0,
        "course": 1,
        "SatInFix": 5,
        "FixAge": 37,
        "TimeActive": 82847,
        "lastResetCause": 32
    },
    "tag_fields": {
        "name": "EC 224"
    }
}
```


# FIRST OBS:

CREATE THING (WITH LOCATION): 1


```json
{
    "name": "lantern",
    "description": "camping lantern",
    "properties": {
        "property1": "it’s waterproof",
        "property2": "it glows in the dark",
        "property3": "it repels insects"
    },
    "Locations": [
        {
            "name": "why o why does a location need a name....",
            "description": "my backyard",
            "encodingType": "application/vnd.geo+json",
            "location": {
                "type": "Point",
                "coordinates": [-117.123,
                54.123]
            }
        }
    ]
}
```

CREATE OBSERVED PROPERTY: *

```json
{
    "name":"name",
    "description": "http://schema.org/description",
    "definition": "Calibration date:  Jan 1, 2014"
}
```

CREATE SENSOR: 1 for each thing

```json
{   
    "name": "My Sensor",
    "description": "SensorUp Tempomatic 2000",
    "encodingType": "application/pdf",
    "metadata": "Calibration date:  Jan 1, 2014"
}
```


CREATE DATASTREAM:

```json
{
    "name": "DS2",
    "unitOfMeasurement": {
        "symbol": "%",
        "name": "Percentage",
        "definition": "http://www.qudt.org/qudt/owl/1.0.0/unit/Instances.html"
    },
  "observationType":"http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
  "description": "Temperature measurement",
  "observedArea": { "type": "Polygon",
    "coordinates": [
      [ [100.0, 0.0], [101.0, 0.0], [101.0, 1.0], [100.0, 1.0], [100.0, 0.0] ]
      ]
   },
  "Thing": {"@iot.id": "1"},
  "ObservedProperty": {"@iot.id": "1"},
  "Sensor": {"@iot.id": "1"}
}
```

    CREATE OBSERVATION: 1

    ```json
    {
    "phenomenonTime": "2015-04-13T00:00:00+02:00",
    "result" : 38,
    "Datastream":{"@iot.id":"2"}
    }
    ```

# any other observation

