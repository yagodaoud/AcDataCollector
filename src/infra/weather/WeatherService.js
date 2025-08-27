// import axios from 'axios';

// export class WeatherService {
//   constructor() {
//     this.apiKey = 'cd1619886773a07b410b5b4239e15e54'; // Demo key – replace with yours if needed
//     this.lat = -20.5382; // Franca-SP latitude
//     this.lon = -47.4009; // Franca-SP longitude
//   }

//   async getWeather() {
//     try {
//       const response = await axios.get('https://api.openweathermap.org/data/3.0/weather', {
//         params: {
//           lat: this.lat,
//           lon: this.lon,
//           appid: this.apiKey,
//           units: 'metric'
//         }
//       });

//       const data = response.data;

//       return {
//         weather: data.weather[0].main, // e.g. "Clear", "Rain"
//         humidity: data.main.humidity   // in %
//       };
//     } catch (error) {
//       console.error('Failed to fetch weather data:', error.message);

//       // Fallback dummy data if API fails
//       return {
//         weather: 'Unknown',
//         humidity: 0
//       };
//     }
//   }
// }

import axios from 'axios';

export class WeatherService {
  constructor() {
    this.lat = -20.5382; // Franca-SP latitude
    this.lon = -47.4009; // Franca-SP longitude
  }

  async getWeather() {
    try {
      const url = 'https://api.open-meteo.com/v1/forecast';

      const response = await axios.get(url, {
        params: {
          latitude: this.lat,
          longitude: this.lon,
          current: 'temperature_2m,relative_humidity_2m,weather_code',
          timezone: 'America/Sao_Paulo'
        }
      });

      const data = response.data.current;

      return {
        weather: this.mapWeatherCode(data.weather_code),
        humidity: data.relative_humidity_2m
      };
    } catch (error) {
      console.error('Failed to fetch weather data:', error.message);

      // Fallback dummy data
      return {
        weather: 'Unknown',
        humidity: 0
      };
    }
  }

  mapWeatherCode(code) {
    const map = {
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
    };

    return map[code] || 'Unknown';
  }
}
