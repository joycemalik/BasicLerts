import matplotlib.pyplot as plt
import numpy as np
import random

# Simulation parameters
zone_radius = 10
num_rickshaws = 5
num_initial_requests = 10
rickshaw_speed = 0.5

# Central metro station coordinates
metro_station = (0, 0)


# Helper function to generate random points inside a circle
def random_point_in_circle(radius):
    angle = random.uniform(0, 2 * np.pi)
    r = radius * np.sqrt(random.uniform(0, 1))
    return r * np.cos(angle), r * np.sin(angle)


# Initialize rickshaws with random positions inside the circle
rickshaws = [{"pos": random_point_in_circle(zone_radius), "status": "free", "target": None}
             for _ in range(num_rickshaws)]

# Generate initial requests inside the circle
requests = [{"pickup": random_point_in_circle(zone_radius), "dropoff": metro_station, "type": "to_metro"}
            for _ in range(num_initial_requests)]


# Function to generate new requests dynamically
def generate_request():
    if random.random() < 0.5:  # Type 1: To Metro Station
        pickup = random_point_in_circle(zone_radius)
        dropoff = metro_station
        req_type = "to_metro"
    else:  # Type 2: From Metro Station
        pickup = metro_station
        dropoff = random_point_in_circle(zone_radius)
        req_type = "from_metro"
    return {"pickup": pickup, "dropoff": dropoff, "type": req_type}


# Function to calculate distance
def distance(a, b):
    return np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


# Function to move rickshaws towards their targets
def move_towards(current, target, speed):
    dist = distance(current, target)
    if dist <= speed:
        return target
    else:
        dx, dy = target[0] - current[0], target[1] - current[1]
        scale = speed / dist
        return current[0] + dx * scale, current[1] + dy * scale


# Simulation loop
plt.ion()
fig, ax = plt.subplots(figsize=(8, 8))

for step in range(1000):  # Number of simulation steps
    # Assign free rickshaws to requests
    for rickshaw in rickshaws:
        if rickshaw["status"] == "free" and requests:
            nearest_request = min(requests, key=lambda req: distance(rickshaw["pos"], req["pickup"]))
            rickshaw["status"] = "to_pickup"
            rickshaw["target"] = nearest_request
            requests.remove(nearest_request)

    # Update rickshaw positions
    for rickshaw in rickshaws:
        if rickshaw["status"] in ["to_pickup", "to_dropoff"]:
            target = rickshaw["target"]["pickup"] if rickshaw["status"] == "to_pickup" else rickshaw["target"][
                "dropoff"]
            rickshaw["pos"] = move_towards(rickshaw["pos"], target, rickshaw_speed)

            # Check if target is reached
            if rickshaw["pos"] == target:
                if rickshaw["status"] == "to_pickup":
                    rickshaw["status"] = "to_dropoff"
                else:
                    rickshaw["status"] = "free"
                    rickshaw["target"] = None

    # Generate new requests dynamically
    if random.random() < 0.2:  # 20% chance to generate a new request at each step
        requests.append(generate_request())

    # Visualization
    ax.clear()
    ax.set_xlim(-zone_radius - 1, zone_radius + 1)
    ax.set_ylim(-zone_radius - 1, zone_radius + 1)
    ax.add_artist(plt.Circle((0, 0), zone_radius, color="blue", fill=False, linestyle="--"))

    # Plot metro station
    ax.plot(*metro_station, "bo", markersize=10, label="Metro Station")

    # Plot requests
    for req in requests:
        ax.plot(*req["pickup"], "go" if req["type"] == "to_metro" else "yo", markersize=8)

    # Plot rickshaws with different colors based on status
    for rickshaw in rickshaws:
        if rickshaw["status"] == "free":
            ax.plot(*rickshaw["pos"], "go", markersize=6)  # Green for free
        elif rickshaw["status"] == "to_pickup":
            ax.plot(*rickshaw["pos"], "bo", markersize=6)  # Blue for en route to pickup
        elif rickshaw["status"] == "to_dropoff":
            ax.plot(*rickshaw["pos"], "ro", markersize=6)  # Red for en route to dropoff

    # Display stats
    num_free = sum(1 for rickshaw in rickshaws if rickshaw["status"] == "free")
    num_active = sum(1 for rickshaw in rickshaws if rickshaw["status"] != "free")
    num_requests = len(requests)

    ax.text(0.02, 0.98, f"Requests: {num_requests}", transform=ax.transAxes, fontsize=12, verticalalignment='top')
    ax.text(0.02, 0.94, f"Active Rickshaws: {num_active}", transform=ax.transAxes, fontsize=12, verticalalignment='top')
    ax.text(0.02, 0.90, f"Free Rickshaws: {num_free}", transform=ax.transAxes, fontsize=12, verticalalignment='top')

    ax.legend(loc="upper left")
    ax.set_title(f"Step {step + 1}")
    plt.pause(0.1)

plt.ioff()
plt.show()