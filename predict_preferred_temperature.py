import argparse
import sqlite3
import datetime as dt
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

DB_PATH = "ac_data.db"

FEATURE_CAT = ["weather", "season", "period_of_day"]
FEATURE_NUM = ["humidity", "weather_temperature"]
FEATURES = FEATURE_CAT + FEATURE_NUM

def log(msg: str):
    print(msg, flush=True)

def read_table(db_path: str) -> pd.DataFrame:
    log("Fetching historical data from DB...")
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("SELECT * FROM temperature_entries", conn)
    finally:
        conn.close()
    if df.empty:
        log("No data in table 'temperature_entries'.")
        return df
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    if 'user_id' not in df.columns:
        df['user_id'] = None
    # Garante coluna nova
    if 'weather_temperature' not in df.columns:
        df['weather_temperature'] = np.nan
    log(f"Loaded {len(df)} historical entries")
    return df

def ensure_period_and_season(df: pd.DataFrame) -> pd.DataFrame:
    def infer_period(h):
        if 0 <= h < 6: return 'night'
        if 6 <= h < 12: return 'morning'
        if 12 <= h < 18: return 'afternoon'
        return 'evening'
    def infer_season(m):
        if m in (12,1,2): return 'summer'
        if m in (3,4,5): return 'autumn'
        if m in (6,7,8): return 'winter'
        return 'spring'
    if 'period_of_day' not in df.columns or df['period_of_day'].isna().any():
        df['hour'] = df['timestamp'].dt.hour
        df['period_of_day'] = df['hour'].apply(lambda h: infer_period(int(h) if pd.notna(h) else 12))
    if 'season' not in df.columns or df['season'].isna().any():
        df['month'] = df['timestamp'].dt.month
        df['season'] = df['month'].apply(lambda m: infer_season(int(m) if pd.notna(m) else 1))
    return df

def fetch_current_weather() -> dict:
    log("Fetching current weather data...")
    import requests
    LAT = -20.5382
    LON = -47.4009
    TIMEZONE = "America/Sao_Paulo"
    url = "https://api.open-meteo.com/v1/forecast"
    params = dict(
        latitude=LAT,
        longitude=LAT and LON,  # dummy to keep linter happy if needed
        current="temperature_2m,relative_humidity_2m,weather_code",
        timezone=TIMEZONE,
        hourly="relative_humidity_2m,weather_code,temperature_2m"
    )
    # Corrige params
    params["longitude"] = LON
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    cur = data.get("current", {})
    humidity = cur.get("relative_humidity_2m")
    weather_code = cur.get("weather_code")
    outside_temp = cur.get("temperature_2m")

    if (humidity is None or outside_temp is None) and "hourly" in data:
        hours = data["hourly"].get("time", [])
        hums = data["hourly"].get("relative_humidity_2m", [])
        temps = data["hourly"].get("temperature_2m", [])
        now_hour = dt.datetime.now().strftime("%Y-%m-%dT%H")
        for t, h, tmp in zip(hours, hums, temps):
            if isinstance(t, str) and t.startswith(now_hour):
                if humidity is None: humidity = h
                if outside_temp is None: outside_temp = tmp
                break

    code_map = {
        0: 'Clear', 1: 'Mainly Clear', 2: 'Partly Cloudy', 3: 'Overcast',
        45: 'Fog', 48: 'Depositing Rime Fog',
        51: 'Light Drizzle', 53: 'Moderate Drizzle', 55: 'Dense Drizzle',
        61: 'Light Rain', 63: 'Moderate Rain', 65: 'Heavy Rain',
        71: 'Light Snow', 73: 'Moderate Snow', 75: 'Heavy Snow',
        80: 'Rain Showers', 81: 'Moderate Showers', 82: 'Violent Showers',
        95: 'Thunderstorm', 96: 'Thunderstorm w/ Hail', 99: 'Thunderstorm w/ Heavy Hail'
    }
    weather = code_map.get(weather_code, 'Unknown')
    if humidity is None: humidity = 50
    if outside_temp is None: outside_temp = 24.0
    weather_dict = {"humidity": float(humidity), "weather": weather, "weather_temperature": float(outside_temp)}
    log(f"Current weather: {weather_dict}")
    return weather_dict

def exponential_time_weight(ts: pd.Series, half_life_days: float = 60.0) -> np.ndarray:
    now = pd.Timestamp.now(tz=ts.dt.tz) if hasattr(ts.dt, "tz") else pd.Timestamp.now()
    days = (now - ts).dt.total_seconds() / 86400.0
    days = days.fillna(days.median() if len(days) else 0.0)
    lam = np.log(2.0) / half_life_days
    w = np.exp(-lam * days.clip(lower=0))
    return w.to_numpy()

