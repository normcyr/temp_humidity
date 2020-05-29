#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to listen to the serial port where an Arduino recorded the temperature
and relative humidity from a DHT22 module.

The data is printed to the standard output, saved to a CSV file and to InfluxDB.

Needs a running InfluxDB instance to save to database.
Vizualisation can be done with Grafana.
"""

import csv
import time
import argparse

import serial
from influxdb import InfluxDBClient

__author__ = "Normand Cyr"
__copyright__ = "Copyright 2020, Normand Cyr"
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Normand Cyr"
__email__ = "normand.cyr@umontreal.ca"
__status__ = "Development"


def get_serial_data(serial_port, baud_rate):

    serial_data = serial.Serial(serial_port, baud_rate)
    serial_data.flushInput()
    serial_bytes = serial_data.readline()
    decoded_bytes = serial_bytes.decode("utf-8")
    humidity = float(decoded_bytes.split(",", 1)[0].replace("\r", "").replace("\n", ""))
    temperature = float(
        decoded_bytes.split(",", 1)[1].replace("\r", "").replace("\n", "")
    )

    return temperature, humidity


def print_stdout(temperature, humidity):

    print("temperature: {}°C, relative humidity: {}%".format(temperature, humidity))


def save_to_csv(args, temperature, humidity):

    with open(args.csv, "a") as f:
        writer = csv.writer(f, delimiter=",")
        writer.writerow([time.time(), temperature, humidity])


def save_to_db(args, temperature, humidity):

    json_body = [
        {
            "measurement": "environment",
            "tags": {"position": "salon"},
            "fields": {"humidity": humidity, "temperature": temperature},
        }
    ]

    db_client = InfluxDBClient(host=args.host, port=args.port)
    db_client.create_database(args.db)
    db_client.switch_database(args.db)
    db_client.write_points(json_body, protocol="json")


def parse_args():

    parser = argparse.ArgumentParser(
        description="Arguments to specify the behaviour of the script."
    )
    parser.add_argument(
        "--host",
        type=str,
        required=False,
        default="localhost",
        help="hostname of InfluxDB http API",
    )
    parser.add_argument(
        "--port",
        type=int,
        required=False,
        default=8086,
        help="port of InfluxDB http API",
    )
    parser.add_argument(
        "--db",
        nargs="?",
        const="temp_humidity",
        type=str,
        help="saves the data to InfluxDB",
    )
    parser.add_argument(
        "--csv",
        nargs="?",
        const="data.csv",
        type=str,
        help="saves the data to a csv file",
    )
    parser.add_argument(
        "--stdout", action="store_true", help="prints the data to stdout",
    )

    return parser.parse_args()


def main(args):

    serial_port = "/dev/ttyACM1"
    baud_rate = 9600

    while True:
        try:
            temperature, humidity = get_serial_data(serial_port, baud_rate)

            if args.db:
                save_to_db(args, temperature, humidity)
            if args.csv:
                save_to_csv(args, temperature, humidity)
            if args.stdout:
                print_stdout(temperature, humidity)

        except serial.SerialException:
            print("Port {} is unavailable.".format(serial_port))
            break

        except ValueError:
            print("Failed to read from DHT sensor!")
            time.sleep(30)
            pass

        except IndexError:
            print(
                "The output format from the serial data is incorrect. Please review your Arduino code."
            )
            break

        except KeyboardInterrupt:
            print("Keyboard Interrupt.")
            break


if __name__ == "__main__":

    args = parse_args()
    main(args)
