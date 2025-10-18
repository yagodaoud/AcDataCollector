import express from 'express';
import { TemperatureController } from './interface/controllers/TemperatureController.js';
import './interface/arduino/serialListener.js'

const app = express();
const port = 3000;

app.use(express.json());

const tempController = new TemperatureController();

// Simulate Arduino sending temperature (mockable)
app.post('/arduino/temperature', (req, res) => {
  tempController.handleTemperatureInput(req, res);
});

app.get('/entries', (req, res) => {
  tempController.fetchAllEntries(req, res);
});

app.listen(port, () => {
  console.log(`🚀 Server running at http://localhost:${port}`);
});
