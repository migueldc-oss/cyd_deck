import serial
import json
import time
import pyautogui

# --- CONFIGURACIÓN DE TU STREAM DECK ---
# Aquí defines qué hace cada botón. 
# 'action' puede ser teclas (ctrl+c), abrir apps, o macros.
CONFIG = {
    "buttons": [
        # Fila 1
        {"id": 0, "label": "Pretty print", "color": "#1A1819", "icon": "/refresh.bmp", "action": "shift+f1"},
        {"id": 1, "label": "Activar", "color": "#641271", "icon": "/activate.bmp", "action": "ctrl+f3"},
        {"id": 2, "label": "Copy", "color": "#1A1819", "icon": "/copy.bmp", "action": "ctrl+alt+down"},
        {"id": 3, "label": "Chrome", "color": "#1A1819", "icon": "", "action": "open:chrome.exe"},
        # Fila 2
        {"id": 4, "label": "Copiar", "color": "#1A1819", "icon": "", "action": "ctrl+c"},
        {"id": 5, "label": "Pegar", "color": "#1A1819", "icon": "", "action": "ctrl+v"},
        {"id": 6, "label": "Vol -", "color": "#1A1819", "icon": "/volume_down.bmp", "action": "volumedown"},
        {"id": 7, "label": "Vol +", "color": "#1A1819", "icon": "/volume_up.bmp", "action": "volumeup"},
        # Fila 3
        {"id": 8, "label": "Mute Mic", "color": "#1A1819", "icon": "/mute.bmp", "action": "volumemute"},
        {"id": 9, "label": "Play/Pause", "color": "#1A1819", "icon": "/pause.bmp", "action": "playpause"},
        {"id": 10, "label": "Siguiente", "color": "#1A1819", "icon": "/fast-backward.bmp", "action": "nexttrack"},
        {"id": 11, "label": "Anterior", "color": "#1A1819", "icon": "/fast-forward-button.bmp", "action": "prevtrack"}
    ]
}

def connect_serial():
    # Ajusta 'COM3' al puerto donde se conecta tu CYD
    # Puedes ver el puerto en el Administrador de Dispositivos de Windows
    ser = serial.Serial('COM3', 115200, timeout=1)
    time.sleep(2) # Esperar a que el ESP32 reinicie
    return ser

def execute_action(action_str):
    """Ejecuta la acción en Windows"""
    try:
        if action_str.startswith("open:"):
            # Abrir aplicación
            app = action_str.replace("open:", "")
            pyautogui.hotkey('win', 'r')
            time.sleep(0.2)
            pyautogui.write(app)
            pyautogui.press('enter')
        elif action_str in ["volumedown", "volumeup", "volumemute", "playpause", "nexttrack", "prevtrack"]:
            # Teclas multimedia
            pyautogui.press(action_str)
        else:
            # Atajos de teclado (ej: "ctrl+shift+m")
            keys = action_str.split('+')
            pyautogui.hotkey(*keys)
        print(f"[OK] Ejecutado: {action_str}")
    except Exception as e:
        print(f"[ERROR] No se pudo ejecutar {action_str}: {e}")

def main():
    print("Iniciando CYD Stream Deck...")
    ser = connect_serial()
    
    # Esperar a que la CYD diga que está lista
    #while True:
    #    line = ser.readline().decode('utf-8').strip()
    #    if '"ready"' in line:
    #        print("CYD conectada y lista. Enviando configuración...")
    #        break

    # Enviar configuración a la CYD
    config_json = json.dumps(CONFIG) + '\n'
    ser.write(config_json.encode('utf-8'))
    
    # Confirmar que la CYD recibió la config
    while True:
        line = ser.readline().decode('utf-8').strip()
        if '"updated"' in line:
            print("Configuración cargada en pantalla. ¡Listo para usar!")
            break

    # Bucle principal: Escuchar pulsaciones
    print("Escuchando pulsaciones...")
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line:
                data = json.loads(line)
                if data.get("type") == "press":
                    btn_id = data.get("id")
                    # Buscar la acción correspondiente en nuestra CONFIG
                    action = next((b["action"] for b in CONFIG["buttons"] if b["id"] == btn_id), None)
                    if action:
                        execute_action(action)
        except json.JSONDecodeError:
            pass
        except KeyboardInterrupt:
            print("Saliendo...")
            ser.close()
            break

if __name__ == "__main__":
    main()