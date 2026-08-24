# CYD Command Deck - Documentación Completa

**Transforma tu ESP32-Cheap-Yellow-Display en un Command Deck funcional como Stream Deck**

---

## Índice

1. Descripción del Proyecto
2. Arquitectura del Sistema
3. Requisitos
4. Instalación y Configuración
5. Guía de Uso
6. Referencia de Comandos
7. Creación de Iconos
8. Documentación Técnica
9. Configuración de User_Setup.h
10. Solución de Problemas
11. Personalización Avanzada

---

## Descripción del Proyecto

Este proyecto convierte la placa ESP32-2432S028 (conocida como CYD - Cheap Yellow Display) en un controlador macro programable similar a un Stream Deck, comunicándose con Windows vía USB/Serial.

### Características
- 12 botones programables (grid 4x3)
- Pantalla táctil a color 2.8" (320x240)
- Iconos personalizables desde la tarjeta SD
- Configuración dinámica sin reprogramar el ESP32
- Ejecución de macros, atajos de teclado y apertura de aplicaciones
- Comunicación bidireccional vía JSON sobre puerto serie
- Gestión inteligente del bus SPI (SD y táctil no comparten SPI simultáneamente)

---

## Arquitectura del Sistema

    +-----------------------------------------------------------------+
    |                         CYD (ESP32)                             |
    |                                                                 |
    |  +--------------+    +----------------+    +--------------+     |
    |  |   Pantalla   |    |  Controlador   |    |  MicroSD     |     |
    |  |   ST7789     |<-->|     SPI        |<-->|  (iconos)    |     |
    |  |  320x240     |    |  (HSPI)        |    |              |     |
    |  +--------------+    +-------+--------+    +--------------+     |
    |                              |                                  |
    |  +--------------+    +-------v--------+                         |
    |  |   Táctil     |    |  Controlador   |                         |
    |  |  XPT2046     |<-->|     SPI        |                         |
    |  |              |    |  (VSPI)        |                         |
    |  +--------------+    +----------------+                         |
    |                              |                                  |
    +------------------------------|----------------------------------+
                                   | USB/Serial (JSON)
                                   v
                        +---------------------+
                        |    Windows PC       |
                        |   cyd_deck.py       |
                        |                     |
                        |  +---------------+  |
                        |  |  pyautogui    |  |
                        |  |  (teclas)     |  |
                        |  +---------------+  |
                        +---------------------+

### Consideración Importante: Gestión del Bus SPI

La CYD tiene una peculiaridad hardware: la pantalla, el táctil y la SD comparten el mismo bus SPI. Esto significa que no pueden funcionar simultáneamente.

Solución implementada:
1. Pantalla: Usa el bus HSPI (pines dedicados)
2. SD y Táctil: Se alternan en el bus VSPI
3. Flujo inteligente:
   - Al recibir configuración -> se inicializa la SD -> se leen iconos -> se cierra la SD (SD.end())
   - Después se inicializa el táctil en un segundo bus SPI (VSPI)
   - El táctil queda activo para detectar pulsaciones

---

## Requisitos

### Hardware
- Placa ESP32-2432S028 (CYD)
- Tarjeta MicroSD formateada en FAT32 (recomendada)
- Cable USB-C o Micro-USB (dependiendo de tu placa)
- PC con Windows

### Software
- Arduino IDE o PlatformIO
- Python 3.7+ en Windows
- Librerías de Arduino:
  - TFT_eSPI
  - XPT2046_Touchscreen
  - ArduinoJson (v6 o v7)
- Paquetes de Python:
    pip install pyserial pyautogui

---

## Instalación y Configuración

### Paso 1: Configurar TFT_eSPI para CYD

Importante: Sin esto, la pantalla no funcionará.

1. Ve a: C:\Users\[TU_USUARIO]\Documents\Arduino\libraries\TFT_eSPI\
2. Abre User_Setup.h y reemplaza TODO su contenido con el archivo proporcionado en la sección "Configuración de User_Setup.h"
3. Guarda el archivo y reinicia Arduino IDE

