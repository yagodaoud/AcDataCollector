import sqlite3
import random
from datetime import datetime, timedelta

# Path to your SQLite file
DB_PATH = "ac_data.db"

# Sample categories
WEATHERS = ['Clear', 'Partly Cloudy', 'Overcast', 'Light Rain', 'Moderate Rain', 'Fog']
SEASONS = ['summer', 'autumn', 'winter', 'spring']
PERIODS = ['morning', 'afternoon', 'evening', 'night']

# Mapping period → hour ranges for realistic timestamps
PERIOD_HOURS = {
    'morning': (6, 11),
    'afternoon': (12, 17),
    'evening': (18, 23),
    'night': (0, 5)
}

def random_timestamp(season, period):
    """Generate a random timestamp in 2024 based on season and period."""
    # Approximate season to month range
    SEASON_MONTHS = {
        'summer': [12, 1, 2],
        'autumn': [3, 4, 5],
        'winter': [6, 7, 8],
        'spring': [9, 10, 11]
    }

    month = random.choice(SEASON_MONTHS[season])
    day = random.randint(1, 28)  # Safe across months
    hour_range = PERIOD_HOURS[period]
    hour = random.randint(*hour_range)
    minute = random.randint(0, 59)

    # Choose year 2024 to avoid future dates
    year = 2024 if month != 12 else 2023

    dt = datetime(year, month, day, hour, minute)
    return dt.isoformat()

def generate_entry():
    season = random.choice(SEASONS)
    period = random.choice(PERIODS)
    weather = random.choice(WEATHERS)

    # Humidity depends loosely on weather
    if "Rain" in weather:
        humidity = random.randint(70, 90)
    elif weather == "Fog":
        humidity = random.randint(80, 95)
    elif weather == "Overcast":
        humidity = random.randint(60, 80)
    else:
        humidity = random.randint(30, 60)

    # Preferred temp could vary slightly depending on weather/humidity
    base_temp = 24
    temp_adjustment = 0

    if humidity > 75:
        temp_adjustment -= 1  # Cooler preferred when humid
    if season == "winter":
        temp_adjustment += 1
    if season == "summer":
        temp_adjustment -= 1
    if weather == "Clear":
        temp_adjustment += random.choice([-1, 0])

    temperature = base_temp + temp_adjustment + random.choice([-1, 0, 1])

    timestamp = random_timestamp(season, period)

    return (temperature, datetime.fromisoformat(timestamp).isoformat(timespec='milliseconds') + 'Z', period, season, weather, humidity)

def seed_database(num_entries=100):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for _ in range(num_entries):
        entry = generate_entry()
        cur.execute("""
            INSERT INTO temperature_entries (
                temperature, timestamp, period_of_day, season, weather, humidity
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, entry)

    conn.commit()
    conn.close()
    print(f"✅ Inserted {num_entries} fake temperature entries into {DB_PATH}")

if __name__ == "__main__":
    seed_database(1000000)  # You can adjust the number here
