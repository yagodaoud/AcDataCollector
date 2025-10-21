export class TemperatureEntry {
  constructor(temperature, timestamp, weatherData) {
    this.temperature = temperature;
    this.weather_temperature = weatherData.temperature;
    this.timestamp = timestamp;
    this.periodOfDay = this.getPeriodOfDay(timestamp);
    this.season = this.getSeason(timestamp);
    this.weather = weatherData.weather;
    this.humidity = weatherData.humidity;
  }

  getPeriodOfDay(date) {
    const hour = date.getHours();
    if (hour >= 0 && hour < 6) return "night";
    if (hour >= 6 && hour < 12) return "morning";
    if (hour >= 12 && hour < 18) return "afternoon";
    return "evening";
  }

  getSeason(date) {
    const month = date.getMonth() + 1;
    if ([12, 1, 2].includes(month)) return "summer";
    if ([3, 4, 5].includes(month)) return "autumn";
    if ([6, 7, 8].includes(month)) return "winter";
    return "spring";
  }
}
