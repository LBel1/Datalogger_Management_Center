import os
import pandas as pd
import pathlib
from datetime import datetime
from collections import Counter

def plot_results(data, path):
    import matplotlib.pyplot as plt

    data[data.columns[0]] = pd.to_datetime(data[data.columns[0]])
    data[data.columns[1]] = pd.to_numeric(data[data.columns[1]])

    plt.figure(figsize=(10,5))
    plt.plot(data[data.columns[0]], data[data.columns[1]],marker='o',markersize=2,linestyle='-')
    plt.title(path.split("/")[-1].split(".png")[0])
    plt.xlabel("DateTime UTC")
    plt.ylabel(data.columns[1])
    plt.xticks([data.iloc[0,0], data.iloc[len(data)//2,0], data.iloc[-1,0]])
    plt.grid()
    plt.savefig(path)
    plt.close()

def format_date(data):
    # Get the year, month and day of the beginning and the end of measurement
    date_i = str(data["DateTime UTC"].iloc[0]).split(" ")[0]
    date_f = str(data["DateTime UTC"].iloc[-1]).split(" ")[0]

    # Initial
    Yi = str(date_i.split("-")[0])
    Mi = str(date_i.split("-")[1])
    Di = str(date_i.split("-")[2])

    # Final
    Yf = str(date_f.split("-")[0])
    Mf = str(date_f.split("-")[1])
    Df = str(date_f.split("-")[2])

    # Results string and conditions
    if(Yi != Yf):
        # Different years
        return f"{Yi}-{Yf}"
    elif(Mi != Mf):
        # Same year different months
        return f"{Yi}_{Mi}-{Mf}"
    elif(Di != Df):
        # Same year, same month but different days
        return f"{Yi}_{Mi}_{Di}-{Df}"
    else:
        # Same year, month and day
        return f"{Yi}_{Mi}_{Di}"

def format_hobo_data(filename):
    
    # Get the actual path
    filepath = os.getcwd()

    # Read the data
    data = pd.read_csv(f"{filepath}\{filename}",sep=",",skiprows=1,index_col=0)

    # ----------------- Section to check if it is an initialisation or not -----------------
    # Remove all the rows where the Hobo datalogger is getting initialised

    # List of the rows to remove
    id_remove = []

    # Remove the rows where "Enregistré" is present
    for i in range(1,len(data)):    
        for j in range(len(data.columns)):
            if(data.iloc[i,j] == "Enregistré"):
                id_remove.append(i+1)

    # Drop the rows
    data.drop(index=id_remove,inplace=True)

    # ----------------- Section to change the time to UTC -----------------
    # Change the datetime column to the right format
    time_header = data.columns[0]
    
    # Delay (timezone)
    delay = int(time_header.split("GMT")[-1].split(":")[0])
    
    data[time_header] = pd.to_datetime(data[time_header]) # It gives a warning but it understands the format so don't worry about it

    # Change the time of the column to UTC, works also if the time is GMT+X or GMT-X
    data[time_header] = data[time_header] - pd.Timedelta(hours=int(delay))
    data.rename(columns={time_header:"DateTime UTC"},inplace=True)

    # ----------------- Section to check if the timestep is consistent -----------------
    # Check the time difference between each row
    diff = data["DateTime UTC"].diff()
    
    # Create the stats for timesteps
    stats_dt = Counter(sorted(diff.to_list()))
    
    # Use the most common timestep as timestep for data completion
    dt = pd.to_timedelta(stats_dt.most_common(1)[0][0])

    # Check if an approximately continuous datetime can be reconstructed or not
    # If yes, we try to fill in the gaps with holes in the dataset as following :

    if stats_dt.most_common(1)[0][1] > len(data) * 0.5:
        # List of all the inconsistent steps
        inconsistent_steps = diff[diff != dt]
        nb_line_added = 0

        # If the time missing is greater than the timestep, we fill artificially the missing times without any data (yes it creates holes in the dataset)
        for i in inconsistent_steps.index:
            missing_time = (inconsistent_steps[i] // dt)
            if(missing_time >= 2):
                
                # Create the new rows
                new_rows = []
                for j in range(1,missing_time):
                    new_time = pd.to_datetime(data["DateTime UTC"].iloc[i+nb_line_added-1]) + j * dt
                    new_row = {"DateTime UTC":new_time}
                    for col in data.columns[1:]:
                        new_row[col] = None
                    new_rows.append(new_row)
                
                # Insert the new rows into the dataframe
                upper_part = data.iloc[:i+nb_line_added]
                lower_part = data.iloc[i+nb_line_added:]
                data = pd.concat([upper_part,pd.DataFrame(new_rows),lower_part],ignore_index=True)
                
                # To ensure that the new indices does not interfere with the next insertions
                nb_line_added += len(new_rows)
    # else : we leave the datetime as it is !

    # ----------------- Section for the folders creation -----------------

    # Get the date string
    date = format_date(data)

    # Create the folder for the output if it does not exist
    pathlib.Path(f"../../FORMATED_DATA/Temperature").mkdir(parents=True, exist_ok=True)
    pathlib.Path(f"../../CLEANED_DATA/Temperature").mkdir(parents=True, exist_ok=True)

    # Check the unit of measurement and create the corresponding output file
    # This variable is here to separate the different temperatures measured
    n_temp = 0

    for i in data.columns:
        if("temp" in i.lower()):
            # Get the unit of temperature
            unit = i.split(" ")[1]
            
            if(unit == "°C"):
                results = data[["DateTime UTC",i]]
            elif(unit == "°F"):
                # Convert to Celsius
                data[i] = round((data[i] - 32.0) * 5.0/9.0,2)
                results = data[["DateTime UTC",i]]
            elif(unit == "K"):
                # Convert to Celsius
                data[i] = round(data[i] - 273.15,2)
                results = data[["DateTime UTC",i]]
            # Rename the columns and save it in a new csv file
            results.columns = ["DateTime UTC","Temperature (°C)"]
            results.to_csv(f"../../FORMATED_DATA/Temperature/{filename.split('.csv')[0]}_Temperature{n_temp}_{date}.csv",index=False)
            plot_results(results, f"../../FORMATED_DATA/Temperature/{filename.split('.csv')[0]}_Temperature{n_temp}_{date}.png")
            n_temp += 1

# Test section
# format_hobo_data("210121_10935617.csv")

# Read all the csv files in the actual directory
for file in os.listdir(path="."):
    if file.endswith(".csv"):
        print("Reading file : ", os.path.join(os.getcwd(), file))
        format_hobo_data(file)