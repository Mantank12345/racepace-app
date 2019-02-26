from __future__ import annotations
import math
import copy
import json
from math import inf

EARTH_RADIUS = 6371000

class Heuristic:
    """
    Heuristic used to generate routes to the users preference's
    Jason Yu
    """
    def __init__(self, file_name):
        pass
        
    def open_file(self, file_name):
        json_file = open(file_name)
        json_data = json.loads(json_file)


class Point:
    """
    Represents a geodetic point with latitude and longitude
    Jason Yu/Abdur Raqueeb/Sunny Yan
    """
    def __init__(self, latitude: float, longitude: float):
        self.latitude = round(float(latitude),9)
        self.longitude = round(float(longitude),9)

    @classmethod
    def from_string(cls, string):
        """
        Generates Point class from string data
        Abdur Raqueeb
        """
        lat, long = string.split(',')
        return cls(lat, long)

    def distance(self, other: Point) -> float:
        """
        Uses spherical geometry to calculate the surface distance between two points.
        Sunny Yan
        """
        lat1, lon1 = self
        lat2, lon2 = other
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2)
            * math.sin(dlat / 2)
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2)
            * math.sin(dlon / 2)
            )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return EARTH_RADIUS * c

    def euclidean_distance(self,other:Point):
        '''
        Euclidean distance between two points (NON SPHERICAL)
        Jason Yu
        '''
        lat1,long1 = self
        lat2,long2 = other
        return math.sqrt((long1-long2)**2 + (lat1-lat2)**2)

    def heuristic_distance(self, other: Point, hor_unit: float, vert_unit: float) -> float:
        """
        Heuristic value based on euclidean distance on geo units
        Jason YU
        """
        delta_lat = abs(self.latitude - other.latitude)
        delta_lon = abs(self.longitude - other.longitude)
        x_dist = hor_unit * delta_lon
        y_dist = vert_unit * delta_lat
        return x_dist**2 + y_dist**2

    def __iter__(self):
        """
        Allows for easy splitting of location data
        Abdur Raqueeb
        """
        return iter((self.latitude, self.longitude))

    def __sub__(self, other: Point) -> int:
        """
        Abdur Raqueeb
        Another way to call the distance function
        """
        return self.distance(other)

    def __repr__(self):
        return f'{self.latitude},{self.longitude}'

    def closest_node(self, nodes: dict) -> Node:
        """
        Returns the closest node from a dict of nodes
        Abdur Raqueeb
        """
        nodes = sorted(nodes.values(), key=lambda other: other - self)
        closest_node = nodes[0]
        return closest_node

    def get_midpoint(self, other) -> Point:
        """
        Midpoint of two points that is calculated via euclidean multi_distance
        Not Accurate over large distances for coordinates
        Jason Yu
        """
        delta_lat = (other.latitude - self.latitude) / 2
        delta_lon = (other.longitude - self.longitude) / 2
        return Point(self.latitude + delta_lat,self.longitude + delta_lon)

    @staticmethod
    def radians_to_degrees(radians):
        return radians / math.pi * 180

    def check_below_line(self,left_point,right_point):
      gradient = left_point.gradient(right_point)
      if gradient == 0: return self.latitude < left_point.latitude # If point y is less, it is below
      elif gradient == math.inf: return self.latitude < max([left_point.latitude,right_point.latitude]) # point y is less than max, it is below
      else:
        line_equation = lambda x: gradient * (x - left_point.longitude) + left_point.latitude
        return self.latitude <= line_equation(left_point.longitude) #Below line
    
    def gradient(self,other):
        """
        Returns gradient from point 1 to point 2
        """
        delta_y = (other.latitude - self.latitude)
        delta_x = (other.longitude - self.longitude)
        if delta_y == 0: return 0
        elif delta_x == 0: return math.inf
        else: return delta_y / delta_x

