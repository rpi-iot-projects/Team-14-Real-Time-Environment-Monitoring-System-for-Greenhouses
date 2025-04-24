"""
Greenhouse Monitoring System - Client Script

This script runs on a PC to receive encrypted environmental data from a Raspberry Pi.
It uses the PyQt5 framework to display real-time temperature, humidity, light intensity, and CO2 concentration
in a graphical user interface. The script decrypts the data using AES-CBC and verifies secure communication via TLS,
ensuring reliable and secure greenhouse monitoring.
"""


import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
import paho.mqtt.client as mqtt
import os
import ssl
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

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

# CA certificate availability check
print(f"Exists: {os.path.exists(CA_CERT)}")
print(f"Readable: {os.access(CA_CERT, os.R_OK)}")


def connect_mqtt(client, broker, port, max_attempts=5):
    attempt = 0
    while attempt < max_attempts:
        try:
            print(f"Attempting to connect to MQTT broker ({broker}:{port}), attempt {attempt + 1}...")
            client.connect(broker, port, 60)
            print("Connected successfully")
            return True
        except Exception as e:
            attempt += 1
            wait_time = min(2 ** attempt, 30)  # exponential backoff, max 30 seconds
            print(f"Connection failed: {e}, retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    print(f"Failed to connect after {max_attempts} attempts, stopping attempt")
    return False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Greenhouse Monitoring System")
        self.setGeometry(100, 100, 400, 300)

        # initialize UI widgets
        self.temp_label = QLabel("Temperature: -- °C")
        self.humidity_label = QLabel("Humidity: -- %")
        self.light_label = QLabel("Light: -- lx")
        self.co2_label = QLabel("CO2: -- ppm")

        # set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.temp_label)
        layout.addWidget(self.humidity_label)
        layout.addWidget(self.light_label)
        layout.addWidget(self.co2_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # initialize MQTT client
        self.client = mqtt.Client(protocol=mqtt.MQTTv311)

        # TLS
        self.client.tls_set(ca_certs=CA_CERT)
        self.client.tls_insecure_set(True)  # ignore certificate verification, remove after testing (self-signed certificate may fail verification!)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        if not connect_mqtt(self.client, BROKER, PORT):
            print("Failed to connect to MQTT broker, closing program")
            sys.exit(1)

        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
            client.subscribe(TOPIC)
        else:
            print(f"Connection failed with code {rc}, reconnecting...")
            if connect_mqtt(self.client, BROKER, PORT):
                print("Reconnected successfully")
                client.subscribe(TOPIC)

    def on_message(self, client, userdata, msg):
        try:
            encrypted_data = msg.payload
            decryptor = cipher.decryptor()
            decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()    # AES Decryption
            decrypted_data = decrypted_data.rstrip(b'\0')
            decrypted_data = decrypted_data.decode('utf-8')                             # strip padding

            data = eval(decrypted_data)
            self.temp_label.setText(f"Temperature: {data['temperature']} °C")
            self.humidity_label.setText(f"Humidity: {data['humidity']} %")
            self.light_label.setText(f"Light: {data['light']} lx")
            self.co2_label.setText(f"CO2: {data['co2']} ppm")
        except Exception as e:
            print(f"Message processing failed: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("Stopped by user")
        window.client.loop_stop()
        window.client.disconnect()
