import { WeatherService } from '../../infra/weather/WeatherService.js';
import { Database } from '../../infra/database/Database.js';
import { TemperatureEntry } from '../../domain/entities/TemperatureEntry.js';

export class HandleTemperatureChange {
  constructor() {
    this.weatherService = new WeatherService();
    this.db = new Database();
  }

  async execute(temperature, timestamp) {
    const weatherData = await this.weatherService.getWeather(); // Hardcoded location inside service

    const entry = new TemperatureEntry(temperature, timestamp, weatherData);

    await this.db.saveTemperatureEntry(entry);
  }
}
