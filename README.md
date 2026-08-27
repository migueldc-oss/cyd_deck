# CYD Command Deck - Complete Documentation
Transform your ESP32-Cheap-Yellow-Display into a functional Command Deck like Stream Deck

---

## Table of Contents
1. Project Description
2. System Architecture
3. Requirements
4. Installation and Configuration
5. User Guide: Windows Service & GUI
6. Action & Command Reference
7. Icon Creation
8. Technical Documentation
9. Troubleshooting
10. Advanced Customization

---

## 1. Project Description

This project converts the ESP32-2432S028 board (known as CYD - Cheap Yellow Display) into a programmable macro controller similar to an Elgato Stream Deck. It communicates with Windows via USB/Serial.

### Features
- 12 programmable buttons (4x3 grid) on a 2.8" color touch screen (320x240).
- Customizable icons read directly from the CYD's MicroSD card.
- Dynamic configuration without reprogramming the ESP32.
- Windows Background Service with a System Tray icon (starts hidden by default).
- Modern GUI (CustomTkinter) for easy button configuration with live previews.
- Multi-Profile Support: create, save, and switch between different button layouts (e.g., Streaming, Office, Gaming) instantly.
- Smart SPI bus management: the CYD alternates between the SD card and Touchscreen to avoid hardware conflicts.

---

## 2. System Architecture

+-----------------------------------------------------------------+
|                         CYD (ESP32)                             |
|                                                                 |
|  +--------------+    +----------------+    +--------------+     |
|  |   Display    |    |  Controller    |    |  MicroSD     |     |
|  |   ST7789     |<-->|     SPI        |<-->|  (icons)     |     |
|  |  320x240     |    |  (HSPI)        |    |              |     |
|  +--------------+    +-------+--------+    +--------------+     |
|                              |                                  |
|  +--------------+    +-------v--------+                         |
|  |   Touch      |    |  Controller    |                         |
|  |  XPT2046     |<-->|     SPI        |                         |
|  |              |    |  (VSPI)        |                         |
|  +--------------+    +----------------+                         |
|                              |                                  |
+------------------------------|----------------------------------+
                               | USB/Serial (JSON)
                               v
                    +---------------------+
                    |    Windows PC       |
                    | cyd_deck_service.py |
                    |                     |
                    |  +---------------+  |
                    |  |  pyautogui    |  |
                    |  |  (keys/apps)  |  |
                    |  +---------------+  |
                    +---------------------+

### Important Consideration: SPI Bus Management
The CYD has a hardware peculiarity: the display, touch, and SD share the same SPI bus. This means they cannot operate simultaneously.

Implemented solution:
- Display: uses HSPI bus (dedicated pins).
- SD and Touch: alternate on VSPI bus.
- Smart flow: when receiving configuration, initialize SD, read icons, close SD (SD.end()), then initialize touch on the second SPI bus (VSPI). Touch remains active to detect presses.

---

## 3. Requirements

### Hardware
- ESP32-2432S028 board (CYD)
- MicroSD card formatted in FAT32 (recommended)
- USB-C or Micro-USB cable
- PC with Windows

### Software
- Arduino IDE or PlatformIO
- Python 3.7+ on Windows
- Arduino libraries: TFT_eSPI, XPT2046_Touchscreen, ArduinoJson (v6 or v7)
- Python packages:

    pip install pyserial pyautogui pystray customtkinter pillow

---

## 4. Installation and Configuration

### Step 1: Configure TFT_eSPI for CYD
Important: without this, the display will not work.
1. Go to: C:\Users\[YOUR_USER]\Documents\Arduino\libraries\TFT_eSPI\
2. Open User_Setup.h and replace ALL its content with the configuration provided in section 8.3.
3. Save the file and restart Arduino IDE.

### Step 2: Prepare the SD Card
1. Format the card in FAT32 (allocation size: 4096 bytes).
2. Create an /icons/ folder in the root.
3. Copy your BMP icons (see section 7).

### Step 3: Upload Firmware to CYD
1. Open Arduino IDE.
2. Install required libraries from the Library Manager.
3. Copy the firmware code cyd_deck.ino (see section 8.1).
4. Select Board: ESP32 Dev Module, Port: COMx.
5. Upload the sketch.

### Step 4: Configure Windows Service
1. Install Python from https://python.org
2. Open CMD or PowerShell and run the pip install command from section 3.
3. Save the cyd_deck_service.py script (see section 8.2).
4. Run as Administrator (required to send keys to some apps):

    python cyd_deck_service.py

By default it starts hidden in the system tray. Use --visible to show the window immediately.

---

## 5. User Guide: Windows Service & GUI

The application cyd_deck_service.py acts as a persistent background service, a configuration GUI, and a system tray app all in one.

### Startup Behavior
- Default: starts minimized in the Windows System Tray (near the clock).
- Arguments: use --visible or --show to open the configuration window on startup.

