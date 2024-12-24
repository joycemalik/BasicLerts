import time
import heapq
import threading
import numpy as np
import random

# ------------------------------
#   PARAMETERS & CONFIGURATION
# ------------------------------
METRO_RADIUS = 3.0               # Radius around the metro station (km)
REQUEST_RATE = 100 / 60.0        # Requests per second (100 per minute -> ~1.67 requests/sec)
INITIAL_LERT_COUNT = 25          # How many Lerts to start with
LERT_SPEED_KMH = 25.0            # Speed in km/h
LERT_SPEED = LERT_SPEED_KMH / 3600.0  # Speed in km/s
POISSON_REQUESTS = True          # Use Poisson arrivals or uniform arrivals?

# For Poisson arrivals:
# The time between arrivals in a Poisson process is exponentially distributed
# with mean = 1 / (requests per second).
# E.g., if we have 1.67 requests/sec, mean inter-arrival time ~ 0.6 seconds.

# ------------------------------
#   SIMULATION DATA STRUCTURES
# ------------------------------
class Request:
    """
    Represents a single ride request:
      - time: The time (simulation clock) the request was created
      - distance: Distance from the metro station (km)
      - direction: Either 'to_station' or 'from_station'
      - assigned: Whether a Lert has been assigned
      - wait_start: When the request first entered the queue
      - wait_end: When a Lert started service (pickup)
      - travel_time: Time the Lert actually spends traveling with the passenger
    """
    def __init__(self, time, distance, direction):
        self.time = time
        self.distance = distance
        self.direction = direction
        
        self.assigned = False
        self.wait_start = time
        self.wait_end = None
        self.travel_time = None

class Lert:
    """
    Represents a Lert vehicle:
      - id: Unique identifier
      - speed: km/s
      - status: 'idle' or 'busy'
      - next_free_time: When this Lert will become available
      - total_trips: How many trips completed
    """
    def __init__(self, id, speed):
        self.id = id
        self.speed = speed
        self.status = 'idle'
        self.next_free_time = 0.0
        self.total_trips = 0

    def assign(self, current_time, request):
        """
        Assign a request to this Lert. Calculate the time needed for:
          1. Travel to passenger (distance)
          2. Travel to/from station (distance again)
        """
        self.status = 'busy'
        pickup_distance = request.distance  # Distance from Lert to passenger
        # For a simplified model, assume Lert is at the station or 'teleports' to passenger
        # In a more advanced model, you'd track the Lert's position over time.

        # Actually, let's assume Lert is currently at the station or idle location
        # so time to reach passenger = distance / speed
        travel_to_passenger_time = pickup_distance / self.speed

        # Time to station or from station also = distance / speed
        # If direction= 'to_station', then we go passenger->station
        # If direction= 'from_station', station->passenger->home distance is the same
        travel_with_passenger_time = pickup_distance / self.speed

        total_travel_time = travel_to_passenger_time + travel_with_passenger_time

        # The Lert will be free only after it completes the entire trip
        self.next_free_time = current_time + total_travel_time
        self.total_trips += 1

        # Record the request's times
        request.wait_end = current_time  # The time the Lert started service
        request.travel_time = total_travel_time

        return total_travel_time


