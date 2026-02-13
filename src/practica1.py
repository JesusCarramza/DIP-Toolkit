import cv2
import numpy as np

# --- FUNCIONES BÁSICAS ---

def convertir_a_grises(img_rgb):
    if len(img_rgb.shape) == 2:
        return img_rgb
    return cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

def binarizar_manual(img_rgb, umbral):
    gris = convertir_a_grises(img_rgb)
    _, binaria = cv2.threshold(gris, umbral, 255, cv2.THRESH_BINARY)
    return binaria

def binarizar_adaptativo(img_rgb):
    """
    Reemplaza a Otsu. Basado en la referencia:
    cv2.adaptiveThreshold(..., cv2.ADAPTIVE_THRESH_MEAN_C, ...)
    """
    gris = convertir_a_grises(img_rgb)
    # Parámetros tomados exactamente de tu archivo de referencia (Block Size 11, C 2)
    binaria = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
    return binaria

# --- MODELOS DE COLOR (VISUALIZACIÓN) ---

def obtener_canales_rgb_visual(img_rgb):
    """Devuelve 3 imágenes RGB listas para visualizar R, G y B individualmente"""
    r, g, b = cv2.split(img_rgb)
    zeros = np.zeros_like(r)
    
    # Referencia usa cmap="Reds", nosotros creamos la imagen tintada real
    img_r = cv2.merge([r, zeros, zeros])
    img_g = cv2.merge([zeros, g, zeros])
    img_b = cv2.merge([zeros, zeros, b])
    
    return img_r, img_g, img_b

def obtener_canales_hsv_visual(img_rgb):
    """
    Devuelve visualización HSV coincidiendo con la lógica de referencia.
    Referencia H: cmap="hsv" (Arcoiris)
    Referencia S y V: cmap="gray" (Escala de grises)
    """
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    h, s, v = cv2.split(hsv)
    
    # --- 1. Visualización Canal H (Color / cmap='hsv') ---
    # Para simular cmap='hsv' en una imagen RGB plana:
    s_max = np.full_like(h, 255)
    v_max = np.full_like(h, 255)
    h_hsv = cv2.merge([h, s_max, v_max])
    img_h_visual = cv2.cvtColor(h_hsv, cv2.COLOR_HSV2RGB)

    # --- 2. Visualización S y V (Grises) ---
    return img_h_visual, s, v

def obtener_canales_cmy_visual(img_rgb):
    """
    Devuelve visualización CMY usando la matemática de la referencia.
    Referencia: imagen_cmy = 255 - imagen_cv_rgb
    """
    # 1. Matemática exacta de la referencia (Inversión directa)
    # Nota: OpenCV usa uint8, así que 255 - img funciona perfecto sin pasar a float
    img_cmy = 255 - img_rgb
    c, m, y_channel = cv2.split(img_cmy)
    zeros = np.zeros_like(c)

    # 2. Visualización
    # La referencia usa cmap="Blues" para Cian, pero visualmente es más correcto
    # mostrar el color Cian real (Mezcla de Verde y Azul).
    
    # Cian (R=0, G=C, B=C)
    img_c = cv2.merge([zeros, c, c]) 
    
    # Magenta (R=M, G=0, B=M)
    img_m = cv2.merge([m, zeros, m])
    
    # Amarillo (R=Y, G=Y, B=0)
    img_y = cv2.merge([y_channel, y_channel, zeros])

    return img_c, img_m, img_y