import sqlite3 from "sqlite3";

export class Database {
  constructor() {
    // Open in-memory DB
    this.db = new sqlite3.Database("ac_data.db");

    // Create the table
    this.db.serialize(() => {
      this.db.run(`
        CREATE TABLE IF NOT EXISTS temperature_entries (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          temperature INTEGER,
          weather_temperature INTEGER,
          timestamp TEXT,
          period_of_day TEXT,
          season TEXT,
          weather TEXT,
          humidity INTEGER
        )
      `);
    });
  }

  saveTemperatureEntry(entry) {
    return new Promise((resolve, reject) => {
      const query = `
        INSERT INTO temperature_entries (
          temperature,
          weather_temperature,
          timestamp,
          period_of_day,
          season,
          weather,
          humidity
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
      `;

      const values = [
        entry.temperature,
        entry.weather_temperature,
        entry.timestamp.toISOString(),
        entry.periodOfDay,
        entry.season,
        entry.weather,
        entry.humidity,
      ];

      this.db.run(query, values, function (err) {
        if (err) {
          console.error("Failed to insert temperature entry:", err.message);
          reject(err);
        } else {
          resolve();
        }
      });
    });
  }

  // Optional: method to fetch entries (for testing)
  getAllEntries() {
    return new Promise((resolve, reject) => {
      this.db.all(`SELECT * FROM temperature_entries`, [], (err, rows) => {
        if (err) {
          reject(err);
        } else {
          resolve(rows);
        }
      });
    });
  }
}
