# CYD Stream Deck - Service Application Documentation
## cyd_deck_service.py (Windows host service + configuration GUI + system tray)

---

## Table of Contents

1. Overview
2. Functional Documentation
   2.1 Purpose
   2.2 Feature Summary
   2.3 Startup Behavior and Command-Line Arguments
   2.4 System Tray (Service Mode)
   2.5 Configuration Window
   2.6 Button Configuration Fields
   2.7 Action Syntax Reference
   2.8 Icon Management
   2.9 Configuration File (config.json)
3. Technical Documentation
   3.1 Architecture and Threading Model
   3.2 Environment Detection and File Layout
   3.3 Dependencies
   3.4 Main Class: CYDStreamDeckApp
   3.5 Button Configuration Frame: ButtonConfigFrame
   3.6 Serial Communication Protocol
   3.7 Action Execution Engine
   3.8 Logging
4. Installation, Build and Deployment
   4.1 Requirements
   4.2 Running from Source
   4.3 Building the .exe
   4.4 Auto-start with Windows
5. Troubleshooting
6. Appendix: Division of Responsibilities (PC vs CYD)

---

## 1. Overview

cyd_deck_service.py is a single-file Windows application that turns an
ESP32-2432S028 "CYD" (Cheap Yellow Display) board into a programmable
macro pad / Stream Deck clone.

The application combines three roles in one program:

  1. SERVICE   - Runs in the background (system tray), keeps the serial
                 connection alive, listens for button presses coming from
                 the CYD and executes the mapped actions on Windows
                 (keyboard shortcuts, multimedia keys, launching apps).
  2. GUI       - A resizable configuration window (CustomTkinter) used to
                 edit the 12 buttons: name, background color, icon path
                 (on the CYD SD card) and action.
  3. TRAY      - A system-tray icon that keeps the service alive when the
                 window is closed and gives access to the main commands.

The CYD firmware (cyd_deck_service.ino) is responsible for rendering the buttons
and detecting touches; the service application is responsible for
configuration, persistence and OS-level action execution.

---

## 2. Functional Documentation

### 2.1 Purpose

Provide a persistent, user-friendly host application that:
- Sends a fully parameterizable button layout (labels, colors, icons)
  to the CYD over USB/Serial.
- Reacts to touch events from the CYD by executing Windows actions.
- Allows reconfiguration at any time without reflashing the ESP32.

### 2.2 Feature Summary

- 12 programmable buttons (4 x 3 grid), matching the CYD layout.
- Per-button: name, background color (color picker), icon path
  (editable text field), action (free text).
- Live visual preview of each button (color + icon + label).
- Icon preview reads the BMP directly from the SD card when it is
  mounted in Windows (via the "SD drive" field).
- Persistent configuration stored in config.json.
- System-tray resident service (starts hidden by default).
- Resizable configuration window.
- Automatic COM port detection.
- Connection status indicator (Connected / Disconnected).
- Hotkey, multimedia and application-launch action engine.
- Working-directory-aware application launching (fixes OBS
  "Failed to find locale/en-US.ini" and similar issues).
- Timestamped log file (cyd_deck_service.log).

### 2.3 Startup Behavior and Command-Line Arguments

By default the application starts MINIMIZED in the system tray:
the serial service and the tray icon start immediately and the
configuration window stays hidden.

Command-line arguments:

  (none)        Start hidden in the tray (default).
  --visible     Show the configuration window at startup.
  --show        Same as --visible.

Closing the window (X button or "Minimize to tray") never terminates
the service; it only hides the window (withdraw). The only way to exit
completely is the tray menu entry "Exit".

### 2.4 System Tray (Service Mode)

The tray icon exposes the following menu:

  Configure buttons   Shows/raises the configuration window
                      (also the default double-click action).
  Reconnect CYD       Reloads config.json, reconnects the serial port
                      and re-sends the configuration to the device.
  Reload config       Re-reads config.json and refreshes the GUI fields
                      without touching the serial connection.
  -----------------   Separator
  Exit                Stops the tray icon, closes the serial port and
                      terminates the application.

While running, the service automatically:
- Connects to the configured COM port at startup.
- Waits for the CYD "ready" handshake.
- Pushes the button configuration.
- Listens forever for touch events and executes actions.

