import os
import pandas as pd
import pathlib

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
    # Starting and ending year
    Yinit = str(data["Year"].iloc[0])
    Yfin = str(data["Year"].iloc[-1])

    # Starting month and ending month
    Minit = str(data["Month"].iloc[0])
    Mfin = str(data["Month"].iloc[-1])

    # Starting and ending day
    Dinit = str(data["Day"].iloc[0])
    Dfin = str(data["Day"].iloc[-1])

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

def format_reefnet_data(filename):
    # Get the actual path
    filepath = os.getcwd()

    # Read the data
    data = pd.read_csv(f"{filepath}\{filename}",sep=",",header=None)

    # Add headers
    if(data.shape[1] == 12):
        data.columns = ["ID","SerialNumber","NotUsed","Year","Month","Day","Hour","Minute","Second","Time","Pression (mbar)","Temperature (K)"]
    elif(data.shape[1] == 13):
        data.columns = ["ID","SerialNumber","NotUsed","Year","Month","Day","Hour","Minute","Second","Time","Pression (mbar)","Temperature (K)","T_decimal (K)"]
        data["Temperature (K)"] = data['Temperature (K)']+data['T_decimal (K)']/100
        data.drop(columns=["T_decimal (K)"],inplace=True)
    else:
        return KeyError("The number of columns in the file is not coherent with other Reefnet sensors.")        

    # Get all the necessary string for the output filenames
    date = format_date(data)

    # Change the temperature from Kelvin to Celsius
    data["Temperature (K)"] = round(data["Temperature (K)"] - 273.15,2)
    data.rename(columns={"Temperature (K)": "Temperature (°C)"}, inplace=True)

    # Create the DateTime column
    TimeDate = pd.Timestamp(year=int(data["Year"][0]), month=int(data["Month"][0]), day=int(data["Day"][0]), hour=int(data["Hour"][0])-1, minute=int(data["Minute"][0]), second=int(data["Second"][0])) # Remove one hour to go from UTC+1 to UTC
    dt = pd.to_timedelta(data["Time"][1]-data["Time"][0], unit='s')

    data["DateTime UTC"] = TimeDate + pd.to_timedelta(data["Time"], unit='s')

    # ------------------ Section to check the timestep consistency -----------------

    # Check the time difference between each row
    diff = data["DateTime UTC"].diff()

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

    # ------------------ Section to create the output files -----------------

    # Create the "formatés" folder with the corresponding subfolder
    pathlib.Path(f"../../FORMATED_DATA/Pression").mkdir(parents=True, exist_ok=True)
    pathlib.Path(f"../../CLEANED_DATA/Pression").mkdir(parents=True, exist_ok=True)
    pathlib.Path(f"../../FORMATED_DATA/Temperature").mkdir(parents=True, exist_ok=True)
    pathlib.Path(f"../../CLEANED_DATA/Temperature").mkdir(parents=True, exist_ok=True)

    # Create the output results dataframe
    Presults = data[["DateTime UTC","Pression (mbar)"]]
    Tresults = data[["DateTime UTC","Temperature (°C)"]]
    
    Presults.to_csv(f"../../FORMATED_DATA/Pression/{filename.split('.csv')[0]}_Pression_{date}.csv",index=False)
    plot_results(Presults, f"../../FORMATED_DATA/Pression/{filename.split('.csv')[0]}_Pression_{date}.png")

    Tresults.to_csv(f"../../FORMATED_DATA/Temperature/{filename.split('.csv')[0]}_Temperature_{date}.csv",index=False)
    plot_results(Tresults, f"../../FORMATED_DATA/Temperature/{filename.split('.csv')[0]}_Temperature_{date}.png")

# Read all the csv files in the actual directory
for file in os.listdir(path="."):
    if file.endswith('.csv'):
        print("Reading file : ", os.path.join(os.getcwd(), file))
        format_reefnet_data(file)