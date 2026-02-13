import cv2
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# --- DEFINICIÓN DE PALETAS ---

colores_pastel = [
    (1.0, 0.8, 0.9), (0.8, 1.0, 0.8), (0.8, 0.9, 1.0), 
    (1.0, 1.0, 0.8), (0.9, 0.8, 1.0)
]

colores_tron = [
    (0/255, 14/255, 82/255), (0/255, 27/255, 145/255), (122/255, 147/255, 255/255)
]

colores_tron_ares = [
    (64/255, 0/255, 32/255), (130/255, 0/255, 7/255), (255/255, 207/255, 208/255)
]

colores_divisiones = [
    (176/255, 0/255, 167/255), (0/255, 176/255, 47/255), (176/255, 91/255, 0/255)
]

colores_arcoiris = [
    (148/255, 0/255, 211/255), (75/255, 0/255, 130/255), (0/255, 0/255, 255/255),
    (0/255, 130/255, 20/255), (240/255, 240/255, 0/255), (240/255, 120/255, 0/255),
    (255/255, 0/255, 0/255)
]

# NUEVO: Colores Popsicle (Rojo -> Blanco -> Azul)
colores_popsicle = [
    (1.0, 0.0, 0.0),  # Rojo Intenso
    (1.0, 1.0, 1.0),  # Blanco Puro
    (0.0, 0.0, 1.0)   # Azul Intenso
]

# --- LÓGICA DE APLICACIÓN ---

def aplicar_colormap_matplotlib(img, nombre_mapa):
    colors = []
    N = 256
    
    if nombre_mapa == "Pastel": colors = colores_pastel
    elif nombre_mapa == "Tron": colors = colores_tron
    elif nombre_mapa == "Tron Ares": colors = colores_tron_ares
    elif nombre_mapa == "Divisiones": 
        colors = colores_divisiones
        N = 3
    elif nombre_mapa == "Arcoiris": 
        colors = colores_arcoiris
        N = 7
    elif nombre_mapa == "Popsicle":  # CAMBIO AQUÍ
        colors = colores_popsicle
        N = 256 # Gradiente suave
    
    # Crear Colormap
    cmap = LinearSegmentedColormap.from_list(nombre_mapa, colors, N=256)
    
    # Convertir a LUT
    gradient = np.linspace(0, 1, 256)
    lut_rgba = cmap(gradient) 
    lut_rgb = (lut_rgba[:, :3] * 255).astype(np.uint8)
    lut_bgr = cv2.cvtColor(np.expand_dims(lut_rgb, 0), cv2.COLOR_RGB2BGR)
    
    # Aplicar
    if len(img.shape) == 3:
        gris = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gris = img
        
    res = cv2.LUT(cv2.cvtColor(gris, cv2.COLOR_GRAY2BGR), lut_bgr)
    return cv2.cvtColor(res, cv2.COLOR_BGR2RGB)

def aplicar_colormap_opencv(img, tipo):
    if len(img.shape) == 3: gris = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else: gris = img
        
    if tipo == "JET": code = cv2.COLORMAP_JET
    elif tipo == "HOT": code = cv2.COLORMAP_HOT
    elif tipo == "OCEAN": code = cv2.COLORMAP_OCEAN
    else: code = cv2.COLORMAP_JET
    
    res = cv2.applyColorMap(gris, code)
    return cv2.cvtColor(res, cv2.COLOR_BGR2RGB)

def crear_mapa_usuario(img, c1, c2, c3):
    # Normalizar colores (0-255 -> 0-1)
    c1_norm = [x/255.0 for x in c1]
    c2_norm = [x/255.0 for x in c2]
    c3_norm = [x/255.0 for x in c3]
    
    colors = [c1_norm, c2_norm, c3_norm]
    
    cmap = LinearSegmentedColormap.from_list("CustomUser", colors, N=256)
    
    gradient = np.linspace(0, 1, 256)
    lut_rgba = cmap(gradient)
    lut_rgb = (lut_rgba[:, :3] * 255).astype(np.uint8)
    lut_bgr = cv2.cvtColor(np.expand_dims(lut_rgb, 0), cv2.COLOR_RGB2BGR)
    
    if len(img.shape) == 3: gris = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else: gris = img
        
    res = cv2.LUT(cv2.cvtColor(gris, cv2.COLOR_GRAY2BGR), lut_bgr)
    return cv2.cvtColor(res, cv2.COLOR_BGR2RGB)