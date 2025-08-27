export class ArduinoInputHandler {
    constructor(callback) {
      this.callback = callback; // Injected handler for processing input
    }
  
    /**
     * Simulate receiving a temperature value from Arduino
     * After 5s of inactivity, sends the temperature
     */
    receiveInput(temperature) {
      if (typeof temperature !== 'number') {
        console.error('Invalid Arduino input: temperature must be a number');
        return;
      }
  
      if (this.timer) {
        clearTimeout(this.timer);
      }
  
      // Wait 5 seconds before triggering callback
      this.timer = setTimeout(() => {
        const timestamp = new Date();
        this.callback(temperature, timestamp);
      }, 5000);
    }
  }
  