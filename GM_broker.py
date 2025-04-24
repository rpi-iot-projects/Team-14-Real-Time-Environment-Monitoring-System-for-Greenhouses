"""
Greenhouse Monitoring System - Broker Script

This script runs on a Raspberry Pi to collect environmental data from DHT11 (temperature/humidity),
BH1750 (light intensity), and MH-Z19 (CO2) sensors. It encrypts the data using AES-CBC and
publishes it to an MQTT broker over a secure TLS connection for real-time greenhouse monitoring.

"""

"""
TLS Certificate Generation Instructions:
To configure TLS, execute the following commands on the Raspberry Pi:

cd /etc/mosquitto/certs

# Generate CA key and certificate
sudo openssl genrsa -out ca.key 2048
sudo openssl req -new -x509 -days 3650 -key ca.key -out ca.crt -subj "/CN=xxx.xxx.x.xxx" # Use your Raspberry Pi IP

# Generate server key and certificate
sudo openssl genrsa -out server.key 2048
sudo openssl req -new -key server.key -out server.csr -subj "/CN=1xxx.xxx.x.xxx"  # Use your Raspberry Pi IP
sudo openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 3650

# Set permissions
sudo chown mosquitto:mosquitto /etc/mosquitto/certs/ca.crt
sudo chown mosquitto:mosquitto /etc/mosquitto/certs/server.crt
sudo chown mosquitto:mosquitto /etc/mosquitto/certs/server.key

"""

import time
import Adafruit_DHT
import smbus2
import serial
import paho.mqtt.client as mqtt
import ssl
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

# sensor settings
DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 4                                                                 # replace with actual pin number
BH1750_ADDR = 0x23                                                          # default I2C address
BUS = smbus2.SMBus(1)
SERIAL_PORT = serial.Serial('/dev/ttyS0', 9600, timeout=1)    # CO2 sensor serial port

# MQTT settings
BROKER = "xxx.xxx.x.xxx"        # replace with actual pi ip
PORT = 8883                     # replace with actual port number
TOPIC = "greenhouse/sensors"    # replace with actual OPIC name

# TLS setting
CA_CERT = "C:/xxxx/xx/ca.crt"   # replace with actual CA certificate path

# AES setting
key = b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'   # replace with actual 32-byte key
iv = b'xxxxxxxxxxxxxxxx'                    # replace with actual 16-byte IV
cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())


# BH1750
def read_light():
    try:
        BUS.write_byte(BH1750_ADDR, 0x10)
        time.sleep(0.18)
        data = BUS.read_i2c_block_data(BH1750_ADDR, 0x10, 2)
        return round(((data[0] << 8) + data[1]) / 1.2, 2)
    except:
        return None

# MH-Z19
def read_co2():
    SERIAL_PORT.write(bytearray([0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79]))
    response = SERIAL_PORT.read(9)
    if len(response) == 9 and response[0] == 0xFF and response[1] == 0x86:
        co2 = (response[2] << 8) + response[3]
        return co2
    return None


def connect_mqtt(client, broker, port, max_attempts=5):
    attempt = 0
    max_attempts = int(max_attempts)
    while attempt < max_attempts:
        try:
            print(f"Attempting to connect to MQTT broker ({broker}:{port}), attempt {attempt + 1}...")
            client.connect(broker, port, 60)
            print("Connected successfully")
            return True
        except Exception as e:
            attempt += 1
            wait_time = min(2 ** attempt, 30)  # exponential backoff
            print(f"Connection failed: {e}, retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    print(f"Failed to connect after {max_attempts} attempts, giving up")
    return False


# initialize MQTT client
client = mqtt.Client(protocol=mqtt.MQTTv311)

# TLS
client.tls_set(ca_certs=CA_CERT)
client.tls_insecure_set(True) # Ignore certificate verification, remove after testing (Self-signed certificate may fail verification!)


if not connect_mqtt(client, BROKER, PORT):
    print("Failed to connect to MQTT broker, exiting program")
    SERIAL_PORT.close()
    exit(1)

try:
    while True:
        # read sensor data
        humidity, temp = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)   #DHT11
        light = read_light()
        co2 = read_co2()

        data = {
            "temperature": temp if temp is not None else "N/A",
            "humidity": humidity if humidity is not None else "N/A",
            "light": light if light is not None else "N/A",
            "co2": co2 if co2 is not None else "N/A"
        }

        payload = str(data).encode()
        encrypted_payload = cipher.encrypt(payload.ljust(16 * ((len(payload) // 16) + 1), b'\0'))  # padding

        # publish
        try:
            client.publish(TOPIC, encrypted_payload)
            print(f"Published data: {payload}")
        except Exception as e:
            print(f"Publish failed: {e}, reconnecting...")
            if connect_mqtt(client, BROKER, PORT):
                print("Reconnected successfully, republishing")
                client.publish(TOPIC, encrypted_payload)  # republish after reconnect
            else:
                print("Reconnection failed, skipping this publish")

        time.sleep(5)  # update every 5 seconds

except KeyboardInterrupt:
    print("Stopped by user")
except Exception as e:
    print(f"Error occurred: {e}")
finally:
    SERIAL_PORT.close()
    client.disconnect()
    print("Program terminated")