# CYD Stream Deck - Service Application Documentation
## cyd_deck_service.py (Windows host service + configuration GUI + system tray)

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. Functional Documentation](#2-functional-documentation)
  - [2.1 Purpose](#21-purpose)
  - [2.2 Feature Summary](#22-feature-summary)
  - [2.3 Startup Behavior and Command-Line Arguments](#23-startup-behavior-and-command-line-arguments)
  - [2.4 System Tray (Service Mode)](#24-system-tray-service-mode)
  - [2.5 Configuration Window](#25-configuration-window)
  - [2.6 Button Configuration Fields](#26-button-configuration-fields)
  - [2.7 Profile Management](#27-profile-management)
  - [2.8 Action Syntax Reference](#28-action-syntax-reference)
  - [2.9 Icon Management](#29-icon-management)
  - [2.10 Configuration Files](#210-configuration-files)
- [3. Technical Documentation](#3-technical-documentation)
  - [3.1 Architecture and Threading Model](#31-architecture-and-threading-model)
  - [3.2 Environment Detection and File Layout](#32-environment-detection-and-file-layout)
  - [3.3 Dependencies](#33-dependencies)
  - [3.4 Main Class: CYDStreamDeckApp](#34-main-class-cydstreamdeckapp)
  - [3.5 Button Configuration Frame: ButtonConfigFrame](#35-button-configuration-frame-buttonconfigframe)
  - [3.6 Serial Communication Protocol](#36-serial-communication-protocol)
  - [3.7 Action Execution Engine](#37-action-execution-engine)
  - [3.8 Profile Switching System](#38-profile-switching-system)
  - [3.9 Logging](#39-logging)
- [4. Installation, Build and Deployment](#4-installation-build-and-deployment)
  - [4.1 Requirements](#41-requirements)
  - [4.2 Running from Source](#42-running-from-source)
  - [4.3 Building the .exe](#43-building-the-exe)
  - [4.4 Auto-start with Windows](#44-auto-start-with-windows)
- [5. Troubleshooting](#5-troubleshooting)
- [6. Appendix: Division of Responsibilities (PC vs CYD)](#6-appendix-division-of-responsibilities-pc-vs-cyd)



---

## 1. Overview

cyd_deck_service.py is a single-file Windows application that turns an ESP32-2432S028 "CYD" (Cheap Yellow Display) board into a programmable macro pad / Stream Deck clone.

The application combines three roles in one program:

  1. SERVICE   - Runs in the background (system tray), keeps the serial
                 connection alive, listens for button presses coming from
                 the CYD and executes the mapped actions on Windows
                 (keyboard shortcuts, multimedia keys, launching apps).
  2. GUI       - A resizable configuration window (CustomTkinter) used to
                 edit the 12 buttons: name, background color, icon path
                 (on the CYD SD card), action, and manage multiple profiles.
  3. TRAY      - A system-tray icon that keeps the service alive when the
                 window is closed and gives access to the main commands.

The CYD firmware (cyd_deck.ino) is responsible for rendering the buttons
and detecting touches; the service application is responsible for
configuration, persistence, profile management and OS-level action execution.

---

## 2. Functional Documentation

### 2.1 Purpose

Provide a persistent, user-friendly host application that:
- Sends a fully parameterizable button layout (labels, colors, icons)
  to the CYD over USB/Serial.
- Reacts to touch events from the CYD by executing Windows actions.
- Allows reconfiguration at any time without reflashing the ESP32.
- Supports multiple configuration profiles that can be switched
  dynamically from the GUI or from the CYD itself.

### 2.2 Feature Summary

- 12 programmable buttons (4 x 3 grid), matching the CYD layout.
- Per-button: name, background color (color picker), icon path
  (editable text field), action (free text).
- Live visual preview of each button (color + icon + label).
- Icon preview reads the BMP directly from the SD card when it is
  mounted in Windows (via the "SD drive" field).
- Multiple profile support: Create, load and switch between different
  configuration files (*.json).
- Profile switching from CYD: Special action "profile:filename.json"
  that allows the CYD to trigger a profile change.
- Persistent configuration stored in config.json (default) or custom files.
- System-tray resident service (starts hidden by default).
- Resizable configuration window.
- Automatic COM port detection.
- Connection status indicator (Connected / Disconnected).
- Hotkey, multimedia and application-launch action engine.
- Working-directory-aware application launching (fixes OBS
  "Failed to find locale/en-US.ini" and similar issues).
- Timestamped log file (cyd_deck.log).

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
  -----------------   Separator
  Exit                Stops the tray icon, closes the serial port and
                      terminates the application.

While running, the service automatically:
- Connects to the configured COM port at startup.
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
  3. Profile selector bar:
       - Profile combo (lists all *.json files in the application folder).
       - "Load" button (loads the selected profile).
       - "New" button (creates a new profile file).
  4. Button grid: 4 columns x 3 rows of ButtonConfigFrame widgets,
     all expanding with the window.
  5. Action bar:
       - Refresh previews   Re-reads icon files from the SD drive.
       - Save               Writes the current profile to disk.
       - Save and Send      Writes the profile and pushes the
                            configuration to the CYD immediately.
       - Minimize to tray   Hides the window (service keeps running).

### 2.6 Button Configuration Fields

Each button frame shows a live preview on the left (spanning all rows)
and four rows of fields:

  Row 0: [ID]  Name      Text shown on the CYD button.
  Row 1:       Color     Color-picker button + hex label. Sets the
                         button background color on the CYD.
  Row 2:       Action    Free-text action (see 2.8). Executed on
                         Windows when the button is pressed.
                         Can also be "profile:filename.json" to switch
                         to another configuration profile.
  Row 3:       Icon      EDITABLE TEXT field with the icon path as the
                         CYD firmware expects it, e.g. /icons/mute.bmp
                         The BMP file lives on the CYD SD card; the PC
                         never transfers the image.
                         An optional folder button helps browse the SD
                         (when the SD drive is configured) and fills the
                         field with the correct relative path.

The preview updates live when the name or color change, and the icon
preview is loaded from <SD drive>/<icon path> when available.

### 2.7 Profile Management

What is a profile?
A profile is a complete button configuration stored in a separate JSON file.
You can create multiple profiles for different scenarios (streaming, office,
gaming, etc.) and switch between them instantly.

Creating a new profile:
1. Click the "New" button in the profile selector bar.
2. Choose a filename (e.g., "streaming.json", "office.json").
3. A new profile is created with default empty buttons.
4. Configure the buttons as needed and click "Save".

Loading a profile:
1. Select a profile from the dropdown combo (shows all *.json files).
2. Click "Load" to load it into the configuration window.
3. The window updates to show the buttons from that profile.

Switching profiles from the CYD:
You can configure a button to switch to another profile by using the
special action syntax:

  profile:streaming.json

When this button is pressed on the CYD:
1. The service receives the action.
2. It loads the specified profile file.
3. It updates the GUI to reflect the new profile.
4. It automatically sends the new configuration to the CYD.
5. The CYD display updates with the new button layout.

Profile file location:
All profile files (*.json) are stored in the same folder as the
application executable (or script). The default profile is "config.json".

### 2.8 Action Syntax Reference

The Action field accepts four kinds of values:

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

  d) Profile switch: "profile:" prefix
       profile:streaming.json          Loads and activates the
                                       "streaming.json" profile.
       profile:office.json             Switches to office configuration.
       profile:gaming.json             Switches to gaming configuration.

     When a profile action is triggered:
     - The service loads the specified JSON file.
     - Updates the GUI to show the new configuration.
     - Automatically sends the new button layout to the CYD.
     - The CYD display refreshes with the new buttons.

### 2.9 Icon Management

- Icons are stored ON THE CYD SD CARD, typically in /icons/.
- The PC application only stores the path string in the profile JSON.
- The user copies BMP files to the SD card manually (with Windows
  Explorer) while the card is mounted.
- Recommended icon format (enforced by the CYD firmware parser):
    BMP, 24-bit RGB, uncompressed, exactly 64x64 pixels.
- If the "SD drive" field is set (e.g. E:), the GUI can preview icons
  and the browse helper can auto-fill paths.

### 2.10 Configuration Files

Default profile:
  config.json - The default configuration file loaded at startup.

Custom profiles:
  Any *.json file in the application folder is treated as a profile.
  Examples:
    - streaming.json
    - office.json
    - gaming.json
    - presentation.json

File discovery:
The application automatically scans the application folder for all
*.json files and lists them in the profile selector combo.

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
- Profile switching operations are marshalled to the main thread to
  safely update the UI.

### 3.2 Environment Detection and File Layout

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)   # packaged .exe
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # source

Files resolved relative to BASE_DIR:
  config.json          default persistent configuration
  *.json               additional profile files
  cyd_deck.log         append-only log
  icon.ico             tray icon (auto-created with a default image if missing)

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

  get_json_files
    Scans BASE_DIR for all *.json files and returns sorted list.

  load_profile(filename)
    Loads a specific profile file and updates the UI.

  create_new_profile()
    Opens a save dialog to create a new profile file with default config.

  refresh_profile_list()
    Updates the profile combo box with current *.json files.

  get_sd_drive
    Returns the configured SD drive letter for preview/browsing.

  setup_ui
    Resizable grid layout: connection bar, profile selector, 4x3 button
    grid with uniform row/column weights, action bar.

  on_profile_changed / load_selected_profile
    Handles profile selection and loading from the UI.

  serial_service / connect_cyd / send_config_to_cyd / listen_cyd
    Serial lifecycle.

  execute_action
    Action engine including profile switching.

  switch_profile_from_cyd
    Handles profile change requests coming from the CYD.

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
    Refreshes all widgets after loading a profile.

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
- get_data()         -> returns the button dict stored in the profile.

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

Handshake at startup:
  1. PC opens COM port, waits ~2 s (ESP32 auto-reset).
  2. PC sends the buttons payload.
  3. PC waits up to 10 s for {"status":"updated"}.

Runtime:
  The listener parses incoming lines; on "press" it looks up the
  button by id in the in-memory config and executes its action.

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

  elif action starts with "profile:":
      profile_name = extract filename
      switch_profile_from_cyd(profile_name)
      # Loads the profile, updates UI, sends to CYD

  elif action in multimedia list:
      pyautogui.press(action)

  else:
      pyautogui.hotkey(*[k.strip() for k in action.split('+')])

Every execution is logged; exceptions are caught and logged, never
crashing the service.

### 3.8 Profile Switching System

From the GUI:
  load_selected_profile():
      selected = profile_combo.get()
      if selected:
          load_profile(selected)
          # Updates UI
          # Updates profile combo

From the CYD:
  switch_profile_from_cyd(profile_name):
      filepath = os.path.join(BASE_DIR, profile_name)
      if not os.path.exists(filepath):
          log error
          return
      
      current_config_file = filepath
      config_data = load_config(filepath)
      
      # Update UI on main thread
      after(0, reload_ui_from_config)
      after(0, update profile_combo)
      
      # Send new config to CYD
      if connected:
          send_config_to_cyd()

Key features:
- Thread-safe UI updates via after(0, ...)
- Automatic CYD reconfiguration
- Profile combo stays in sync
- Error handling for missing files

### 3.9 Logging

log(msg) writes "[YYYY-mm-dd HH:MM:SS] msg" to stdout and appends it
to cyd_deck.log in BASE_DIR. Logged events include: startup paths,
connection results, config sent/updated, received frames, executed
actions, profile switches and errors.

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
  config.json          (created on first run, default profile)
  streaming.json       (optional, custom profiles)
  office.json          (optional, custom profiles)
  cyd_deck.log         (created on first run)
  icon.ico             (created on first run if missing)

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

  Symptom: Keys are not received by some applications.
  Cause:   Target app runs with higher privileges (admin/elevated).
  Fix:     Run CYD_StreamDeck.exe as Administrator.

  Symptom: Icon previews do not appear in the GUI.
  Checks:  "SD drive" field set to the mounted drive letter; SD card
           inserted in the PC; icon path typed exactly as the firmware
           expects (/icons/name.bmp); file is a valid BMP.
           Use "Refresh previews" after changes.

  Symptom: Profile switch from CYD doesn't work.
  Checks:  Profile file exists in the application folder; filename in
           action matches exactly (case-sensitive); check log for
           "Cambiando perfil desde CYD" and any errors.

  Symptom: Profile not found when loading.
  Checks:  File must be in the same folder as the .exe/script; filename
           must end with .json; check cyd_deck.log for load errors.

---

## 6. Appendix: Division of Responsibilities (PC vs CYD)

  PC service (cyd_deck_service.py):
    - Owns the configuration profiles (multiple *.json files).
    - Owns the editing GUI and profile management.
    - Owns OS action execution (keys, media, apps, profile switches).
    - Owns connection lifecycle and reconnection.
    - Never transfers image data; only icon PATH strings.
    - Handles profile switching requests from the CYD.

  CYD firmware (cyd_deck.ino):
    - Renders the 4x3 grid (background color, BMP icon, label).
    - Reads BMP icons from its own SD card.
    - Debounces touches and emits {"type":"press","id":N}.
    - Manages the shared SPI bus (SD vs touchscreen).
    - Can trigger profile changes by sending special actions.

---
