#include <TFT_eSPI.h>
#include <XPT2046_Touchscreen.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <SD.h> // <--- NUEVO: Para la tarjeta SD

// --- PINES CYD ---
#define XPT2046_IRQ 36
#define XPT2046_MOSI 32
#define XPT2046_MISO 39
#define XPT2046_CLK 25
#define XPT2046_CS 33
#define TOUCH_CS 33
#define TOUCH_IRQ 36
#define SD_CS    5  // <--- NUEVO: Pin CS de la SD en la CYD

//CS (Chip Select) / SS: GPIO 5
//SCK (Clock): GPIO 18
//MISO (Master In Slave Out): GPIO 19
//MOSI (Master Out Slave In): GPIO 23
#define _SCK = 18;
#define _CS = 5; // Must be SCK+1 for HW CS support
#define _MISO = 19;
#define _MOSI = 23;


// --- CONFIGURACIÓN DE PANTALLA Y GRID ---
#define COLS 4
#define ROWS 3
#define BTN_W 80
#define BTN_H 80
#define ICON_SIZE 64 // Tamaño de los iconos en píxeles
#define TFT_BL 21

TFT_eSPI tft = TFT_eSPI();
SPIClass touchscreenSpi = SPIClass(VSPI);
SPIClass sdSpi = SPIClass(VSPI);
XPT2046_Touchscreen ts(TOUCH_CS, TOUCH_IRQ);
//XPT2046_Touchscreen ts(TOUCH_CS);

// Estructura actualizada con ruta de icono
struct Button {
  String label;
  String iconPath; // <--- NUEVO: Ruta en la SD (ej: "/mute.bmp")
  uint16_t bgColor;
  uint16_t textColor;
};

Button buttons[COLS * ROWS];
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 250;
bool escucharTouch = false; // Detenemos la escucha

void setup() {
  Serial.begin(115200);
  
   // ts.begin();
 // ts.setRotation(1);
/* 
    //Initialise the touchscreen
  touchscreenSpi.begin(XPT2046_CLK, XPT2046_MISO, XPT2046_MOSI, XPT2046_CS); // Start second SPI bus for touchscreen 
  ts.begin(touchscreenSpi);    // Touchscreen init 
  ts.setRotation(3);   
*/
  tft.init();
  tft.setRotation(3); 
  tft.fillScreen(TFT_BLACK);

  // --- INICIALIZAR SD ---
  /*if(!SD.begin(SD_CS)){
    Serial.println("{\"error\":\"sd_failed\"}");
    // Puedes dibujar un mensaje de error en pantalla aquí si quieres
  } else {
    Serial.println("SD Card inicializada.");
  }*/

  // Inicializar botones por defecto
  for (int i = 0; i < COLS * ROWS; i++) {
    buttons[i].label = "Vacio";
    buttons[i].iconPath = ""; // Vacío por defecto
    buttons[i].bgColor = TFT_DARKGREY;
    buttons[i].textColor = TFT_WHITE;
  }
  
  drawAllButtons();

//  SD.end();

/*    //Initialise the touchscreen
  touchscreenSpi.begin(XPT2046_CLK, XPT2046_MISO, XPT2046_MOSI, XPT2046_CS); // Start second SPI bus for touchscreen 
  ts.begin(touchscreenSpi);    // Touchscreen init 
  ts.setRotation(3);  */

  analogWrite(TFT_BL, 120);   // 0 = apagado ... 255 = máximo

  Serial.println("{\"status\":\"ready\"}");
  
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    parseConfig(input);
  }

  if (escucharTouch == true){
    if (ts.touched()) {
      TS_Point p = ts.getPoint();
      int x = map(p.x, 200, 3800, 0, 320);
      int y = map(p.y, 250, 3850, 0, 240);
      
      int col = x / BTN_W;
      int row = y / BTN_H;
      
      Serial.print("X crudo: "); Serial.print(p.x);
      Serial.print(" | Y crudo: "); Serial.print(p.y);
      Serial.print(" | Z (presión): "); Serial.println(p.z);
      delay(100);

      if (col < COLS && row < ROWS) {
        int btnIndex = (row * COLS) + col;
        if (millis() - lastDebounceTime > debounceDelay) {
          lastDebounceTime = millis();
          Serial.print("{\"type\":\"press\",\"id\":");
          Serial.print(btnIndex);
          Serial.println("}");
          
          /*
          // Feedback visual
          tft.fillRect(col * BTN_W + 2, row * BTN_H + 2, BTN_W - 4, BTN_H - 4, TFT_NAVY);
          delay(50);
          drawButton(col, row, btnIndex);
          */
        }
      }
    }
  }
}

void drawAllButtons() {
  for (int i = 0; i < COLS * ROWS; i++) {
    int col = i % COLS;
    int row = i / COLS;
    drawButton(col, row, i);
  }
}