### Paso 2: Preparar la Tarjeta SD

1. Formatea la tarjeta en FAT32 (tamaño de asignación: 4096 bytes)
2. Crea una carpeta /icons/ en la raíz
3. Copia tus iconos BMP (ver sección "Creación de Iconos")

### Paso 3: Subir Firmware a la CYD

1. Abre Arduino IDE
2. Instala las librerías requeridas desde el Gestor de Librerías
3. Copia el código del firmware cyd_deck.ino (ver Documentación Técnica)
4. Selecciona:
   - Placa: ESP32 Dev Module
   - Puerto: COMx (el que corresponda)
5. Sube el sketch

### Paso 4: Configurar Python en Windows

1. Instala Python desde https://python.org
2. Abre CMD o PowerShell y ejecuta:
    pip install pyserial pyautogui
3. Crea un archivo cyd_deck.py con el código del host (ver Documentación Técnica)
4. Edita el puerto COM en la línea:
    ser = serial.Serial('COM3', 115200, timeout=1)  # <- Cambia COM3 por tu puerto
5. Ejecuta como Administrador (necesario para enviar teclas a algunas apps):
    python cyd_deck.py

---

## Guía de Uso

### Configuración de Botones

Edita el diccionario CONFIG en cyd_deck.py:

    CONFIG = {
        "buttons": [
            {
                "id": 0,                    # ID del botón (0-11)
                "label": "Mute Mic",        # Texto en el botón
                "color": "#FF0000",         # Color de fondo (hex)
                "icon": "/icons/mute.bmp",  # Ruta del icono en SD (opcional)
                "action": "ctrl+shift+m"    # Acción a ejecutar
            },
            # ... más botones
        ]
    }

### IDs de Botones

    +-----+-----+-----+-----+
    |  0  |  1  |  2  |  3  |  <- Fila 0
    +-----+-----+-----+-----+
    |  4  |  5  |  6  |  7  |  <- Fila 1
    +-----+-----+-----+-----+
    |  8  |  9  | 10  | 11  |  <- Fila 2
    +-----+-----+-----+-----+

### Ejemplos Prácticos

#### Botón para OBS Studio
    {
        "id": 2,
        "label": "OBS",
        "color": "#0000FF",
        "icon": "/icons/obs.bmp",
        "action": "open:obs64.exe"
    }

#### Botón para silenciar micrófono (Zoom/Teams/Discord)
    {
        "id": 0,
        "label": "Mute",
        "color": "#FF0000",
        "icon": "/icons/mute.bmp",
        "action": "ctrl+shift+m"
    }

#### Botón para control de volumen
    {
        "id": 6,
        "label": "Vol -",
        "color": "#A52A2A",
        "icon": "/icons/vol_down.bmp",
        "action": "volumedown"
    }

#### Botón para abrir navegador
    {
        "id": 3,
        "label": "Chrome",
        "color": "#FFFF00",
        "icon": "/icons/chrome.bmp",
        "action": "open:chrome.exe"
    }

---

## Referencia de Comandos

### Atajos de Teclado

Usa el formato "tecla1+tecla2+tecla3":

| Combinación              | Sintaxis                  | Uso común              |
|--------------------------|---------------------------|------------------------|
| Ctrl + C                 | "ctrl+c"                  | Copiar                 |
| Ctrl + V                 | "ctrl+v"                  | Pegar                  |
| Ctrl + Z                 | "ctrl+z"                  | Deshacer               |
| Ctrl + Shift + M         | "ctrl+shift+m"            | Mute en Zoom/Teams     |
| Ctrl + Shift + V         | "ctrl+shift+v"            | Activar cámara         |
| Ctrl + Shift + T         | "ctrl+shift+t"            | Reabrir pestaña        |
| Alt + F4                 | "alt+f4"                  | Cerrar ventana         |
| Alt + Tab                | "alt+tab"                 | Cambiar ventana        |
| Win + D                  | "win+d"                   | Mostrar escritorio     |
| Win + E                  | "win+e"                   | Explorador de archivos |
| Win + L                  | "win+l"                   | Bloquear PC            |
| Win + R                  | "win+r"                   | Ejecutar               |
| Shift + F1               | "shift+f1"                | Ayuda contextual       |
| Ctrl + F5                | "ctrl+f5"                 | Refrescar (sin caché)  |
| Ctrl + Shift + Esc       | "ctrl+shift+escape"       | Administrador tareas   |

