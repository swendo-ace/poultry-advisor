import requests

URL = "https://api.open-meteo.com/v1/forecasting"
params = {
    "latitude": -12.1688,
    "longitude": 26.3894,
    "hourly": "temperature_2m,relative_humidity_2m",
    "timezone": "Africa/Lusaka",
    "forecast_days": 3,
}

response = requests.get(URL, params=params, timeout=10)
response.raise_for_status()
data = response.json()

print(list(data.keys()))
print(data["hourly"]["time"][:3])
print(data["hourly"]["temperature_2m"][:3])
print(data["hourly"]["relative_humidity_2m"][:3])      