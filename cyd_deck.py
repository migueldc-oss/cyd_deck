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
        {"id": 0, "label": "Mute Mic", "color": "#641271", "icon": "/bmp.bmp", "action": "ctrl+shift+m"},
        {"id": 1, "label": "Cam On/Off", "color": "#00FF00", "icon": "/bmp.bmp", "action": "ctrl+shift+v"},
        {"id": 2, "label": "OBS", "color": "#0000FF", "icon": "/bmp.bmp", "action": "open:obs64.exe"},
        {"id": 3, "label": "Navegador", "color": "#FFFF00", "icon": "/bmp.bmp", "action": "open:chrome.exe"},
        # Fila 2
        {"id": 4, "label": "Copiar", "color": "#808080", "icon": "/bmp.bmp", "action": "ctrl+c"},
        {"id": 5, "label": "Pegar", "color": "#808080", "icon": "/bmp.bmp", "action": "ctrl+v"},
        {"id": 6, "label": "Vol -", "color": "#A52A2A", "icon": "/bmp.bmp", "action": "volumedown"},
        {"id": 7, "label": "Vol +", "color": "#A52A2A", "icon": "/bmp.bmp", "action": "volumeup"},
        # Fila 3
        {"id": 8, "label": "Mute Vol", "color": "#A52A2A", "icon": "/bmp.bmp", "action": "volumemute"},
        {"id": 9, "label": "Play/Pause", "color": "#4B0082", "icon": "/bmp.bmp", "action": "playpause"},
        {"id": 10, "label": "Siguiente", "color": "#4B0082", "icon": "/bmp.bmp", "action": "nexttrack"},
        {"id": 11, "label": "Anterior", "color": "#4B0082", "icon": "/bmp.bmp", "action": "prevtrack"}
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
    while True:
        line = ser.readline().decode('utf-8').strip()
        if '"ready"' in line:
            print("CYD conectada y lista. Enviando configuración...")
            break

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