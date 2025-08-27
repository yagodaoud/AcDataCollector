import sqlite3
import requests
import datetime
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

# Constants
DB_PATH = "ac_data.db"
LAT = -20.5382
LON = -47.4009
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
TIMEZONE = "America/Sao_Paulo"


def fetch_historical_data():
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT temperature, humidity, weather, season, timestamp FROM temperature_entries"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def preprocess_data(df):
    # Extract hour from timestamp to determine period_of_day slice (0-23)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour

    # Define period_of_day (6-hour slices)
    def period_of_day(hour):
        if 0 <= hour < 6:
            return 'night'
        elif 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 18:
            return 'afternoon'
        else:
            return 'evening'

    df['period_of_day'] = df['hour'].apply(period_of_day)

    # Encode categorical variables
    le_weather = LabelEncoder()
    df['weather_enc'] = le_weather.fit_transform(df['weather'])

    le_season = LabelEncoder()
    df['season_enc'] = le_season.fit_transform(df['season'])

    le_period = LabelEncoder()
    df['period_enc'] = le_period.fit_transform(df['period_of_day'])

    # Features
    X = df[['humidity', 'weather_enc', 'season_enc', 'period_enc']]

    # Target
    y = df['temperature']

    encoders = {
        'weather': le_weather,
        'season': le_season,
        'period': le_period
    }

    return X, y, encoders


def fetch_current_weather():
    params = {
        "latitude": LAT,
        "longitude": LON,
        "current_weather": True,
        "timezone": TIMEZONE,
        "hourly": "relative_humidity_2m,weathercode"
    }

    resp = requests.get(OPEN_METEO_URL, params=params)
    data = resp.json()

    current = data.get('current_weather', {})
    humidity = None
    weather_code = None

    # Sometimes humidity is only in hourly data
    if 'hourly' in data and 'relative_humidity_2m' in data['hourly']:
        # get closest humidity to current hour
        current_hour = current.get('time', '')[:13]  # "YYYY-MM-DDTHH"
        times = data['hourly']['time']
        humidity_list = data['hourly']['relative_humidity_2m']
        humidity = None
        for t, h in zip(times, humidity_list):
            if t.startswith(current_hour):
                humidity = h
                break

    weather_code = current.get('weathercode', None)

    # Map weather code to weather string (same map as Node.js)
    weather_map = {
        0: 'Clear',
        1: 'Mainly Clear',
        2: 'Partly Cloudy',
        3: 'Overcast',
        45: 'Fog',
        48: 'Depositing Rime Fog',
        51: 'Light Drizzle',
        53: 'Moderate Drizzle',
        55: 'Dense Drizzle',
        61: 'Light Rain',
        63: 'Moderate Rain',
        65: 'Heavy Rain',
        71: 'Light Snow',
        73: 'Moderate Snow',
        75: 'Heavy Snow',
        80: 'Rain Showers',
        81: 'Moderate Showers',
        82: 'Violent Showers',
        95: 'Thunderstorm',
        96: 'Thunderstorm w/ Hail',
        99: 'Thunderstorm w/ Heavy Hail'
    }

    weather = weather_map.get(weather_code, 'Unknown')

    return {
        'humidity': humidity if humidity is not None else 50,  # fallback
        'weather': weather
    }


def get_season(month):
    # Approximate seasons for southern hemisphere
    if month in [12, 1, 2]:
        return 'summer'
    elif month in [3, 4, 5]:
        return 'autumn'
    elif month in [6, 7, 8]:
        return 'winter'
    else:
        return 'spring'


def get_period_of_day(hour):
    if 0 <= hour < 6:
        return 'night'
    elif 6 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 18:
        return 'afternoon'
    else:
        return 'evening'


def train_model(X, y):
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model


def predict_preferred_temperature(model, encoders, weather_data):
    now = datetime.datetime.now()

    season = get_season(now.month)
    period = get_period_of_day(now.hour)

    # Encode categorical values using encoders
    weather_enc = encoders['weather'].transform([weather_data['weather']])[0] \
        if weather_data['weather'] in encoders['weather'].classes_ else 0
    season_enc = encoders['season'].transform([season])[0] \
        if season in encoders['season'].classes_ else 0
    period_enc = encoders['period'].transform([period])[0] \
        if period in encoders['period'].classes_ else 0

    X_pred = np.array([[weather_data['humidity'], weather_enc, season_enc, period_enc]])
    pred_temp = model.predict(X_pred)[0]

    return pred_temp


def main():
    print("Fetching historical data from DB...")
    df = fetch_historical_data()

    if df.empty:
        print("No historical data found. Collect data first.")
        return

    print(f"Loaded {len(df)} historical entries")

    X, y, encoders = preprocess_data(df)
    print("Training model...")
    model = train_model(X, y)

    print("Fetching current weather data...")
    weather_data = fetch_current_weather()

    print(f"Current weather: {weather_data}")

    preferred_temp = predict_preferred_temperature(model, encoders, weather_data)
    print(f"Predicted preferred AC temperature: {preferred_temp:.1f} °C")


if __name__ == "__main__":
    main()
