import serial
import json
import time
import threading
import pyautogui
import subprocess
import pystray
from PIL import Image, ImageDraw, ImageTk
import os
import sys
import customtkinter as ctk
from tkinter import colorchooser, filedialog, messagebox
import serial.tools.list_ports
import glob

# ============================================================
# DETECCIÓN DE ENTORNO (funciona en .py y en .exe)
# ============================================================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
ICON_FILE = os.path.join(BASE_DIR, "icon.ico")
LOG_FILE = os.path.join(BASE_DIR, "cyd_deck.log")

# Tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def log(msg):
    """Log en consola y archivo"""
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + "\n")
    except:
        pass


# ============================================================
# FRAME DE CONFIGURACIÓN DE UN BOTÓN
# ============================================================
class ButtonConfigFrame(ctk.CTkFrame):
    """Frame con vista previa + campos editables para un botón"""

    def __init__(self, parent, button_data, index, app):
        super().__init__(parent)
        self.app = app
        self.button_data = button_data
        self.index = index
        self.current_color = button_data.get("color", "#3498db")
        self.icon_path = button_data.get("icon", "")
        self.preview_image = None  # Mantener referencia

        self.configure(corner_radius=8)
        # Grid: col 0 = preview, cols 1+ = campos
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---------- VISTA PREVIA (ahora abarca 4 filas) ----------
        self.preview_frame = ctk.CTkFrame(self, width=80, height=100,
                                          fg_color=self.current_color)
        self.preview_frame.grid(row=0, column=0, rowspan=4, padx=5, pady=5, sticky="nsew")
        self.preview_frame.grid_propagate(False)

        self.preview_icon_label = ctk.CTkLabel(self.preview_frame, text="", width=64, height=64)
        self.preview_icon_label.place(relx=0.5, rely=0.38, anchor="center")

        self.preview_label = ctk.CTkLabel(self.preview_frame,
                                          text=button_data.get("label", "") or "Botón",
                                          font=ctk.CTkFont(size=10, weight="bold"))
        self.preview_label.place(relx=0.5, rely=0.85, anchor="center")

        # ---------- CAMPOS ----------
        # Fila 0: ID + Nombre
        self.lbl_id = ctk.CTkLabel(self, text=f"#{index}", width=30,
                                   font=ctk.CTkFont(weight="bold", size=12))
        self.lbl_id.grid(row=0, column=1, padx=(5, 2), pady=(5, 0), sticky="w")

        self.entry_label = ctk.CTkEntry(self, width=130, placeholder_text="Nombre")
        self.entry_label.grid(row=0, column=2, padx=5, pady=(5, 0), sticky="ew")
        self.entry_label.insert(0, button_data.get("label", ""))
        self.entry_label.bind("<KeyRelease>", lambda e: self._update_preview())

        # Fila 1: Color (fila propia)
        color_row = ctk.CTkFrame(self, fg_color="transparent")
        color_row.grid(row=1, column=1, columnspan=2, padx=5, pady=3, sticky="ew")

        ctk.CTkLabel(color_row, text="Color:", width=45).grid(row=0, column=0, sticky="w")
        self.btn_color = ctk.CTkButton(color_row, text="", width=38, height=26,
                                       command=self.pick_color,
                                       fg_color=self.current_color,
                                       hover_color=self.current_color)
        self.btn_color.grid(row=0, column=1, padx=(0, 5))
        self.lbl_color_hex = ctk.CTkLabel(color_row, text=self.current_color,
                                          font=ctk.CTkFont(size=11), width=65)
        self.lbl_color_hex.grid(row=0, column=2, sticky="w")

        # Fila 2: Acción (fila propia)
        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.grid(row=2, column=1, columnspan=2, padx=5, pady=3, sticky="ew")
        action_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(action_row, text="Acción:", width=45).grid(row=0, column=0, sticky="w")
        self.entry_action = ctk.CTkEntry(action_row, placeholder_text="ctrl+shift+m / open:app.exe")
        self.entry_action.grid(row=0, column=1, sticky="ew")
        self.entry_action.insert(0, button_data.get("action", ""))

        # Fila 3: Icono (CAMPO DE TEXTO EDITABLE)
        icon_row = ctk.CTkFrame(self, fg_color="transparent")
        icon_row.grid(row=3, column=1, columnspan=2, padx=5, pady=(0, 5), sticky="ew")
        icon_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(icon_row, text="Icono:", width=45).grid(row=0, column=0, sticky="w")
        self.entry_icon = ctk.CTkEntry(icon_row, placeholder_text="/icons/nombre.bmp")
        self.entry_icon.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        self.entry_icon.insert(0, self.icon_path)
        self.entry_icon.bind("<KeyRelease>", lambda e: self._on_icon_text_change())

        # Botón opcional para buscar el archivo (ayuda a rellenar el campo)
        self.btn_browse = ctk.CTkButton(icon_row, text="📁", width=32,
                                        command=self.browse_icon)
        self.btn_browse.grid(row=0, column=2)

        self._update_preview_icon()

    # ---------- UTILIDADES ----------
    def _get_icon_full_path(self):
        """Construye la ruta completa del icono usando la unidad SD configurada"""
        icon = self.entry_icon.get().strip()
        if not icon:
            return None
        sd_drive = self.app.get_sd_drive()
        if not sd_drive:
            return None
        # Normalizar: quitar / inicial para unir con la unidad
        rel = icon.lstrip("/").replace("/", os.sep)
        return os.path.join(sd_drive, rel)

    def _update_preview(self):
        """Actualiza color y texto de la vista previa"""
        self.preview_frame.configure(fg_color=self.current_color)
        self.btn_color.configure(fg_color=self.current_color, hover_color=self.current_color)
        self.lbl_color_hex.configure(text=self.current_color)
        txt = self.entry_label.get() or "Botón"
        self.preview_label.configure(text=txt)

    def _update_preview_icon(self):
        """Actualiza el icono de la vista previa leyendo desde la unidad SD"""
        path = self._get_icon_full_path()
        if path and os.path.exists(path):
            try:
                img = Image.open(path)
                img = img.resize((50, 50), Image.Resampling.LANCZOS)
                self.preview_image = ImageTk.PhotoImage(img)
                self.preview_icon_label.configure(image=self.preview_image, text="")
                return
            except Exception as e:
                log(f"Error cargando preview {path}: {e}")
        # Sin icono o no encontrado
        self.preview_image = None
        self.preview_icon_label.configure(image=None, text="🖼️" if self.entry_icon.get().strip() else "")

    def _on_icon_text_change(self):
        """Cuando el usuario escribe en el campo de icono"""
        self.icon_path = self.entry_icon.get().strip()
        self._update_preview_icon()

    def pick_color(self):
        """Selector de color"""
        color = colorchooser.askcolor(title="Color de fondo", initialcolor=self.current_color)
        if color[1]:
            self.current_color = color[1].lower()
            self._update_preview()

    def browse_icon(self):
        """
        Botón opcional: busca el archivo y rellena el campo con la ruta /icons/...
        Busca en la unidad SD si está configurada, si no, en cualquier carpeta.
        """
        sd_drive = self.app.get_sd_drive()
        if sd_drive and os.path.exists(sd_drive):
            # Examinar dentro de la unidad SD
            base = os.path.join(sd_drive, "icons")
            if not os.path.exists(base):
                base = sd_drive
            file = filedialog.askopenfilename(
                title="Seleccionar icono en la SD",
                initialdir=base,
                filetypes=[("Imágenes", "*.bmp *.png *.jpg"), ("Todos", "*.*")]
            )
            if file:
                # Convertir a ruta relativa tipo /icons/nombre.bmp
                try:
                    rel = os.path.relpath(file, sd_drive)
                    rel = "/" + rel.replace(os.sep, "/")
                    self.entry_icon.delete(0, "end")
                    self.entry_icon.insert(0, rel)
                    self._on_icon_text_change()
                except Exception as e:
                    log(f"Error calculando ruta relativa: {e}")
        else:
            messagebox.showinfo("Info",
                "Configura la 'Unidad SD' en la sección de conexión\n"
                "para poder buscar iconos en la tarjeta.")

    def get_data(self):
        """Devuelve los datos del botón"""
        return {
            "id": self.index,
            "label": self.entry_label.get(),
            "color": self.current_color,
            "icon": self.entry_icon.get().strip(),
            "action": self.entry_action.get()
        }


