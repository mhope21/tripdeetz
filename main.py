import requests
from datetime import datetime
import psycopg2
import configparser
import tkinter as tk
import tkinter.messagebox as messagebox

# Use config file for sensitive data
# Create a configuration parser
config = configparser.ConfigParser()

# Load the configuration file
config.read('config.ini')

# Read the database connection parameters
dbname = config['database']['dbname']
host = config['database']['host']
user = config['database']['user']
password = config['database']['password']


# Define functions for GUI actions

# Function to retrieve flight status and weather
def get_flight_status_and_weather():
    # Create a configuration parser
    config = configparser.ConfigParser()

    # Load the configuration file
    config.read('config.ini')

    # Read API keys
    api_keys_section = config['api_keys']
    api_key = api_keys_section['api_key']
    air_api_key = api_keys_section['air_api_key']
    weather_api_key = api_keys_section['weather_api_key']

    # Get user input from entry fields (Tkinter)
    target_flight_number = flight_number_entry.get()
    target_date = date_entry.get()

    flight_status = get_flight_status(api_key, target_flight_number, target_date)

    if flight_status:

        # Search for the target flight in the response data
        for entry in flight_status['data']:
            if entry['flight']['iata'] == target_flight_number and entry['flight_date'] == target_date:
                airline = entry['airline']['name']
                flight_number = entry['flight']['iata']
                departure_airport = entry['departure']['airport']
                scheduled_departure = iso_to_readable(entry['departure']['scheduled'])
                arrival_airport = entry['arrival']['airport']
                scheduled_arrival = iso_to_readable(entry['arrival']['scheduled'])
                status = entry['flight_status']
                airport_code = entry['arrival']['iata']

                # Check if there's a delay and include it in the status
                delay = entry['departure']['delay']
                if delay is not None:
                    status += f" (Delayed by {delay} minutes)"

                    # Display flight information in the Tkinter GUI (Label widgets)
                    airline_label.config(text=f"Airline: {airline}")
                    flight_number_label.config(text=f"Flight Number: {flight_number}")
                    departure_airport_label.config(text=f"Departure Airport: {departure_airport}")
                    scheduled_departure_label.config(text=f"Scheduled Departure: {scheduled_departure}")
                    arrival_airport_label.config(text=f"Arrival Airport: {arrival_airport}")
                    scheduled_arrival_label.config(text=f"Scheduled Arrival: {scheduled_arrival}")
                    status_label.config(text=f"Status: {status}")

                iata_code = airport_code

                city_info = get_city_info_by_iata(air_api_key, iata_code)

                if city_info:
                    # Accessing specific values
                    airport_data = city_info["response"][0]  # Get the first element of the "response" list

                    airport_name = airport_data["name"]
                    iata_code = airport_data["iata_code"]
                    latitude = airport_data["lat"]
                    longitude = airport_data["lng"]

                    weather_data = get_weather(weather_api_key, latitude, longitude)

                    if weather_data:
                        # Accessing specific weather values
                        weather_main = weather_data["weather"][0]["main"]
                        weather_description = weather_data["weather"][0]["description"]
                        temperature = weather_data["main"]["temp"]
                        humidity = weather_data["main"]["humidity"]
                        feels_like = weather_data["main"]["feels_like"]
                        temp_min = weather_data["main"]["temp_min"]
                        temp_max = weather_data["main"]["temp_max"]

                        # Accessing wind information
                        wind_speed = weather_data["wind"]["speed"]
                        wind_direction_degrees = weather_data["wind"]["deg"]

                        # Convert wind direction to cardinal direction
                        wind_direction = degrees_to_cardinal(wind_direction_degrees)

                        flight_details = (
                            f"Flight Details\n"
                            f"Airline: {airline}\n"
                            f"Flight Number: {flight_number}\n"
                            f"Departure Airport: {departure_airport}\n"
                            f"Scheduled Departure: {scheduled_departure}\n"
                            f"Arrival Airport: {arrival_airport}\n"
                            f"Scheduled Arrival: {scheduled_arrival}\n"
                            f"Status: {status}\n\n\n"
                            f"Weather Details\n"
                            f"Airport Name: {airport_name}\n"
                            f"Weather: {weather_main}\n"
                            f"Description: {weather_description}\n"
                            f"Temperature: {temperature}°F\n"
                            f"Humidity: {humidity}%\n"
                            f"Feels Like: {feels_like}°F\n"
                            f"Min Temperature: {temp_min}°F\n"
                            f"Max Temperature: {temp_max}°F\n"
                            f"Wind: {wind_speed} mph ({wind_direction})\n"
                        )

                        # Display flight and weather information in a messagebox
                        messagebox.showinfo("Flight and Weather Details", flight_details)

                        break  # Once information is collected end loop

                    else:
                        print("Weather information not found.")
                        messagebox.showinfo("Error. Cannot access information.")

                else:
                    print("City information not found.")
                    messagebox.showinfo("Error. Cannot access information.")
            else:
                print("Flight not found in the response.")
                messagebox.showinfo("Error. Cannot access information.")


