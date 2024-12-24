import numpy as np
import matplotlib.pyplot as plt
import time
import threading

# Simulation Parameters
METRO_RADIUS = 3  # km
LERT_SPEED = 25 / 3600  # km per second
REQUESTS_PER_MINUTE = 100
LERT_COUNT = 25

# Lert Class
class Lert:
    def __init__(self, id):
        self.id = id
        self.available = True
        self.position = np.random.uniform(0, METRO_RADIUS)  # Random start location
        self.traveling_to = None
        self.pickup_distance = 0
        self.drop_distance = 0
        self.waiting_time = 0

    def assign_request(self, request):
        self.traveling_to = request
        self.pickup_distance = request['distance']
        self.drop_distance = request['distance']
        self.available = False
    
    def move(self):
        if not self.available:
            if self.pickup_distance > 0:
                self.pickup_distance -= LERT_SPEED
            else:
                self.drop_distance -= LERT_SPEED

            if self.drop_distance <= 0:
                self.available = True
                self.traveling_to = None

# Simulation Class
class MetroSimulation:
    def __init__(self):
        self.lerts = [Lert(i) for i in range(LERT_COUNT)]
        self.requests = []
        self.completed_requests = 0
        self.time = 0

    def generate_requests(self):
        for _ in range(REQUESTS_PER_MINUTE // 60):
            distance = np.random.uniform(0, METRO_RADIUS)
            direction = np.random.choice(["to_station", "from_station"])
            self.requests.append({
                'distance': distance,
                'direction': direction
            })

    def assign_requests(self):
        for request in self.requests:
            available_lert = next((lert for lert in self.lerts if lert.available), None)
            if available_lert:
                available_lert.assign_request(request)
                self.requests.remove(request)
                self.completed_requests += 1
    
    def update(self):
        self.time += 1
        for lert in self.lerts:
            lert.move()
        self.generate_requests()
        self.assign_requests()

    def run_simulation(self):
        while True:
            self.update()
            self.display_status()
            time.sleep(1)

    def display_status(self):
        available_count = sum([lert.available for lert in self.lerts])
        print(f"Time: {self.time}s | Available Lerts: {available_count} | Pending Requests: {len(self.requests)} | Completed: {self.completed_requests}")

# Start Simulation
simulation = MetroSimulation()

# Run in a separate thread to keep it dynamic
thread = threading.Thread(target=simulation.run_simulation)
thread.start()