# ============================================================
# APLICACIÓN PRINCIPAL (Servicio + Configuración + Tray)
# ============================================================
class CYDStreamDeckApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Estado del servicio ---
        self.ser = None
        self.connected = False
        self.running = True
        self.tray_icon = None
        self.current_config_file = CONFIG_FILE  # Archivo de configuración actual
        self.config_data = self.load_config()

        # --- Configurar ventana ---
        self.title("CYD Stream Deck - Configuración")
        self.geometry("1000x720")
        self.minsize(800, 550)
        self.resizable(True, True)  # Ventana redimensionable
        self.protocol("WM_DELETE_WINDOW", self.on_close_window)

        # --- UI ---
        self.setup_ui()

        # --- Arrancar servicios en hilos ---
        threading.Thread(target=self.serial_service, daemon=True).start()
        threading.Thread(target=self.setup_tray, daemon=True).start()

        # Por defecto arranca oculto en el tray.
        # Para mostrar la ventana al arrancar, usar: --visible o --show
        if "--visible" in sys.argv or "--show" in sys.argv:
            pass  # Se muestra la ventana (comportamiento visible)
        else:
            self.withdraw()  # Minimizar a la bandeja por defecto

    # ========================================================
    # CONFIGURACIÓN (JSON)
    # ========================================================
    def load_config(self, filepath=None):
        """Carga la configuración desde un archivo específico o el actual"""
        if filepath is None:
            filepath = self.current_config_file
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                log(f"Error cargando config: {e}")
        return self.get_default_config()

    def save_config_to_file(self, filepath=None):
        """Guarda la configuración en un archivo específico o el actual"""
        if filepath is None:
            filepath = self.current_config_file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            log(f"Configuración guardada en {filepath}")
            return True
        except Exception as e:
            log(f"Error guardando config: {e}")
            return False

    def get_default_config(self):
        return {
            "port": "COM3",
            "baudrate": 115200,
            "sd_drive": "",
            "buttons": [
                {"id": i, "label": f"Botón {i+1}", "color": "#3498db",
                 "icon": "", "action": ""}
                for i in range(12)
            ]
        }

    def get_sd_drive(self):
        """Devuelve la letra de unidad SD configurada"""
        return self.config_data.get("sd_drive", "").strip()

    def get_json_files(self):
        """Devuelve la lista de archivos JSON en BASE_DIR"""
        pattern = os.path.join(BASE_DIR, "*.json")
        files = glob.glob(pattern)
        # Extraer solo los nombres de archivo
        filenames = [os.path.basename(f) for f in files]
        return sorted(filenames)

    def load_profile(self, filename):
        """Carga un perfil de configuración específico"""
        filepath = os.path.join(BASE_DIR, filename)
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"El archivo {filename} no existe")
            return False
        
        self.current_config_file = filepath
        self.config_data = self.load_config(filepath)
        
        # Actualizar UI
        self.after(0, self.reload_ui_from_config)
        
        # Actualizar selector de perfiles
        if hasattr(self, 'profile_combo'):
            self.profile_combo.set(filename)
        
        log(f"Perfil cargado: {filename}")
        return True

    def create_new_profile(self):
        """Crea un nuevo perfil de configuración"""
        name = filedialog.asksaveasfilename(
            title="Crear nuevo perfil",
            initialdir=BASE_DIR,
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json")]
        )
        if name:
            filename = os.path.basename(name)
            # Crear archivo con configuración por defecto
            default_config = self.get_default_config()
            default_config["port"] = self.config_data.get("port", "COM3")
            default_config["baudrate"] = self.config_data.get("baudrate", 115200)
            default_config["sd_drive"] = self.config_data.get("sd_drive", "")
            
            try:
                with open(name, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                log(f"Nuevo perfil creado: {filename}")
                # Recargar lista de perfiles
                self.refresh_profile_list()
                # Cargar el nuevo perfil
                self.load_profile(filename)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear el perfil: {e}")

    def refresh_profile_list(self):
        """Actualiza la lista de perfiles en el combobox"""
        if hasattr(self, 'profile_combo'):
            profiles = self.get_json_files()
            self.profile_combo.configure(values=profiles)

    # ========================================================
    # INTERFAZ GRÁFICA
    # ========================================================
    def setup_ui(self):
        # Grid principal: 3 filas (título, conexión, botones, acciones)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # La fila de botones se expande

        # --- Título ---
        title = ctk.CTkLabel(self, text="🎮 CYD Stream Deck - Configuración",
                             font=ctk.CTkFont(size=22, weight="bold"))
        title.grid(row=0, column=0, pady=(10, 2), sticky="n")

        subtitle = ctk.CTkLabel(self,
            text="Configura nombres, colores, iconos (ruta en SD) y acciones",
            font=ctk.CTkFont(size=12), text_color="gray")
        subtitle.grid(row=1, column=0, pady=(0, 8), sticky="n")

        # --- Conexión ---
        conn = ctk.CTkFrame(self)
        conn.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        conn.grid_columnconfigure(7, weight=1)

        ctk.CTkLabel(conn, text="🔌", font=ctk.CTkFont(size=16)).grid(row=0, column=0, padx=(10, 5))

        ctk.CTkLabel(conn, text="Puerto COM:").grid(row=0, column=1, padx=5)
        try:
            ports = [p.device for p in serial.tools.list_ports.comports()]
        except:
            ports = ["COM1", "COM2", "COM3"]
        self.port_combo = ctk.CTkComboBox(conn, values=ports, width=110)
        self.port_combo.grid(row=0, column=2, padx=5)
        self.port_combo.set(self.config_data.get("port", "COM3"))

        ctk.CTkLabel(conn, text="Baudrate:").grid(row=0, column=3, padx=(15, 5))
        self.baud_combo = ctk.CTkComboBox(conn, values=["9600", "115200", "230400", "460800"], width=90)
        self.baud_combo.grid(row=0, column=4, padx=5)
        self.baud_combo.set(str(self.config_data.get("baudrate", 115200)))

        ctk.CTkLabel(conn, text="Unidad SD:").grid(row=0, column=5, padx=(15, 5))
        self.sd_entry = ctk.CTkEntry(conn, width=70, placeholder_text="E:")
        self.sd_entry.grid(row=0, column=6, padx=5)
        self.sd_entry.insert(0, self.config_data.get("sd_drive", ""))

        #btn_reconnect = ctk.CTkButton(conn, text="🔄 Reconectar",
        #                              command=self._on_reconnect_clicked, width=100,
        #                              fg_color="#e67e22", hover_color="#d35400")
        #btn_reconnect.grid(row=0, column=6, padx=(15, 5))
        #btn_reconnect.pack(side="left", padx=5)

        self.lbl_status = ctk.CTkLabel(conn, text="● Desconectado", text_color="red",
                                       font=ctk.CTkFont(weight="bold"))
        self.lbl_status.grid(row=0, column=7, padx=10, sticky="e")

        # --- Selector de perfiles ---
        profile_frame = ctk.CTkFrame(self)
        profile_frame.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        
        ctk.CTkLabel(profile_frame, text="📁 Perfil:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        
        profiles = self.get_json_files()
        self.profile_combo = ctk.CTkComboBox(profile_frame, values=profiles, width=200)
        self.profile_combo.pack(side="left", padx=5)
        
        # Seleccionar el archivo actual
        current_filename = os.path.basename(self.current_config_file)
        if current_filename in profiles:
            self.profile_combo.set(current_filename)
        else:
            self.profile_combo.set("config.json")
        
        self.profile_combo.bind("<<ComboboxSelected>>", self.on_profile_changed)
        
        btn_load = ctk.CTkButton(profile_frame, text="📂 Cargar", command=self.load_selected_profile, width=80)
        btn_load.pack(side="left", padx=5)
        
        btn_new = ctk.CTkButton(profile_frame, text="➕ Nuevo", command=self.create_new_profile, width=80)
        btn_new.pack(side="left", padx=5)

        btn_reconnect = ctk.CTkButton(profile_frame, text="🔄 Reconectar",
                                      command=self._on_reconnect_clicked, width=100,
                                      fg_color="#e67e22", hover_color="#d35400")
        btn_reconnect.pack(side="right", padx=5)

        # --- Grid de botones 4x3 ---
        grid_container = ctk.CTkFrame(self, fg_color="transparent")
        grid_container.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        # Hacer que todas las columnas y filas del grid sean redimensionables
        for c in range(4):
            grid_container.grid_columnconfigure(c, weight=1, uniform="btn")
        for r in range(3):
            grid_container.grid_rowconfigure(r, weight=1, uniform="btn")

        self.button_frames = []
        for i in range(12):
            row = i // 4
            col = i % 4
            btn_data = next((b for b in self.config_data.get("buttons", [])
                             if b.get("id") == i),
                            {"id": i, "label": "", "color": "#3498db",
                             "icon": "", "action": ""})
            frame = ButtonConfigFrame(grid_container, btn_data, i, self)
            frame.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            self.button_frames.append(frame)

        # --- Botones de acción ---
        actions = ctk.CTkFrame(self)
        actions.grid(row=5, column=0, padx=20, pady=(5, 15), sticky="ew")
        for c in range(4):
            actions.grid_columnconfigure(c, weight=1)

        self.btn_refresh_preview = ctk.CTkButton(actions, text=" Actualizar vistas previas",
                                                 command=self.refresh_previews, height=36)
        self.btn_refresh_preview.grid(row=0, column=0, padx=8, sticky="ew")

        self.btn_save = ctk.CTkButton(actions, text="💾 Guardar",
                                      command=self.save_config, height=36)
        self.btn_save.grid(row=0, column=1, padx=8, sticky="ew")

        self.btn_send = ctk.CTkButton(actions, text="📤 Guardar y Enviar a CYD",
                                      command=self.save_and_send, height=36,
                                      fg_color="green", hover_color="darkgreen")
        self.btn_send.grid(row=0, column=2, padx=8, sticky="ew")

        self.btn_minimize = ctk.CTkButton(actions, text="🗕 Minimizar a bandeja",
                                          command=self.on_close_window, height=36,
                                          fg_color="#555555", hover_color="#333333")
        self.btn_minimize.grid(row=0, column=3, padx=8, sticky="ew")

    def _on_reconnect_clicked(self):
        """Callback del botón Reconectar: lanza la reconexión en un hilo"""
        # Primero recoge los datos actuales de la UI (puerto, baudrate)
        self.collect_config()
        # Lanza la reconexión en un hilo para no bloquear la UI
        threading.Thread(target=self._reconnect_worker, daemon=True).start()

    def _reconnect_worker(self):
        """Trabajo de reconexión en segundo plano"""
        log("Reconectando manualmente...")
        if self.connect_cyd():
            # Si conecta, envía la configuración actual
            self.send_config_to_cyd()
        else:
            log("No se pudo reconectar")

    def on_profile_changed(self, event):
        """Cuando el usuario selecciona un perfil del combobox"""
        pass  # Solo carga al hacer clic en "Cargar"

    def load_selected_profile(self):
        """Carga el perfil seleccionado en el combobox"""
        selected = self.profile_combo.get()
        if selected:
            if self.load_profile(selected):
                messagebox.showinfo("✓ Éxito", f"Perfil '{selected}' cargado correctamente")

    def refresh_previews(self):
        """Refresca todas las vistas previas de iconos"""
        for f in self.button_frames:
            f._update_preview_icon()
        log("Vistas previas actualizadas")

    # ========================================================
    # SERVICIO SERIAL (hilo)
    # ========================================================
    def serial_service(self):
        """Hilo principal del servicio: conecta, envía config y escucha"""
        time.sleep(1)  # Esperar a que la UI arranque
        self.connect_cyd()
        if self.connected:
            self.send_config_to_cyd()
        self.listen_cyd()

    def connect_cyd(self):
        port = self.config_data.get("port", "COM3")
        baudrate = self.config_data.get("baudrate", 115200)
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.ser = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)
            self.connected = True
            log(f"✓ Conectado a {port}")
            self.after(0, lambda: self.lbl_status.configure(
                text=f"● Conectado ({port})", text_color="green"))
            return True
        except Exception as e:
            log(f"✗ Error conectando a {port}: {e}")
            self.connected = False
            self.after(0, lambda: self.lbl_status.configure(
                text="● Desconectado", text_color="red"))
            return False

    def send_config_to_cyd(self):
        if not self.connected or not self.ser or not self.ser.is_open:
            log("No hay conexión con la CYD")
            return False
        try:
            cyd_config = {"buttons": self.config_data.get("buttons", [])}
            payload = json.dumps(cyd_config) + '\n'
            self.ser.write(payload.encode('utf-8'))
            log(f"Configuración enviada ({len(payload)} bytes)")

            # Esperar confirmación
            #timeout = time.time() + 10
            #while time.time() < timeout and self.running:
            #    if self.ser.in_waiting > 0:
            #        line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            #        if '"updated"' in line:
            #            log("✓ CYD actualizada")
            #            return True
            #        elif '"error"' in line:
            #            log(f"✗ Error CYD: {line}")
            #           return False
            time.sleep(1.1)
            return True
            return False
        except Exception as e:
            log(f"Error enviando config: {e}")
            self.connected = False
            return False

    def listen_cyd(self):
        """Bucle que escucha pulsaciones de la CYD"""
        while self.running:
            if self.connected and self.ser and self.ser.is_open:
                try:
                    if self.ser.in_waiting > 0:
                        line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            try:
                                data = json.loads(line)
                                if data.get("type") == "press":
                                    btn_id = data.get("id")
                                    action = next(
                                        (b["action"] for b in self.config_data.get("buttons", [])
                                         if b.get("id") == btn_id), None)
                                    if action:
                                        threading.Thread(target=self.execute_action,
                                                         args=(action,), daemon=True).start()
                            except json.JSONDecodeError:
                                pass
                except serial.SerialException as e:
                    self.connected = False
                    log(f"Desconectado: {e}")
                    self.after(0, lambda: self.lbl_status.configure(
                        text="● Desconectado", text_color="red"))
                except Exception as e:
                    log(f"Error listener: {e}")
            time.sleep(0.05)

    def execute_action(self, action_str):
        try:
            if not action_str or not action_str.strip():
                return
            action_str = action_str.strip()
            
            # NUEVO: Comando para cambiar de perfil desde la CYD
            if action_str.startswith("profile:"):
                profile_name = action_str.replace("profile:", "").strip()
                self.switch_profile_from_cyd(profile_name)
                return
            
            if action_str.startswith("open:"):
                app = action_str.replace("open:", "").strip()
                # Normalizar separadores (admite / o \)
                app_path = app.replace("/", os.sep)
                if os.path.isfile(app_path):
                    # RUTA COMPLETA: ejecutar con su propia carpeta como cwd
                    # (esto soluciona el error "Failed to find locale/en-US.ini" de OBS)
                    cwd = os.path.dirname(os.path.abspath(app_path))
                    subprocess.Popen([app_path], cwd=cwd)
                else:
                    # Solo nombre: dejar que Windows lo resuelva
                    subprocess.Popen(app_path, shell=True)
                log(f"[OK] Abierto: {app}")
            elif action_str in ["volumedown", "volumeup", "volumemute",
                                "playpause", "nexttrack", "prevtrack"]:
                pyautogui.press(action_str)
                log(f"[OK] Multimedia: {action_str}")
            else:
                keys = [k.strip() for k in action_str.split('+')]
                pyautogui.hotkey(*keys)
                log(f"[OK] Teclas: {action_str}")
        except Exception as e:
            log(f"[ERROR] {action_str}: {e}")

    def switch_profile_from_cyd(self, profile_name):
        """Cambia de perfil cuando la CYD envía el comando"""
        log(f"Cambiando perfil desde CYD: {profile_name}")
        
        # Verificar que el archivo existe
        filepath = os.path.join(BASE_DIR, profile_name)
        if not os.path.exists(filepath):
            log(f"Error: El perfil {profile_name} no existe")
            return
        
        # Cargar el nuevo perfil
        self.current_config_file = filepath
        self.config_data = self.load_config(filepath)
        
        # Actualizar UI
        self.after(0, self.reload_ui_from_config)

        
        # Actualizar selector de perfiles
        if hasattr(self, 'profile_combo'):
            self.after(0, lambda: self.profile_combo.set(profile_name))
        
        # Enviar la nueva configuración a la CYD
        if self.connected:
            time.sleep(0.1)  # Esperar a que la UI arranque
            self.send_config_to_cyd()
        
        log(f"✓ Perfil cambiado a: {profile_name}")

    # ========================================================
    # GUARDAR / ENVIAR
    # ========================================================
    def collect_config(self):
        """Recoge los datos de la UI al dict de configuración"""
        self.config_data["port"] = self.port_combo.get()
        self.config_data["baudrate"] = int(self.baud_combo.get())
        self.config_data["sd_drive"] = self.sd_entry.get().strip()
        self.config_data["buttons"] = [f.get_data() for f in self.button_frames]

    def save_config(self):
        self.collect_config()
        if self.save_config_to_file():
            messagebox.showinfo("✓ Éxito", f"Configuración guardada en:\n{os.path.basename(self.current_config_file)}")
            return True
        else:
            messagebox.showerror("✗ Error", "No se pudo guardar la configuración.")
            return False

    def save_and_send(self):
        self.collect_config()
        if not self.save_config_to_file():
            messagebox.showerror("✗ Error", "No se pudo guardar la configuración.")
            return
        if not self.connected:
            messagebox.showwarning("Sin conexión",
                "No hay conexión con la CYD.\n"
                "Usa 'Reconectar CYD' en el menú de la bandeja.")
            return
        threading.Thread(target=self.send_config_to_cyd, daemon=True).start()
        #self.send_config_to_cyd()
        messagebox.showinfo("📤 Enviando",
            "Configuración enviada a la CYD.\nEspera unos segundos para que se aplique.")

    # ========================================================
    # SYSTEM TRAY (hilo)
    # ========================================================
    def setup_tray(self):
        """Crea y ejecuta el icono de bandeja"""
        self.create_default_icon()
        try:
            image = Image.open(ICON_FILE)
        except:
            image = Image.new('RGB', (64, 64), color=(50, 150, 250))
        menu = pystray.Menu(
            pystray.MenuItem("⚙ Configurar botones", self.tray_open_config, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Salir", self.tray_quit)
        )
        self.tray_icon = pystray.Icon("cyd_deck", image, "CYD Stream Deck", menu)
        self.tray_icon.run()

    def create_default_icon(self):
        if not os.path.exists(ICON_FILE):
            try:
                img = Image.new('RGB', (64, 64), color=(50, 150, 250))
                d = ImageDraw.Draw(img)
                d.text((15, 20), "CYD", fill=(255, 255, 255))
                img.save(ICON_FILE)
            except Exception as e:
                log(f"Error creando icono: {e}")

    # --- Callbacks del tray (se ejecutan en el hilo del icono) ---
    def tray_open_config(self, icon, item):
        self.after(0, self.show_window)

    def tray_quit(self, icon, item):
        self.after(0, self.quit_app)

    # ========================================================
    # GESTIÓN DE VENTANA
    # ========================================================
    def show_window(self):
        """Muestra y enfoca la ventana"""
        self.deiconify()
        self.lift()
        self.focus_force()

    def on_close_window(self):
        """Al cerrar con X o botón minimizar: se va al tray"""
        self.withdraw()
        log("Ventana minimizada a la bandeja")

    def reload_ui_from_config(self):
        """Recarga la UI desde self.config_data"""
        self.port_combo.set(self.config_data.get("port", "COM3"))
        self.baud_combo.set(str(self.config_data.get("baudrate", 115200)))
        self.sd_entry.delete(0, "end")
        self.sd_entry.insert(0, self.config_data.get("sd_drive", ""))
        for i, frame in enumerate(self.button_frames):
            btn_data = next((b for b in self.config_data.get("buttons", [])
                             if b.get("id") == i), None)
            if btn_data:
                frame.entry_label.delete(0, "end")
                frame.entry_label.insert(0, btn_data.get("label", ""))
                frame.entry_action.delete(0, "end")
                frame.entry_action.insert(0, btn_data.get("action", ""))
                frame.entry_icon.delete(0, "end")
                frame.entry_icon.insert(0, btn_data.get("icon", ""))
                frame.current_color = btn_data.get("color", "#3498db")
                frame._update_preview()
                frame._update_preview_icon()

    def quit_app(self):
        """Cierra completamente la aplicación"""
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except:
                pass
        log("Aplicación cerrada")
        self.destroy()


# ============================================================
# PUNTO DE ENTRADA
# ============================================================
if __name__ == "__main__":
    app = CYDStreamDeckApp()
    app.mainloop()