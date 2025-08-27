import { ArduinoInputHandler } from '../arduino/ArduinoInputHandler.js';
import { HandleTemperatureChange } from '../../application/usecases/HandleTemperatureChange.js';

export class TemperatureController {
  constructor() {
    this.handleTemperatureChange = new HandleTemperatureChange();
    this.db = this.handleTemperatureChange.db;

    this.arduino = new ArduinoInputHandler(async (temperature, timestamp) => {
      await this.handleTemperatureChange.execute(temperature, timestamp);
      console.log(`[✓] Arduino reading processed: ${temperature}°C at ${timestamp}`);
    });
  }

  async handleTemperatureInput(req, res) {
    try {
      const { temperature } = req.body;

      if (typeof temperature !== 'number') {
        return res.status(400).json({ error: 'Invalid temperature input' });
      }

      // Pass to Arduino abstraction
      this.arduino.receiveInput(temperature);

      res.status(200).json({ message: 'Temperature received, waiting 5s for inactivity' });
    } catch (error) {
      console.error('Error in controller:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  }

  async fetchAllEntries(req, res) {
    try {
      const entries = await this.db.getAllEntries();
      res.status(200).json(entries);
    } catch (error) {
      console.error('Error fetching entries:', error);
      res.status(500).json({ error: 'Failed to fetch entries' });
    }
  }
}
