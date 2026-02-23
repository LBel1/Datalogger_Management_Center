import os
import pandas as pd
import pathlib
from collections import Counter

def plot_results(data, path):
    import matplotlib.pyplot as plt

    print(data)
    data["DateTime UTC"] = pd.to_datetime(data["DateTime UTC"])
    data[data.columns[1]] = pd.to_numeric(data[data.columns[1]])

    plt.figure(figsize=(10,5))
    plt.plot(data["DateTime UTC"], data[data.columns[1]],marker='o',markersize=2,linestyle='-')
    plt.title(path.split("/")[-1].split(".png")[0])
    plt.xlabel("DateTime UTC")
    plt.ylabel(data.columns[1])
    plt.xticks([data.iloc[0,0], data.iloc[len(data)//2,0], data.iloc[-1,0]])
    plt.grid()
    plt.savefig(path)
    plt.close()

def format_date(data):
    # Starting and ending year
    Yinit = str(data["DateTime UTC"].iloc[0]).split("-")[0]
    Yfin = str(data["DateTime UTC"].iloc[-1]).split("-")[0]

    # Starting month and ending month
    Minit = str(data["DateTime UTC"].iloc[0]).split("-")[1]
    Mfin = str(data["DateTime UTC"].iloc[-1]).split("-")[1]

    # Starting and ending day
    Dinit = str(data["DateTime UTC"].iloc[0]).split("-")[2]
    Dfin = str(data["DateTime UTC"].iloc[-1]).split("-")[2]

    # Conditions
    if(Yinit != Yfin):
        # Different years
        return f"{Yinit}-{Yfin}"
    elif(Minit != Mfin):
        # Same year but different months
        return f"{Yinit}_{Minit}-{Mfin}"
    elif(Dinit != Dfin):
        # Same year, same month but different days
        return f"{Yinit}_{Minit}_{Dinit}-{Dfin}"
    else:
        return f"{Yinit}_{Minit}_{Dinit}"

def format_keller_data(filename):
    # Get the actual path
    filepath = os.getcwd()

    # datalogger's name
    dname = filepath.split("\\")[-1]

    # Read the data
    if filename.endswith(".xlsx"):
        data = pd.read_excel(f"{filepath}\{filename}",skiprows=9,index_col=0)
    
    elif filename.endswith(".xls") or filename.endswith(".XLS"):
        data = pd.read_excel(f"{filepath}\{filename}",skiprows=8,index_col=0)
        
        data["DateTime UTC"] = pd.to_datetime(data["Date"].astype(str) + " " + data["Time"].astype(str),format="%d.%m.%Y %H:%M:%S")
        data.drop(columns=["Date", "Time"], inplace=True)

        data = data[["DateTime UTC"] + [col for col in data.columns if col != "DateTime UTC"]]

    # Rename the datetime column to a specific name
    data.rename(columns={"Datetime _x000d_\n[UTC]":"DateTime UTC"}, inplace=True)

    # Create the DateTime column
    date = pd.to_datetime(data["DateTime UTC"])

    # ------------------ Section to check the timestep consistency -----------------

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

        # If the time missing is greater than 2 times the timestep, we fill artificially the missing times without any data (yes it creates holes in the dataset)
        for i in inconsistent_steps.index:
            missing_time = (inconsistent_steps[i] // dt)
            if(missing_time > 2):
                
                # Create the new rows
                new_rows = []
                for j in range(1,missing_time+1):
                    new_time = pd.to_datetime(data["DateTime UTC"].iloc[i+nb_line_added-1]) + j * dt
                    new_row = {"DateTime UTC":new_time}
                    for col in data.columns[:-2]:
                        new_row[col] = None
                    new_rows.append(new_row)

                # Insert the new rows into the dataframe
                upper_part = data.iloc[:i+nb_line_added]
                lower_part = data.iloc[i+nb_line_added:]
                data = pd.concat([upper_part,pd.DataFrame(new_rows),lower_part],ignore_index=True)

                # To ensure that the new indices does not interfere with the next insertions
                nb_line_added += len(new_rows)
    # else : we leave the datetime as it is !

    # Create the output dataframe
    output_data = pd.DataFrame()

    # Create the output folders if they do not exist
    pathlib.Path(f"../../FORMATED_DATA/Pression").mkdir(parents=True, exist_ok=True)
    pathlib.Path(f"../../CLEANED_DATA/Pression").mkdir(parents=True, exist_ok=True)

    pathlib.Path(f"../../FORMATED_DATA/Temperature").mkdir(parents=True, exist_ok=True)
    pathlib.Path(f"../../CLEANED_DATA/Temperature").mkdir(parents=True, exist_ok=True)

    # Create the output files for each sensor
    for i in data.columns[2:]: # Skip the n° and datetime columns (local and UTC)

        # Create an output dataframe for each sensor
        header_str = i.split("_x000d_\n")[0].strip()

        output_data = pd.concat([date, data[i]],axis=1)
        output_data.rename(columns={i:header_str}, inplace=True)

        if "P" in header_str:
            # Pressure data
            output_data.to_csv(f"../../FORMATED_DATA/Pression/{dname}_{header_str}_{format_date(output_data)}.csv", index=False)
            plot_results(output_data, f"../../FORMATED_DATA/Pression/{dname}_{header_str}_{format_date(output_data)}.png")
        elif "T" in header_str:
            # Temperature data
            output_data.to_csv(f"../../FORMATED_DATA/Temperature/{dname}_{header_str}_{format_date(output_data)}.csv", index=False)
            plot_results(output_data, f"../../FORMATED_DATA/Temperature/{dname}_{header_str}_{format_date(output_data)}.png")

# Test section
# format_keller_data("210818_Keller_Saivu_04_06_2021-06_51_22.XLS")

# Read all the csv files in the actual directory
for file in os.listdir(path="."):
    if file.endswith(".xlsx") or file.endswith(".xls"):
        print("Reading file : ", file)
        format_keller_data(file)