void drawButton(int col, int row, int index) {
  int x = col * BTN_W;
  int y = row * BTN_H;
  
  // Fondo y borde
  tft.fillRect(x, y, BTN_W, BTN_H, buttons[index].bgColor);
  tft.drawRect(x, y, BTN_W, BTN_H, TFT_WHITE); 
  
  // Si tiene icono, dibujarlo y poner el texto abajo
  if (buttons[index].iconPath.length() > 0) {
    // Dibujar BMP (Centrado horizontalmente, pegado arriba)
    int iconX = x + (BTN_W - ICON_SIZE) / 2;
    int iconY = y + 4; 
    drawBmpFile(buttons[index].iconPath.c_str(), iconX, iconY, ICON_SIZE, ICON_SIZE);
    
    // Dibujar texto en la parte inferior
    tft.setTextColor(buttons[index].textColor, buttons[index].bgColor);
    tft.setTextSize(1); // Tamaño 1 para que quepa abajo
    int textWidth = tft.textWidth(buttons[index].label);
    int textX = x + (BTN_W - textWidth) / 2;
    tft.drawString(buttons[index].label, textX, y + 70);
  } 
  // Si no tiene icono, dibujar solo el texto grande centrado
  else {
    tft.setTextColor(buttons[index].textColor, buttons[index].bgColor);
    tft.setTextSize(2);
    int textWidth = tft.textWidth(buttons[index].label);
    int textX = x + (BTN_W - textWidth) / 2;
    int textY = y + (BTN_H - 16) / 2;
    tft.drawString(buttons[index].label, textX, textY);
  }
}

void parseConfig(String jsonStr) {
  DynamicJsonDocument doc(4096); 
  DeserializationError error = deserializeJson(doc, jsonStr);

  if (error) return;

//  ts.close();
//touchscreenSpi.close(); 
//digitalWrite(TOUCH_CS, HIGH);

  touchscreenSpi.end();
  escucharTouch = false;
  delay(10);  // Pequeña pausa para estabilizar

  //if (escucharTouch == false){
    // --- INICIALIZAR SD ---
    if(!SD.begin(SD_CS, sdSpi)){
      Serial.println("{\"error\":\"sd_failed\"}");
      // Puedes dibujar un mensaje de error en pantalla aquí si quieres
    } else {
      Serial.println("SD Card inicializada.");
    }
  //}


  if (doc.containsKey("buttons")) {
    JsonArray arr = doc["buttons"];
    for (JsonObject btn : arr) {
      int id = btn["id"];
      if (id >= 0 && id < COLS * ROWS) {
        buttons[id].label = btn["label"].as<String>();
        
        // <--- NUEVO: Leer la ruta del icono
        if (btn.containsKey("icon")) {
          buttons[id].iconPath = btn["icon"].as<String>();
        } else {
          buttons[id].iconPath = "";
        }
        
        String hexColor = btn["color"].as<String>();
        buttons[id].bgColor = hexToColor(hexColor);
      }
    }
    drawAllButtons();
    Serial.println("{\"status\":\"updated\"}");
    
    //if (escucharTouch == false){    
      SD.end();
      sdSpi.end();
      delay(10);  // Pequeña pausa para estabilizar
        //Initialise the touchscreen
      touchscreenSpi.begin(XPT2046_CLK, XPT2046_MISO, XPT2046_MOSI, XPT2046_CS); // Start second SPI bus for touchscreen 
      ts.begin(touchscreenSpi);    // Touchscreen init 
      ts.setRotation(3);        
      escucharTouch = true;
    //}

/*

    //Initialise the touchscreen
  touchscreenSpi.begin(XPT2046_CLK, XPT2046_MISO, XPT2046_MOSI, XPT2046_CS); // Start second SPI bus for touchscreen 
  ts.begin(touchscreenSpi);    // Touchscreen init 
  ts.setRotation(3);   
  */   
  //escucharTouch = true;
  }
}

uint16_t hexToColor(String hex) {
  hex.replace("#", "");
  long number = strtol(&hex[0], NULL, 16);
  int r = (number >> 16) & 0xFF;
  int g = (number >> 8) & 0xFF;
  int b = number & 0xFF;
  return tft.color565(r, g, b);
}

// --- FUNCIÓN MÁGICA: Lee un BMP de 24 bits de la SD y lo dibuja ---
void drawBmpFile(const char *filename, int16_t x, int16_t y, int16_t w, int16_t h) {
  File bmpFile = SD.open(filename);
  if (!bmpFile) {
    Serial.print("No se encontro: "); Serial.println(filename);
    return;
  }

  if (bmpFile.read() != 'B' || bmpFile.read() != 'M') {
    bmpFile.close();
    return;
  }

  bmpFile.seek(10);
  uint32_t dataOffset = bmpFile.read();
  dataOffset |= (uint32_t)bmpFile.read() << 8;
  dataOffset |= (uint32_t)bmpFile.read() << 16;
  dataOffset |= (uint32_t)bmpFile.read() << 24;

  bmpFile.seek(dataOffset);
  uint16_t rowSize = (w * 3 + 3) & ~3; // Padding de 4 bytes para BMP 24-bit
  uint8_t sdbuffer[3 * 80]; // Buffer para 80 pixeles (suficiente para 64)

  for (int row = 0; row < h; row++) {
    bmpFile.read(sdbuffer, rowSize);
    for (int col = 0; col < w; col++) {
      int b = sdbuffer[col * 3];
      int g = sdbuffer[col * 3 + 1];
      int r = sdbuffer[col * 3 + 2];
      uint16_t color = tft.color565(r, g, b);
      // Los BMP se guardan de abajo a arriba, por eso invertimos el eje Y
      tft.drawPixel(x + col, y + (h - 1 - row), color); 
    }
  }
  bmpFile.close();
}