### Teclas de Función

| Tecla | Sintaxis |
|-------|----------|
| F1    | "f1"     |
| F2    | "f2"     |
| F3    | "f3"     |
| F4    | "f4"     |
| F5    | "f5"     |
| F6    | "f6"     |
| F7    | "f7"     |
| F8    | "f8"     |
| F9    | "f9"     |
| F10   | "f10"    |
| F11   | "f11"    |
| F12   | "f12"    |

### Teclas Multimedia

| Acción           | Sintaxis       |
|------------------|----------------|
| Bajar volumen    | "volumedown"   |
| Subir volumen    | "volumeup"     |
| Silenciar        | "volumemute"   |
| Play/Pause       | "playpause"    |
| Siguiente pista  | "nexttrack"    |
| Anterior pista   | "prevtrack"    |

### Teclas Especiales

| Tecla            | Sintaxis       |
|------------------|----------------|
| Enter            | "enter"        |
| Escape           | "escape"       |
| Tab              | "tab"          |
| Espacio          | "space"        |
| Backspace        | "backspace"    |
| Delete           | "delete"       |
| Insert           | "insert"       |
| Home             | "home"         |
| End              | "end"          |
| Page Up          | "pageup"       |
| Page Down        | "pagedown"     |
| Flecha arriba    | "up"           |
| Flecha abajo     | "down"         |
| Flecha izquierda | "left"         |
| Flecha derecha   | "right"        |

### Abrir Aplicaciones

Formato: "open:nombre_ejecutable.exe"

    "open:obs64.exe"           # OBS Studio
    "open:chrome.exe"          # Google Chrome
    "open:firefox.exe"         # Mozilla Firefox
    "open:notepad.exe"         # Bloc de notas
    "open:calc.exe"            # Calculadora
    "open:mspaint.exe"         # Paint
    "open:explorer.exe"        # Explorador de archivos
    "open:discord.exe"         # Discord
    "open:spotify.exe"         # Spotify

---

## Creación de Iconos

### Especificaciones Técnicas

Los iconos DEBEN cumplir estos requisitos:

1. Formato: BMP (Bitmap de Windows)
2. Resolución: 64x64 píxeles exactos
3. Profundidad de color: 24 bits (RGB, sin canal alpha)
4. Compresión: Ninguna (sin comprimir)
5. Tamaño máximo: ~12 KB por icono

### Método 1: Usando Paint (Windows)

1. Abre Paint
2. Pega o dibuja tu imagen
3. Ve a Archivo -> Cambiar tamaño
4. Selecciona Píxeles y desmarca "Mantener proporción"
5. Introduce 64 en Ancho y 64 en Alto
6. Ve a Archivo -> Guardar como -> Imagen de mapa de bits de 24 bits
7. Nombra el archivo (ej: mute.bmp)

### Método 2: Usando GIMP (Gratis)

1. Abre GIMP
2. Abre tu imagen
3. Imagen -> Escalar imagen
4. Introduce 64x64 píxeles
5. Archivo -> Exportar como
6. Elige extensión .bmp
7. En opciones de exportación:
   - Especificar tipo de mapa de bits
   - Selecciona: RGB (24-bit)
   - No marques "Compresión RLE"
8. Exportar

### Método 3: Usando Python (Automático)