### System Tray Menu
Right-click the tray icon to access:
- Configure buttons: opens the main configuration window (default double-click action).
- Exit: completely closes the service and disconnects the CYD.

### Configuration Window
The window is fully resizable and divided into four sections:

1. Connection Bar:
   - COM Port: auto-detected dropdown.
   - Baudrate: usually 115200.
   - SD Drive: enter the Windows drive letter where the CYD SD card is mounted (e.g., E:) to enable icon previews.
   - Status: shows Connected (green) or Disconnected (red).

2. Profile Selector:
   - Dropdown: lists all *.json files in the application folder.
   - Load: loads the selected profile into the GUI.
   - New: creates a new blank profile file.

3. Button Grid (4x3):
   - Each button has a Live Preview on the left.
   - Name: text shown on the CYD.
   - Color: color picker for the button background.
   - Action: the command to execute (see section 6).
   - Icon: editable text field for the path (e.g., /icons/mute.bmp). Use the folder button to browse the SD card.

4. Action Bar:
   - Refresh Previews: reloads icons from the SD card.
   - Save: saves the current profile to disk.
   - Save and Send: saves and immediately pushes the layout to the CYD.
   - Minimize to Tray: hides the window; the service keeps running.

### Multi-Profile Workflow
You can create different profiles for different tasks (e.g., streaming.json, office.json).
- From the GUI: select a profile from the dropdown and click Load.
- From the CYD: assign the action "profile:streaming.json" to a button. Pressing it on the CYD will instantly switch the PC service to that profile and update the CYD screen.

---

## 6. Action & Command Reference

The Action field in the GUI accepts four types of commands:

### a) Keyboard Shortcuts
Keys joined with "+".

| Syntax                | Example use                |
|-----------------------|----------------------------|
| ctrl+shift+m          | Mute mic in Zoom/Teams     |
| ctrl+c / ctrl+v       | Copy / Paste               |
| alt+f4                | Close window               |
| win+d                 | Show desktop               |
| shift+f1              | Shift + function key F1    |
| ctrl+shift+escape     | Task Manager               |

Supported keys: f1-f12, enter, escape, tab, space, backspace, delete, insert, home, end, pageup, pagedown, up, down, left, right.

### b) Multimedia Keys
volumedown, volumeup, volumemute, playpause, nexttrack, prevtrack

### c) Application Launch ("open:" prefix)
- open:chrome.exe -> resolved by Windows PATH.
- open:C:/Program Files/obs-studio/bin/64bit/obs64.exe -> Full path: launched with its own folder as the working directory. Crucial for apps like OBS Studio to avoid "Failed to find locale" errors.

### d) Profile Switching ("profile:" prefix)
- profile:streaming.json -> loads the specified JSON profile, updates the GUI, and pushes the new layout to the CYD.

---

## 7. Icon Creation

Icons are stored ON THE CYD SD CARD, not on the PC. The PC only stores the path string.

### Technical Specifications
- Format: BMP (Windows Bitmap)
- Resolution: exactly 64x64 pixels
- Color depth: 24 bits (RGB, no alpha channel)
- Compression: none (uncompressed)

### Quick Method (Windows Paint)
1. Open Paint, paste image, Resize -> Pixels (64x64), uncheck "Maintain aspect ratio".
2. File -> Save as -> 24-bit Bitmap.