def build_pipeline():
    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), FEATURE_CAT),
            ("num", SimpleImputer(strategy="median"), FEATURE_NUM),
        ],
        remainder="drop"
    )
    rf = RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        min_samples_leaf=2,
        n_jobs=-1
    )
    pipe = Pipeline([("pre", pre), ("rf", rf)])
    return pipe

def train(pipe: Pipeline, X: pd.DataFrame, y: pd.Series, sample_weight=None) -> Pipeline:
    log("Training model...")
    X = X[FEATURES].copy()
    if sample_weight is not None:
        pipe.fit(X, y, **{"rf__sample_weight": sample_weight})
    else:
        pipe.fit(X, y)
    return pipe

def predict_with_interval(pipe: Pipeline, x_one: pd.DataFrame, q_low=0.1, q_high=0.9):
    x_one = x_one[FEATURES].copy()
    rf = pipe.named_steps["rf"]
    Xt = pipe.named_steps["pre"].transform(x_one)
    preds = np.vstack([est.predict(Xt) for est in rf.estimators_])
    point = preds.mean(axis=0)[0]
    low = np.percentile(preds, q_low * 100, axis=0)[0]
    high = np.percentile(preds, q_high * 100, axis=0)[0]
    return float(point), float(low), float(high)

def blend_user_global(user_pred, global_pred, n_user):
    if user_pred is None or n_user <= 0:
        return global_pred
    alpha = min(0.8, n_user / 100.0)
    return alpha * user_pred + (1 - alpha) * global_pred

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH, help="Path to SQLite DB (default: ac_data.db)")
    ap.add_argument("--user-id", default=None, help="Personalize for this user if there is history (user_id column)")
    ap.add_argument("--print-interval", action="store_true", help="Print 80% interval from the ensemble")
    ap.add_argument("--debug", action="store_true", help="Print internal global/user predictions and sample counts")
    args = ap.parse_args()

    df = read_table(args.db)
    if df.empty:
        return
    df = ensure_period_and_season(df)

    needed = {"temperature", "humidity", "weather", "season", "period_of_day", "timestamp", "weather_temperature"}
    missing = needed - set(df.columns)
    if missing:
        log(f"Warning: missing columns found {missing} — will impute when possible.")

    # Imputação p/ linhas antigas
    if df["weather_temperature"].isna().any():
        df["weather_temperature"] = df.groupby(["season", "weather"])["weather_temperature"].transform(
            lambda s: s.fillna(s.median())
        )
        df["weather_temperature"] = df["weather_temperature"].fillna(df["weather_temperature"].median())

    X_all = df[FEATURES].copy()
    y_all = df["temperature"].astype(float)
    w_all = exponential_time_weight(df["timestamp"])

    pipe_global = build_pipeline()
    pipe_global = train(pipe_global, X_all, y_all, sample_weight=w_all)

    weather_now = fetch_current_weather()
    now = dt.datetime.now()
    season = ("summer" if now.month in (12,1,2) else
              "autumn" if now.month in (3,4,5) else
              "winter" if now.month in (6,7,8) else "spring")
    period = ("night" if 0 <= now.hour < 6 else
              "morning" if 6 <= now.hour < 12 else
              "afternoon" if 12 <= now.hour < 18 else "evening")

    x_cur = pd.DataFrame([{
        "weather": weather_now["weather"],
        "season": season,
        "period_of_day": period,
        "humidity": weather_now["humidity"],
        "weather_temperature": weather_now["weather_temperature"]
    }], columns=FEATURES)

    g_point, g_low, g_high = predict_with_interval(pipe_global, x_cur)

    user_pred = None
    n_user = 0
    if args.user_id is not None and "user_id" in df.columns:
        df_u = df[df["user_id"] == args.user_id]
        n_user = len(df_u)
        if n_user >= 12:
            X_u = df_u[FEATURES].copy()
            y_u = df_u["temperature"].astype(float)
            w_u = exponential_time_weight(df_u["timestamp"])
            pipe_user = build_pipeline()
            pipe_user = train(pipe_user, X_u, y_u, sample_weight=w_u)
            u_point, _, _ = predict_with_interval(pipe_user, x_cur)
            bias = (y_u.mean() - y_all.mean())
            user_pred = float(u_point + bias)

    final_pred = blend_user_global(user_pred, g_point, n_user)
    setpoint = round(final_pred)

    log(f"Predicted preferred AC temperature: {final_pred:.1f} °C (recommended setpoint: {int(setpoint)} °C)")
    if args.print_interval:
        log(f"Global model 80% interval: [{g_low:.1f}, {g_high:.1f}] °C")
    if args.debug:
        log(f"[DEBUG] Global={g_point:.3f}; User={user_pred if user_pred is not None else 'NA'}; n_user={n_user}; "
            f"Season/Period={season}/{period}; Weather={weather_now['weather']} "
            f"({weather_now['humidity']}% RH); Outside={weather_now['weather_temperature']:.1f} °C")

if __name__ == '__main__':
    main()
