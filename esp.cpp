#include <OneWire.h>
#include <DallasTemperature.h>

// --- Configuração do sensor ---
#define ONE_WIRE_BUS 4
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// --- Configuração dos botões ---
const int botaoAumentar = 2;
const int botaoDiminuir = 3;

// --- Variáveis de temperatura ---
int temperatura;
int estadoAnteriorAumentar = HIGH;
int estadoAnteriorDiminuir = HIGH;

// --- Função para enviar temperatura via Serial ---
void sendTemperature(int temp)
{
  Serial.print("TEMP:");
  Serial.println(temp); // prefixo TEMP: para o Node.js identificar
}

void setup()
{
  Serial.begin(9600);
  Serial.println("Inicializando sensor Dallas...");

  // Inicializa sensor e botões
  sensors.begin();
  pinMode(botaoAumentar, INPUT_PULLUP);
  pinMode(botaoDiminuir, INPUT_PULLUP);

  // Verifica quantos sensores estão conectados
  int count = sensors.getDeviceCount();
  Serial.print("Sensores encontrados: ");
  Serial.println(count);

  if (count == 0)
  {
    Serial.println("⚠️ Nenhum sensor detectado! Verifique o fio de dados e o resistor de 4.7kΩ.");
  }

  // Lê temperatura inicial do sensor
  sensors.requestTemperatures();
  float tempC = sensors.getTempCByIndex(0);

  if (tempC == DEVICE_DISCONNECTED_C)
  {
    Serial.println("❌ Erro: sensor desconectado ou leitura inválida (-127°C).");
    temperatura = 25; // valor padrão caso o sensor falhe
  }
  else
  {
    Serial.print("Temperatura inicial detectada: ");
    Serial.print(tempC);
    Serial.println(" °C");
    temperatura = tempC;
  }

  // Envia temperatura inicial para o Node.js
  sendTemperature(temperatura);

  Serial.println("Monitor iniciado. Use os botões para ajustar a temperatura.");
  Serial.print("Temperatura inicial: ");
  Serial.println(temperatura);
}

void loop()
{
  // Leitura dos estados atuais dos botões
  int estadoAtualAumentar = digitalRead(botaoAumentar);
  int estadoAtualDiminuir = digitalRead(botaoDiminuir);

  // Detecta pressão do botão Aumentar
  if (estadoAnteriorAumentar == HIGH && estadoAtualAumentar == LOW)
  {
    temperatura++;
    Serial.print("Temperatura aumentada para: ");
    Serial.println(temperatura);
    sendTemperature(temperatura);
  }

  // Detecta pressão do botão Diminuir
  if (estadoAnteriorDiminuir == HIGH && estadoAtualDiminuir == LOW)
  {
    temperatura--;
    Serial.print("Temperatura diminuída para: ");
    Serial.println(temperatura);
    sendTemperature(temperatura);
  }

  // Atualiza os estados anteriores
  estadoAnteriorAumentar = estadoAtualAumentar;
  estadoAnteriorDiminuir = estadoAtualDiminuir;

  delay(50); // debounce simples
}