### Automatic Method (Python converter)

    from PIL import Image
    import os

    def convert_to_bmp(input_file, output_file):
        img = Image.open(input_file)
        img = img.resize((64, 64), Image.Resampling.LANCZOS)
        if img.mode == 'RGBA':
            background = Image.new('RGB', (64, 64), (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(output_file, 'BMP', format='BMP')

### Design Tips
- Simulated transparency: paint the icon background the exact same color as the button color in the JSON (e.g., #FF0000).
- High contrast: bright colors on dark backgrounds.
- Avoid fine details: at 64x64, simple and recognizable shapes work best.

### Folder Structure on SD

    / (SD root)
    +-- icons/
    |   +-- mute.bmp
    |   +-- camera.bmp
    |   +-- obs.bmp
    |   +-- chrome.bmp
    |   +-- ...

---

## 8. Technical Documentation

### 8.1 ESP32 Firmware (cyd_deck.ino)
The firmware handles display rendering, touch detection, and SD card reading.
- SPI management: the display uses HSPI. The SD and Touch share VSPI. The firmware initializes the SD only when a configuration is received, reads the icons, calls SD.end(), and then initializes the Touchscreen on VSPI to prevent bus conflicts.
- Communication: listens for JSON over Serial. Expects {"buttons":[...]} and replies with {"status":"updated"}. Emits {"type":"press","id":N} on touch.
- Backlight: GPIO 21, brightness adjustable via analogWrite(TFT_BL, value) with 0-255.

Key pin definition:

    #define XPT2046_IRQ 36
    #define XPT2046_MOSI 32
    #define XPT2046_MISO 39
    #define XPT2046_CLK 25
    #define XPT2046_CS 33
    #define SD_CS 5
    #define TFT_BL 21
    #define COLS 4
    #define ROWS 3
    #define BTN_W 80
    #define BTN_H 80
    #define ICON_SIZE 64

### 8.2 Windows Service (cyd_deck_service.py)
A single-file Python application combining three roles:
1. Service: background thread listening to Serial and executing actions.
2. GUI: main thread running CustomTkinter for configuration.
3. Tray: daemon thread running pystray for background persistence.

Environment detection (portable .exe support):

    if getattr(sys, 'frozen', False):
        BASE_DIR = os.path.dirname(sys.executable)   # packaged .exe
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # source

Profile system: profiles are standard JSON files stored in BASE_DIR. The service scans for *.json files to populate the GUI dropdown. Switching profiles updates the in-memory config_data, refreshes the UI, and serializes the new layout to the CYD. The special action "profile:name.json" can be triggered from a CYD button.

Action engine: supports keyboard shortcuts (pyautogui.hotkey), multimedia keys (pyautogui.press), application launch with working-directory fix (subprocess.Popen with cwd), and profile switching.

### 8.3 User_Setup.h Configuration
Replace your TFT_eSPI/User_Setup.h with this exact configuration for the CYD:

    #define USER_SETUP_INFO "User_Setup"
    #define ST7789_DRIVER
    #define TFT_RGB_ORDER TFT_BGR
    #define TFT_INVERSION_OFF

    #define TFT_BL 21
    #define TFT_BACKLIGHT_ON HIGH

    #define TFT_MISO 12
    #define TFT_MOSI 13
    #define TFT_SCLK 14
    #define TFT_CS 15
    #define TFT_DC 2
    #define TFT_RST -1

    #define LOAD_GLCD
    #define LOAD_FONT2
    #define LOAD_FONT4
    #define LOAD_FONT6
    #define LOAD_FONT7
    #define LOAD_FONT8
    #define LOAD_GFXFF
    #define SMOOTH_FONT

    #define SPI_FREQUENCY 55000000
    #define SPI_READ_FREQUENCY 20000000
    #define SPI_TOUCH_FREQUENCY 2500000
    #define USE_HSPI_PORT

Pins configured for CYD: TFT_MISO 12, TFT_MOSI 13, TFT_SCLK 14, TFT_CS 15, TFT_DC 2, TFT_RST -1, TFT_BL 21. Driver ST7789, color order BGR, SPI 55 MHz on HSPI (to free VSPI for touch).

---

## 9. Troubleshooting

Blank display
  Cause: User_Setup.h misconfigured.
  Fix: replace with the config in 8.3 and restart Arduino IDE.

Touch not responding
  Cause: SPI conflict or calibration.
  Fix: ensure firmware calls SD.end() before ts.begin(). Adjust map() values in cyd_deck.ino.

Icons not showing
  Cause: wrong BMP format or path.
  Fix: ensure 64x64 24-bit uncompressed BMP. Path must match exactly (e.g., /icons/mute.bmp).

OBS shows "Failed to find locale/en-US.ini"
  Cause: wrong working directory.
  Fix: use the full path in the action: open:C:/Program Files/.../obs64.exe

Keys not received by some applications
  Cause: privilege mismatch.
  Fix: run cyd_deck_service.py (or the .exe) as Administrator.

Profile switch from CYD does not work
  Cause: file not found.
  Fix: ensure the .json file is in the same folder as the .exe/script. Check cyd_deck.log.

Status stays Disconnected
  Checks: correct COM port (Device Manager); no other program holding the port; correct baudrate; CH340 driver installed.

---

## 10. Advanced Customization

### Change Grid Size
To use a 3x4 grid instead of 4x3 in cyd_deck.ino:

    #define COLS 3
    #define ROWS 4
    #define BTN_W 106  // 320/3
    #define BTN_H 60   // 240/4

### Adjust Display Brightness (PWM)
The backlight is on GPIO 21:

    analogWrite(TFT_BL, 120); // 0 = off, 255 = max

### Add LED Feedback
The CYD has an RGB LED on pins 4, 16, 17:

    #define LED_G 16
    // On touch:
    digitalWrite(LED_G, LOW); delay(100); digitalWrite(LED_G, HIGH);

### App Synchronization (OBS/Streamlabs)
You can integrate with OBS using WebSockets in the Python service:

    from obswebsocket import obsws, requests
    ws = obsws("localhost", 4444, "password")
    ws.connect()
    # ws.call(requests.StartStreaming())

---

## Credits and Resources
- Hardware: ESP32-Cheap-Yellow-Display (github.com/witnessmenow/ESP32-Cheap-Yellow-Display)
- Libraries: TFT_eSPI (github.com/Bodmer/TFT_eSPI), pyautogui, CustomTkinter
