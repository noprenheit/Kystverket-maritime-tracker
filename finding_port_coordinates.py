import requests
import time
import csv
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("API_KEY")

if not api_key:
    raise ValueError("Do you have an API key? Add it to the .env file")

port_coords = {}
file_path = "unique_ports.txt"
output_csv = "port_coordinates.csv"

with open(file_path, "r") as file:
    ports = [line.strip() for line in file]

for port in ports:
    url = f"https://api.opencagedata.com/geocode/v1/json?q={port}&key={api_key}"
    response = requests.get(url).json()
    if response['results']:
        coords = response['results'][0]['geometry']
        port_coords[port] = (coords['lat'], coords['lng'])
    else:
        port_coords[port] = None
        print(f"Coordinates not found for: {port}")
    time.sleep(1)  # Do not pressure the API

with open(output_csv, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Port", "Latitude", "Longitude"])
    for port, coords in port_coords.items():
        if coords:
            writer.writerow([port, coords[0], coords[1]])
        else:
            writer.writerow([port, None, None])

print(f"Coordinates saved to {output_csv}")
