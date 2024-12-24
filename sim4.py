import tkinter as tk
from tkinter import ttk
import time
import heapq
import numpy as np
import threading
import random

# ------------------------------
# SIMULATION PARAMETERS
# ------------------------------
METRO_RADIUS = 3.0
REQUEST_RATE = 100 / 60.0
INITIAL_LERT_COUNT = 25
LERT_SPEED_KMH = 25.0
LERT_SPEED = LERT_SPEED_KMH / 3600.0
POISSON_REQUESTS = True

# ------------------------------
# CORE SIMULATION (Same as Before)
# ------------------------------
class Request:
    def __init__(self, time, distance, direction):
        self.time = time
        self.distance = distance
        self.direction = direction
        self.assigned = False
        self.wait_start = time
        self.wait_end = None
        self.travel_time = None

class Lert:
    def __init__(self, id, speed):
        self.id = id
        self.speed = speed
        self.status = 'idle'
        self.next_free_time = 0.0
        self.total_trips = 0

    def assign(self, current_time, request):
        pickup_distance = request.distance
        travel_to_passenger_time = pickup_distance / self.speed
        travel_with_passenger_time = pickup_distance / self.speed
        total_travel_time = travel_to_passenger_time + travel_with_passenger_time
        self.next_free_time = current_time + total_travel_time
        self.total_trips += 1
        request.wait_end = current_time
        request.travel_time = total_travel_time
        return total_travel_time

class MetroSimulation:
    def __init__(self):
        self.current_time = 0.0
        self.event_queue = []
        self.requests = []
        self.completed_requests = 0
        self.total_wait_time = 0.0
        self.total_travel_time = 0.0
        self.lerts = [Lert(i, LERT_SPEED) for i in range(INITIAL_LERT_COUNT)]
        self.schedule_next_request_arrival(self.current_time)

    def schedule_next_request_arrival(self, now):
        if POISSON_REQUESTS:
            rate = REQUEST_RATE
            mean_inter_arrival = 1.0 / rate
            gap = np.random.exponential(mean_inter_arrival)
        else:
            gap = 1.0 / REQUEST_RATE
        next_arrival_time = now + gap
        heapq.heappush(self.event_queue, (next_arrival_time, 'arrival', None))

    def handle_arrival_event(self):
        direction = random.choice(['to_station', 'from_station'])
        distance = np.random.uniform(0, METRO_RADIUS)
        req = Request(self.current_time, distance, direction)
        self.requests.append(req)
        self.schedule_next_request_arrival(self.current_time)

    def find_available_lert(self):
        for lert in self.lerts:
            if lert.next_free_time <= self.current_time:
                return lert
        return None

    def handle_requests(self):
        unassigned_requests = [r for r in self.requests if not r.assigned]
        unassigned_requests.sort(key=lambda r: r.time)
        for request in unassigned_requests:
            lert = self.find_available_lert()
            if lert:
                request.assigned = True
                travel_time = lert.assign(self.current_time, request)
                heapq.heappush(self.event_queue, (self.current_time + travel_time, 'complete', request))

    def handle_complete_event(self, request):
        self.completed_requests += 1
        wait_time = request.wait_end - request.wait_start
        self.total_wait_time += wait_time
        self.total_travel_time += request.travel_time

    def run_step(self):
        if not self.event_queue:
            return
        event_time, event_type, request = heapq.heappop(self.event_queue)
        self.current_time = event_time
        if event_type == 'arrival':
            self.handle_arrival_event()
        elif event_type == 'complete':
            self.handle_complete_event(request)
        self.handle_requests()

    def run_until(self, end_time):
        while self.event_queue and self.current_time < end_time:
            self.run_step()

    def get_stats(self):
        avg_wait = (self.total_wait_time / self.completed_requests if self.completed_requests > 0 else 0)
        avg_travel = (self.total_travel_time / self.completed_requests if self.completed_requests > 0 else 0)
        queue_length = sum(not r.assigned for r in self.requests)
        return {
            'time': self.current_time,
            'completed_requests': self.completed_requests,
            'avg_wait_time': avg_wait,
            'avg_travel_time': avg_travel,
            'queue_length': queue_length
        }

# ------------------------------
# GUI INTERFACE
# ------------------------------
class MetroSimulationGUI:
    def __init__(self, root, simulation):
        self.root = root
        self.simulation = simulation
        self.root.title("Metro Station Simulation")
        self.running = True

        # Labels
        self.label_completed = ttk.Label(root, text="Completed Requests: 0")
        self.label_completed.pack(pady=5)

        self.label_queue = ttk.Label(root, text="Queue Length: 0")
        self.label_queue.pack(pady=5)

        self.label_wait = ttk.Label(root, text="Avg Wait Time: 0 s")
        self.label_wait.pack(pady=5)

        # Controls
        self.btn_add_lert = ttk.Button(root, text="Add Lert", command=self.add_lert)
        self.btn_add_lert.pack(pady=5)

        self.btn_remove_lert = ttk.Button(root, text="Remove Lert", command=self.remove_lert)
        self.btn_remove_lert.pack(pady=5)

        self.scale_rate = ttk.Scale(root, from_=10, to=200, orient="horizontal", command=self.change_rate)
        self.scale_rate.set(REQUEST_RATE * 60)
        self.scale_rate.pack(pady=5)
        ttk.Label(root, text="Request Rate (per min)").pack()

        # Real-time updates
        self.update_display()

    def update_display(self):
        stats = self.simulation.get_stats()
        self.label_completed.config(text=f"Completed Requests: {stats['completed_requests']}")
        self.label_queue.config(text=f"Queue Length: {stats['queue_length']}")
        self.label_wait.config(text=f"Avg Wait Time: {stats['avg_wait_time']:.2f} s")

        if self.running:
            self.simulation.run_until(self.simulation.current_time + 1)
            self.root.after(1000, self.update_display)

    def add_lert(self):
        self.simulation.lerts.append(Lert(len(self.simulation.lerts), LERT_SPEED))
    
    def remove_lert(self):
        if len(self.simulation.lerts) > 0:
            self.simulation.lerts.pop()
    
    def change_rate(self, value):
        global REQUEST_RATE
        REQUEST_RATE = float(value) / 60.0

# ------------------------------
# MAIN
# ------------------------------
if __name__ == "__main__":
    sim = MetroSimulation()
    root = tk.Tk()
    app = MetroSimulationGUI(root, sim)
    root.mainloop()
