import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gamma

# Parameters for the two gamma distributions (morning and evening peaks)
k1, theta1 = 4, 0.5  # Morning peak (sharp)
k2, theta2 = 6, 1    # Evening peak (broader)
k3, theta3 = 3, 2    # Base level distribution for hours 0 to 8

# Mixing proportions
p1, p2, p3 = 0.4, 0.4, 0.2  # Lower weight for early morning

# Generate x values (time of day in hours)
x = np.linspace(0, 24, 1000)

# Calculate the bi-modal gamma distribution
pdf1 = gamma.pdf(x - 8, k1, scale=theta1)  # Morning peak at 8 to 10
pdf2 = gamma.pdf(x - 16, k2, scale=theta2)  # Evening peak at 16 to 19
pdf3 = gamma.pdf(x, k3, scale=theta3)       # Base level for early hours

# Combine the three gamma distributions
pdf_combined = p1 * pdf1 + p2 * pdf2 + p3 * pdf3
pdf_combined /= np.trapz(pdf_combined, x)  # Normalize to make it a valid distribution

# Simulate the number of people per hour
total_people = 30000
hourly_people = np.histogram(np.random.choice(x, total_people, p=pdf_combined / pdf_combined.sum()), bins=24, range=(0, 24))[0]

# Print the number of people per hour
for hour in range(24):
    print(f"Hour {hour}: {hourly_people[hour]} people")

# Plotting
plt.figure(figsize=(12, 7))
plt.plot(x, pdf_combined, label="Bi-modal Gamma Distribution (Rush Hour)")
plt.bar(np.arange(24), hourly_people, width=0.8, alpha=0.5, label="Simulated Hourly People")
plt.xlabel("Time of Day (Hours)")
plt.ylabel("Passenger Flow / Hour")
plt.title("Delhi Metro Rush Hour Simulation (30,000 People)")
plt.xticks(np.arange(0, 25, 1))
plt.legend()
plt.grid(True)
plt.show()