# Function to look up reservations by confirmation number
def lookup_reservation():
    # Code to look up reservations by confirmation number
    # Establish a connection to the database
    try:
        connection = psycopg2.connect(
            dbname=dbname,
            host=host,
            user=user,
            password=password
        )
        print("Connected to the database.")

        # Create a cursor object for executing SQL commands
        cursor = connection.cursor()

        # Specify the confirmation number you want to retrieve
        target_confirmation_number = confirmation_number_entry.get()

        # Define the SQL command to retrieve a reservation by confirmation number
        select_reservation_sql = """
        SELECT * FROM reservations WHERE reserve_confirm = %s;
        """

        # Execute the SQL command with the confirmation number as a parameter
        cursor.execute(select_reservation_sql, (target_confirmation_number,))

        # Fetch the result (one row) and print it
        reservation = cursor.fetchone()
        if reservation:
            reservation_details = (
                f"Confirmation Number: {reservation[0]}\n"
                f"Date: {reservation[1]}\n"
                f"Location: {reservation[2]}\n"
                f"Duration: {reservation[3]}\n"
                f"Reservation Type: {reservation[4]}\n"
                f"Web Address: {reservation[5]}\n"
            )
            # Display reservation information in a messagebox
            messagebox.showinfo("Reservation Details", reservation_details)
        else:
            # Display an error message in a messagebox
            messagebox.showerror("Error", "Reservation not found.")

        # Close the cursor and connection when done.
        cursor.close()
        connection.close()
        print("Connection closed.")
    except psycopg2.Error as e:
        print("Error connecting to the database:", e)


def lookup_reservations_by_date():
    # Code to look up reservations by date
    # Establish a connection to the database
    try:
        connection = psycopg2.connect(
            dbname=dbname,
            host=host,
            user=user,
            password=password
        )
        print("Connected to the database.")

        # Create a cursor object for executing SQL commands
        cursor = connection.cursor()

        # Specify the date to retrieve reservations for
        target_reservation_date = target_date_entry.get()

        # Define the SQL command to retrieve reservations by date
        select_reservation_sql = """
        SELECT * FROM reservations WHERE reserve_date = %s;
        """

        # Execute the SQL command with the date as a parameter
        cursor.execute(select_reservation_sql, (target_reservation_date,))

        # Fetch all the results and print each reservation
        reservations = cursor.fetchall()
        if reservations:
            reservation_details = ""
            for reservation in reservations:
                reservation_details += (
                    f"Confirmation Number: {reservation[0]}\n"
                    f"Date: {reservation[1]}\n"
                    f"Location: {reservation[2]}\n"
                    f"Duration: {reservation[3]}\n"
                    f"Reservation Type: {reservation[4]}\n"
                    f"Web Address: {reservation[5]}\n\n\n"
                )
            messagebox.showinfo("Reservation Details", reservation_details)
        else:
            messagebox.showinfo("Reservation Details", "No reservations found for the specified date.")

        # Close the cursor and connection when done.
        cursor.close()
        connection.close()
        print("Connection closed.")
    except psycopg2.Error as e:
        print("Error connecting to the database:", e)