class Node(Point):
    """
    Node class holds tags and is parent to Point
    Jason Yu
    """
    def __init__(self, latitude: float, longitude: float, id: str, tags:dict):
        super().__init__(latitude, longitude)
        self.id = id
        self.tags = tags
        self.ways = set()
        self.tag_multiplier = 1

    def __eq__(self, other: Point):
        """
        Abdur Raqueeb
        """
        return self.id == other.id

    def get_tag_multiplier(self, profile):
        """
        Jason Yu
        """
        return 1

    @staticmethod
    def json_to_nodes(json_nodes: dict) -> dict:
        """
        Generates a dictionary of nodes from json
        Jason Yu/Abdur Raqueeb
        """
        return {node['id']: Node.from_json(node) for node in json_nodes['elements']}

    @classmethod
    def from_json(cls, json_nodes: dict) -> Node:
        """
        Generates a Node class from a json
        Jason Yu/Abdur Raqueeb
        """
        return cls(json_nodes['lat'], json_nodes['lon'], json_nodes['id'],json_nodes.get('tags',{}))

class Way:
    """
    Way class is a class that holds nodes
    Jason Yu/Abdur Raqueeb
    """
    def __init__(self, nodes: list, id: str, tags):
        self.node_ids = nodes
        self.id = id
        self.tags = tags

    @classmethod
    def from_json(cls, json_way: dict):
        """
        Generates a Way class from a json
        Jason Yu/Abdur Raqueeb
        """
        return cls(json_way['nodes'], json_way['id'], json_way.get('tags',{}))

    @staticmethod
    def json_to_ways(json_ways):
        """
        Generates a dictionary of ways from json
        Jason Yu/Abdur Raqueeb
        """
        return {way['id']:Way.from_json(way) for way in json_ways['elements']}

    def update_node_tags(self, nodes):
        for node_id in self.node_ids:
            if node_id in nodes:
                nodes[node_id].tags.update(self.tags)

