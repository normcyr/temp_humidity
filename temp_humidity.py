#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to listen to the serial port where an Arduino recorded the temperature
and relative humidity from a DHT22 module.

The data is printed to the standard output, saved to a CSV file and to InfluxDB.

Requires a running InfluxDB instance.
Vizualisation can be done with Grafana.
"""

import csv
import time

import serial
from influxdb import InfluxDBClient

__author__ = "Normand Cyr"
__copyright__ = "Copyright 2020"
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Normand Cyr"
__email__ = "normand.cyr@umontreal.ca"
__status__ = "Development"


def record_data(serial_data, output_csv_file, db_name):

    serial_bytes = serial_data.readline()
    decoded_bytes = serial_bytes.decode("utf-8")
    humidity = decoded_bytes.split(",", 1)[0].replace("\r", "").replace("\n", "")
    temperature = decoded_bytes.split(",", 1)[1].replace("\r", "").replace("\n", "")

    print_stdout(temperature, humidity)
    save_to_csv(output_csv_file, temperature, humidity)
    save_to_db(db_name, temperature, humidity)


def print_stdout(temperature, humidity):

    print("temperature: {}°C, relative humidity: {}%".format(temperature, humidity))


def save_to_csv(output_csv_file, temperature, humidity):

    with open(output_csv_file, "a") as f:
        writer = csv.writer(f, delimiter=",")
        writer.writerow([time.time(), temperature, humidity])


def save_to_db(db_name, temperature, humidity):

    json_body = [
        {
            "measurement": "environment",
            "tags": {"position": "salon"},
            "fields": {"humidity": humidity, "temperature": temperature},
        }
    ]

    db_client = InfluxDBClient(host="localhost", port=8086)
    db_client.switch_database(db_name)
    db_client.write_points(json_body, protocol="json")


def main():

    serial_port = "/dev/ttyACM1"
    baud_rate = 9600
    output_csv_file = "data.csv"
    db_name = "temp_humidity"

    while True:
        try:
            serial_data = serial.Serial(serial_port, baud_rate)
            serial_data.flushInput()
            record_data(serial_data, output_csv_file, db_name)

        except serial.SerialException:
            print("Port {} is unavailable.".format(serial_port))
            break

        except IndexError:
            print("The output format is incorrect. Please review your Arduino code.")
            break

        except KeyboardInterrupt:
            print("Keyboard Interrupt.")
            break


if __name__ == "__main__":
    main()
