#!/usr/bin/env python3
import json
import datetime
import traceback
from urllib.parse import urlparse
import chevron
import requests
import click
import paho.mqtt.client as mqtt

# logging.basicConfig(level=logging.DEBUG)

class Error(Exception):
   """Base class for other exceptions"""
   pass

class STAError(Exception):
   """SensorthingsAPI Error handling"""
   pass

STA_BASE_URL = ""
STA_MQTT_PORT = -1

def get_sta_entity(path):
    try:
        print(f"GET {path}")
        url = f"{BASE_URL}/{path}"
        response = requests.get(url, headers={"Accept":"application/json"})
        if response.status_code != 200:
            status_code = response.status_code
            body = response.text
            raise STAError(f"unexpected return code STA GET request, status_code: {status_code}, url: {url}, response_body: {body}")
    except (requests.exceptions.RequestException, STAError) as exc:  # This is the correct syntax
        print(exc)
    return response.json()

def get_thing_with_location_json(obs_json):
        input_values = {}
        thing = {}
        properties = []
        location = {}
        app_id = obs_json["app_id"]
        dev_id = obs_json["dev_id"]
        thing["name"] = dev_id
        thing["description"] = f"sensemakersams app_id: {app_id}, dev_id: {dev_id}"
        properties.append({"key":"id", "value": dev_id})
        properties.append({"key":"app_id", "value":app_id, "last": True})
        location["name"] = dev_id
        location["description"] = f"sensemakersams app_id: {app_id}, dev_id: {dev_id}"
        location["x"] = obs_json["payload_fields"]["Lon"]
        location["y"] = obs_json["payload_fields"]["Lat"]
        input_values["thing"] = thing
        input_values["thing"]["properties"] = properties
        input_values["location"] = location
        with open("sta_templates/thing.json.template") as template_file:
            return chevron.render(template_file, input_values)

def get_observed_property_json(name, description, definition):
    input_values = {}
    input_values["name"] = name
    input_values["description"] = description
    input_values["definition"] = definition
    with open("sta_templates/observed_property.json.template") as template_file:
        return chevron.render(template_file, input_values)

def get_sensor_json(obs_json):
    input_values = {}
    app_id = obs_json["app_id"]
    dev_id = obs_json["dev_id"]
    input_values["name"] = dev_id
    input_values["description"] = f"sensemakersams app_id: {app_id}, dev_id: {dev_id}"
    input_values["metadata"] = "missing"
    with open("sta_templates/sensor.json.template") as template_file:
        return chevron.render(template_file, input_values)

def get_datastream_name(thing_id, observed_property_id, sensor_id):
    return f"ds_{thing_id}_{observed_property_id}_{sensor_id}"

def get_datastream_json(obs_json, thing_id, observed_property_id, sensor_id, property_of_interest):
    input_values = {}
    uom = {}
    input_values["name"] = get_datastream_name(thing_id, observed_property_id, sensor_id)
    input_values["description"] = f"datastream of thing:{thing_id}, observed_property:{observed_property_id}, sensor:{sensor_id}"
    input_values["thing_id"] = thing_id
    input_values["sensor_id"] = sensor_id
    input_values["observed_property_id"] = observed_property_id
    if property_of_interest == "waterTemperature":
        uom["symbol"] = "degree Celsius"
        uom["name"] = "°C"
        uom["definition"] = "http://unitsofmeasure.org/ucum.html#para-30"
    input_values["uom"] = uom
    with open("sta_templates/datastream.json.template") as template_file:
        return chevron.render(template_file, input_values)

def get_observation_json(obs_json, datastream_id, property_of_interest):
    input_values = {}
    input_values["timestamp"] = datetime.datetime.utcfromtimestamp(obs_json["payload_fields"]["timestamp"]).strftime('%Y-%m-%dT%H:%M:%SZ')
    input_values["value"] = obs_json["payload_fields"][property_of_interest]
    input_values["datastream_id"] = datastream_id
    with open("sta_templates/observation.json.template") as template_file:
        return chevron.render(template_file, input_values)


def create_sta_entity(path, payload):
    print(f"POST {path}")
    url = f"{BASE_URL}/{path}"
    try:
        response = requests.post(url, data=payload, headers={"Accept": "application/json", "Content-Type": "application/json"})
        if response.status_code != 201:
            status_code = response.status_code
            body = response.text
            raise STAError(f"unexpected return code STA request, status_code: {status_code}, url: {url}, response_body: {body}")
        if not "location" in response.headers:
            raise STAError(f"missing location key in return headers, url: {url}")
    except (requests.exceptions.RequestException, STAError) as exc:  # This is the correct syntax
        print(exc)

    data = response.json()
    return data["@iot.id"]

def get_thing_by_id(id):
    things = get_sta_entity(f"Things?$filter=properties/id%20eq%20'{id}'")
    if things["value"]:
        return things["value"][0]
    return {}

