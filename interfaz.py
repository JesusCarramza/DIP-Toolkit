import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import colorchooser 
from tkinter import simpledialog 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import cv2
import numpy as np
from PIL import Image, ImageTk
from src import practica1
from src import practica2    
from src import practica3    
from src import practica4
from src import practica5
from src import practica6
from src import practica7

# --- CONFIGURACIÓN DE COLORES ---
COLOR_BG = "#2E2E2E"        # Fondo General
COLOR_PANEL = "#333333"     # Fondo Paneles
COLOR_FG = "#FFFFFF"        # Texto
COLOR_ACCENT = "#D4AF37"    # Dorado
COLOR_BTN_BG = "#1C1C1C"    # Botones
COLOR_BTN_FG = "#D4AF37"    # Texto Botones

class PDIApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema PDI - Jesus Eduardo Carranza Mercado")
        self.root.geometry("1400x900")
        self.root.configure(bg=COLOR_BG)

        # --- ESTRUCTURA DE DATOS CENTRALIZADA ---
        self.data = {
            1: {"orig": None, "proc": None, "hist": []},
            2: {"orig": None, "proc": None, "hist": []}
        }
        
        self.active_slot = tk.IntVar(value=1)
        self.view_mode = tk.IntVar(value=1)
        
        self.setup_styles()

        # --- LAYOUT PRINCIPAL (CON PANEDWINDOW AJUSTABLE) ---
        # Usamos PanedWindow para permitir redimensionar los paneles arrastrando
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=6, bg="#444")
        self.paned_window.pack(fill="both", expand=True, padx=5, pady=5)

        # --- PANEL IZQUIERDO (HERRAMIENTAS CON SCROLL) ---
        # Este frame será el contenedor del canvas y scrollbar dentro del panel ajustable
        self.panel_left = tk.Frame(self.paned_window, bg=COLOR_BG)
        
        # 1. Canvas y Scrollbar
        self.canvas_left = tk.Canvas(self.panel_left, bg=COLOR_BG, highlightthickness=0)
        self.scrollbar_left = ttk.Scrollbar(self.panel_left, orient="vertical", command=self.canvas_left.yview)
        
        # 2. Frame interno (Contenido real de botones)
        self.scroll_content = tk.Frame(self.canvas_left, bg=COLOR_BG)

        # 3. Configuración del Scroll
        self.scroll_content.bind(
            "<Configure>", 
            lambda e: self.canvas_left.configure(scrollregion=self.canvas_left.bbox("all"))
        )

        # Crear ventana dentro del canvas
        self.canvas_window = self.canvas_left.create_window((0, 0), window=self.scroll_content, anchor="nw")

        # CRUCIAL: Esto permite que al arrastrar la barra divisoria, el contenido interno se ensanche
        self.canvas_left.bind(
            "<Configure>", 
            lambda e: self.canvas_left.itemconfig(self.canvas_window, width=e.width)
        )

        self.canvas_left.configure(yscrollcommand=self.scrollbar_left.set)

        # Empaquetado interno del panel izquierdo
        self.scrollbar_left.pack(side="right", fill="y")
        self.canvas_left.pack(side="left", fill="both", expand=True)
        
        # Binding para la rueda del ratón (MouseWheel)
        self.bind_mousewheel(self.canvas_left, self.scroll_content)

        # --- PANEL DERECHO (VISUALIZACIÓN) ---
        self.panel_right = tk.Frame(self.paned_window, bg=COLOR_BG)
        
        # Configuración interna del panel derecho (Grilla y Controles)
        self.grid_area = tk.Frame(self.panel_right, bg=COLOR_BG)
        self.grid_area.pack(side="top", fill="both", expand=True)
        
        self.view_controls = tk.Frame(self.panel_right, bg=COLOR_BG, height=40)
        self.view_controls.pack(side="bottom", fill="x", pady=5)

        # --- AÑADIR PANELES AL PANEDWINDOW ---
        # 'minsize' evita que el usuario oculte completamente el panel por error
        self.paned_window.add(self.panel_left, minsize=200, width=360) 
        self.paned_window.add(self.panel_right, minsize=400, stretch="always")

        # Inicialización (Nota: ahora usaremos self.scroll_content como padre)
        self.crear_barra_herramientas_superior()
        self.crear_switch_operacion() 
        self.crear_pestanas_practicas()
        self.inicializar_grilla()
        self.actualizar_controles_vista()

    def bind_mousewheel(self, widget, inner_frame):
        # Función interna para manejar el evento
        def _on_mousewheel(event):
            widget.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Vincular eventos cuando el mouse entra/sale del área izquierda
        inner_frame.bind('<Enter>', lambda e: widget.bind_all('<MouseWheel>', _on_mousewheel))
        inner_frame.bind('<Leave>', lambda e: widget.unbind_all('<MouseWheel>'))

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=COLOR_BG)
        style.configure("TLabel", background=COLOR_BG, foreground=COLOR_FG)
        style.configure("TNotebook", background=COLOR_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=COLOR_BTN_BG, foreground=COLOR_BTN_FG, padding=[10, 5])
        style.map("TNotebook.Tab", background=[("selected", COLOR_ACCENT)], foreground=[("selected", "black")])
        
        style.configure("Gold.TButton", background=COLOR_BTN_BG, foreground=COLOR_BTN_FG, font=("Segoe UI", 9, "bold"), borderwidth=1)
        style.map("Gold.TButton", background=[("active", COLOR_ACCENT)], foreground=[("active", "black")])
        
        style.configure("Red.TButton", background="#500000", foreground="#FF9999", font=("Segoe UI", 8), borderwidth=1)
        style.map("Red.TButton", background=[("active", "#FF0000")], foreground=[("active", "white")])
        
        # Estilo Radiobuttons
        style.configure("TRadiobutton", background=COLOR_BG, foreground="white", font=("Segoe UI", 10))
        style.map("TRadiobutton", background=[("active", COLOR_BG)], indicatorcolor=[("selected", COLOR_ACCENT)])

    def crear_barra_herramientas_superior(self):
        frame_top = tk.LabelFrame(self.scroll_content, text="Gestión de Archivos", 
                                bg=COLOR_BG, fg=COLOR_ACCENT, font=("Segoe UI", 10, "bold"))
        frame_top.pack(fill="x", pady=(0, 10), ipady=5)

        # Cargar 1 / Borrar 1
        f1 = tk.Frame(frame_top, bg=COLOR_BG)
        f1.pack(fill="x", pady=2)
        ttk.Button(f1, text="📂 Cargar Img 1", style="Gold.TButton", width=15, 
                command=lambda: self.cargar_imagen(1)).pack(side="left", padx=5)
        ttk.Button(f1, text="🗑 Borrar", style="Red.TButton", width=8, 
                command=lambda: self.borrar_imagen(1)).pack(side="right", padx=5)

        # Cargar 2 / Borrar 2
        f2 = tk.Frame(frame_top, bg=COLOR_BG)
        f2.pack(fill="x", pady=2)
        ttk.Button(f2, text="📂 Cargar Img 2", style="Gold.TButton", width=15, 
                command=lambda: self.cargar_imagen(2)).pack(side="left", padx=5)
        ttk.Button(f2, text="🗑 Borrar", style="Red.TButton", width=8, 
                command=lambda: self.borrar_imagen(2)).pack(side="right", padx=5)
        
        ttk.Separator(frame_top, orient='horizontal').pack(fill='x', pady=5)
        
        # Acciones Generales (Afectan a la imagen ACTIVA según el switch)
        self.btn_save = ttk.Button(frame_top, text="💾 Guardar Activa", style="Gold.TButton", command=self.guardar_imagen)
        self.btn_save.pack(fill="x", padx=5, pady=2)
        
        self.btn_reset = ttk.Button(frame_top, text="↺ Reset Activa", style="Gold.TButton", command=self.reset_imagen)
        self.btn_reset.pack(fill="x", padx=5, pady=2)
        
        self.btn_undo = ttk.Button(frame_top, text="↩ Deshacer (Undo)", style="Gold.TButton", command=self.deshacer)
        self.btn_undo.pack(fill="x", padx=5, pady=2)

    def crear_switch_operacion(self):
        # Este frame contiene el switch para decidir qué imagen se edita
        self.frame_switch = tk.LabelFrame(self.scroll_content, text="Selector de Operación", 
                                    bg=COLOR_BG, fg=COLOR_ACCENT, font=("Segoe UI", 10, "bold"))
        self.frame_switch.pack(fill="x", pady=(0, 10))
        
        tk.Label(self.frame_switch, text="¿Qué imagen deseas editar?", bg=COLOR_BG, fg="gray").pack(anchor="w", padx=5)
        
        self.rb1 = ttk.Radiobutton(self.frame_switch, text="Editar Imagen 1", variable=self.active_slot, value=1)
        self.rb1.pack(anchor="w", padx=10, pady=2)
        
        self.rb2 = ttk.Radiobutton(self.frame_switch, text="Editar Imagen 2", variable=self.active_slot, value=2)
        self.rb2.pack(anchor="w", padx=10, pady=2)
        
        # Se habilitarán/deshabilitarán según cargues imágenes
        self.actualizar_estado_switch()

    def actualizar_estado_switch(self):
        # Lógica: Si no hay img 1, disable rb1. Si no hay img 2, disable rb2.
        has_1 = self.data[1]["orig"] is not None
        has_2 = self.data[2]["orig"] is not None
        
        # Configurar estados
        self.rb1.config(state="normal" if has_1 else "disabled")
        self.rb2.config(state="normal" if has_2 else "disabled")
        
        # Auto-selección lógica
        if has_1 and not has_2:
            self.active_slot.set(1)
        elif not has_1 and has_2:
            self.active_slot.set(2)
        # Si tiene ambas, se queda donde el usuario lo dejó

    def crear_pestanas_practicas(self):
        self.notebook = ttk.Notebook(self.scroll_content)
        self.notebook.pack(fill="both", expand=True)
        titulos = ["Básicos/Color", "Mapa Color", "Aritmética/Lógica", "Filtros/Ruido", "Segmentación", "Morfología", "Frecuencia"]
        self.tabs = {}
        for i, titulo in enumerate(titulos):
            frame = tk.Frame(self.notebook, bg=COLOR_BG)
            self.notebook.add(frame, text=f"P{i+1}")
            self.tabs[titulo] = frame

        self.construir_tab_1(self.tabs["Básicos/Color"])        
        self.construir_tab_2(self.tabs["Mapa Color"])
        self.construir_tab_3(self.tabs["Aritmética/Lógica"])
        self.construir_tab_4(self.tabs["Filtros/Ruido"])
        self.construir_tab_5(self.tabs["Segmentación"])
        self.construir_tab_6(self.tabs["Morfología"])
        self.construir_tab_7(self.tabs["Frecuencia"])

    def construir_tab_1(self, parent):
        # --- SECCIÓN 1: ESCALA DE GRISES Y BINARIZACIÓN ---
        lf_basic = tk.LabelFrame(parent, text="Conversión y Binarización", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_basic.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(lf_basic, text="Escala de Grises", style="Gold.TButton", 
                command=lambda: self.aplicar_filtro(practica1.convertir_a_grises)).pack(fill="x", padx=5, pady=2)
        
        ttk.Separator(lf_basic, orient='horizontal').pack(fill='x', pady=5)

        # Umbral Manual
        tk.Label(lf_basic, text="Umbral Manual:", bg=COLOR_BG, fg="white").pack(anchor="w", padx=5)
        self.slider_umbral = tk.Scale(lf_basic, from_=0, to=255, orient="horizontal", bg=COLOR_BG, fg="white", highlightthickness=0)
        self.slider_umbral.set(127)
        self.slider_umbral.pack(fill="x", padx=5)
        
        ttk.Button(lf_basic, text="Aplicar Umbral Manual", style="Gold.TButton",
                command=lambda: self.aplicar_filtro(practica1.binarizar_manual, self.slider_umbral.get())).pack(fill="x", padx=5, pady=2)

        # CAMBIO AQUÍ: Otsu eliminado, entra Adaptativo
        ttk.Button(lf_basic, text="Binarizar Adaptativo", style="Gold.TButton",
                command=lambda: self.aplicar_filtro(practica1.binarizar_adaptativo)).pack(fill="x", padx=5, pady=2)

        # --- SECCIÓN 2: MODELOS DE COLOR ---
        lf_color = tk.LabelFrame(parent, text="Visualización Canales", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_color.pack(fill="x", padx=10, pady=10)
        ttk.Button(lf_color, text="Separación RGB", style="Gold.TButton", command=lambda: self.abrir_ventana_canales("RGB")).pack(fill="x", padx=5, pady=2)
        ttk.Button(lf_color, text="Separación HSV", style="Gold.TButton", command=lambda: self.abrir_ventana_canales("HSV")).pack(fill="x", padx=5, pady=2)
        ttk.Button(lf_color, text="Separación CMY", style="Gold.TButton", command=lambda: self.abrir_ventana_canales("CMY")).pack(fill="x", padx=5, pady=2)

    def construir_tab_2(self, parent):
        # --- PARTE 1: MAPAS PREDEFINIDOS ---
        lf_pre = tk.LabelFrame(parent, text="Mapas Predefinidos (Librería)", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_pre.pack(fill="x", padx=10, pady=5)
        
        btn_config = {'style': "Gold.TButton", 'width': 12}
        
        f_cv = tk.Frame(lf_pre, bg=COLOR_BG)
        f_cv.pack(fill="x", pady=2)
        tk.Label(f_cv, text="OpenCV:", bg=COLOR_BG, fg="gray").pack(side="left")
        ttk.Button(f_cv, text="JET", **btn_config, command=lambda: self.aplicar_filtro(practica2.aplicar_colormap_opencv, "JET")).pack(side="left", padx=2)
        ttk.Button(f_cv, text="HOT", **btn_config, command=lambda: self.aplicar_filtro(practica2.aplicar_colormap_opencv, "HOT")).pack(side="left", padx=2)
        ttk.Button(f_cv, text="OCEAN", **btn_config, command=lambda: self.aplicar_filtro(practica2.aplicar_colormap_opencv, "OCEAN")).pack(side="left", padx=2)

        # Matplotlib Personalizados
        f_plt = tk.Frame(lf_pre, bg=COLOR_BG)
        f_plt.pack(fill="x", pady=5)
        tk.Label(f_plt, text="Custom:", bg=COLOR_BG, fg="gray").pack(anchor="w")
        
        grid_frame = tk.Frame(f_plt, bg=COLOR_BG)
        grid_frame.pack(fill="x")
        
        nombres_mapas = ["Pastel", "Tron", "Tron Ares", "Divisiones", "Arcoiris", "Popsicle"]
        
        for i, nombre in enumerate(nombres_mapas):
            r = i // 2
            c = i % 2
            ttk.Button(grid_frame, text=nombre, style="Gold.TButton", 
                    command=lambda n=nombre: self.aplicar_filtro(practica2.aplicar_colormap_matplotlib, n)).grid(row=r, column=c, padx=2, pady=2, sticky="ew")
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)


        # --- PARTE 2: MAPA PERSONALIZADO ---
        lf_custom = tk.LabelFrame(parent, text="Creador de Mapa Personalizado", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_custom.pack(fill="x", padx=10, pady=10)
        
        tk.Label(lf_custom, text="Define 3 puntos de control (RGB)", bg=COLOR_BG, fg="white").pack(pady=5)
        
        self.custom_colors = [None, None, None] 
        self.btn_colors_widgets = []
        
        f_pickers = tk.Frame(lf_custom, bg=COLOR_BG)
        f_pickers.pack(fill="x", pady=5)
        
        labels = ["0 (Inicio)", "127 (Medio)", "255 (Fin)"]
        
        for i in range(3):
            sub_f = tk.Frame(f_pickers, bg=COLOR_BG)
            sub_f.pack(side="left", expand=True)
            
            tk.Label(sub_f, text=labels[i], bg=COLOR_BG, fg="gray", font=("Arial", 8)).pack()
            
            canvas_color = tk.Canvas(sub_f, width=40, height=40, bg="#333", highlightthickness=1, highlightbackground="gray")
            canvas_color.pack(pady=2)
            
            ttk.Button(sub_f, text="Seleccionar", style="Gold.TButton", 
                    command=lambda idx=i, cnv=canvas_color: self.seleccionar_color(idx, cnv)).pack()
            
        self.btn_crear_mapa = ttk.Button(lf_custom, text="Crear Mapa Personalizado", style="Gold.TButton", 
                                        state="disabled", command=self.aplicar_mapa_personalizado)
        self.btn_crear_mapa.pack(fill="x", padx=20, pady=10)

    def construir_tab_3(self, parent):
        # --- ARITMÉTICA ESCALAR ---
        lf_esc = tk.LabelFrame(parent, text="Aritmética con Escalar", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_esc.pack(fill="x", padx=10, pady=5)
        
        btn_conf = {'style': "Gold.TButton", 'width': 10}
        
        # Fila de botones
        f_btns = tk.Frame(lf_esc, bg=COLOR_BG)
        f_btns.pack(fill="x", pady=2)
        
        ttk.Button(f_btns, text="Suma (+)", **btn_conf, 
                command=lambda: self.solicitar_escalar_y_aplicar(practica3.sumar_escalar)).pack(side="left", padx=5)
        ttk.Button(f_btns, text="Resta (-)", **btn_conf, 
                command=lambda: self.solicitar_escalar_y_aplicar(practica3.restar_escalar)).pack(side="left", padx=5)
        ttk.Button(f_btns, text="Multi (*)", **btn_conf, 
                command=lambda: self.solicitar_escalar_y_aplicar(practica3.multiplicar_escalar)).pack(side="left", padx=5)

        # --- ARITMÉTICA ENTRE IMÁGENES ---
        lf_img = tk.LabelFrame(parent, text="Operaciones Entre Imágenes", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_img.pack(fill="x", padx=10, pady=5)
        
        f_arit_img = tk.Frame(lf_img, bg=COLOR_BG)
        f_arit_img.pack(fill="x", pady=2)
        ttk.Button(f_arit_img, text="Img A + Img B", **btn_conf,
                command=lambda: self.operacion_dual(practica3.suma_imagenes)).pack(side="left", padx=5)
        ttk.Button(f_arit_img, text="Img A - Img B", **btn_conf,
                command=lambda: self.operacion_dual(practica3.resta_imagenes)).pack(side="left", padx=5)
        ttk.Button(f_arit_img, text="Img A * Img B", **btn_conf,
                command=lambda: self.operacion_dual(practica3.multiplicacion_imagenes)).pack(side="left", padx=5)

        # --- LÓGICA ---
        lf_log = tk.LabelFrame(parent, text="Operaciones Lógicas", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_log.pack(fill="x", padx=10, pady=5)
        
        f_log = tk.Frame(lf_log, bg=COLOR_BG)
        f_log.pack(fill="x", pady=2)
        ttk.Button(f_log, text="AND", **btn_conf, command=lambda: self.operacion_dual(practica3.logica_and)).pack(side="left", padx=5)
        ttk.Button(f_log, text="OR", **btn_conf, command=lambda: self.operacion_dual(practica3.logica_or)).pack(side="left", padx=5)
        ttk.Button(f_log, text="XOR", **btn_conf, command=lambda: self.operacion_dual(practica3.logica_xor)).pack(side="left", padx=5)
        ttk.Button(f_log, text="NOT (Inv)", **btn_conf, command=lambda: self.aplicar_filtro(practica3.logica_not)).pack(side="left", padx=5)

        # --- CONEXAS Y CONTORNOS ---
        lf_conn = tk.LabelFrame(parent, text="Componentes Conexas y Contornos", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_conn.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(lf_conn, text="Vecindad 4 (Etiquetado)", style="Gold.TButton", 
                command=lambda: self.aplicar_filtro(practica3.componentes_conexas, 4)).pack(fill="x", padx=5, pady=2)
        ttk.Button(lf_conn, text="Vecindad 8 (Etiquetado)", style="Gold.TButton", 
                command=lambda: self.aplicar_filtro(practica3.componentes_conexas, 8)).pack(fill="x", padx=5, pady=2)
        ttk.Button(lf_conn, text="Dibujar Contornos", style="Gold.TButton", 
                command=lambda: self.aplicar_filtro(practica3.dibujar_contornos)).pack(fill="x", padx=5, pady=2)

    # --- HELPERS PARA P3 ---

    def solicitar_escalar_y_aplicar(self, funcion):
        # Pide un numero flotante
        valor = simpledialog.askfloat("Entrada", "Ingresa el valor escalar:")
        if valor is not None:
            self.aplicar_filtro(funcion, valor)

    def operacion_dual(self, funcion_logica):
        """
        Maneja la lógica de verificar 2 imágenes, avisar al usuario
        y ejecutar la operación pasando la segunda imagen como argumento.
        """
        # 1. Verificar que existan las dos imágenes originales cargadas en memoria
        if self.data[1]["orig"] is None or self.data[2]["orig"] is None:
            messagebox.showwarning("Faltan Imágenes", "Para esta operación necesitas cargar Imagen 1 e Imagen 2.")
            return

        # 2. Determinar quién es la activa y quién la secundaria
        slot_activo = self.active_slot.get()
        slot_secundario = 2 if slot_activo == 1 else 1
        
        # 3. Mensaje de confirmación
        confirm = messagebox.askokcancel(
            "Confirmar Operación Dual", 
            f"La operación se aplicará sobre la IMAGEN {slot_activo} (Activa).\n"
            f"Se usará la IMAGEN {slot_secundario} como operando secundario.\n\n"
            "¿Deseas continuar?"
        )
        
        if confirm:
            img_secundaria = self.data[slot_secundario]["proc"]
            self.aplicar_filtro(funcion_logica, img_secundaria)

    def construir_tab_4(self, parent):
        # --- CONFIGURACIÓN DE KERNEL ---
        f_config = tk.Frame(parent, bg=COLOR_BG)
        f_config.pack(fill="x", padx=10, pady=5)
        
        tk.Label(f_config, text="Tamaño de Kernel (K):", bg=COLOR_BG, fg="white").pack(side="left")
        
        # Selector de valores impares (3, 5, 7, 9...)
        self.spin_kernel = tk.Spinbox(f_config, values=(3, 5, 7, 9, 11), width=5)
        self.spin_kernel.pack(side="left", padx=5)
        
        # --- GENERACIÓN DE RUIDO ---
        lf_ruido = tk.LabelFrame(parent, text="Generación de Ruido", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_ruido.pack(fill="x", padx=10, pady=5)
        
        btn_s = {'style': "Gold.TButton", 'width': 15}
        
        ttk.Button(lf_ruido, text="Sal y Pimienta", **btn_s,
                command=lambda: self.aplicar_filtro(practica4.ruido_sal_pimienta)).pack(side="left", padx=5, pady=2)
        ttk.Button(lf_ruido, text="Gaussiano", **btn_s,
                command=lambda: self.aplicar_filtro(practica4.ruido_gaussiano)).pack(side="left", padx=5, pady=2)

        # --- FILTROS PASO BAJAS (Lineales) ---
        lf_low = tk.LabelFrame(parent, text="Paso Bajas (Lineales)", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_low.pack(fill="x", padx=10, pady=5)
        
        # Usamos una función lambda auxiliar para leer el kernel actual del Spinbox
        def get_k(): return int(self.spin_kernel.get())

        ttk.Button(lf_low, text="Promedio", **btn_s,
                command=lambda: self.aplicar_filtro(practica4.filtro_promedio, get_k())).pack(side="left", padx=2)
        ttk.Button(lf_low, text="Prom. Pesado", **btn_s,
                command=lambda: self.aplicar_filtro(practica4.filtro_promedio_pesado, get_k())).pack(side="left", padx=2)
        ttk.Button(lf_low, text="Gaussiano", **btn_s,
                command=lambda: self.aplicar_filtro(practica4.filtro_gaussiano, get_k())).pack(side="left", padx=2)
        ttk.Button(lf_low, text="Bilateral", **btn_s,
                command=lambda: self.aplicar_filtro(practica4.filtro_bilateral, get_k())).pack(side="left", padx=2)

        # --- FILTROS NO LINEALES ---
        lf_nolin = tk.LabelFrame(parent, text="Filtros No Lineales (Estadísticos)", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_nolin.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(lf_nolin, text="Mediana", **btn_s,
                command=lambda: self.aplicar_filtro(practica4.filtro_mediana, get_k())).pack(side="left", padx=2)
        ttk.Button(lf_nolin, text="Moda (Lento)", **btn_s,
                command=lambda: self.aplicar_filtro(practica4.filtro_moda, get_k())).pack(side="left", padx=2)
        ttk.Button(lf_nolin, text="Máximo", **btn_s,
                command=lambda: self.aplicar_filtro(practica4.filtro_maximo, get_k())).pack(side="left", padx=2)
        ttk.Button(lf_nolin, text="Mínimo", **btn_s,
                command=lambda: self.aplicar_filtro(practica4.filtro_minimo, get_k())).pack(side="left", padx=2)

        # --- FILTROS PASO ALTAS (Bordes) ---
        lf_high = tk.LabelFrame(parent, text="Paso Altas (Detección de Bordes)", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_high.pack(fill="x", padx=10, pady=5)
        
        # Grid para ordenar tantos botones
        f_grid_h = tk.Frame(lf_high, bg=COLOR_BG)
        f_grid_h.pack(fill="x")
        
        ttk.Button(f_grid_h, text="Sobel", **btn_s,
                command=lambda: self.aplicar_filtro(practica4.filtro_sobel)).grid(row=0, column=0, padx=2, pady=2)
        ttk.Button(f_grid_h, text="Prewitt", **btn_s,
                command=lambda: self.aplicar_filtro(practica4.filtro_prewitt)).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(f_grid_h, text="Roberts", **btn_s,
                command=lambda: self.aplicar_filtro(practica4.filtro_roberts)).grid(row=0, column=2, padx=2, pady=2)
        
        ttk.Button(f_grid_h, text="Canny", **btn_s,
                command=lambda: self.aplicar_filtro(practica4.filtro_canny)).grid(row=1, column=0, padx=2, pady=2)
        ttk.Button(f_grid_h, text="Laplaciano", **btn_s,
                command=lambda: self.aplicar_filtro(practica4.filtro_laplaciano)).grid(row=1, column=1, padx=2, pady=2)
        ttk.Button(f_grid_h, text="Kirsch (Brújula)", **btn_s,
                command=lambda: self.aplicar_filtro(practica4.filtro_kirsch)).grid(row=1, column=2, padx=2, pady=2)

    def construir_tab_5(self, parent):
        # --- SEGMENTACIÓN ---
        lf_seg = tk.LabelFrame(parent, text="Técnicas de Segmentación", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_seg.pack(fill="x", padx=10, pady=5)
        
        btn_s = {'style': "Gold.TButton", 'width': 14}
        
        # Grid para botones de segmentación
        f_g1 = tk.Frame(lf_seg, bg=COLOR_BG)
        f_g1.pack(fill="x", pady=2)
        
        ttk.Button(f_g1, text="Otsu", **btn_s, 
                command=lambda: self.aplicar_filtro(practica5.seg_otsu)).grid(row=0, column=0, padx=2, pady=2)
        ttk.Button(f_g1, text="Kapur (Entropía)", **btn_s, 
                command=lambda: self.aplicar_filtro(practica5.seg_kapur)).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(f_g1, text="Min. Histograma", **btn_s, 
                command=lambda: self.aplicar_filtro(practica5.seg_min_histograma)).grid(row=0, column=2, padx=2, pady=2)
        
        ttk.Button(f_g1, text="Media", **btn_s, 
                command=lambda: self.aplicar_filtro(practica5.seg_media)).grid(row=1, column=0, padx=2, pady=2)
        ttk.Button(f_g1, text="Multiumbral", **btn_s, 
                command=lambda: self.aplicar_filtro(practica5.seg_multiumbral)).grid(row=1, column=1, padx=2, pady=2)
        ttk.Button(f_g1, text="Umbral Banda", **btn_s, 
                command=self.pedir_banda_y_aplicar).grid(row=1, column=2, padx=2, pady=2)

        # --- AJUSTE DE BRILLO Y CONTRASTE ---
        lf_eq = tk.LabelFrame(parent, text="Ajuste de Brillo y Contraste", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_eq.pack(fill="x", padx=10, pady=5)
        
        # Ecualizaciones
        tk.Label(lf_eq, text="Ecualizaciones:", bg=COLOR_BG, fg="gray").pack(anchor="w", padx=5)
        f_g2 = tk.Frame(lf_eq, bg=COLOR_BG)
        f_g2.pack(fill="x", pady=2)
        
        ttk.Button(f_g2, text="Uniforme", **btn_s, command=lambda: self.aplicar_filtro(practica5.eq_uniforme)).grid(row=0, column=0, padx=2)
        ttk.Button(f_g2, text="Exponencial", **btn_s, command=lambda: self.aplicar_filtro(practica5.eq_exponencial)).grid(row=0, column=1, padx=2)
        ttk.Button(f_g2, text="Rayleigh", **btn_s, command=lambda: self.aplicar_filtro(practica5.eq_rayleigh)).grid(row=0, column=2, padx=2)
        ttk.Button(f_g2, text="Hipercúbica", **btn_s, command=lambda: self.aplicar_filtro(practica5.eq_hipercubica)).grid(row=1, column=0, padx=2)
        ttk.Button(f_g2, text="Logarítmica", **btn_s, command=lambda: self.aplicar_filtro(practica5.eq_logaritmica)).grid(row=1, column=1, padx=2)
        
        # Funciones de Transferencia
        tk.Label(lf_eq, text="Funciones de Transferencia:", bg=COLOR_BG, fg="gray").pack(anchor="w", padx=5, pady=(5,0))
        f_g3 = tk.Frame(lf_eq, bg=COLOR_BG)
        f_g3.pack(fill="x", pady=2)
        
        ttk.Button(f_g3, text="Gamma (Input)", **btn_s, command=self.pedir_gamma_y_aplicar).pack(side="left", padx=2)
        ttk.Button(f_g3, text="Potencia ^2", **btn_s, command=lambda: self.aplicar_filtro(practica5.func_potencia, 2.0)).pack(side="left", padx=2)
        
        # Operaciones Histograma
        tk.Label(lf_eq, text="Operaciones Histograma:", bg=COLOR_BG, fg="gray").pack(anchor="w", padx=5, pady=(5,0))
        f_g4 = tk.Frame(lf_eq, bg=COLOR_BG)
        f_g4.pack(fill="x", pady=2)
        
        ttk.Button(f_g4, text="Desplazar (+/-)", **btn_s, command=self.pedir_desplazamiento).grid(row=0, column=0, padx=2)
        ttk.Button(f_g4, text="Expansión (Stret)", **btn_s, command=lambda: self.aplicar_filtro(practica5.expansion_histograma)).grid(row=0, column=1, padx=2)
        ttk.Button(f_g4, text="Contracción", **btn_s, command=self.pedir_contraccion).grid(row=0, column=2, padx=2)

    # --- HELPERS PARA P5 ---
    
    def pedir_banda_y_aplicar(self):
        # Pide min y max
        min_v = simpledialog.askinteger("Umbral Banda", "Valor Mínimo (0-255):", initialvalue=100)
        if min_v is None: return
        max_v = simpledialog.askinteger("Umbral Banda", "Valor Máximo (0-255):", initialvalue=200)
        if max_v is None: return
        self.aplicar_filtro(practica5.seg_umbral_banda, min_v, max_v)

    def pedir_gamma_y_aplicar(self):
        g = simpledialog.askfloat("Gamma", "Valor Gamma (Ej. 0.5 o 2.2):", initialvalue=1.0)
        if g is not None: self.aplicar_filtro(practica5.correccion_gamma, g)

    def pedir_desplazamiento(self):
        val = simpledialog.askinteger("Desplazar", "Valor a sumar/restar (-255 a 255):", initialvalue=50)
        if val is not None: self.aplicar_filtro(practica5.desplazar_histograma, val)

    def pedir_contraccion(self):
        min_c = simpledialog.askinteger("Contracción", "Nuevo Mínimo (Ej. 50):", initialvalue=50)
        if min_c is None: return
        max_c = simpledialog.askinteger("Contracción", "Nuevo Máximo (Ej. 200):", initialvalue=200)
        if max_c is None: return
        self.aplicar_filtro(practica5.contraccion_histograma, min_c, max_c)

    def construir_tab_6(self, parent):
        # --- CONFIGURACIÓN ---
        f_conf = tk.Frame(parent, bg=COLOR_BG)
        f_conf.pack(fill="x", padx=10, pady=10)
        
        tk.Label(f_conf, text="Tamaño de Kernel:", bg=COLOR_BG, fg="white").pack(side="left")
        
        # Spinbox para tamaño de kernel (Impares: 3, 5, 7...)
        self.spin_morph = tk.Spinbox(f_conf, values=(3, 5, 7, 9, 11, 13, 15, 21), width=5)
        self.spin_morph.pack(side="left", padx=5)
        self.spin_morph.delete(0, "end")
        self.spin_morph.insert(0, 5) # Valor por defecto 5
        
        def get_k(): return int(self.spin_morph.get())
        
        # --- OPERACIONES ---
        lf_ops = tk.LabelFrame(parent, text="Operaciones Morfológicas", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_ops.pack(fill="x", padx=10, pady=5)
        
        btn_s = {'style': "Gold.TButton", 'width': 20}
        
        # Erosión y Dilatación
        f_row1 = tk.Frame(lf_ops, bg=COLOR_BG)
        f_row1.pack(fill="x", pady=5)
        ttk.Button(f_row1, text="Erosión (Adelgazar)", **btn_s, 
                command=lambda: self.aplicar_filtro(practica6.erosion, get_k())).pack(side="left", padx=5, expand=True)
        ttk.Button(f_row1, text="Dilatación (Engrosar)", **btn_s, 
                command=lambda: self.aplicar_filtro(practica6.dilatacion, get_k())).pack(side="left", padx=5, expand=True)
        
        # Apertura y Cierre
        f_row2 = tk.Frame(lf_ops, bg=COLOR_BG)
        f_row2.pack(fill="x", pady=5)
        ttk.Button(f_row2, text="Apertura (Quitar Ruido)", **btn_s, 
                command=lambda: self.aplicar_filtro(practica6.apertura, get_k())).pack(side="left", padx=5, expand=True)
        ttk.Button(f_row2, text="Cierre (Tapar Huecos)", **btn_s, 
                command=lambda: self.aplicar_filtro(practica6.cierre, get_k())).pack(side="left", padx=5, expand=True)

        # Extra: Gradiente (útil para bordes)
        ttk.Separator(lf_ops, orient='horizontal').pack(fill='x', pady=5)
        ttk.Button(lf_ops, text="Gradiente Morfológico", style="Gold.TButton",
                command=lambda: self.aplicar_filtro(practica6.gradiente_morfologico, get_k())).pack(pady=5, padx=5, fill="x")
        
        lbl_nota = tk.Label(lf_ops, text="Nota: Estas operaciones funcionan mejor\nsobre imágenes Binarizadas (Blanco/Negro).", 
                            bg=COLOR_BG, fg="gray", font=("Arial", 8, "italic"))
        lbl_nota.pack(pady=5)

    def construir_tab_7(self, parent):
        # --- VISUALIZACIÓN DE ESPECTRO ---
        lf_spec = tk.LabelFrame(parent, text="Análisis de Espectro", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_spec.pack(fill="x", padx=10, pady=5)
        
        btn_s = {'style': "Gold.TButton", 'width': 18}
        
        ttk.Button(lf_spec, text="Ver Espectro Magnitud", **btn_s,
                command=lambda: self.aplicar_filtro(practica7.obtener_espectro_magnitud)).pack(side="left", padx=5, pady=5)
        ttk.Button(lf_spec, text="Ver Espectro Fase", **btn_s,
                command=lambda: self.aplicar_filtro(practica7.obtener_espectro_fase)).pack(side="left", padx=5, pady=5)
        
        # --- FILTRADO EN FRECUENCIA ---
        lf_filter = tk.LabelFrame(parent, text="Filtros en el Dominio de Frecuencia", bg=COLOR_BG, fg=COLOR_ACCENT)
        lf_filter.pack(fill="x", padx=10, pady=10)
        
        # Controles de Parámetros
        f_params = tk.Frame(lf_filter, bg=COLOR_BG)
        f_params.pack(fill="x", padx=5, pady=5)
        
        # Slider Cutoff (Frecuencia de corte)
        tk.Label(f_params, text="Frecuencia de Corte (Radio %):", bg=COLOR_BG, fg="white").pack(anchor="w")
        self.slider_cutoff = tk.Scale(f_params, from_=1, to=100, orient="horizontal", bg=COLOR_BG, fg="white", highlightthickness=0)
        self.slider_cutoff.set(15) # Valor por defecto 15%
        self.slider_cutoff.pack(fill="x", pady=2)

        # Slider Orden (Butterworth)
        tk.Label(f_params, text="Orden (Solo Butterworth):", bg=COLOR_BG, fg="white").pack(anchor="w")
        self.slider_orden = tk.Scale(f_params, from_=1, to=10, orient="horizontal", bg=COLOR_BG, fg="white", highlightthickness=0)
        self.slider_orden.set(2)
        self.slider_orden.pack(fill="x", pady=2)
        
        # Botones de Filtros
        # PASA BAJAS
        f_low = tk.Frame(lf_filter, bg=COLOR_BG)
        f_low.pack(fill="x", pady=5)
        tk.Label(f_low, text="Pasa Bajas (Suavizar):", bg=COLOR_BG, fg=COLOR_ACCENT).pack(anchor="w")
        
        # Función auxiliar para obtener params
        def get_params(): return (self.slider_cutoff.get(), self.slider_orden.get())
        
        ttk.Button(f_low, text="Ideal", width=10, style="Gold.TButton",
                   command=lambda: self.aplicar_filtro(practica7.aplicar_filtro_frecuencia, 'Ideal', 'Bajas', *get_params())).pack(side="left", padx=2)
        ttk.Button(f_low, text="Gaussiano", width=10, style="Gold.TButton",
                   command=lambda: self.aplicar_filtro(practica7.aplicar_filtro_frecuencia, 'Gaussiano', 'Bajas', *get_params())).pack(side="left", padx=2)
        ttk.Button(f_low, text="Butterworth", width=10, style="Gold.TButton",
                   command=lambda: self.aplicar_filtro(practica7.aplicar_filtro_frecuencia, 'Butterworth', 'Bajas', *get_params())).pack(side="left", padx=2)

        # PASA ALTAS
        f_high = tk.Frame(lf_filter, bg=COLOR_BG)
        f_high.pack(fill="x", pady=5)
        tk.Label(f_high, text="Pasa Altas (Bordes):", bg=COLOR_BG, fg=COLOR_ACCENT).pack(anchor="w")
        
        ttk.Button(f_high, text="Ideal", width=10, style="Gold.TButton",
                   command=lambda: self.aplicar_filtro(practica7.aplicar_filtro_frecuencia, 'Ideal', 'Altas', *get_params())).pack(side="left", padx=2)
        ttk.Button(f_high, text="Gaussiano", width=10, style="Gold.TButton",
                   command=lambda: self.aplicar_filtro(practica7.aplicar_filtro_frecuencia, 'Gaussiano', 'Altas', *get_params())).pack(side="left", padx=2)
        ttk.Button(f_high, text="Butterworth", width=10, style="Gold.TButton",
                   command=lambda: self.aplicar_filtro(practica7.aplicar_filtro_frecuencia, 'Butterworth', 'Altas', *get_params())).pack(side="left", padx=2)

    # --- FUNCIONES AUXILIARES PARA PESTAÑA 2 ---------------------------------------------------------------------------
    
    def seleccionar_color(self, index, canvas_widget):
        # Abre el selector de color nativo del sistema (Círculo Cromático)
        color = colorchooser.askcolor(title=f"Seleccionar color {index+1}")
        
        if color[1] is not None: # color[0] es (r,g,b), color[1] es hex "#RRGGBB"
            rgb = color[0]
            hex_val = color[1]
            
            # Guardar valor
            self.custom_colors[index] = rgb
            
            # Actualizar visualización (Canvas)
            canvas_widget.config(bg=hex_val)
            
            # Verificar si ya tenemos los 3 colores para habilitar el botón
            if all(c is not None for c in self.custom_colors):
                self.btn_crear_mapa.config(state="normal")

    def aplicar_mapa_personalizado(self):
        c1, c2, c3 = self.custom_colors
        if any(c is None for c in [c1, c2, c3]):
            return # Seguridad extra
            
        self.aplicar_filtro(practica2.crear_mapa_usuario, c1, c2, c3)

    # --- FUNCIONES AUXILIARES PARA PESTAÑA 2 ---
    
    def seleccionar_color(self, index, canvas_widget):
        # Abre el selector de color nativo del sistema (Círculo Cromático)
        color = colorchooser.askcolor(title=f"Seleccionar color {index+1}")
        
        if color[1] is not None: # color[0] es (r,g,b), color[1] es hex "#RRGGBB"
            rgb = color[0]
            hex_val = color[1]
            
            # Guardar valor
            self.custom_colors[index] = rgb
            
            # Actualizar visualización (Canvas)
            canvas_widget.config(bg=hex_val)
            
            # Verificar si ya tenemos los 3 colores para habilitar el botón
            if all(c is not None for c in self.custom_colors):
                self.btn_crear_mapa.config(state="normal")

    def aplicar_mapa_personalizado(self):
        c1, c2, c3 = self.custom_colors
        if any(c is None for c in [c1, c2, c3]):
            return # Seguridad extra
            
        self.aplicar_filtro(practica2.crear_mapa_usuario, c1, c2, c3)

    # --- LÓGICA DE GESTIÓN DE DATOS ---

    def cargar_imagen(self, slot):
        path = filedialog.askopenfilename(filetypes=[("Imagenes", "*.jpg *.png *.bmp *.tif")])
        if not path: return
        img = cv2.imread(path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Guardar en estructura de datos
        self.data[slot]["orig"] = img
        self.data[slot]["proc"] = img.copy()
        self.data[slot]["hist"] = [] # Reset historial
        
        # Lógica de Cambio de Vista Automático
        has_1 = self.data[1]["orig"] is not None
        has_2 = self.data[2]["orig"] is not None

        if slot == 1:
            self.active_slot.set(1) # Enfocar la nueva
            if not has_2: self.view_mode.set(1) # Solo img 1 -> ver img 1
        elif slot == 2:
            self.active_slot.set(2) # Enfocar la nueva
            if not has_1: self.view_mode.set(2) # Solo img 2 -> ver img 2

        self.actualizar_estado_switch()
        self.actualizar_controles_vista()
        self.renderizar_grilla() # Redibujar todo

    def borrar_imagen(self, slot):
        if self.data[slot]["orig"] is None: return
        
        # Limpiar datos
        self.data[slot] = {"orig": None, "proc": None, "hist": []}
        
        # Ajustar vista si borramos la activa
        other = 1 if slot == 2 else 2
        if self.data[other]["orig"] is not None:
            self.active_slot.set(other)
            self.view_mode.set(other)
        else:
            # Si no queda ninguna
            self.view_mode.set(1) 
        
        self.actualizar_estado_switch()
        self.actualizar_controles_vista()
        self.renderizar_grilla()

    def aplicar_filtro(self, func_logica, *args):
        slot = self.active_slot.get()
        if self.data[slot]["orig"] is None:
            messagebox.showwarning("Error", f"No hay imagen cargada en el Slot {slot}")
            return
        
        # Guardar en historial antes de modificar
        img_actual = self.data[slot]["proc"]
        self.data[slot]["hist"].append(img_actual.copy())
        
        # Procesar (SIEMPRE sobre la original del slot, o sobre la actual si quisieras encadenar efectos.
        # Por simplicidad y robustez, aplicamos sobre la ORIGINAL del slot como base para filtros absolutos
        # PERO para deshacer funcione bien con flujo continuo, aplicamos sobre la ACTUAL si es acumulativo?
        # En tu prompt pides volver a la previa. Asumiremos flujo acumulativo para que "Deshacer" tenga sentido.
        
        # MODIFICACIÓN: Aplicamos sobre la procesada actual para permitir encadenamiento, 
        # o sobre la original si la función lo requiere.
        # Para filtros como grises/binarizar, normalmente se parte de la original para no degradar.
        # Usaremos la imagen procesada actual como input:
        try:
            res = func_logica(self.data[slot]["proc"], *args)
            self.data[slot]["proc"] = res
            self.renderizar_grilla() # Actualizar visualización
        except Exception as e:
            messagebox.showerror("Error PDI", str(e))
            if self.data[slot]["hist"]: self.data[slot]["hist"].pop() # Revertir historial si falló

    def deshacer(self):
        slot = self.active_slot.get()
        historia = self.data[slot]["hist"]
        if not historia:
            messagebox.showinfo("Info", f"No hay acciones para deshacer en Imagen {slot}")
            return
        
        # Recuperar penúltimo estado
        prev = historia.pop()
        self.data[slot]["proc"] = prev
        self.renderizar_grilla()

    def reset_imagen(self):
        slot = self.active_slot.get()
        if self.data[slot]["orig"] is None: return
        
        self.data[slot]["hist"].append(self.data[slot]["proc"].copy())
        self.data[slot]["proc"] = self.data[slot]["orig"].copy()
        self.renderizar_grilla()

    def guardar_imagen(self):
        slot = self.active_slot.get()
        img = self.data[slot]["proc"]
        if img is None: return
        
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png"), ("JPG", "*.jpg")])
        if path:
            if len(img.shape) == 3: img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            cv2.imwrite(path, img)

    # --- VISUALIZACIÓN Y GRILLA (NUEVA LÓGICA) ---

    def actualizar_controles_vista(self):
        # Limpiar botones viejos
        for w in self.view_controls.winfo_children(): w.destroy()
        
        has_1 = self.data[1]["orig"] is not None
        has_2 = self.data[2]["orig"] is not None
        
        if has_1 and has_2:
            # Mostrar selector de 3 vías
            tk.Label(self.view_controls, text="Modo de Vista:", bg=COLOR_BG, fg="gray").pack(side="left", padx=10)
            
            ttk.Button(self.view_controls, text="[1] Ver Img 1", width=10, 
                    command=lambda: self.set_vista(1)).pack(side="left", padx=2)
            ttk.Button(self.view_controls, text="[2] Ver Img 2", width=10, 
                    command=lambda: self.set_vista(2)).pack(side="left", padx=2)
            ttk.Button(self.view_controls, text="[↔] Ver Ambas", width=12, style="Gold.TButton",
                    command=lambda: self.set_vista(3)).pack(side="left", padx=2)

    def set_vista(self, modo):
        self.view_mode.set(modo)
        self.renderizar_grilla()

    def inicializar_grilla(self):
        # Crea placeholders vacíos
        self.renderizar_grilla()

    def renderizar_grilla(self):
        # Limpiar todo el área de grilla
        for widget in self.grid_area.winfo_children(): widget.destroy()
        
        mode = self.view_mode.get()
        
        # --- CASO A: VISTA SIMPLE (2x2) ---
        if mode == 1 or mode == 2:
            slot = mode
            # Datos a mostrar
            d_orig = self.data[slot]["orig"]
            d_proc = self.data[slot]["proc"]
            titulo_base = f"IMAGEN {slot}"
            
            # Configurar Grid 2x2
            self.grid_area.columnconfigure(0, weight=1)
            self.grid_area.columnconfigure(1, weight=1)
            self.grid_area.rowconfigure(0, weight=3) # Imagenes
            self.grid_area.rowconfigure(1, weight=1) # Histogramas
            
            # Crear Widgets
            self.crear_panel_imagen(self.grid_area, d_orig, f"{titulo_base} - ORIGINAL", 0, 0)
            self.crear_panel_imagen(self.grid_area, d_proc, f"{titulo_base} - MODIFICADA", 0, 1)
            self.crear_panel_histo(self.grid_area, d_orig, 1, 0)
            self.crear_panel_histo(self.grid_area, d_proc, 1, 1)

        # --- CASO B: VISTA DUAL (2x4) ---
        elif mode == 3:
            # Configurar Grid 2x4
            for c in range(4): self.grid_area.columnconfigure(c, weight=1)
            self.grid_area.rowconfigure(0, weight=3)
            self.grid_area.rowconfigure(1, weight=1)
            
            # Slot 1 (Columnas 0 y 1)
            self.crear_panel_imagen(self.grid_area, self.data[1]["orig"], "IMG 1 - ORIG", 0, 0)
            self.crear_panel_imagen(self.grid_area, self.data[1]["proc"], "IMG 1 - MOD", 0, 1)
            self.crear_panel_histo(self.grid_area, self.data[1]["orig"], 1, 0)
            self.crear_panel_histo(self.grid_area, self.data[1]["proc"], 1, 1)
            
            # Slot 2 (Columnas 2 y 3)
            self.crear_panel_imagen(self.grid_area, self.data[2]["orig"], "IMG 2 - ORIG", 0, 2)
            self.crear_panel_imagen(self.grid_area, self.data[2]["proc"], "IMG 2 - MOD", 0, 3)
            self.crear_panel_histo(self.grid_area, self.data[2]["orig"], 1, 2)
            self.crear_panel_histo(self.grid_area, self.data[2]["proc"], 1, 3)

    # --- HELPERS VISUALES ---
    def crear_panel_imagen(self, parent, img_data, titulo, r, c):
        frame = tk.Frame(parent, bg="black", bd=1, relief="sunken")
        frame.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
        tk.Label(frame, text=titulo, bg="black", fg="white", font=("Arial", 8)).pack(side="top", fill="x")
        lbl = tk.Label(frame, bg="#111", text="[Vacio]")
        lbl.pack(fill="both", expand=True)
        
        if img_data is not None:
            self.mostrar_imagen_en_label(img_data, lbl)

    def crear_panel_histo(self, parent, img_data, r, c):
        frame = tk.Frame(parent, bg=COLOR_BG)
        frame.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
        
        fig = Figure(figsize=(2, 1.5), dpi=70, facecolor=COLOR_BG)
        ax = fig.add_subplot(111)
        ax.set_facecolor(COLOR_BG)
        ax.tick_params(colors='white', labelsize=5)
        for spine in ax.spines.values(): spine.set_color(COLOR_BG)
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        if img_data is not None:
            self.dibujar_histo(ax, img_data)
            canvas.draw()

    def mostrar_imagen_en_label(self, img_arr, lbl):
        # Determinar tamaño dinámico según el label (o fijo pequeño para la grilla 2x4)
        h, w = img_arr.shape[:2]
        
        # Convertir a RGB para PIL
        if len(img_arr.shape) == 2:
            disp = cv2.cvtColor(img_arr, cv2.COLOR_GRAY2RGB)
        else:
            disp = img_arr
            
        pil_img = Image.fromarray(disp)
        pil_img.thumbnail((350, 350)) # Thumbnail max size
        tk_img = ImageTk.PhotoImage(pil_img)
        lbl.config(image=tk_img, text="")
        lbl.image = tk_img

    # --- Reemplazar esta función en interfaz.py ---
    def dibujar_histo(self, ax, img_arr, es_hue=False):
        ax.clear()
        
        # CASO ESPECIAL: Histograma de Matiz (Multicolor)
        if es_hue:
            # La imagen img_arr viene en RGB (arcoiris). 
            # Convertimos a HSV para contar los valores reales de H (0-179)
            hsv_temp = cv2.cvtColor(img_arr, cv2.COLOR_RGB2HSV)
            hist = cv2.calcHist([hsv_temp], [0], None, [180], [0, 180])
            
            # Dibujar barra por barra con su color correspondiente
            # Esto puede ser un poco lento, pero es la forma de tener el arcoiris exacto
            bins = np.arange(180)
            vals = hist.flatten()
            
            # Crear mapa de colores para las barras
            colors = []
            for h_val in range(180):
                # Convertir H(0-179) S(255) V(255) a RGB normalizado (0-1) para matplotlib
                rgb_norm = cv2.cvtColor(np.uint8([[[h_val, 255, 255]]]), cv2.COLOR_HSV2RGB)[0][0] / 255.0
                colors.append(rgb_norm)
            
            ax.bar(bins, vals, color=colors, width=1.0)
            ax.set_xlim([0, 180])
            
        # CASO NORMAL: Escala de Grises (1 canal)
        elif len(img_arr.shape) == 2:
            hist = cv2.calcHist([img_arr], [0], None, [256], [0, 256])
            ax.plot(hist, color='white', linewidth=1)
            ax.fill_between(range(256), hist.flatten(), color='gray', alpha=0.3)
            ax.set_xlim([0, 256])
            
        # CASO NORMAL: RGB (3 canales)
        else:
            for i, col in enumerate(['r', 'g', 'b']):
                hist = cv2.calcHist([img_arr], [i], None, [256], [0, 256])
                ax.plot(hist, color=col, linewidth=1)
            ax.set_xlim([0, 256])

        # Ajustes finales de estilo
        ax.set_facecolor(COLOR_BG)
        ax.tick_params(colors='white', labelsize=6)
        for spine in ax.spines.values(): spine.set_color(COLOR_BG)
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')

    # --- POPUP CANALES (Igual que antes pero adaptado a data) ---
    # --- Reemplazar esta función en interfaz.py ---
    def abrir_ventana_canales(self, modelo):
        slot = self.active_slot.get()
        img = self.data[slot]["orig"]
        if img is None: return

        vent = tk.Toplevel(self.root)
        vent.title(f"Canales {modelo} - Imagen {slot}")
        vent.geometry("1000x800")
        vent.configure(bg=COLOR_BG)
        
        # Obtener imágenes procesadas
        if modelo == "RGB":
            imgs = [img] + list(practica1.obtener_canales_rgb_visual(img))
            lbls = ["Original", "Rojo", "Verde", "Azul"]
        elif modelo == "HSV":
            imgs = [img] + list(practica1.obtener_canales_hsv_visual(img))
            lbls = ["Original", "Hue (Matiz)", "Sat (Saturación)", "Val (Brillo)"]
        elif modelo == "CMY":
            imgs = [img] + list(practica1.obtener_canales_cmy_visual(img))
            lbls = ["Original", "Cian", "Magenta", "Amarillo"]

        # Configurar Grilla
        for i in range(4):
            vent.rowconfigure(i, weight=1)
        vent.columnconfigure(0, weight=3)
        vent.columnconfigure(1, weight=2)

        for i, (im, txt) in enumerate(zip(imgs, lbls)):
            # Panel Imagen
            f_img = tk.LabelFrame(vent, text=txt, bg="black", fg="white")
            f_img.grid(row=i, column=0, sticky="nsew", padx=5, pady=2)
            l = tk.Label(f_img, bg="#111")
            l.pack(fill="both", expand=True)
            self.mostrar_imagen_en_label(im, l)
            
            # Panel Histograma
            f_hist = tk.Frame(vent, bg=COLOR_BG)
            f_hist.grid(row=i, column=1, sticky="nsew", padx=5, pady=2)
            
            fig = Figure(figsize=(4, 2), dpi=60, facecolor=COLOR_BG)
            ax = fig.add_subplot(111)
            ax.set_facecolor(COLOR_BG)
            ax.tick_params(colors='white', labelsize=6)
            canvas = FigureCanvasTkAgg(fig, master=f_hist)
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
            # DETECCIÓN ESPECIAL: Si estamos en HSV y es el canal Hue (índice 1 en la lista)
            es_hue = (modelo == "HSV" and i == 1)
            self.dibujar_histo(ax, im, es_hue=es_hue) # Pasamos el flag