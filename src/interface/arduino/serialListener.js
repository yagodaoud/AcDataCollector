import { SerialPort } from "serialport";
import { ReadlineParser } from "@serialport/parser-readline";
import { TemperatureController } from "../controllers/TemperatureController.js";

const port = new SerialPort({
    path: "COM9",
    baudRate: 9600
});
const parser = port.pipe(new ReadlineParser({ delimiter: "\n" }));

const tempController = new TemperatureController();

parser.on("data", (line) => {
    line = line.trim();
    if (line.startsWith("TEMP:")) {
        const temp = parseInt(line.replace("TEMP:", ""));
        if (!isNaN(temp)) {
            tempController.arduino.receiveInput(temp);
            console.log(`[✓] Serial input received: ${temp}°C`);
        } else {
            console.warn("[!] Serial input invalid:", line);
        }
    }
});

console.log("🚀 Serial listener started, waiting for Arduino...");
