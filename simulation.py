import json
import math
import os
import random
import re
from math import radians, cos, sin, sqrt
from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy_garden.mapview import MapView, MapMarker
from kivy_garden.mapview.clustered_marker_layer import ClusteredMarkerLayer

from pathfinder import RouteView as rv

TIMISOARA_LAT = 45.747231774279214
TIMISOARA_LON = 21.231679569701775

class MapViewWithConstraints(MapView):
    def __init__(self, **kwargs):
        super(MapViewWithConstraints, self).__init__(**kwargs)
        self.bind(on_region_change=self.check_constraints)

        # Define your constraints
        self.min_lat = 45.673645
        self.max_lat = 45.833905
        self.min_lon = 21.022479
        self.max_lon = 21.451205

    def check_constraints(self, instance, value):
        # Check if the new region violates the constraints
        if (self.min_lat < value[1] < self.max_lat) and (self.min_lon < value[0] < self.max_lon):
            pass  # Region is within constraints
        else:
            # Adjust the region to stay within constraints
            new_lat = max(self.min_lat, min(self.max_lat, value[1]))
            new_lon = max(self.min_lon, min(self.max_lon, value[0]))
            self.center_on(new_lat, new_lon)

class MapApp(App):

    def build(self):
        # Create a MapView on Timisoara
        try:
            mapview = MapViewWithConstraints(zoom=20, lat=TIMISOARA_LAT, lon=TIMISOARA_LON, map_source='osm')
        except Exception as e:
            print(f"Image in Osm not loaded: {e}")

        script_dir = os.path.dirname(os.path.abspath(__file__))

        black_tl_png = os.path.join(script_dir, 'venv', 'icons', 'BlackTL3.png')

        # Load the JSON data from the file
        with open('markers_data.json', 'r') as infile:
            data = json.load(infile)

        with open('filtered_trafficlight_response.json', 'r') as f:
            trafficlight_data = json.load(f)
        traffic_light_dict = dict()

        # Traffic Lights

        clustered_layer = ClusteredMarkerLayer()

        for feature in trafficlight_data["features"]:
            if "geometry" in feature and "coordinates" in feature["geometry"]:
                coordinates = feature["geometry"]["coordinates"]
                if feature["properties"]["intersection_id"] not in traffic_light_dict:
                    traffic_light_dict[feature["properties"]["intersection_id"]] = []
                    traffic_light_dict[feature["properties"]["intersection_id"]].append([coordinates[1], coordinates[0]])
                else:
                    traffic_light_dict[feature["properties"]["intersection_id"]].append([coordinates[1], coordinates[0]])
                if len(coordinates) == 2:
                    marker = MapMarker(lat=coordinates[1], lon=coordinates[0], source=black_tl_png)
                    clustered_layer.add_marker(marker.lon, marker.lat, cls=MapMarker, options={'source': marker.source})

        intersection_dict = {}
        print(traffic_light_dict.items())

        for key, values in traffic_light_dict.items():
            # Calculate the average for each subarray
            averages = [[key] + [round(sum(x) / len(x), 6)for x in zip(*values[1:])]]

            # Combine the key and averages into the result dictionary
            intersection_dict[key] = averages

        print(intersection_dict.items())
        mapview.add_layer(clustered_layer)

        # Emergency Stations

        for location_type, locations in data['features'].items():
            # Display information about every location found
            self.display_location_information(mapview=mapview, script_dir=script_dir,
                                              location_type=location_type, locations=locations)

        # Add events
        # self.add_random_marker(mapview=mapview)
        Clock.schedule_interval(lambda dt: self.add_random_marker(mapview=mapview), 6)
        # Returns the mapview
        return mapview

    def display_location_information(self, mapview, script_dir, location_type, locations):
        if location_type == 'hospital':
            img_hospital = os.path.join(script_dir, 'hospital.png')
            print("Hospital Locations:")
            for location in locations:
                lat, lon = self.write_location_information(location)
                marker_hospital = MapMarker(lat=lat, lon=lon, source=img_hospital)
                mapview.add_marker(marker_hospital)
        elif location_type == 'police':
            img_police = os.path.join(script_dir, 'police.png')
            print("Police Locations:")
            for location in locations:
                lat, lon = self.write_location_information(location)
                marker_police = MapMarker(lat=lat, lon=lon, source=img_police)
                mapview.add_marker(marker_police)
        elif location_type == 'firemen':
            img_firemen = os.path.join(script_dir, 'firemen.png')
            print("Firemen Locations:")
            for location in locations:
                lat, lon = self.write_location_information(location)
                marker_firemen = MapMarker(lat=lat, lon=lon, source=img_firemen)
                mapview.add_marker(marker_firemen)
        else:
            print(f"Unknown Location Type: {location_type}")

    @staticmethod
    def write_location_information(location):
        name = location['name']
        lat = location['lat']
        lon = location['lon']
        print(f"Name: {name}")
        print(f"Latitude: {lat}, Longitude: {lon}")
        return lat, lon

    def add_random_marker(self, mapview):
        instance_rv = rv()
        # Center coordinates
        lat_center = TIMISOARA_LAT
        lon_center = TIMISOARA_LON

        # Radius in meters
        radius = 6000

        # Generate random coordinates within the specified radius
        r = radius * sqrt(random.uniform(0, 1))
        theta = random.uniform(0, 2 * 3.141592653589793)  # Random angle in radians

        # Convert to Cartesian coordinates
        x = r * cos(theta)
        y = r * sin(theta)

        # Convert Cartesian coordinates to latitude and longitude offsets
        lat_offset = y / 111111  # Approx. 111111 meters per degree latitude
        lon_offset = x / (111111 * cos(radians(lat_center)))  # Approx. 111111 meters per degree longitude at equator

        # Calculate the random coordinates
        lat = lat_center + lat_offset
        lon = lon_center + lon_offset

        victim_type = random.choice(["police_victim", "firemen_victim", "hospital_victim"])

        # Create a map marker based on the chosen type
        if victim_type == "police_victim":
            script_dir = os.path.dirname(os.path.abspath(__file__))
            img_police_victim = os.path.join(script_dir, 'police_victim.png')
            marker_victim = MapMarker(lat=lat, lon=lon, source=img_police_victim)
        elif victim_type == "firemen_victim":
            script_dir = os.path.dirname(os.path.abspath(__file__))
            img_firemen_victim = os.path.join(script_dir, 'firemen_victim.png')
            marker_victim = MapMarker(lat=lat, lon=lon, source=img_firemen_victim)
        else:  # "hospital_victim"
            script_dir = os.path.dirname(os.path.abspath(__file__))
            img_hospital_victim = os.path.join(script_dir, 'hospital_victim.png')
            marker_victim = MapMarker(lat=lat, lon=lon, source=img_hospital_victim)

        mapview.add_marker(marker_victim)
        route_points, marker_dest = (self.find_nearest_building(mapview, marker_victim, lat, lon,
                                                                re.sub(r'_victim$', '', victim_type)))
        map_line = instance_rv.draw_route(mapview=mapview, route_coordinates=route_points)
        marker = instance_rv.create_marker(mapview=mapview, marker1=marker_dest)
        t = Thread(target=instance_rv.animate_marker,
                   args=(mapview, marker, marker_victim, map_line, route_points))
        t.start()

    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        radius = 6371000  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = radius * c
        return distance

    def find_nearest_building(self, mapview, marker_victim, victim_lat, victim_lon, victim_type):
        # Reads data from a json file
        with open('markers_data.json') as f:
            markers_data = json.load(f)

        # Declaration of variables
        nearest_building_distance_lat, nearest_building_distance_lon = 0, 0
        nearest_building = None
        nearest_building_distance = float('inf')
        instance_pathfinder = rv()

        # Checking for the nearest building for the victim
        for building in markers_data['features'][victim_type]:
            building_lat = building['lat']
            building_lon = building['lon']
            nearest_building = building
            distance = self.calculate_distance(victim_lat, victim_lon, building_lat, building_lon)
            if distance < nearest_building_distance:
                nearest_building_distance_lat = building_lat
                nearest_building_distance_lon = building_lon
                nearest_building_distance = distance
                nearest_building = building

        # Fetches the points needed to draw the path between 2 points
        route_points = instance_pathfinder.fetch_route(nearest_building_distance_lat,
                                                       nearest_building_distance_lon, victim_lat, victim_lon)

        # Checks if the victim is in a valid place
        if len(route_points) == 0:
            # If it is then removes the marker
            mapview.remove_marker(marker_victim)

        # Returns the points needed and the nearest building
        return route_points, nearest_building


# Starts the program
if __name__ == '__main__':
    MapApp().run()
