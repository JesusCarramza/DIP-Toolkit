import cv2
import numpy as np

# --- OPERACIONES ARITMÉTICAS CON ESCALAR ---

def sumar_escalar(img, valor):
    # cv2.add maneja la saturación (si pasa de 255 se queda en 255, no da la vuelta a 0)
    # Creamos una tupla con el valor para los 3 canales si es color
    val_tuple = (valor, valor, valor, 0) if len(img.shape) == 3 else (valor, 0, 0, 0)
    return cv2.add(img, val_tuple)

def restar_escalar(img, valor):
    val_tuple = (valor, valor, valor, 0) if len(img.shape) == 3 else (valor, 0, 0, 0)
    return cv2.subtract(img, val_tuple)

def multiplicar_escalar(img, valor):
    # Para multiplicar usamos numpy con cuidado de tipos para no desbordar antes de recortar
    res = img.astype(np.float32) * valor
    res = np.clip(res, 0, 255).astype(np.uint8)
    return res

# --- OPERACIONES ENTRE IMÁGENES ---

def preparar_img_secundaria(img_base, img_secundaria):
    """Redimensiona la imagen secundaria para que coincida con la base"""
    h, w = img_base.shape[:2]
    return cv2.resize(img_secundaria, (w, h))

def suma_imagenes(imgA, imgB):
    imgB_resized = preparar_img_secundaria(imgA, imgB)
    return cv2.add(imgA, imgB_resized)

def resta_imagenes(imgA, imgB):
    imgB_resized = preparar_img_secundaria(imgA, imgB)
    return cv2.subtract(imgA, imgB_resized)

def multiplicacion_imagenes(imgA, imgB):
    imgB_resized = preparar_img_secundaria(imgA, imgB)
    # Multiplicar matrices normalizadas y luego escalar
    # Esto evita que la imagen se vuelva blanca inmediatamente
    res = cv2.multiply(imgA.astype(np.float32), imgB_resized.astype(np.float32))
    # Normalizamos para que vuelva a rango visible (opcional, pero recomendado para visualización)
    res = res / 255.0 
    return np.clip(res, 0, 255).astype(np.uint8)

# --- OPERACIONES LÓGICAS ---

def logica_and(imgA, imgB):
    imgB_resized = preparar_img_secundaria(imgA, imgB)
    return cv2.bitwise_and(imgA, imgB_resized)

def logica_or(imgA, imgB):
    imgB_resized = preparar_img_secundaria(imgA, imgB)
    return cv2.bitwise_or(imgA, imgB_resized)

def logica_xor(imgA, imgB):
    imgB_resized = preparar_img_secundaria(imgA, imgB)
    return cv2.bitwise_xor(imgA, imgB_resized)

def logica_not(img):
    return cv2.bitwise_not(img)

# --- COMPONENTES CONEXAS Y CONTORNOS ---

def componentes_conexas(img, conectividad=8):
    """
    Etiquetado de componentes. 
    Requiere imagen binaria (1 canal). Hacemos la conversión interna.
    """
    # 1. Asegurar escala de grises
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img

    # 2. Binarizar (Otsu) para asegurar que hay objetos definidos
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 3. Calcular componentes
    # output: num_labels, labels_image, stats, centroids
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=conectividad)

    # 4. Visualización (Mapear etiquetas a colores)
    # Normalizamos las etiquetas para que cubran el rango 0-255
    labels_norm = cv2.normalize(labels, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    # Aplicamos un mapa de color (JET) para diferenciar vecindades
    res_color = cv2.applyColorMap(labels_norm, cv2.COLORMAP_JET)
    
    return cv2.cvtColor(res_color, cv2.COLOR_BGR2RGB)

def dibujar_contornos(img):
    # 1. Preparar binaria
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 2. Encontrar contornos
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 3. Dibujar sobre la imagen original
    # Hacemos copia para no dañar la original si no se quiere
    res = img.copy()
    # Dibujamos en verde neón, grosor 2
    cv2.drawContours(res, contours, -1, (0, 255, 0), 2)
    
    return res