def get_ds_from_thing_by_name(thing_id, ds_name):
    datastreams = get_sta_entity(f"Things?$filter=id eq {thing_id}&$expand=Datastreams($filter=name eq '{ds_name}')&$select=Datastreams")
    if datastreams["value"] and "Datastreams" in datastreams["value"][0] and datastreams["value"][0]["Datastreams"]:
        return datastreams["value"][0]["Datastreams"][0]
    return {}

def get_sta_entity_by_name(entity_name, name):
    observed_properties = get_sta_entity(f"{entity_name}?$filter=name eq '{name}'")
    if observed_properties["value"]:
        return observed_properties["value"][0]
    return {}

def init_sensor_with_property(obs_json, property_of_interest):
    # thing
    try:
        dev_id = obs_json["dev_id"]
        thing = get_thing_by_id(dev_id)
        if not thing:
            thing_json = get_thing_with_location_json(obs_json)
            thing_id = create_sta_entity("Things", thing_json)
        else:
            thing_id = thing["@iot.id"]
        # observed_property
        obs_prop = get_sta_entity_by_name("ObservedProperties", property_of_interest)
        if not obs_prop:
            observed_property_json = get_observed_property_json(property_of_interest, "water temperature in degrees Celsius", "http://dbpedia.org/page/Temperature")
            observed_property_id = create_sta_entity("ObservedProperties", observed_property_json)
        else:
            observed_property_id = obs_prop["@iot.id"]
        # sensor
        sensor = get_sta_entity_by_name("Sensors", dev_id)
        if not sensor:
            sensor_json = get_sensor_json(obs_json)
            sensor_id = create_sta_entity("Sensors", sensor_json)
        else:
            sensor_id = sensor["@iot.id"]
        # ds
        ds_name = get_datastream_name(thing_id, observed_property_id, sensor_id)
        datastream = get_ds_from_thing_by_name(thing_id, ds_name)
        if not datastream:
            ds_json = get_datastream_json(obs_json, thing_id, observed_property_id, sensor_id, property_of_interest)
            ds_id = create_sta_entity("Datastreams", ds_json)
        else:
            ds_id = datastream["@iot.id"]
        return ds_id
    except Exception as e:
        traceback.print_tb(e.__traceback__)

def create_sta_observation(obs_json, ds_id, property_of_interest):
    observation_json = get_observation_json(obs_json, ds_id, property_of_interest)
    obs_id = create_sta_entity("Observations", observation_json)
    return obs_id

class ClientWrapper(mqtt.Client):
    topic = ""
    # contains kvp of device_id:stream_id
    devices = {}
    blacklist = []

    def __init__(self, topic, property_of_interest):
        mqtt.Client.__init__(self)
        self.topic = topic
        self.property_of_interest = property_of_interest

    def add_device(self, key, value):
        self.devices[key] = value

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        payload_json = json.loads(msg.payload)
        dev_id = payload_json["dev_id"]
        if dev_id in client.blacklist:
            return
        if not "Lat" in payload_json["payload_fields"] or not "Lon" in payload_json["payload_fields"]:
            client.blacklist.append(dev_id)
            return
        if not dev_id in client.devices.keys():
            ds_id = init_sensor_with_property(payload_json, client.property_of_interest)
            create_sta_observation(payload_json, ds_id, client.property_of_interest)
            client.add_device(dev_id, ds_id)
        else:
            create_sta_observation(payload_json, client.devices[dev_id], client.property_of_interest)

    def create_sta_observation_mqtt(payload_json, datastream_id):
        parsed_url = urlparse(STA_BASE_URL)
        host = parsed_url.netloc.split(":")[0]
        client1 = mqtt.Client("control1")
        # client1.on_publish = on_publish
        client1.connect(host, STA_MQTT_PORT)
        client1.publish(f"GOST/Datastreams({datastream_id})/Observations", payload_json)

@click.command()
@click.argument('sta_base_url')
@click.argument('mqtt_host')
@click.argument('mqtt_port', type=int)
@click.argument('mqtt_topic')
@click.option('-u', '--mqtt_user')
@click.option('-p', '--mqtt_password')
@click.option('-s', '--sta_mqtt_port')
def convert_mqtt2sta_command(sta_base_url, mqtt_host, mqtt_port, mqtt_topic, mqtt_user, mqtt_password, sta_mqtt_port):
    print(sta_base_url, mqtt_host, mqtt_port, mqtt_topic, mqtt_user, mqtt_password)
    STA_BASE_URL = sta_base_url
    STA_MQTT_PORT = sta_mqtt_port
    property_of_interest = "waterTemperature"
    client = ClientWrapper(mqtt_topic, property_of_interest)
    client.connect(mqtt_host, mqtt_port, 60)
    if mqtt_user:
        client.username_pw_set(mqtt_user, password=mqtt_password)
    client.loop_forever()

if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    convert_mqtt2sta_command()