### 2.5 Configuration Window

The window is resizable (minimum size 800x550). Layout, top to bottom:

  1. Title and subtitle.
  2. Connection bar:
       - COM port combo (auto-detected list of available ports).
       - Baudrate combo (9600 / 115200 / 230400 / 460800).
       - SD drive entry (Windows drive letter where the CYD SD card is
         mounted, e.g. "E:"). Used only for icon preview and browsing.
       - Connection status label (green "Connected" / red "Disconnected").
  3. Button grid: 4 columns x 3 rows of ButtonConfigFrame widgets,
     all expanding with the window.
  4. Action bar:
       - Refresh previews   Re-reads icon files from the SD drive.
       - Save               Writes config.json.
       - Save and Send      Writes config.json and pushes the
                            configuration to the CYD immediately.
       - Minimize to tray   Hides the window (service keeps running).

### 2.6 Button Configuration Fields

Each button frame shows a live preview on the left (spanning all rows)
and four rows of fields:

  Row 0: [ID]  Name      Text shown on the CYD button.
  Row 1:       Color     Color-picker button + hex label. Sets the
                         button background color on the CYD.
  Row 2:       Action    Free-text action (see 2.7). Executed on
                         Windows when the button is pressed.
  Row 3:       Icon      EDITABLE TEXT field with the icon path as the
                         CYD firmware expects it, e.g. /icons/mute.bmp
                         The BMP file lives on the CYD SD card; the PC
                         never transfers the image.
                         An optional folder button helps browse the SD
                         (when the SD drive is configured) and fills the
                         field with the correct relative path.

The preview updates live when the name or color change, and the icon
preview is loaded from <SD drive>/<icon path> when available.

### 2.7 Action Syntax Reference

The Action field accepts three kinds of values:

  a) Keyboard shortcuts: keys joined with "+"
       ctrl+shift+m        Mute mic in Zoom/Teams/Discord
       ctrl+shift+v        Toggle camera
       ctrl+c / ctrl+v     Copy / paste
       alt+f4              Close window
       alt+tab             Switch window
       win+d               Show desktop
       shift+f1            Shift + function key F1
       ctrl+shift+escape   Task manager

     Function keys: f1..f12
     Special keys: enter, escape, tab, space, backspace, delete,
                   insert, home, end, pageup, pagedown,
                   up, down, left, right

  b) Multimedia keys (single keyword):
       volumedown, volumeup, volumemute,
       playpause, nexttrack, prevtrack

  c) Application launch: "open:" prefix
       open:chrome.exe                 Resolved by the system (PATH).
       open:C:/Program Files/obs-studio/bin/64bit/obs64.exe
                                       Full path: launched with its own
                                       folder as working directory.

     NOTE: Always use the FULL PATH for applications that need their
     own working directory (OBS Studio is the typical case). The
     service automatically sets cwd to the executable's folder when a
     full path is given.

### 2.8 Icon Management

- Icons are stored ON THE CYD SD CARD, typically in /icons/.
- The PC application only stores the path string in config.json.
- The user copies BMP files to the SD card manually (with Windows
  Explorer) while the card is mounted.
- Recommended icon format (enforced by the CYD firmware parser):
    BMP, 24-bit RGB, uncompressed, exactly 64x64 pixels.
- If the "SD drive" field is set (e.g. E:), the GUI can preview icons
  and the browse helper can auto-fill paths.

### 2.9 Configuration File (config.json)

Stored next to the executable/script. Schema:

{
  "port": "COM3",
  "baudrate": 115200,
  "sd_drive": "E:",
  "buttons": [
    {
      "id": 0,
      "label": "Mute",
      "color": "#ff0000",
      "icon": "/icons/mute.bmp",
      "action": "ctrl+shift+m"
    },
    ... (12 entries, id 0..11)
  ]
}

The file is created automatically with default values on first run if
it does not exist.

---

## 3. Technical Documentation

### 3.1 Architecture and Threading Model

Three concurrent execution contexts:

  MAIN THREAD
    CustomTkinter / Tkinter mainloop. Owns all widgets. The window is
    created at startup and hidden (withdraw) unless --visible/--show.

  SERIAL THREAD (daemon)
    serial_service():
      sleep(1) -> connect_cyd() -> send_config_to_cyd() -> listen_cyd()
    listen_cyd() is an infinite loop polling ser.in_waiting every 50 ms,
    parsing JSON lines and spawning one short-lived thread per action.

  TRAY THREAD (daemon)
    setup_tray(): builds the pystray icon and runs icon.run()
    (blocking inside this thread).

