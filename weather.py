def getweather():
    # importing modules
    import requests
    import json

    # API base URL
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather?"

    # City Name
    CITY = "5389489"

    # Your API key
    API_KEY = "bfb4cac70284e6ed8d55a504768975b5"

    # updating the URL
    URL = BASE_URL + "id=" + CITY + "&units=imperial" + "&appid=" + API_KEY 

    # Sending HTTP request
    response = requests.get(URL)

    # checking the status code of the request
    if response.status_code == 200:

        # retrieving data in the json format
        data = response.json()

        # take the main dict block
        main = data['main']

        # getting temperature
        temp = main['temp']
        high_temp = main['temp_max']
        low_temp = main['temp_min']
        # getting feel like
        feels_like = main['feels_like']
        # getting the humidity
        humidity = main['humidity']
        # getting the pressure
        pressure = main['pressure']

        dt = data['dt']
        # wind report
        wind_report = data['wind']

        wind_speed = wind_report['speed']
        
        return temp, feels_like, low_temp, high_temp, humidity,wind_report

