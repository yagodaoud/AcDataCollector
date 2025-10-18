import { SerialPort } from "serialport";
import { ReadlineParser } from "@serialport/parser-readline";

// SerialPort agora espera um objeto com "path" e "baudRate"
const port = new SerialPort({
    path: "COM9",
    baudRate: 9600
});

// Parser para ler linhas
const parser = port.pipe(new ReadlineParser({ delimiter: "\n" }));

parser.on("data", (line) => {
    console.log("Arduino ->", line);
});

port.on("open", () => console.log("Porta Serial aberta!"));

port.on("error", (err) => console.error("Erro na porta:", err));