Cross-thread rules:
- Tray callbacks never touch Tk widgets directly; they schedule UI
  work on the main thread via self.after(0, callable).
- Actions (pyautogui / subprocess) run in their own daemon threads so
  the serial listener is never blocked.

### 3.2 Environment Detection and File Layout

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)   # packaged .exe
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # source

Files resolved relative to BASE_DIR:
  config.json     persistent configuration
  cyd_deck.log    append-only log
  icon.ico        tray icon (auto-created with a default image if missing)

This makes the .exe fully portable: it can be copied to any folder
(including a USB stick) and keeps its configuration with it.

### 3.3 Dependencies

  pyserial          serial port communication
  pyautogui         keyboard / multimedia key synthesis
  pystray           system tray icon
  Pillow (PIL)      tray icon image + icon previews
  customtkinter     modern Tkinter theme/widgets

### 3.4 Main Class: CYDStreamDeckApp

Key members and methods:

  __init__
    Builds state (ser, connected, running, tray_icon), loads config,
    builds the UI, starts serial and tray threads, applies startup
    visibility (hidden by default).

  load_config / save_config_to_file / get_default_config
    JSON persistence with fallback defaults (12 grey buttons).

  get_sd_drive
    Returns the configured SD drive letter for preview/browsing.

  setup_ui
    Resizable grid layout: connection bar, 4x3 button grid with
    uniform row/column weights, action bar.

  serial_service / connect_cyd / send_config_to_cyd / listen_cyd
    Serial lifecycle (see 3.6).

  execute_action
    Action engine (see 3.7).

  collect_config
    Reads every ButtonConfigFrame plus connection fields into
    self.config_data.

  save_config / save_and_send
    Persist to disk; optionally push to the device in a thread.

  setup_tray + tray_* callbacks
    pystray menu; UI-affecting callbacks are marshalled with
    self.after(0, ...).

  show_window / on_close_window / quit_app
    deiconify+lift+focus / withdraw / full shutdown (icon.stop,
    ser.close, destroy).

  reload_ui_from_config
    Refreshes all widgets after "Reload configuration".

### 3.5 Button Configuration Frame: ButtonConfigFrame

Layout (grid):
  column 0: preview frame (rowspan=4, 80x100 px, fixed size)
  row 0: ID label + Name entry
  row 1: Color row (picker button + hex label)
  row 2: Action row (single entry, own row for readability)
  row 3: Icon row (editable entry + optional browse button)

Behavior:
- Name <KeyRelease>  -> preview label refresh.
- Color picker       -> stores lowercase hex, refreshes preview.
- Icon <KeyRelease>  -> reloads preview from SD drive if possible.
- Browse button      -> opens a file dialog rooted at <SD drive>/icons
                        and writes the relative "/icons/name.bmp"
                        path into the icon entry.
- get_data()         -> returns the button dict stored in config.json.

Icon full-path resolution for previews:
  rel  = icon.lstrip("/").replace("/", os.sep)
  path = os.path.join(sd_drive, rel)

### 3.6 Serial Communication Protocol

Physical layer: USB serial, 115200 8N1 (configurable).
Message layer: one JSON object per line, terminated with "\n".

CYD -> PC:
  {"status":"ready"}            firmware booted, awaiting config
  {"status":"updated"}          config parsed and drawn
  {"type":"press","id":N}       button N (0..11) touched
  {"error":"sd_failed"}         SD card not initialized
  {"error":"json_parse"}        malformed JSON received

PC -> CYD:
  {"buttons":[ {"id":0,"label":"...","color":"#rrggbb",
                "icon":"/icons/x.bmp","action":"..."}, ... ]}

Handshake at startup / reconnect:
  1. PC opens COM port, waits ~2 s (ESP32 auto-reset).
  2. PC waits up to 10 s for {"status":"ready"}.
  3. PC sends the buttons payload.
  4. PC waits up to 10 s for {"status":"updated"}.

