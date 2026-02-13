import cv2
import numpy as np

# --- UTILIDADES INTERNAS ---

def preparar_imagen_fft(img):
    """Convierte a escala de grises float32 para procesar"""
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img
    # Normalizar a 0-1 para los cálculos matemáticos del filtro
    return gray.astype(np.float32) / 255.0

def postprocesar_imagen(img_float):
    """Convierte float 0-1 de vuelta a uint8 0-255 para mostrar"""
    # Clip para evitar valores locos fuera de rango
    img_clipped = np.clip(img_float, 0, 1)
    res = (img_clipped * 255).astype(np.uint8)
    # Devolver como RGB para que la interfaz lo muestre bien
    return cv2.cvtColor(res, cv2.COLOR_GRAY2RGB)

# --- FFT Y ESPECTROS ---

def obtener_espectro_magnitud(img):
    gray = preparar_imagen_fft(img)
    F = np.fft.fft2(gray)
    Fshift = np.fft.fftshift(F)
    # Magnitud logarítmica para visualización: log(1 + abs(F))
    magnitude = np.log(1 + np.abs(Fshift))
    
    # Normalizar magnitud a 0-255 para visualizar
    magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    # Colorear con JET para que se vea "científico"
    return cv2.applyColorMap(magnitude_norm, cv2.COLORMAP_JET)

def obtener_espectro_fase(img):
    gray = preparar_imagen_fft(img)
    F = np.fft.fft2(gray)
    Fshift = np.fft.fftshift(F)
    phase = np.angle(Fshift)
    
    # La fase va de -pi a pi. Normalizar a 0-255.
    # phase + pi -> 0 a 2pi. / 2pi -> 0 a 1.
    phase_norm = ((phase + np.pi) / (2 * np.pi)) * 255
    phase_uint8 = phase_norm.astype(np.uint8)
    return cv2.cvtColor(phase_uint8, cv2.COLOR_GRAY2RGB)

# --- FILTROS DE FRECUENCIA ---

def crear_mascara(shape, tipo_filtro, modo_paso, cutoff_norm, orden=2):
    rows, cols = shape
    crow, ccol = rows // 2, cols // 2
    
    # Crear malla de coordenadas
    y, x = np.ogrid[:rows, :cols]
    # Distancia euclidiana al centro
    d_center = np.sqrt((x - ccol)**2 + (y - crow)**2)
    
    # Radio máximo para normalizar cutoff (0.0 - 1.0)
    # Usamos min dimension / 2 como referencia del radio total
    radius = min(crow, ccol)
    d0 = cutoff_norm * radius # Frecuencia de corte en pixeles
    
    if d0 == 0: d0 = 1e-8 # Evitar división por cero

    if tipo_filtro == 'Ideal':
        H = np.zeros((rows, cols), dtype=np.float32)
        if modo_paso == 'Bajas':
            H[d_center <= d0] = 1
        else: # Altas
            H[d_center > d0] = 1
            
    elif tipo_filtro == 'Gaussiano':
        # H(u,v) = exp(-D^2 / (2*D0^2))
        H = np.exp(-(d_center**2) / (2 * (d0**2)))
        if modo_paso == 'Altas':
            H = 1 - H
            
    elif tipo_filtro == 'Butterworth':
        # H(u,v) = 1 / (1 + (D/D0)^(2n))
        H = 1 / (1 + (d_center / d0)**(2 * orden))
        if modo_paso == 'Altas':
            H = 1 - H
            
    return H

def aplicar_filtro_frecuencia(img, tipo_filtro, modo_paso, cutoff, orden=2):
    """
    img: Imagen de entrada
    tipo_filtro: 'Ideal', 'Gaussiano', 'Butterworth'
    modo_paso: 'Bajas', 'Altas'
    cutoff: Valor 0-100 (slider), lo dividimos por 100 internamente
    orden: Entero (para Butterworth)
    """
    gray = preparar_imagen_fft(img)
    rows, cols = gray.shape
    
    # 1. FFT
    F = np.fft.fft2(gray)
    Fshift = np.fft.fftshift(F)
    
    # 2. Crear Máscara
    # Convertir cutoff de slider (0-100) a normalizado (0.0 - 1.0)
    cutoff_norm = cutoff / 100.0
    H = crear_mascara((rows, cols), tipo_filtro, modo_paso, cutoff_norm, orden)
    
    # 3. Aplicar Filtro
    Gshift = Fshift * H
    
    # 4. Inversa (IFFT)
    G = np.fft.ifftshift(Gshift)
    g = np.fft.ifft2(G)
    g_real = np.abs(g) # Magnitud de la inversa (parte real aprox)
    
    return postprocesar_imagen(g_real)