Crea un script convertir_iconos.py:

    from PIL import Image
    import os

    def convertir_a_bmp(archivo_entrada, archivo_salida):
        """Convierte cualquier imagen a BMP 64x64 24-bit"""
        img = Image.open(archivo_entrada)
        img = img.resize((64, 64), Image.Resampling.LANCZOS)
        # Convertir a RGB (eliminar canal alpha si existe)
        if img.mode == 'RGBA':
            # Crear fondo blanco
            fondo = Image.new('RGB', (64, 64), (255, 255, 255))
            fondo.paste(img, mask=img.split()[3])  # Usar alpha como máscara
            img = fondo
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        img.save(archivo_salida, 'BMP', format='BMP')
        print(f"Convertido: {archivo_entrada} -> {archivo_salida}")

    # Convertir todos los PNG/JPG de una carpeta
    carpeta_entrada = "iconos_originales"
    carpeta_salida = "icons"

    os.makedirs(carpeta_salida, exist_ok=True)

    for archivo in os.listdir(carpeta_entrada):
        if archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
            nombre_sin_ext = os.path.splitext(archivo)[0]
            entrada = os.path.join(carpeta_entrada, archivo)
            salida = os.path.join(carpeta_salida, f"{nombre_sin_ext}.bmp")
            convertir_a_bmp(entrada, salida)

Instalar Pillow: pip install Pillow

### Consejos de Diseño

1. Fondo transparente simulado: Como BMP 24-bit no soporta transparencia, usa el mismo color de fondo que el color del botón en el JSON.

   Ejemplo: Si tu botón es rojo #FF0000, pinta el fondo del BMP de rojo puro.

2. Contraste alto: Usa colores brillantes sobre fondos oscuros o viceversa para mejor visibilidad.

3. Evita detalles finos: A 64x64 píxeles, los detalles pequeños se pierden. Usa iconos simples y reconocibles.

