import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gamma, norm

# Generate x values (time of day in hours)
x = np.linspace(0, 24, 1000)

# Model parameters for different phases of the day
morning_peak = norm.pdf(x, 9, 0.8)  # Sharp peak at 9 AM
midday_decline = norm.pdf(x, 11, 1.5)  # Gradual decline after 11 AM

afternoon_rise = norm.pdf(x, 16, 1.2)  # Gradual rise around 4 PM
evening_drop = norm.pdf(x, 19, 0.9)  # Steep drop after 7 PM

night_low = gamma.pdf(x, 2, scale=3) * 0.1  # Low distribution from 1 AM to 4 AM

# Combine the distributions with appropriate weights
pdf_combined = (
    1.5 * morning_peak +
    0.8 * midday_decline +
    1.2 * afternoon_rise +
    1.3 * evening_drop +
    night_low
)

pdf_combined /= np.trapz(pdf_combined, x)  # Normalize the combined distribution

# Simulate the number of people per hour
total_people = 30000
hourly_people = np.histogram(
    np.random.choice(x, total_people, p=pdf_combined / pdf_combined.sum()),
    bins=24, range=(0, 24)
)[0]

# Print the number of people per hour
for hour in range(24):
    print(f"Hour {hour}: {hourly_people[hour]} people")

# Plotting
plt.figure(figsize=(12, 7))
plt.plot(x, pdf_combined, label="Simulated Traffic Model (Rush Hour)")
plt.bar(np.arange(24), hourly_people, width=0.8, alpha=0.5, label="Simulated Hourly People")
plt.xlabel("Time of Day (Hours)")
plt.ylabel("Passenger Flow / Hour")
plt.title("Delhi Metro Traffic Simulation (30,000 People)")
plt.xticks(np.arange(0, 25, 1))
plt.legend()
plt.grid(True)
plt.show()
