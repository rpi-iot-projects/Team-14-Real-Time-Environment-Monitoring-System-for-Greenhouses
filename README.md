# Real-Time Environmental Monitoring System for Greenhouses

A system for real-time greenhouse condition monitoring with secure data transmission using TLS and AES encryption.

## Table of Contents

- [Overview](#overview)  
- [Hardware Components](#hardware-components)  
- [Software and Dependencies](#software-and-dependencies)  
- [Usage](#usage)  
- [Results and Demonstration](#results-and-demonstration)

## Overview

This project develops a real-time environmental monitoring system to optimize greenhouse conditions for crop growth. It addresses the need for precise control of temperature, humidity, light intensity, and CO2 levels by integrating sensor data collection, secure data transmission, and real-time visualization. Key features include:

- Environmental data monitoring using DHT11, BH1750, and MH-Z19 sensors.
- Secure data transmission via MQTT with TLS and AES-CBC encryption.
- PyQt5-based GUI for displaying data on a PC.
- Reliable operation validated through live demonstration and Wireshark analysis.

The system enhances greenhouse management by enabling management to adjust conditions dynamically, improving crop yields and resource efficiency.

## Hardware Components

- **Raspberry Pi**: Central control unit for sensor interfacing and data transmission.
- **DHT11 Sensor**: Measures temperature and humidity, connected via GPIO4.
- **BH1750 Sensor**: Measures light intensity in lux, connected via I2C.
- **MH-Z19 Sensor**: Measures CO2 concentration, connected via UART.

**Wiring Configuration**:



## Software and Dependencies

- **Programming Language**: Python
- **Libraries**:
  - `Adafruit_DHT`: For DHT11 sensor data collection.
  - `smbus2`: For BH1750 I2C communication.
  - `serial`: For MH-Z19 UART communication.
  - `paho-mqtt`: For MQTT client functionality.
  - `cryptography`: For AES-CBC encryption.
  - `PyQt5`: For GUI development.
- **Tools**:
  - Mosquitto: MQTT broker for communication.
  - Wireshark: For analyzing network traffic and verifying TLS encryption.
- **Scripts**:
  - `GM_Broker.py`: Runs on Raspberry Pi to collect, encrypt, and publish sensor data.
  - `GM_Client.py`: Runs on PC to receive, decrypt, and display data via GUI.

## Usage

1. **Setup Hardware**:
   - Connect DHT11, BH1750, and MH-Z19 sensors to the Raspberry Pi as per the wiring configuration.
   - Ensure the Raspberry Pi is connected to a Wi-Fi network.

2. **Configure TLS Certificates**:
   - Generate CA and server certificates using self-signed methods (see `GM_Broker.py` comments for commands) or from a public Certificate Authority .
   - Place `ca.crt`, `server.crt`, and `server.key` in `/etc/mosquitto/certs` on the Raspberry Pi.
   - Copy `ca.crt` to the PC for client authentication.

3. **Install Dependencies**:
   - On PC and Raspberry Pi: Install required libraries.
   - Install and configure Mosquitto MQTT broker on the Raspberry Pi.

4. **Run the System**:
   - Update `GM_Broker.py` and `GM_Client.py` with the correct broker IP, port, topic, CA certificate path, AES key, and IV.
   - Install and configure Mosquitto MQTT broker on the Raspberry Pi.
   - Run the broker script on the Raspberry Pi and Run the client script on the PC to launch the GUI.

4. **Monitor and Adjust**:
   - Use the GUI to monitor temperature (°C), humidity (%), light intensity (lx), and CO2 (ppm).
   - Adjust greenhouse conditions (e.g., ventilation, lighting) based on displayed data.


## Results and Demonstration

### Test Setup
The system was tested with a Raspberry Pi, sensors, and a PC over a local network. Data was transmitted every 5 seconds using MQTT with TLS and AES-CBC encryption.

### Performance
The GUI accurately displayed real-time data, with no errors during a one-hour live demonstration.

### Security
Wireshark captures confirmed successful TLSv1.2 handshakes and encrypted MQTT messages, ensuring secure communication.

### Reproducibility
The system is reproducible with the provided scripts, hardware, and setup instructions. Ensure correct certificate paths and AES keys for successful operation.


---

This system provides a reliable, secure, and user-friendly solution for greenhouse monitoring, with potential for future integration with autonomous control systems.

