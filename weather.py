import requests

URL = "https://api.open-meteo.com/v1/forecast"

def get_hourly_readings(lat=-12.1688, lon=26.3894, days=3):
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m",
        "timezone": "Africa/Lusaka",
        "forecast_days": days,
    }
    try:
        response = requests.get(URL, params, timeout=10)
        response.raise_for_status()
        hourly = response.json()["hourly"]
    except requests.exceptions.RequestException as error:
        raise RuntimeError(f"Could not reach the weather service: {error}")
    except KeyError:
        raise RuntimeError("The weather service sent back an unexpected response.")

    return [
        {"time": t, "temp_c": temp, "humidity": rh}
        for t, temp, rh in zip(
            hourly["time"],
            hourly["temperature_2m"],
            hourly["relative_humidity_2m"],
        )
    ]

if __name__ == "__main__":
    readings = get_hourly_readings()
    print(len(readings))
    print(readings[:3])

