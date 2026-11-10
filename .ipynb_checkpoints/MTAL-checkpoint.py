#MTAL --> Membrane test automatic loop
#This one autosets the y axis 
# Needs to run pip instll pyabf

import os
import tkinter as tk
from tkinter import filedialog
import pyabf
import numpy as np
import matplotlib.pyplot as plt

# ------------------------------- file selection dialog ---------------------------------
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)  # Brings the file picker window to the front

file_path = filedialog.askopenfilename(
    title="Select ABF Membrane Test File",
    filetypes=[("ABF files", "*.abf"), ("All files", "*.*")]
)

if not file_path:
    raise ValueError("No file selected. Please re-run the script and choose an ABF file.")

data_dir = os.path.dirname(file_path)
abf_file_name = os.path.basename(file_path)

# Set the working directory to the data file's folder
os.chdir(data_dir)
print(f"Loaded file: {abf_file_name}\nWorking directory set to: {data_dir}")

# Load the data from the ABF file
abf = pyabf.ABF(abf_file_name)

# Set the sweep
abf.setSweep(1)

while True: ##Looping

    # Prompt user for the stimulus number to analyze
    stim_num = int(input("Enter stimulus number (1-4): "))

    # Set stim_start and x-axis limits based on user input
    if stim_num == 1:
        stim_start = 0.117
        x_limits = [0, 1]
    elif stim_num == 2:
        stim_start = 1.138
        x_limits = [1, 2]
    elif stim_num == 3:
        stim_start = 2.158
        x_limits = [2, 3]
    else:
        stim_start = 3.178
        x_limits = [3, 4]

    # Measure the membrane resistance from the trace
    current_amplitude = 1  # nA
    stim_duration = 0.4 # s
    stim_end = stim_start + stim_duration
    sampling_rate = abf.dataRate  # Hz
    capacitance = 0.003 # uF, this is based on Bing Zhang's paper, where 30 msec. tau gives 10 MOhm membrane resistance. Most cells actually have a capacitance around 1 uF, so this is very low

    # Get the trace data during the stimulus period
    sweepX = abf.sweepX
    stim_data = abf.sweepY[(sweepX >= stim_start) & (sweepX < stim_end)]

    # Calculate the peak voltage from only the last 0.05 seconds of the stimulus period
    peak_voltage = np.max(stim_data[-int(sampling_rate*0.05):])

    # Calculate the threshold voltage and the time constant
    threshold_voltage = stim_data[0] + 0.37*(peak_voltage - stim_data[0])
    stim_end_index = np.where(sweepX >= stim_end)[0][0]  # index of the end of the stimulus period
    threshold_index = np.argmax(abf.sweepY[stim_end_index+1:] <= threshold_voltage)  # index of the first occurrence of threshold_voltage after the stimulus period
    time_constant = (threshold_index + 1) / sampling_rate  # add 1 to account for the slice indexing

    # Calculate the membrane resistance
    membrane_resistance = time_constant / capacitance

    # Calculate RMP (average voltage before stimulus)
    rmp = np.mean(abf.sweepY[(sweepX >= stim_start - 0.1) & (sweepX < stim_start)])
    
    # Print the frequency and membrane resistance
    print("Membrane resistance: {:.2f} MOhm".format(membrane_resistance))

    # Get the trace data during the stimulus period
    stim_mask = (sweepX >= stim_start) & (sweepX < stim_end)
    stim_data = abf.sweepY[stim_mask]

    # Print the time range of the stimulus period
    stim_start_time = sweepX[stim_mask][0]
    stim_end_time = sweepX[stim_mask][-1]
    print("Stimulus period: {:.3f} to {:.3f} s".format(stim_start_time, stim_end_time))

    # Print parameters
    print("Peak voltage: {:.2f} mV".format(peak_voltage))
    print("Threshold voltage: {:.2f} mV".format(threshold_voltage))
    print("Time constant: {:.2f} msec.".format(time_constant * 1000))
    print("RMP: {:.2f} mV".format(rmp))

    # Get the minimum and maximum values of the data
    y_min = abf.sweepY[np.argmin(np.abs(sweepX - 0.01))]
    y_max = peak_voltage

    # Calculate the minimum and maximum y-values to display
    y_min_display = round((y_min - 2.5) / 5) * 5
    y_max_display = round((y_max + 5) / 5) * 5

    # Create a new figure with a larger size
    fig, ax = plt.subplots(figsize=(14, 9))

    # Plot the stimulus data
    ax.set_xlim(x_limits[0], x_limits[1])
    ax.set_ylim(y_min_display, y_max_display)
    ax.plot(sweepX, abf.sweepY)
    ax.axvspan(stim_start, stim_end, alpha=0.5, color="gray")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Membrane potential (mV)")

    # Add horizontal and vertical lines
    ax.axhline(y=threshold_voltage, linestyle='--', color='red')
    ax.axvline(x=sweepX[stim_end_index+threshold_index+1], linestyle='--', color='green')
    
    # Show the plot
    plt.show()
    
    # Ask user if they want to save the image
    save_image = input("Do you want to save this image? (y/n): ").lower()
    if save_image == 'y': 
        # Save the plot with a filename based on the ABF file name and the time frame analyzed
        abf_file_base_name = os.path.splitext(os.path.basename(abf_file_name))[0]
        plot_file_name = "{}_stim{}.png".format(abf_file_base_name, stim_num)
        fig.savefig(plot_file_name)
        print(f"Image saved as {plot_file_name}")
    else:
        print("Image not saved.")
    
    # Close the figure to free up memory
    plt.close(fig)
        
    #Looping
    repeat = input('Do you want to plot another range? (y/n): ').lower()
    if repeat != 'y':
        break  # exit the loop if the user enters anything other than 'yes'