class Route:
    """
    Class that describes a running route
    Jason Yu/Abdur Raqueeb
    """
    def __init__(self, route: list, distance: int, nodes: dict):
        self.route = route
        self.distance = distance
        self.nodes = nodes

    @property
    def json(self):
        """
        Jason Yu/Abdur Raqueeb
        """
        route_nodes = [self.nodes[node_id] for node_id in self.route]
        route = [{'latitude': node.latitude, 'longitude': node.longitude} for node in route_nodes]
        return {
            "success": True,
            "route": route,
            "dist": self.distance
        }

    @classmethod
    def rectangle_bounding_box(cls,location:Point,length:float,width:float)-> str:
        """
        Takes point and generates rectangular bounding box
        around point with width and length
        Jason Yu
        """
        vert_unit,hor_unit = cls.get_coordinate_units(location)
        latitude,longitude = location
        lat_unit = (width/2) / vert_unit
        lon_unit = (length/2) / hor_unit
        la1 = latitude - lat_unit
        lo1 = longitude - lon_unit
        la2 = latitude + lat_unit
        lo2 = longitude + lon_unit
        bounding_coords = ','.join(list(map(str,[la1,lo1,la2,lo2])))
        return bounding_coords

    @classmethod
    def two_point_bounding_box(cls,location:Point,other_location:Point)-> str:
        """
        Takes two points and generates rectangular bounding box
        that is uniquely oritentated about points
        Jason Yu
        """
        #Constants and distance units
        vert_unit,hor_unit = cls.get_coordinate_units(location)
        pi = math.pi
        lat1,long1 = location
        lat2,long2 = other_location
        #Scaling factors
        distance = location - other_location
        vert_scale = 1 * distance / vert_unit
        hor_scale = 1 * distance / hor_unit
        #Two Point Extensions for intial in either direction
        theta = math.atan2((lat2 - lat1),(long2 - long1)) #Intial theta based on intial points
        mlat1,mlong1 = lat1 + math.sin(theta - pi) * vert_scale, long1 + math.cos(theta - pi) * hor_scale
        mlat2,mlong2 = lat2 + math.sin(theta)      * vert_scale, long2 + math.cos(theta)      * hor_scale
        #Four perpendicular vertices extended from extensions in either direction
        theta2 = (2*pi - (pi/2 - theta)) #Perpendicular to initial theta
        a = Point(mlat1 + math.sin(theta2)      * vert_scale, mlong1 + math.cos(theta2)      * hor_scale)
        b = Point(mlat1 + math.sin(theta2 - pi) * vert_scale, mlong1 + math.cos(theta2 - pi) * hor_scale)
        c = Point(mlat2 + math.sin(theta2)      * vert_scale, mlong2 + math.cos(theta2)      * hor_scale)
        d = Point(mlat2 + math.sin(theta2 - pi) * vert_scale, mlong2 + math.cos(theta2 - pi) * hor_scale)
        #Point Order
        points = [a,b,d,c]
        return ' '.join(f'{p.latitude} {p.longitude}' for p in points)

    @classmethod 
    def get_convex_hull_points(cls, waypoints):
        points = []
        for index in range(len(waypoints) - 2):
            start = waypoints[index]
            end = waypoints[index + 1]
            lat_lon_list = cls.two_point_bounding_box(start,end).split()
            bounding_box_points = []
            while len(lat_lon_list) != 0:
                lat = lat_lon_list.pop(0)
                lon = lat_lon_list.pop(0)
                bounding_box_points.append(Point(lat,lon))
            points += bounding_box_points
        return points

    @classmethod
    def convex_hull(cls, waypoints)-> str:
        if len(waypoints) == 2: return cls.two_point_bounding_box(waypoints[0],waypoints[1])
        points = cls.get_convex_hull_points(waypoints)
        starting_point = min(points, key=lambda point: point.latitude)
        theta_dict = {}
        for point in points:
            if point is starting_point: continue
            delta_x = point.longitude - starting_point.longitude
            delta_y = point.latitude - starting_point.latitude
            theta = Point.radians_to_degrees(math.atan2(delta_y,delta_x))
            theta_dict[point] = theta
        sorted_points = sorted(theta_dict, key=lambda k:theta_dict[k])
        left, right = [], []
        while True:
            if len(sorted_points) < 2:
                if len(sorted_points) == 1: left.append(sorted_points.pop())
                break
            left_point = sorted_points.pop()
            right_point = sorted_points.pop(0)
            left.append(left_point)
            right.append(right_point)
            sorted_points = [point for point in sorted_points if not point.check_below_line(left_point,right_point)]
        convex_hull = [starting_point] + right + list(reversed(left))
        return ' '.join(f'{p.latitude} {p.longitude}' for p in convex_hull)

    @classmethod
    async def from_database(cls,db,route_id):
        """
        Creates a route object from a route stored in the database
        Abdur
        """
        route = await db.find_one({'id_':route_id})
        return cls(route_id, **route['route'])

    @classmethod
    async def from_GPX(cls, nodes: dict, track): #<--XML object
        """
        Sunny Yan
        """
        route = [Node(pt[0],pt.get[1],"").closest_distance(nodes)
                 for pt in track]
        dist = cls.get_route_distance(route,nodes)
        return cls(route,dist)

    @classmethod
    def generate_route(cls, nodes: dict, ways: dict, start_id: int, end_id: int) -> Route:
        """
        Generates the shortest route to a destination
        Uses A* with euclidean distance as heuristic
        Uses tags to change cost of moving to nodes
        Jason Yu
        """
        #Set up constants, sets and distance units
        unvisited = set(node_id for node_id in nodes)
        visited = set()
        path_dict = dict((node,(inf,[node])) for node in nodes)
        neighbours = cls.find_neighbours(ways)
        path_dict[start_id] = (0,[start_id])
        vert_unit,hor_unit = cls.get_coordinate_units(nodes[start_id])
        end_point = nodes[end_id]
        #Verify whether route can be completed
        if end_id not in nodes:     raise Exception('End node not in node space. Specify a valid node.')
        elif start_id not in nodes: raise Exception('End node not in node space. Specify a valid node.')
        elif end_id not in neighbours or start_id not in neighbours: raise Exception('No connecting neighbour')
        else: current = start_id
        #Loop through nodes and find all best sub-routes to then determine best route
        while True:
            current_point = nodes[current]
            current_cost,current_path = path_dict[current]
            current_neighbours = neighbours[current]
            #Loop neighbours and determine lowest heuristic value for sub-route
            for neighbour in (current_neighbours & unvisited): #Intersection of neighbours and unvisited
                neighbour_cost,neighbour_path = path_dict[neighbour]
                neighbour_node = nodes[neighbour]
                # Determine heuristic distance which is modified by tag multiplier
                heuristic_cost = neighbour_node.tag_multiplier * current_point.heuristic_distance(neighbour_node,vert_unit,hor_unit)
                new_cost = heuristic_cost + current_cost
                if new_cost < neighbour_cost:
                    path_dict[neighbour] = (new_cost,current_path + [neighbour])
            #Update visited and unvisited to stop backtracking
            unvisited.remove(current)
            visited.add(current)
            #Find next node which is cheapest accounting for distance to end
            if end_id in visited: break
            else:
                unvisited_node_costs = dict()
                for node_id in unvisited:
                    current_distance,path = path_dict[node_id]
                    current_cost = current_distance + end_point.heuristic_distance(nodes[node_id],vert_unit,hor_unit)
                    unvisited_node_costs[node_id] = current_cost
                next_node,cost = min(unvisited_node_costs.items(),key=lambda item:item[1])
                if cost == inf: raise Exception("End node cannot be reached")
                else: current = next_node
        #Retrieve route, calculate actual distance
        heuristic_cost, fastest_route = path_dict[end_id]
        actual_distance = cls.get_route_distance(fastest_route,nodes)
        return cls(fastest_route, actual_distance, nodes)

    @classmethod
    def generate_multi_route(cls, nodes: dict, ways: dict, node_waypoints: list) -> Route:
        """
        Generate route that passes through all way points in order
        Jason Yu
        """
        start = node_waypoints[0]
        multi_distance = 0
        multi_route = [start]
        multi_route_nodes = dict()
        for current_index in range(len(node_waypoints)-1):
            current_node = node_waypoints[current_index]
            next_node = node_waypoints[current_index+1]
            route = cls.generate_route(nodes,ways,current_node,next_node)
            multi_route_nodes.update(route.nodes)
            multi_distance += route.distance
            multi_route += route.route[1:]
        return cls(multi_route,multi_distance,multi_route_nodes)

    @staticmethod
    def get_route_distance(fastest_route:list,nodes:dict)-> float:
        """
        Find route distance from route nodes
        Jason Yu
        """
        route_points = [nodes[node_id] for node_id in fastest_route]
        actual_distance = sum(route_points[index]-route_points[index+1] for index in range(len(route_points)-1))
        return actual_distance

    @staticmethod
    def find_neighbours(ways: dict) -> dict:
        """
        Generates neighbours for every node in provided ways
        Jason Yu
        """
        neighbours = {}
        for way in ways.values():
            for index, node in enumerate(way.node_ids):
                if node not in neighbours: neighbours[node] = set()
                if (index - 1) != 0: neighbours[node].add(way.node_ids[index - 1])
                if (index + 1) != len(way.node_ids): neighbours[node].add(way.node_ids[index + 1])
        return neighbours

    @staticmethod
    def get_coordinate_units(location):
        """
        Coordinate unit in terms of metres for localized area
        Horizontal Unit is distance for 1 unit of longitude
        Vertical Unit is distance for 1 unit of latitude
        Jason Yu
        """
        latitude,longitude = location
        hor_unit  = location - Point(latitude,longitude + 1)
        vert_unit  = location - Point(latitude + 1,longitude)
        return vert_unit, hor_unit

    @staticmethod
    def transform_json_nodes_and_ways(nodes_json:dict,ways_json:dict,profile:dict={}):
        """
        Convert node and way data to objects
        Update node tags and multipliers
        Jason Yu
        """
        nodes = Node.json_to_nodes(nodes_json)
        ways = Way.json_to_ways(ways_json)
        for way in ways.values():
            way.update_node_tags(nodes)
        for node in nodes.values():
            node.get_tag_multiplier(profile)
        return nodes,ways

    async def save_route(self, db, user_id):
        """
        Adds to database of routes
        """
        document = {
            "author":user_id,
            "route":{
                "route":self.route,
                "distance":self.distance,
                }
            }
        self.id = await db.routes.insert_one(document).inserted_id

if __name__ == '__main__':
    pass
