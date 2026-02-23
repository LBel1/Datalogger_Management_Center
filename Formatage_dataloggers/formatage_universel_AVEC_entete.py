import os
import pandas as pd
import pathlib
import csv

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
    # Years
    Yi = str(data["DateTime UTC"].iloc[0]).split(" ")[0].split("-")[0]
    Yf = str(data["DateTime UTC"].iloc[-1]).split(" ")[0].split("-")[0]

    # Months
    Mi = str(data["DateTime UTC"].iloc[0]).split(" ")[0].split("-")[1]
    Mf = str(data["DateTime UTC"].iloc[-1]).split(" ")[0].split("-")[1]

    # Days
    Di = str(data["DateTime UTC"].iloc[0]).split(" ")[0].split("-")[2]
    Df = str(data["DateTime UTC"].iloc[-1]).split(" ")[0].split("-")[2]

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

def format_data(file):

    if pathlib.Path(file).suffix == ".csv":
        with open(file,newline='', encoding='utf-8') as f:
            # Check the delimiter of the csv file
            dialect = csv.Sniffer().sniff(f.read(1024))
            f.seek(0)
            data = pd.read_csv(f, delimiter=dialect.delimiter)
    elif pathlib.Path(file).suffix == ".xlsx":
        # Read the excel file
        data = pd.read_excel(file)
    else:
        print(f"Unsupported file format: {file}")
        return

    # Find the columns with the date information
    date_column = [col for col in data.columns if "date" in col.lower()]
    
    if date_column:
        # Check the file if the date format is YYYY/MM/DD,hh:mm:ss
        if "," in data[date_column[0]].iloc[0]:
            data[date_column[0]] = data[date_column[0]].str.replace(",", " ")

        # Convert the date column to datetime format
        data[date_column[0]] = pd.to_datetime(data[date_column[0]], format="%Y/%m/%d %H:%M:%S")
        data.rename(columns={date_column[0]:"DateTime UTC"}, inplace=True)

    # ------------------ Section to check the timestep consistency -----------------

    # Check the time difference between each row
    diff = data["DateTime UTC"].diff()
    dt = pd.to_timedelta(data["DateTime UTC"].iloc[1] - data["DateTime UTC"].iloc[0])

    # List of all the inconsistent steps
    inconsistent_steps = diff[diff != dt]
    nb_line_added = 0

    # If the time missing is greater than the timestep, we fill artificially the missing times without any data (yes it creates holes in the dataset)
    for i in inconsistent_steps.index:
        missing_time = (inconsistent_steps[i] // dt) # Number of missing dt
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

    # Create the FORMATTED and CLEANED directories if they don't exist
    pathlib.Path(f"../../FORMATTED_DATA").mkdir(parents=True, exist_ok=True)
    pathlib.Path(f"../../CLEANED_DATA").mkdir(parents=True, exist_ok=True)

    for i in data.columns:
        # Output dataframe
        results = pd.DataFrame()

        # Check the headers. If egal to date column, we skip
        if (i == "DateTime UTC"):
            continue
        else:
            # Create the output dataframe
            results = pd.DataFrame({"DateTime UTC": data["DateTime UTC"], i: data[i]})
            # Save the output in the right directory
            if "temp" in i.lower():
                # Create the output filename for the dataset
                output_filename = f"../../FORMATTED_DATA/Temperature/{file.split('.')[0].split('/')[-1]}_{format_date(data)}.csv"
                
                # Create the new folders if they don't exist already
                pathlib.Path(f"../../FORMATTED_DATA/Temperature").mkdir(parents=True, exist_ok=True)
                pathlib.Path(f"../../CLEANED_DATA/Temperature").mkdir(parents=True, exist_ok=True)
                
                # To save the formatted data with a plot
                results.to_csv(output_filename, index=False)
                plot_results(results,f"../../FORMATTED_DATA/Temperature/{file.split('.')[0].split('/')[-1]}_{format_date(data)}.png")
            elif "press" in i.lower():
                # Same as temperature
                output_filename = f"../../FORMATTED_DATA/Pression/{file.split('.')[0].split('/')[-1]}_{format_date(data)}.csv"
                pathlib.Path(f"../../FORMATTED_DATA/Pression").mkdir(parents=True, exist_ok=True)
                pathlib.Path(f"../../CLEANED_DATA/Pression").mkdir(parents=True, exist_ok=True)
                results.to_csv(output_filename, index=False)
                plot_results(results,f"../../FORMATTED_DATA/Pression/{file.split('.')[0].split('/')[-1]}_{format_date(data)}.png")
            elif "hum" in i.lower():
                # Same as temperature
                output_filename = f"../../FORMATTED_DATA/Humidite/{file.split('.')[0].split('/')[-1]}_{format_date(data)}.csv"
                pathlib.Path(f"../../FORMATTED_DATA/Humidite").mkdir(parents=True, exist_ok=True)
                pathlib.Path(f"../../CLEANED_DATA/Humidite").mkdir(parents=True, exist_ok=True)
                results.to_csv(output_filename, index=False)
                plot_results(results,f"../../FORMATTED_DATA/Humidite/{file.split('.')[0].split('/')[-1]}_{format_date(data)}.png")
            elif "haut" in i.lower():
                # Same as temperature
                output_filename = f"../../FORMATTED_DATA/Hauteur_eau/{file.split('.')[0].split('/')[-1]}_{format_date(data)}.csv"
                pathlib.Path(f"../../FORMATTED_DATA/Hauteur_eau").mkdir(parents=True, exist_ok=True)
                pathlib.Path(f"../../CLEANED_DATA/Hauteur_eau").mkdir(parents=True, exist_ok=True)
                results.to_csv(output_filename, index=False)
                plot_results(results,f"../../FORMATTED_DATA/Hauteur_eau/{file.split('.')[0].split('/')[-1]}_{format_date(data)}.png")
            elif "co2" in i.lower():
                # Same as temperature
                output_filename = f"../../FORMATTED_DATA/CO2/{file.split('.')[0].split('/')[-1]}_{format_date(data)}.csv"
                pathlib.Path(f"../../FORMATTED_DATA/CO2").mkdir(parents=True, exist_ok=True)
                pathlib.Path(f"../../CLEANED_DATA/CO2").mkdir(parents=True, exist_ok=True)
                results.to_csv(output_filename, index=False)
                plot_results(results,f"../../FORMATTED_DATA/CO2/{file.split('.')[0].split('/')[-1]}_{format_date(data)}.png")
            elif "o2" in i.lower():
                # Same as temperature
                output_filename = f"../../FORMATTED_DATA/O2/{file.split('.')[0].split('/')[-1]}_{format_date(data)}.csv"
                pathlib.Path(f"../../FORMATTED_DATA/O2").mkdir(parents=True, exist_ok=True)
                pathlib.Path(f"../../CLEANED_DATA/O2").mkdir(parents=True, exist_ok=True)
                results.to_csv(output_filename, index=False)
                plot_results(results,f"../../FORMATTED_DATA/O2/{file.split('.')[0].split('/')[-1]}_{format_date(data)}.png")

# Test section
# format_data("Format_bizarre.csv")

# Read all the csv files in the directory
for file in os.listdir(path="."):
    if file.endswith(".csv"):
        print("Reading file : ", os.path.join(os.getcwd(), file))
        format_data(file)