Runtime:
  The listener parses incoming lines; on "press" it looks up the
  button by id in the in-memory config and executes its action.

Note on firmware constraints (context): the CYD alternates SD and
touch on the shared SPI bus; the SD is released (SD.end()) after the
first configuration is drawn, then the touchscreen is started on a
second SPI bus (VSPI). The service is unaffected by this detail but
explains why icons are only (re)loaded when a config is received.

### 3.7 Action Execution Engine

execute_action(action_str):

  if action starts with "open:":
      path = remainder, separators normalized
      if os.path.isfile(path):
          subprocess.Popen([path], cwd=dirname(abspath(path)))
          # cwd fix: apps like OBS Studio need their own install
          # directory as working directory, otherwise they fail with
          # "Failed to find locale/en-US.ini".
      else:
          subprocess.Popen(path, shell=True)   # name resolved by OS
  elif action in multimedia list:
      pyautogui.press(action)
  else:
      pyautogui.hotkey(*[k.strip() for k in action.split('+')])

Every execution is logged; exceptions are caught and logged, never
crashing the service.

### 3.8 Logging

log(msg) writes "[YYYY-mm-dd HH:MM:SS] msg" to stdout and appends it
to cyd_deck.log in BASE_DIR. Logged events include: startup paths,
connection results, config sent/updated, received frames, executed
actions and errors.

---

## 4. Installation, Build and Deployment

### 4.1 Requirements

  Python 3.7+ (Windows)
  pip install pyserial pyautogui pystray pillow customtkinter

### 4.2 Running from Source

  python cyd_deck_service.py            # starts hidden in the tray
  python cyd_deck_service.py --visible  # starts with the window open

### 4.3 Building the .exe

  pip install pyinstaller
  pyinstaller --onefile --noconsole --icon=icon.ico ^
              --name="CYD_StreamDeck" cyd_deck_service.py

Deploy folder (portable):
  CYD_StreamDeck.exe
  config.json      (created on first run)
  cyd_deck.log     (created on first run)
  icon.ico         (created on first run if missing)

### 4.4 Auto-start with Windows

  1. Win+R -> shell:startup
  2. Create a shortcut to CYD_StreamDeck.exe there.
  Since the app starts hidden by default, it boots silently into the
  tray. To open the window at boot, add "--visible" to the shortcut
  target.

---

## 5. Troubleshooting

  Symptom: OBS shows "Failed to find locale/en-US.ini".
  Cause:   OBS launched with a wrong working directory.
  Fix:     Use a FULL PATH in the action, e.g.
           open:C:/Program Files/obs-studio/bin/64bit/obs64.exe
           The service then starts it with cwd = its own folder.
           If it still fails, verify that
           <OBS folder>\data\locale\en-US.ini exists (repair/reinstall
           OBS otherwise).

  Symptom: Status stays "Disconnected".
  Checks:  Correct COM port (Device Manager); no other program holding
           the port (close Arduino Serial Monitor); correct baudrate;
           CH340/CP2102 driver installed; cable is data-capable.
           Then use tray -> "Reconnect CYD".

  Symptom: Keys are not received by some applications.
  Cause:   Target app runs with higher privileges (admin/elevated).
  Fix:     Run CYD_StreamDeck.exe as Administrator.

  Symptom: Icon previews do not appear in the GUI.
  Checks:  "SD drive" field set to the mounted drive letter; SD card
           inserted in the PC; icon path typed exactly as the firmware
           expects (/icons/name.bmp); file is a valid BMP.
           Use "Refresh previews" after changes.

  Symptom: CYD does not redraw after saving.
  Checks:  Service connected (green status); use "Save and Send";
           check cyd_deck.log for "updated" or error frames.

---

## 6. Appendix: Division of Responsibilities (PC vs CYD)

  PC service (cyd_deck_service.py):
    - Owns the configuration (config.json) and the editing GUI.
    - Owns OS action execution (keys, media, apps).
    - Owns connection lifecycle and reconnection.
    - Never transfers image data; only icon PATH strings.

  CYD firmware (cyd_deck.ino):
    - Renders the 4x3 grid (background color, BMP icon, label).
    - Reads BMP icons from its own SD card.
    - Debounces touches and emits {"type":"press","id":N}.
    - Manages the shared SPI bus (SD vs touchscreen).

---
