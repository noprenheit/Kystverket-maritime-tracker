import pandas as pd

port_coords_df = pd.read_csv("port_coordinates.csv")  # columns must be "Port" - "Latitude" - "Longitude"
port_coords = port_coords_df.set_index("Port").to_dict(orient="index")

df = pd.read_csv("ship_routes.csv", sep=",")

def get_lat(port_name):
    return port_coords[port_name]["Latitude"] if port_name in port_coords else None

def get_lon(port_name):
    return port_coords[port_name]["Longitude"] if port_name in port_coords else None

df["dep_lat"] = df["avgangshavn_navn"].apply(get_lat)
df["dep_lon"] = df["avgangshavn_navn"].apply(get_lon)

df["arr_lat"] = df["ankomsthavn_navn"].apply(get_lat)
df["arr_lon"] = df["ankomsthavn_navn"].apply(get_lon)

df.to_csv("ship_routes_with_coords.csv", sep=",", index=False)

print(f"Data saved to {'ship_routes_with_coords.csv'}")
