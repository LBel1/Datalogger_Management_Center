import os
import requests

############################### FUNCTIONS ###############################

# To find the canton in which the station is located
def canton_finder(station):
    # Load the data of the sites in JSON format
    data_site = r_site.json()['results']

    # Create a list of all sites 
    for i in range(len(data_site)):
        for j in range(len(data_site[i]['Stations'])):
            if(station == data_site[i]['Stations'][j]['value']):
                return data_site[i]['Canton'][0]['value']
    
    return "Sans_station"

def site_finder(station_name):
    # Get all the sites
    sites = r_site.json()['results']

    # Search for the site name and return it
    for i in range(len(sites)):
        for j in range(len(sites[i]['Stations'])):
            if(station_name == sites[i]['Stations'][j]['value']):
                return sites[i]['Nom']

def create_historic(stations_name):
    
    # Get the length of the list
    l = len(stations_name)
    
    # Create empty lists
    canton_name = []
    site_name = []
    station_name = []

    for i in range(l):
        sname = stations_name[i]['value'] # Define the station name

        canton_name.append(canton_finder(sname))
        station_name.append(sname)
        site_name.append(site_finder(sname))

    return canton_name, site_name, station_name

# To load the data from Baserow
def get_data(): 
    
    page_number = 1

    # Pull the data directly from the Baserow database using the API - first page
    r_dataloggers = requests.get(
        "https://api.baserow.io/api/database/rows/table/653094/?user_field_names=true",
        headers={
            "Authorization": "Token wzxe1NzVO9k1gbsFfUGMcY81U8qX0PlR"
        },params={
            "page" : str(page_number),
            "size" : "200"
        }
    )

    full_data = r_dataloggers.json()['results']

    while len(r_dataloggers.json()['results']) != 0:
        page_number += 1
        
        r_dataloggers = requests.get(
            "https://api.baserow.io/api/database/rows/table/653094/?user_field_names=true",
            headers={
                "Authorization": "Token wzxe1NzVO9k1gbsFfUGMcY81U8qX0PlR"
            },params={
                "page" : str(page_number),
                "size" : "200"
            }
        )

        # To append correctly the new data in the data list and avoid nesting
        for i in range(len(r_dataloggers.json()['results'])):
            full_data.append(r_dataloggers.json()['results'][i])

    return full_data

############################### MAIN CODE #####################################

# Pull the data directly from the Baserow database using the API
r_dataloggers = get_data()

# If one day, you have more than 200 sites, you'll need to copy paste the get_data function but for the sites !
r_site = requests.get(
    "https://api.baserow.io/api/database/rows/table/653102/?user_field_names=true",
    headers={
        "Authorization": "Token wzxe1NzVO9k1gbsFfUGMcY81U8qX0PlR"
    },params={
        "size" : "200",
        "page":"1"
    }
)

# Create folders for all dataloggers
for i in r_dataloggers:
    
    # First, create the historic folders if the datalogger has been used before in any station
    if len(i["Historique d'utilisation"]) > 0:
        canton_name, site_name, station_name = create_historic(i['Historique d\'utilisation'])
        
        # loop over all the historic entries
        for j in range(len(canton_name)):
            # Create the according folders if non existent
            os.makedirs("DATA",exist_ok=True)
            path = os.path.join("DATA",canton_name[j], site_name[j], station_name[j], "RAW_DATA", i['Numéro de série'])
            os.makedirs(path, exist_ok=True)
        
    # Check that the actual "Station" and "Site" fields are not empty
    if [] not in [i['Station'], i['Site']]:
        
        # Get the necessary fields for the folders creation
        canton_fname = canton_finder(i['Station'][0]['value'])
        station_fname = i['Station'][0]['value']
        site_fname = i['Site'][0]['value']
        last_fname = i['Numéro de série']

        # Create the path and the respective folders using the fname above
        os.makedirs("DATA",exist_ok=True)
        path = os.path.join("DATA",canton_fname, site_fname, station_fname, "RAW_DATA", last_fname)
        os.makedirs(path, exist_ok=True)
    
    else:
        # If "Station" or "Site" is empty, create the folder in "SANS_STATION_ACTIVE"
        last_fname = i['Numéro de série']

        # Create the path and respective folders for stationless data
        os.makedirs("DATA",exist_ok=True)
        path = os.path.join("DATA", "SANS_STATION_ACTIVE", "RAW_DATA", last_fname)
        os.makedirs(path, exist_ok=True)