# Function to add a new reservation
def add_reservation():
    # Your existing code to add new reservations to the database
    # Establish a connection to the database
    try:
        connection = psycopg2.connect(
            dbname=dbname,
            host=host,
            user=user,
            password=password
        )
        print("Connected to the database.")

        # Create a cursor object for executing SQL commands
        cursor = connection.cursor()

        # Get user input from entry fields (Tkinter)
        reserve_confirm = reservation_confirmation_entry.get()
        reserve_date = reservation_date_entry.get()
        reserve_location = reservation_location_entry.get()
        reserve_duration = reservation_duration_entry.get()
        reserve_type = reservation_type_entry.get()
        reserve_link = reservation_link_entry.get()

        # Define the SQL command to insert a new reservation
        insert_reservation_sql = """
        INSERT INTO reservations (reserve_confirm, reserve_date, reserve_location, reserve_duration, reserve_type, reserve_link)
        VALUES (%s, %s, %s, %s, %s, %s);
        """

        # Execute the SQL command to insert the reservation
        cursor.execute(insert_reservation_sql,
                       (reserve_confirm, reserve_date, reserve_location, reserve_duration, reserve_type, reserve_link))
        connection.commit()
        # Display reservation information in a messagebox
        messagebox.showinfo("Add Reservation Details", "Your reservation has been added.")
        # Don't forget to close the cursor and connection when done.
        cursor.close()
        connection.close()
        print("Connection closed.")
    except psycopg2.Error as e:
        messagebox.showinfo("Error", "Error connecting to the database")


# Define the ISO 8601 to human-readable date and time conversion function
def iso_to_readable(iso_datetime):
    datetime_obj = datetime.fromisoformat(iso_datetime)
    formatted_datetime = datetime_obj.strftime("%Y-%m-%d %I:%M %p")
    return formatted_datetime


