#include <OneWire.h>
#include <DallasTemperature.h>
#include "LedControl.h"

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

// --- Configuração do display 8x8 ---
LedControl lc = LedControl(12, 11, 10, 1); // DIN, CLK, CS, 1 display

// --- Digitos 3x5 para display 8x8 ---
byte numbers[10][5] = {
    {B111, B101, B101, B101, B111}, // 0
    {B010, B110, B010, B010, B111}, // 1
    {B111, B001, B111, B100, B111}, // 2
    {B111, B001, B111, B001, B111}, // 3
    {B101, B101, B111, B001, B001}, // 4
    {B111, B100, B111, B001, B111}, // 5
    {B111, B100, B111, B101, B111}, // 6
    {B111, B001, B010, B010, B010}, // 7
    {B111, B101, B111, B101, B111}, // 8
    {B111, B101, B111, B001, B111}  // 9
};

// --- Sinal de menos 3x5 ---
byte minusSign[5] = {
    B000,
    B000,
    B111,
    B000,
    B000};

// --- Função para mostrar temperatura no display (com suporte a negativos) ---
void showTemperature(int temp)
{
  lc.clearDisplay(0);

  bool isNegative = (temp < 0);
  int absTemp = abs(temp); // trabalha com valor absoluto

  int tens = absTemp / 10;
  int units = absTemp % 10;

  for (int row = 0; row < 5; row++)
  {
    byte line = 0;

    if (isNegative)
    {
      // Mostra sinal de menos à esquerda
      line |= (minusSign[row] << 5);
      // Unidade na direita (sem dezena para números -9 a -1)
      if (tens > 0)
      {
        // Para -10 a -99: mostra apenas as dezenas (sem espaço para unidades)
        line |= (numbers[tens][row] << 1);
      }
      else
      {
        // Para -1 a -9: mostra a unidade
        line |= numbers[units][row];
      }
    }
    else
    {
      // Número positivo (código original)
      if (tens > 0)
        line |= (numbers[tens][row] << 4);
      line |= numbers[units][row];
    }

    lc.setRow(0, row + 1, line); // centraliza verticalmente
  }
}

// --- Função para enviar temperatura via Serial ---
void sendTemperature(int temp)
{
  Serial.print("TEMP:");
  Serial.println(temp);
}

void setup()
{
  Serial.begin(9600);
  Serial.println("Inicializando sensor Dallas...");

  // Inicializa sensor e botões
  sensors.begin();
  pinMode(botaoAumentar, INPUT_PULLUP);
  pinMode(botaoDiminuir, INPUT_PULLUP);

  // Inicializa display
  lc.shutdown(0, false);
  lc.setIntensity(0, 8);
  lc.clearDisplay(0);

  // Lê temperatura inicial
  sensors.requestTemperatures();
  float tempC = sensors.getTempCByIndex(0);
  temperatura = (tempC == DEVICE_DISCONNECTED_C) ? 25 : tempC;

  Serial.print("Temperatura inicial: ");
  Serial.println(temperatura);

  // Mostra no display
  showTemperature(temperatura);

  // Envia temperatura inicial para o Node.js
  sendTemperature(temperatura);

  Serial.println("Monitor iniciado. Use os botões para ajustar a temperatura.");
}

void loop()
{
  // Leitura dos estados atuais dos botões
  int estadoAtualAumentar = digitalRead(botaoAumentar);
  int estadoAtualDiminuir = digitalRead(botaoDiminuir);

  bool mudou = false;

  // Detecta pressão do botão Aumentar
  if (estadoAnteriorAumentar == HIGH && estadoAtualAumentar == LOW)
  {
    temperatura++;
    Serial.print("Temperatura aumentada para: ");
    Serial.println(temperatura);
    mudou = true;
  }

  // Detecta pressão do botão Diminuir
  if (estadoAnteriorDiminuir == HIGH && estadoAtualDiminuir == LOW)
  {
    temperatura--;
    Serial.print("Temperatura diminuída para: ");
    Serial.println(temperatura);
    mudou = true;
  }

  // Atualiza os estados anteriores
  estadoAnteriorAumentar = estadoAtualAumentar;
  estadoAnteriorDiminuir = estadoAtualDiminuir;

  // Atualiza display e envia via Serial se mudou
  if (mudou)
  {
    showTemperature(temperatura);
    sendTemperature(temperatura);
  }

  delay(50); // debounce simples
}