# ------------------------------
#    DISCRETE EVENT SIMULATION
# ------------------------------
class MetroSimulation:
    def __init__(self):
        self.current_time = 0.0
        self.event_queue = []  # Priority queue for events (min-heap by event_time)
        
        # Stats
        self.requests = []
        self.completed_requests = 0
        self.total_wait_time = 0.0
        self.total_travel_time = 0.0
        
        # Initialize Lerts
        self.lerts = [Lert(i, LERT_SPEED) for i in range(INITIAL_LERT_COUNT)]

        # Next arrival time
        self.schedule_next_request_arrival(self.current_time)

    def schedule_next_request_arrival(self, now):
        """
        Randomly schedule the next request arrival using either:
        1) Poisson (exponential inter-arrival times)
        2) Uniform or fixed rate
        """
        if POISSON_REQUESTS:
            # Exponential distribution for inter-arrival time
            rate = REQUEST_RATE  # requests per second
            mean_inter_arrival = 1.0 / rate  
            gap = np.random.exponential(mean_inter_arrival)
        else:
            # Uniform or fixed approach: simply 1/rate
            gap = 1.0 / REQUEST_RATE

        next_arrival_time = now + gap
        # Push an "arrival event" into the queue
        heapq.heappush(self.event_queue, (next_arrival_time, 'arrival', None))

    def handle_arrival_event(self):
        """
        Create a new Request. It can be 'to_station' or 'from_station' randomly.
        Place it in the request list.
        """
        direction = random.choice(['to_station', 'from_station'])
        distance = np.random.uniform(0, METRO_RADIUS)
        req = Request(self.current_time, distance, direction)
        
        self.requests.append(req)
        
        # Schedule the next arrival
        self.schedule_next_request_arrival(self.current_time)

    def find_available_lert(self):
        """
        Find a Lert that is idle at current_time (if any).
        If none are idle, returns None.
        """
        for lert in self.lerts:
            if lert.next_free_time <= self.current_time:
                return lert
        return None
    
    def handle_requests(self):
        """
        Match available Lerts with waiting requests in FIFO or any queue discipline.
        """
        # We'll do a simple FIFO approach
        unassigned_requests = [r for r in self.requests if not r.assigned]
        
        # Sort unassigned requests by arrival time (FIFO)
        unassigned_requests.sort(key=lambda r: r.time)
        
        for request in unassigned_requests:
            # Check if there is an idle Lert
            lert = self.find_available_lert()
            if lert is not None:
                # Assign request
                request.assigned = True
                travel_time = lert.assign(self.current_time, request)
                
                # Schedule a "request completed" event at current_time + travel_time
                heapq.heappush(
                    self.event_queue, 
                    (self.current_time + travel_time, 'complete', request)
                )
            else:
                # No Lert available at this moment; break
                break
    
    def handle_complete_event(self, request):
        """
        When a request is completed, record stats.
        """
        self.completed_requests += 1
        wait_time = request.wait_end - request.wait_start
        self.total_wait_time += wait_time
        self.total_travel_time += request.travel_time

    def run_step(self):
        """
        Process the next event in the queue.
        Then attempt to handle new requests with newly freed Lerts.
        """
        if not self.event_queue:
            # No more events scheduled, the simulation could end.
            return

        # Pop the next event by chronological order
        event_time, event_type, request = heapq.heappop(self.event_queue)
        
        # Advance simulation time
        self.current_time = event_time
        
        # Process this event
        if event_type == 'arrival':
            self.handle_arrival_event()
        elif event_type == 'complete':
            # A request is done
            self.handle_complete_event(request)

        # After processing an event, try to assign waiting requests
        self.handle_requests()

    def run_until(self, end_time):
        """
        Run the simulation until current_time >= end_time.
        """
        while self.event_queue and self.current_time < end_time:
            self.run_step()

    def get_stats(self):
        """
        Return current stats about the simulation:
          - completed_requests
          - average_wait_time
          - average_travel_time
          - queue_length
        """
        avg_wait = (self.total_wait_time / self.completed_requests 
                    if self.completed_requests > 0 else 0.0)
        avg_travel = (self.total_travel_time / self.completed_requests 
                      if self.completed_requests > 0 else 0.0)
        queue_length = sum(not r.assigned for r in self.requests)  # unassigned requests
        return {
            'time': self.current_time,
            'completed_requests': self.completed_requests,
            'avg_wait_time': avg_wait,
            'avg_travel_time': avg_travel,
            'queue_length': queue_length
        }

    # ------------------------------
    #   DYNAMIC / GAME-LIKE METHODS
    # ------------------------------
    def add_lert(self):
        """
        Dynamically add a new Lert to the simulation.
        """
        new_id = len(self.lerts)
        l = Lert(new_id, self.lerts[0].speed)  # use same speed or a new one
        self.lerts.append(l)
        print(f"Added new Lert #{new_id} at time {self.current_time:.2f}.")

    def remove_lert(self):
        """
        Dynamically remove an idle Lert from the simulation.
        If none is idle, do nothing or pick the first that will finish soon.
        """
        idle_lerts = [l for l in self.lerts if l.next_free_time <= self.current_time]
        if idle_lerts:
            lert_to_remove = idle_lerts[0]
            self.lerts.remove(lert_to_remove)
            print(f"Removed Lert #{lert_to_remove.id} at time {self.current_time:.2f}.")
        else:
            print("No idle Lert available to remove at this moment.")

    def set_request_rate(self, new_rate_per_minute):
        """
        Dynamically change the request rate (requests per minute).
        """
        global REQUEST_RATE
        REQUEST_RATE = new_rate_per_minute / 60.0
        print(f"Request rate set to {new_rate_per_minute} requests/min (i.e., {REQUEST_RATE:.2f} requests/sec).")

    def set_speed(self, new_speed_kmh):
        """
        Dynamically update the speed of all Lerts.
        """
        global LERT_SPEED, LERT_SPEED_KMH
        LERT_SPEED_KMH = new_speed_kmh
        LERT_SPEED = LERT_SPEED_KMH / 3600.0
        for l in self.lerts:
            l.speed = LERT_SPEED
        print(f"Lert speed set to {new_speed_kmh} km/h (i.e., {LERT_SPEED:.5f} km/s).")


