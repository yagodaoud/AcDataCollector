import sqlite3
import random
from datetime import datetime

DB_PATH = "ac_data.db"

WEATHERS = ['Clear', 'Partly Cloudy', 'Overcast', 'Light Rain', 'Moderate Rain', 'Fog']
SEASONS = ['summer', 'autumn', 'winter', 'spring']
PERIODS = ['morning', 'afternoon', 'evening', 'night']

PERIOD_HOURS = {
    'morning': (6, 11),
    'afternoon': (12, 17),
    'evening': (18, 23),
    'night': (0, 5)
}

USERS = ["arthur", "yago"]

def ensure_table(conn):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS temperature_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL NOT NULL,
            weather_temperature REAL,
            timestamp TEXT NOT NULL,
            period_of_day TEXT,
            season TEXT,
            weather TEXT,
            humidity REAL,
            user_id TEXT
        )
        """
    )
    conn.commit()

def maybe_add_columns(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(temperature_entries)")
    cols = [row[1] for row in cur.fetchall()]
    if "user_id" not in cols:
        cur.execute("ALTER TABLE temperature_entries ADD COLUMN user_id TEXT")
    if "weather_temperature" not in cols:
        cur.execute("ALTER TABLE temperature_entries ADD COLUMN weather_temperature REAL")
    conn.commit()

def random_timestamp(season, period):
    SEASON_MONTHS = {
        'summer': [12, 1, 2],
        'autumn': [3, 4, 5],
        'winter': [6, 7, 8],
        'spring': [9, 10, 11]
    }
    month = random.choice(SEASON_MONTHS[season])
    day = random.randint(1, 28)
    hour_range = PERIOD_HOURS[period]
    hour = random.randint(*hour_range)
    minute = random.randint(0, 59)
    year = 2024 if month != 12 else 2023
    dt_ = datetime(year, month, day, hour, minute)
    return dt_.isoformat()

def generate_user_bias(user_id):
    return 24.0 + (0.8 if user_id == "arthur" else -0.8 if user_id == "yago" else 0.0)

def sample_outside_temp(season, weather):
    base = {"summer": 28, "autumn": 24, "winter": 18, "spring": 23}[season]
    w_adj = {"Clear": 1, "Partly Cloudy": 0, "Overcast": -1, "Light Rain": -2, "Moderate Rain": -3, "Fog": -1}.get(weather, 0)
    return base + w_adj + random.choice([-1, 0, 1])

def generate_entry(user_id):
    season = random.choice(SEASONS)
    period = random.choice(PERIODS)
    weather = random.choice(WEATHERS)

    if "Rain" in weather:
        humidity = random.randint(70, 90)
    elif weather == "Fog":
        humidity = random.randint(80, 95)
    elif weather == "Overcast":
        humidity = random.randint(60, 80)
    else:
        humidity = random.randint(30, 60)

    outside_temp = sample_outside_temp(season, weather)

    base_temp = generate_user_bias(user_id)
    temp_adjustment = 0.0
    if humidity > 75:
        temp_adjustment -= 1.0
    if season == "winter":
        temp_adjustment += 1.0
    if season == "summer":
        temp_adjustment -= 1.0
    if weather == "Clear":
        temp_adjustment += random.choice([-0.5, 0])

    temperature = round(base_temp + temp_adjustment + random.choice([-1, -0.5, 0, 0.5, 1]), 1)
    timestamp = random_timestamp(season, period)

    return (temperature, outside_temp, timestamp, period, season, weather, humidity, user_id)

def seed_database(num_entries=1000):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    ensure_table(conn)
    maybe_add_columns(conn)

    for _ in range(num_entries):
        user = random.choice(USERS)
        temperature, outside_temp, timestamp, period, season, weather, humidity, user_id = generate_entry(user)
        cur.execute(
            """
            INSERT INTO temperature_entries (
                temperature, weather_temperature, timestamp, period_of_day, season, weather, humidity, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (temperature, outside_temp, timestamp, period, season, weather, humidity, user_id)
        )

    conn.commit()
    conn.close()
    print(f"✅ Inserted {num_entries} synthetic entries (with weather_temperature & user_id) into {DB_PATH}")

if __name__ == "__main__":
    seed_database(2000)