# request flight status
def get_flight_status(api_key, flight_number, date):
    base_url = "http://api.aviationstack.com/v1/flights"

    # Construct the URL with the access_key parameter
    url = f"{base_url}?access_key={api_key}"

    params = {
        "flight_iata": flight_number,  # For IATA flight codes
        "date": date,  # Format: YYYY-MM-DD
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Error fetching flight status.")
        return None


# Get city info to determine the lat and lon
def get_city_info_by_iata(air_api_key, iata_code):
    url = f"https://airlabs.co/api/v9/airports?iata_code={iata_code}&api_key={air_api_key}"

    params = {
        "iata_code": iata_code,
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Error fetching city information.")
        return None


# Get weather info based on lon and lat
def get_weather(weather_api_key, latitude, longitude):
    base_url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": weather_api_key,
        "units": "imperial",  # Fahrenheit
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Error fetching weather information.")
        return None


# Convert degrees to cardinal direction
def degrees_to_cardinal(degrees):
    if 22.5 <= degrees < 67.5:
        return "Northeast"
    elif 67.5 <= degrees < 112.5:
        return "East"
    elif 112.5 <= degrees < 157.5:
        return "Southeast"
    elif 157.5 <= degrees < 202.5:
        return "South"
    elif 202.5 <= degrees < 247.5:
        return "Southwest"
    elif 247.5 <= degrees < 292.5:
        return "West"
    elif 292.5 <= degrees < 337.5:
        return "Northwest"
    else:
        return "North"


if __name__ == "__main__":

    # Create the main application window
    app = tk.Tk()
    app.title("TripDeetz")

    # Create labels and entry widgets for flight number and date input (Tkinter)
    flight_number_label = tk.Label(app, text="Enter flight number (e.g., AA123):")
    flight_number_entry = tk.Entry(app)

    date_label = tk.Label(app, text="Enter date (YYYY-MM-DD):")
    date_entry = tk.Entry(app)

    # Create a button to trigger the get_flight_status_and_weather function
    get_status_button = tk.Button(app, text="Get Status and Weather", command=get_flight_status_and_weather)

    # Create labels and entry widget for confirmation number input (Tkinter)
    confirmation_number_label = tk.Label(app, text="Enter confirmation number:")
    confirmation_number_entry = tk.Entry(app)

    # Create a button to trigger the lookup_reservation function
    lookup_button = tk.Button(app, text="Lookup Reservation", command=lookup_reservation)

    # Create labels and entry widgets for adding a new reservation (Tkinter)
    reservation_confirmation_label = tk.Label(app, text="Confirmation Number:")
    reservation_confirmation_entry = tk.Entry(app)

    reservation_date_label = tk.Label(app, text="Reservation Date (YYYY-MM-DD):")
    reservation_date_entry = tk.Entry(app)

    reservation_location_label = tk.Label(app, text="Reservation Location:")
    reservation_location_entry = tk.Entry(app)

    reservation_duration_label = tk.Label(app, text="Reservation Duration (in days):")
    reservation_duration_entry = tk.Entry(app)

    reservation_type_label = tk.Label(app, text="Reservation Type:")
    reservation_type_entry = tk.Entry(app)

    reservation_link_label = tk.Label(app, text="Web Link:")
    reservation_link_entry = tk.Entry(app)

    # Create a button to trigger the add_reservation function
    add_reservation_button = tk.Button(app, text="Add Reservation", command=add_reservation)

    #Widget for date search
    target_date_label = tk.Label(app, text="Search for Date:")
    target_date_entry = tk.Entry(app)

    search_date_button = tk.Button(app, text="Search Reservations", command=lookup_reservations_by_date)

    # Arrange widgets using grid
    # Section 1
    flight_number_label.grid(row=0, column=0, padx=10, pady=5)
    flight_number_entry.grid(row=0, column=1, padx=10, pady=5)

    date_label.grid(row=1, column=0, padx=10, pady=5)
    date_entry.grid(row=1, column=1, padx=10, pady=5)

    get_status_button.grid(row=2, columnspan=2, padx=10, pady=10)

    # Create labels for displaying flight and weather information (Tkinter)
    airline_label = tk.Label(app, text="Airline:")
    flight_number_label = tk.Label(app, text="Flight Number:")
    departure_airport_label = tk.Label(app, text="Departure Airport:")
    scheduled_departure_label = tk.Label(app, text="Scheduled Departure:")
    arrival_airport_label = tk.Label(app, text="Arrival Airport:")
    scheduled_arrival_label = tk.Label(app, text="Scheduled Arrival:")
    status_label = tk.Label(app, text="Status:")
    airport_name_label = tk.Label(app, text="Airport Name:")
    iata_code_label = tk.Label(app, text="IATA Code:")
    weather_main_label = tk.Label(app, text="Weather:")
    weather_description_label = tk.Label(app, text="Description:")
    temperature_label = tk.Label(app, text="Temperature:")
    humidity_label = tk.Label(app, text="Humidity:")
    feels_like_label = tk.Label(app, text="Feels Like:")
    temp_min_label = tk.Label(app, text="Min Temperature:")
    temp_max_label = tk.Label(app, text="Max Temperature:")
    wind_label = tk.Label(app, text="Wind:")

    # Section 2
    confirmation_number_label.grid(row=3, column=0, padx=10, pady=5)
    confirmation_number_entry.grid(row=3, column=1, padx=10, pady=5)

    lookup_button.grid(row=4, columnspan=2, padx=10, pady=10)

    # Section 3
    target_date_label.grid(row=5, column=0, padx=10, pady=5)
    target_date_entry.grid(row=5, column=1, padx=10, pady=5)

    search_date_button.grid(row=6, columnspan=2, padx=10, pady=10)

    # Section 4
    reservation_confirmation_label.grid(row=7, column=0, padx=10, pady=5)
    reservation_confirmation_entry.grid(row=7, column=1, padx=10, pady=5)

    reservation_date_label.grid(row=8, column=0, padx=10, pady=5)
    reservation_date_entry.grid(row=8, column=1, padx=10, pady=5)

    reservation_location_label.grid(row=9, column=0, padx=10, pady=5)
    reservation_location_entry.grid(row=9, column=1, padx=10, pady=5)

    reservation_duration_label.grid(row=10, column=0, padx=10, pady=5)
    reservation_duration_entry.grid(row=10, column=1, padx=10, pady=5)

    reservation_type_label.grid(row=11, column=0, padx=10, pady=5)
    reservation_type_entry.grid(row=11, column=1, padx=10, pady=5)

    reservation_link_label.grid(row=12, column=0, padx=10, pady=5)
    reservation_link_entry.grid(row=12, column=1, padx=10, pady=5)

    add_reservation_button.grid(row=13, columnspan=2, padx=10, pady=10)

    # Start the Tkinter main loop
    app.mainloop()