# ------------------------------
#   RUN SIMULATION IN REAL TIME
# ------------------------------
def run_simulation_real_time(sim, real_time_duration=60):
    """
    Example loop that runs the simulation in real time for a specified 
    'real_time_duration' in seconds. 
    We step through the discrete events as they occur, but we 
    also apply a small sleep to make it feel 'game-like'.
    """
    start_wall_time = time.time()
    while True:
        current_wall_time = time.time()
        elapsed_wall_time = current_wall_time - start_wall_time
        if elapsed_wall_time >= real_time_duration:
            print("Real-time simulation ended.")
            break

        # Step the simulation if there is an event in the queue 
        # and the next event is not far in the future
        if sim.event_queue:
            # Peek next event time
            next_event_time, _, _ = sim.event_queue[0]
            if next_event_time <= sim.current_time:
                # This can happen if events are scheduled exactly at current_time
                sim.run_step()
            else:
                sim.run_step()
        else:
            # No events left - we can either break or keep spinning
            break

        # Print status periodically (e.g., every 1 second of real time)
        stats = sim.get_stats()
        print((
            f"[t={stats['time']:.2f}s] Completed: {stats['completed_requests']}, "
            f"Queue: {stats['queue_length']}, "
            f"Avg Wait: {stats['avg_wait_time']:.2f}s, "
            f"Avg Travel: {stats['avg_travel_time']:.2f}s"
        ))

        time.sleep(0.5)  # Sleep half a second to simulate a real-time "tick"


# ------------------------------
#   MAIN EXECUTION / EXAMPLE
# ------------------------------
if __name__ == "__main__":
    sim = MetroSimulation()

    # We can run the simulation in a background thread to allow dynamic user input
    simulation_thread = threading.Thread(
        target=run_simulation_real_time, 
        args=(sim, 60),   # run for 60 seconds in real-time
        daemon=True
    )
    simulation_thread.start()

    # Example of dynamic changes
    # You could imagine these calls being triggered by user inputs in a "game"
    time.sleep(10)  
    print("\n---> Adding a new Lert at 10s of real time.\n")
    sim.add_lert()
    
    time.sleep(15)
    print("\n---> Increasing request rate to 200/min at 25s of real time.\n")
    sim.set_request_rate(200)

    time.sleep(10)
    print("\n---> Removing an idle Lert at 35s of real time.\n")
    sim.remove_lert()

    # The simulation thread will stop after 60 seconds (real_time_duration).
    simulation_thread.join()

    # Final stats
    final_stats = sim.get_stats()
    print("\n--- Final Simulation Stats ---")
    print(f"Total Completed Requests: {final_stats['completed_requests']}")
    print(f"Average Waiting Time: {final_stats['avg_wait_time']:.2f} s")
    print(f"Average Travel Time: {final_stats['avg_travel_time']:.2f} s")
    print(f"Final Queue Length: {final_stats['queue_length']}")