4. Paleta de iconos recomendada:
   - Material Design Icons (https://pictogrammers.com/library/mdi/) (gratuitos)
   - FontAwesome (https://fontawesome.com/) (versión gratuita)
   - Icons8 (https://icons8.com/) (gratuitos con atribución)

### Estructura de Carpetas en la SD

    / (raíz de la SD)
    +-- icons/
    |   +-- mute.bmp
    |   +-- camera.bmp
    |   +-- obs.bmp
    |   +-- chrome.bmp
    |   +-- copy.bmp
    |   +-- paste.bmp
    |   +-- vol_up.bmp
    |   +-- vol_down.bmp
    |   +-- vol_mute.bmp
    |   +-- play.bmp
    |   +-- next.bmp
    |   +-- prev.bmp
    +-- config.json (opcional, para backup)

---

## Documentación Técnica

### Firmware ESP32 (Arduino) - cyd_deck.ino

#### Librerías Requeridas

    #include <TFT_eSPI.h>           // Driver de pantalla
    #include <XPT2046_Touchscreen.h> // Driver táctil
    #include <ArduinoJson.h>         // Parser JSON
    #include <SD.h>                  // Lectura de tarjeta SD
    #include <SPI.h>                 // Comunicación SPI

#### Definición de Pines

    // Pines del táctil (segundo bus SPI - VSPI)
    #define XPT2046_IRQ  36
    #define XPT2046_MOSI 32
    #define XPT2046_MISO 39
    #define XPT2046_CLK  25
    #define XPT2046_CS   33
    #define TOUCH_CS     33
    #define TOUCH_IRQ    36

    // Pin CS de la SD (comparte bus con la pantalla)
    #define SD_CS 5

    // Configuración del grid
    #define COLS 4
    #define ROWS 3
    #define BTN_W 80
    #define BTN_H 80
    #define ICON_SIZE 64

#### Código Completo del Firmware

    #include <TFT_eSPI.h>
    #include <XPT2046_Touchscreen.h>
    #include <ArduinoJson.h>
    #include <SPI.h>
    #include <SD.h>

    // --- PINES CYD ---
    #define XPT2046_IRQ 36
    #define XPT2046_MOSI 32
    #define XPT2046_MISO 39
    #define XPT2046_CLK 25
    #define XPT2046_CS 33
    #define TOUCH_CS 33
    #define TOUCH_IRQ 36
    #define SD_CS 5

    // --- CONFIGURACIÓN DE PANTALLA Y GRID ---
    #define COLS 4
    #define ROWS 3
    #define BTN_W 80
    #define BTN_H 80
    #define ICON_SIZE 64

    TFT_eSPI tft = TFT_eSPI();
    SPIClass touchscreenSpi = SPIClass(VSPI);
    XPT2046_Touchscreen ts(TOUCH_CS, TOUCH_IRQ);

    struct Button {
      String label;
      String iconPath;
      uint16_t bgColor;
      uint16_t textColor;
    };

    Button buttons[COLS * ROWS];
    unsigned long lastDebounceTime = 0;
    const unsigned long debounceDelay = 250;
    bool escucharSD = false;

    void setup() {
      Serial.begin(115200);
      
      tft.init();
      tft.setRotation(3);
      tft.fillScreen(TFT_BLACK);

      // Inicializar botones por defecto
      for (int i = 0; i < COLS * ROWS; i++) {
        buttons[i].label = "Vacio";
        buttons[i].iconPath = "";
        buttons[i].bgColor = TFT_DARKGREY;
        buttons[i].textColor = TFT_WHITE;
      }
      
      drawAllButtons();
      Serial.println("{\"status\":\"ready\"}");
    }

    void loop() {
      if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        parseConfig(input);
      }
      
      if (escucharSD == true) {
        if (ts.touched()) {
          TS_Point p = ts.getPoint();
          int x = map(p.x, 200, 3800, 0, 320);
          int y = map(p.y, 250, 3850, 0, 240);
          int col = x / BTN_W;
          int row = y / BTN_H;
          
          if (col < COLS && row < ROWS) {
            int btnIndex = (row * COLS) + col;
            if (millis() - lastDebounceTime > debounceDelay) {
              lastDebounceTime = millis();
              Serial.print("{\"type\":\"press\",\"id\":");
              Serial.print(btnIndex);
              Serial.println("}");
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
      
      tft.fillRect(x, y, BTN_W, BTN_H, buttons[index].bgColor);
      tft.drawRect(x, y, BTN_W, BTN_H, TFT_WHITE);
      
      if (buttons[index].iconPath.length() > 0) {
        int iconX = x + (BTN_W - ICON_SIZE) / 2;
        int iconY = y + 4;
        drawBmpFile(buttons[index].iconPath.c_str(), iconX, iconY, ICON_SIZE, ICON_SIZE);
        
        tft.setTextColor(buttons[index].textColor, buttons[index].bgColor);
        tft.setTextSize(1);
        int textWidth = tft.textWidth(buttons[index].label);
        int textX = x + (BTN_W - textWidth) / 2;
        tft.drawString(buttons[index].label, textX, y + 70);
      } else {
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
      
      if (escucharSD == false) {
        if (!SD.begin(SD_CS)) {
          Serial.println("{\"error\":\"sd_failed\"}");
        } else {
          Serial.println("SD Card inicializada.");
        }
      }
      
      if (doc.containsKey("buttons")) {
        JsonArray arr = doc["buttons"];
        for (JsonObject btn : arr) {
          int id = btn["id"];
          if (id >= 0 && id < COLS * ROWS) {
            buttons[id].label = btn["label"].as<String>();
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
        
        if (escucharSD == false) {
          SD.end();
          touchscreenSpi.begin(XPT2046_CLK, XPT2046_MISO, XPT2046_MOSI, XPT2046_CS);
          ts.begin(touchscreenSpi);
          ts.setRotation(3);
          escucharSD = true;
        }
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
      uint16_t rowSize = (w * 3 + 3) & ~3;
      uint8_t sdbuffer[3 * 80];
      
      for (int row = 0; row < h; row++) {
        bmpFile.read(sdbuffer, rowSize);
        for (int col = 0; col < w; col++) {
          int b = sdbuffer[col * 3];
          int g = sdbuffer[col * 3 + 1];
          int r = sdbuffer[col * 3 + 2];
          uint16_t color = tft.color565(r, g, b);
          tft.drawPixel(x + col, y + (h - 1 - row), color);
        }
      }
      bmpFile.close();
    }

### Host Windows (Python) - cyd_deck.py

#### Código Completo del Host

    import serial
    import json
    import time
    import pyautogui
    import subprocess

    CONFIG = {
        "buttons": [
            {"id": 0, "label": "Mute", "color": "#FF0000", "icon": "/icons/mute.bmp", "action": "ctrl+shift+m"},
            {"id": 1, "label": "Cam", "color": "#00FF00", "icon": "/icons/camera.bmp", "action": "ctrl+shift+v"},
            {"id": 2, "label": "OBS", "color": "#0000FF", "icon": "/icons/obs.bmp", "action": "open:obs64.exe"},
            {"id": 3, "label": "Web", "color": "#FFFF00", "icon": "/icons/chrome.bmp", "action": "open:chrome.exe"},
            {"id": 4, "label": "Copy", "color": "#808080", "icon": "/icons/copy.bmp", "action": "ctrl+c"},
            {"id": 5, "label": "Paste", "color": "#808080", "icon": "/icons/paste.bmp", "action": "ctrl+v"},
            {"id": 6, "label": "Vol-", "color": "#A52A2A", "icon": "/icons/vol_down.bmp", "action": "volumedown"},
            {"id": 7, "label": "Vol+", "color": "#A52A2A", "icon": "/icons/vol_up.bmp", "action": "volumeup"},
            {"id": 8, "label": "Mute", "color": "#A52A2A", "icon": "/icons/vol_mute.bmp", "action": "volumemute"},
            {"id": 9, "label": "Play", "color": "#4B0082", "icon": "/icons/play.bmp", "action": "playpause"},
            {"id": 10, "label": "Next", "color": "#4B0082", "icon": "/icons/next.bmp", "action": "nexttrack"},
            {"id": 11, "label": "Prev", "color": "#4B0082", "icon": "/icons/prev.bmp", "action": "prevtrack"}
        ]
    }

    def connect_serial():
        ser = serial.Serial('COM3', 115200, timeout=1)  # <- Cambia COM3
        time.sleep(2)
        return ser

    def execute_action(action_str):
        try:
            if action_str.startswith("open:"):
                app = action_str.replace("open:", "")
                subprocess.Popen(app)
                print(f"[OK] Abierto: {app}")
            elif action_str in ["volumedown", "volumeup", "volumemute", 
                                "playpause", "nexttrack", "prevtrack"]:
                pyautogui.press(action_str)
                print(f"[OK] Multimedia: {action_str}")
            else:
                keys = action_str.split('+')
                pyautogui.hotkey(*keys)
                print(f"[OK] Teclas: {action_str}")
        except Exception as e:
            print(f"[ERROR] {action_str}: {e}")

    def main():
        print("Iniciando CYD Stream Deck...")
        ser = connect_serial()
        
        while True:
            line = ser.readline().decode('utf-8').strip()
            if '"ready"' in line:
                print("CYD conectada")
                break
        
        config_json = json.dumps(CONFIG) + '\n'
        ser.write(config_json.encode('utf-8'))
        print("Configuracion enviada")
        
        while True:
            line = ser.readline().decode('utf-8').strip()
            if '"updated"' in line:
                print("Configuracion cargada en CYD")
                break
        
        print("Escuchando pulsaciones...")
        while True:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    print(f"[RX] {line}")
                    data = json.loads(line)
                    if data.get("type") == "press":
                        btn_id = data.get("id")
                        action = next(
                            (b["action"] for b in CONFIG["buttons"] if b["id"] == btn_id),
                            None
                        )
                        if action:
                            execute_action(action)
                        else:
                            print(f"[WARN] Sin accion para boton {btn_id}")
            except json.JSONDecodeError as e:
                print(f"[JSON ERROR] {e}")
            except KeyboardInterrupt:
                print("\nCerrando...")
                ser.close()
                break

    if __name__ == "__main__":
        main()

### Protocolo de Comunicación

#### Mensajes CYD -> PC

    {"status":"ready"}                    // CYD inicializada
    {"status":"updated"}                  // Configuracion aplicada
    {"type":"press","id":5}               // Boton 5 presionado
    {"error":"sd_failed"}                 // Error: SD no detectada
    {"error":"json_parse"}                // Error: JSON invalido

#### Mensajes PC -> CYD

    {
      "buttons": [
        {
          "id": 0,
          "label": "Mute",
          "color": "#FF0000",
          "icon": "/icons/mute.bmp"
        }
      ]
    }

### Calibración del Táctil

Si los toques no se registran en la posición correcta:

    // Valores típicos para CYD (pueden variar)
    #define X_MIN 200
    #define X_MAX 3800
    #define Y_MIN 250
    #define Y_MAX 3850

    int x = map(p.x, X_MIN, X_MAX, 0, 320);
    int y = map(p.y, Y_MIN, Y_MAX, 0, 240);
    x = constrain(x, 0, 319);
    y = constrain(y, 0, 239);

---

## Configuración de User_Setup.h

Archivo completo para la CYD (ESP32-2432S028). Copia este contenido y reemplaza el archivo User_Setup.h en tu librería TFT_eSPI:

    // USER DEFINED SETTINGS
    // Set driver type, fonts to be loaded, pins used and SPI control method etc

    #define USER_SETUP_INFO "User_Setup"

    // ##################################################################################
    // Section 1. Call up the right driver file and any options for it
    // ##################################################################################

    #define ST7789_DRIVER
    #define TFT_RGB_ORDER TFT_BGR

    #define TFT_INVERSION_OFF

    // ##################################################################################
    // Section 2. Define the pins that are used to interface with the display here
    // ##################################################################################

    #define TFT_BL 21
    #define TFT_BACKLIGHT_ON HIGH

    #define TFT_MISO 12
    #define TFT_MOSI 13
    #define TFT_SCLK 14
    #define TFT_CS 15
    #define TFT_DC 2
    #define TFT_RST -1

    // ##################################################################################
    // Section 3. Define the fonts that are to be used here
    // ##################################################################################

    #define LOAD_GLCD
    #define LOAD_FONT2
    #define LOAD_FONT4
    #define LOAD_FONT6
    #define LOAD_FONT7
    #define LOAD_FONT8
    #define LOAD_GFXFF
    #define SMOOTH_FONT

    // ##################################################################################
    // Section 4. Other options
    // ##################################################################################

    #define SPI_FREQUENCY 55000000
    #define SPI_READ_FREQUENCY 20000000
    #define SPI_TOUCH_FREQUENCY 2500000
    #define USE_HSPI_PORT

Pines configurados para CYD:
- TFT_MISO: 12
- TFT_MOSI: 13
- TFT_SCLK: 14
- TFT_CS: 15
- TFT_DC: 2
- TFT_RST: -1 (conectado al RST del ESP32)
- TFT_BL: 21 (Backlight)
- Driver: ST7789
- Orden de colores: BGR
- Frecuencia SPI: 55 MHz
- Bus SPI: HSPI (para liberar VSPI para el táctil)

---

## Solución de Problemas

### Problema: Pantalla en blanco

Causa: User_Setup.h mal configurado

Solución:
1. Verifica que hayas reemplazado User_Setup.h con la configuración para CYD
2. Reinicia Arduino IDE completamente
3. Vuelve a compilar y subir

### Problema: Táctil no responde

Causa: Calibración incorrecta o conflicto SPI

Solución:
1. Verifica que el código use el segundo bus SPI para el táctil:
    SPIClass touchscreenSpi = SPIClass(VSPI);
    touchscreenSpi.begin(XPT2046_CLK, XPT2046_MISO, XPT2046_MOSI, XPT2046_CS);
    ts.begin(touchscreenSpi);
2. Asegúrate de que SD.end() se llama antes de inicializar el táctil
3. Ajusta los valores X_MIN, X_MAX, Y_MIN, Y_MAX según tu placa

### Problema: Iconos no se muestran

Causa: BMP en formato incorrecto o SD no inicializada

Solución:
1. Verifica que los BMP sean 24-bit sin compresión
2. Verifica que sean exactamente 64x64 píxeles
3. Verifica que la ruta en el JSON coincida con la SD (ej: /icons/mute.bmp)
4. Formatea la SD en FAT32 (no exFAT ni NTFS)
5. Revisa el Serial Monitor para ver si aparece "SD Card inicializada."

### Problema: Python no ejecuta acciones

Causa: Permisos insuficientes o puerto COM incorrecto

Solución:
1. Ejecuta Python como Administrador
2. Verifica el puerto COM en el Administrador de Dispositivos
3. Asegúrate de que la ventana destino tenga el foco

### Problema: "Guru Meditation Error"

Causa: Memoria insuficiente o conflicto de librerías

Solución:
1. Reduce el tamaño de DynamicJsonDocument si es muy grande
2. Actualiza todas las librerías a la última versión
3. Reinicia la placa

### Problema: Conflicto entre SD y Táctil

Causa: Ambos dispositivos intentan usar el mismo bus SPI simultáneamente

Solución:
1. Usa la implementación actual que alterna entre SD y táctil
2. Asegúrate de llamar SD.end() antes de inicializar el táctil
3. Usa un segundo bus SPI (VSPI) para el táctil con pines dedicados

---

## Personalización Avanzada

### Cambiar Tamaño de Grid

Para usar 3x4 (12 botones) en lugar de 4x3:

    // En el firmware
    #define COLS 3
    #define ROWS 4
    #define BTN_W 106  // 320/3
    #define BTN_H 60   // 240/4

### Añadir Sonido al Tocar

Conecta un buzzer al pin 25 y añade:

    #define BUZZER_PIN 25

    void setup() {
      pinMode(BUZZER_PIN, OUTPUT);
    }

    void loop() {
      if (ts.touched()) {
        tone(BUZZER_PIN, 1000, 50);
      }
    }

### Configurar Múltiples Perfiles

Crea un sistema de perfiles en Python:

    PERFILES = {
        "streaming": {
            "buttons": [
                {"id": 0, "label": "OBS", "action": "open:obs64.exe"},
            ]
        },
        "oficina": {
            "buttons": [
                {"id": 0, "label": "Teams", "action": "open:teams.exe"},
            ]
        }
    }

    def cambiar_perfil(nombre):
        global CONFIG
        CONFIG = PERFILES[nombre]
        enviar_configuracion_a_cyd(CONFIG)

### Añadir Retroalimentación LED

La CYD tiene un LED RGB en los pines 4, 16, 17:

    #define LED_R 4
    #define LED_G 16
    #define LED_B 17

    void setup() {
      pinMode(LED_R, OUTPUT);
      pinMode(LED_G, OUTPUT);
      pinMode(LED_B, OUTPUT);
      digitalWrite(LED_R, HIGH);
      digitalWrite(LED_G, HIGH);
      digitalWrite(LED_B, HIGH);
    }

    void parpadear_led() {
      digitalWrite(LED_G, LOW);
      delay(100);
      digitalWrite(LED_G, HIGH);
    }

### Sincronización con Apps

Usa WebSocket o HTTP para integrar con OBS, Streamlabs, etc.:

    import obswebsocket
    from obswebsocket import obsws, requests

    ws = obsws("localhost", 4444, "tu_password")
    ws.connect()

    def execute_action(action_str):
        if action_str == "obs_start_stream":
            ws.call(requests.StartStreaming())
        elif action_str == "obs_stop_stream":
            ws.call(requests.StopStreaming())

---

## Créditos y Recursos

### Proyectos Relacionados
- ESP32-Cheap-Yellow-Display: https://github.com/witnessmenow/ESP32-Cheap-Yellow-Display
- TFT_eSPI: https://github.com/Bodmer/TFT_eSPI
- pyautogui: https://pyautogui.readthedocs.io/
