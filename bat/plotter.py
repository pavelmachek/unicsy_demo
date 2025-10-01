#!/usr/bin/env python3
import matplotlib.pyplot as plt

# Lists to store values
utime = []
voltage = []
current = []
percent = []

# Parse file line by line
with open("data.txt") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        # Split by spaces, then by '='
        data = dict(item.split('=') for item in line.split())
        utime.append(int(data['utime']))
        voltage.append(float(data['voltage']))
        current.append(float(data['current']))
        percent.append(float(data['percent']))

# Plot
fig, ax1 = plt.subplots(figsize=(8,4))

ax1.plot(utime, voltage, label='Voltage (V)', color='blue')
ax1.plot(utime, current, label='Current (A)', color='red')
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Voltage / Current')
ax1.legend(loc='upper left')

ax2 = ax1.twinx()
ax2.plot(utime, percent, label='Percent (%)', color='green', linestyle='--')
ax2.set_ylabel('Percentage')
ax2.legend(loc='upper right')

plt.title("Voltage, Current, and Percent Over Time")
plt.show()
