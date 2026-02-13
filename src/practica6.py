import cv2

def obtener_kernel(k_size):
    """Crea el elemento estructurante (Rectangular por defecto)"""
    # Se puede cambiar a cv2.MORPH_ELLIPSE o cv2.MORPH_CROSS si se desea
    return cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))

def erosion(img, k_size):
    kernel = obtener_kernel(k_size)
    return cv2.erode(img, kernel, iterations=1)

def dilatacion(img, k_size):
    kernel = obtener_kernel(k_size)
    return cv2.dilate(img, kernel, iterations=1)

def apertura(img, k_size):
    # Erosion seguida de Dilatacion (Elimina ruido blanco / puntos pequeños)
    kernel = obtener_kernel(k_size)
    return cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)

def cierre(img, k_size):
    # Dilatacion seguida de Erosion (Cierra huecos negros dentro de objetos)
    kernel = obtener_kernel(k_size)
    return cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)

def gradiente_morfologico(img, k_size):
    # Diferencia entre Dilatación y Erosión (Detecta bordes morfológicos)
    # Agrego este extra porque suele ser muy útil y venía en tu diseño original
    kernel = obtener_kernel(k_size)
    return cv2.morphologyEx(img, cv2.MORPH_GRADIENT, kernel)