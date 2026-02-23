import os
import pandas as pd
import pathlib
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
    
def remove_extra_titles(data):
    # Find the indices where the headers are repeated
    indices = data.index[data["DateTime"] == "DateTime"].tolist()

    # Remove those rows
    data = data.drop(indices)

    data["DateTime"] = pd.to_datetime(data["DateTime"])

    return data.reset_index(drop=True)

def format_date(data):
    # Years
    Yi = str(data["DateTime"].iloc[0]).split(" ")[0].split("-")[2]
    Yf = str(data["DateTime"].iloc[-1]).split(" ")[0].split("-")[2]

    # Months
    Mi = str(data["DateTime"].iloc[0]).split(" ")[0].split("-")[1]
    Mf = str(data["DateTime"].iloc[-1]).split(" ")[0].split("-")[1]

    # Days
    Di = str(data["DateTime"].iloc[0]).split(" ")[0].split("-")[0]
    Df = str(data["DateTime"].iloc[-1]).split(" ")[0].split("-")[0]

    # Conditions
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
        # Same everything
        return f"{Yi}_{Mi}_{Di}"

def format_tinypico_data(filename):
    # Get the actual path
    filepath = os.getcwd()

    # datalogger's name
    dname = filepath.split("\\")[-1]

    # Foldername to create the appropriate folders
    output_filename = filename.split(".csv")[0]

    try:
        if filename.split(".")[-1] == "csv":
            # Read csv files
            data = pd.read_csv(f"{filepath}\{filename}",sep=";",index_col=0)
        elif filename.split(".")[-1] == "xlsx" or filename.split(".")[-1] == "xls":
            # Read excel files
            data = pd.read_excel(f"{filepath}\{filename}",engine="openpyxl")
        else:
            return
    except Exception as e:
        print(f"Error while reading file {filename} : {e}")

    # Remove the rows where the headers are repeated and the empty rows
    data.dropna(axis=0,how="any",inplace=True)
    data = remove_extra_titles(data)

    # Date for the output filename
    date = format_date(data)

    # Rename the first column to "DateTime UTC"
    data.rename(columns={"DateTime":"DateTime UTC"},inplace=True)
    
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
    
    for i in data.columns[1:]:
        if "temp" in i.lower():
            results = data[["DateTime UTC",i]]
            results.columns = ["DateTime UTC","Temperature (°C)"]

            # To tell the difference temperatures between files
            tmp_str = i.lower().split("temp")[1]

            # Create the new files to insert in the new folder "FORMATTED_DATA"
            pathlib.Path(f"../../FORMATED_DATA/Temperature").mkdir(parents=True, exist_ok=True)
            pathlib.Path(f"../../CLEANED_DATA/Temperature").mkdir(parents=True, exist_ok=True)

            results.to_csv(f"../../FORMATED_DATA/Temperature/{dname}_Temp{tmp_str}_{date}.csv",index=False)
            plot_results(results,f"../../FORMATED_DATA/Temperature/{dname}_Temp{tmp_str}_{date}.png")

        elif "press" in i.lower():
            results = data[["DateTime UTC",i]]
            results.columns = ["DateTime UTC","Pression (mbar)"]

            # To tell the difference pressures between files
            tmp_str = i.lower().split("press")[1]

            # Create the folder only if pressure is measured
            pathlib.Path(f"../../FORMATED_DATA/Pression").mkdir(parents=True, exist_ok=True)
            pathlib.Path(f"../../CLEANED_DATA/Pression").mkdir(parents=True, exist_ok=True)

            results.to_csv(f"../../FORMATED_DATA/Pression/{dname}_Press.{tmp_str}_{date}.csv",index=False)
            plot_results(results,f"../../FORMATED_DATA/Pression/{dname}_Press.{tmp_str}_{date}.png")
        
        elif "hum" in i.lower():
            results = data[["DateTime UTC",i]]
            results.columns = ["DateTime UTC","Humidité (%)"]

            # Create the folder only if humidity is measured
            pathlib.Path(f"../../FORMATED_DATA/Humidité").mkdir(parents=True, exist_ok=True)
            pathlib.Path(f"../../CLEANED_DATA/Humidité").mkdir(parents=True, exist_ok=True)

            results.to_csv(f"../../FORMATED_DATA/Humidité/{dname}_Hum_{date}.csv",index=False)
            plot_results(results,f"../../FORMATED_DATA/Humidité/{dname}_Hum_{date}.png")

        elif i.startswith("v"):
            results = data[["DateTime UTC",i]]
            results.columns = ["DateTime UTC","Vitesse (m/s)"]

            # To tell the difference humidities between files
            tmp_str = i.lower().split("v")[1]

            # Create the folder only if humidity is measured
            pathlib.Path(f"../../FORMATED_DATA/Vitesse").mkdir(parents=True, exist_ok=True)
            pathlib.Path(f"../../CLEANED_DATA/Vitesse").mkdir(parents=True, exist_ok=True)

            results.to_csv(f"../../FORMATED_DATA/Vitesse/{dname}_v{tmp_str}_{date}.csv",index=False)
            plot_results(results,f"../../FORMATED_DATA/Vitesse/{dname}_v{tmp_str}_{date}.png")

        elif i.startswith("q"):
            results = data[["DateTime UTC",i]]
            results.columns = ["DateTime UTC","Débit (L/min)"]

            # To tell the difference humidities between files
            tmp_str = i.lower().split("q")[1]

            # Create the folder only if humidity is measured
            pathlib.Path(f"../../FORMATED_DATA/Débit").mkdir(parents=True, exist_ok=True)
            pathlib.Path(f"../../CLEANED_DATA/Débit").mkdir(parents=True, exist_ok=True)

            results.to_csv(f"../../FORMATED_DATA/Débit/{dname}_q{tmp_str}_{date}.csv",index=False)
            plot_results(results,f"../../FORMATED_DATA/Débit/{dname}_q{tmp_str}_{date}.png")
        elif "waterlevel" in i.lower():
            results = data[["DateTime UTC",i]]
            results.columns = ["DateTime UTC","Hauteur d'eau (cm)"]

            # To tell the difference humidities between files
            tmp_str = i.lower().split("waterlevel")[1]

            # Create the folder only if humidity is measured
            pathlib.Path(f"../../FORMATED_DATA/Hauteur_eau").mkdir(parents=True, exist_ok=True)
            pathlib.Path(f"../../CLEANED_DATA/Hauteur_eau").mkdir(parents=True, exist_ok=True)

            results.to_csv(f"../../FORMATED_DATA/Hauteur_eau/{dname}_Waterlevel{tmp_str}_{date}.csv",index=False)
            plot_results(results,f"../../FORMATED_DATA/Hauteur_eau/{dname}_Waterlevel{tmp_str}_{date}.png")
        
        else:
            print(f"Unknown column {i} in file {filename}")

# Test section
# format_tinypico_data("TinyPico_test.csv")

# Read all the csv files in the actual directory
for file in os.listdir(path="."):
    print("Reading file : ", file)
    format_tinypico_data(file)