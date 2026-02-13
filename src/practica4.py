import cv2
import numpy as np
from scipy import ndimage

# --- GENERACIÓN DE RUIDO ---

def ruido_sal_pimienta(img, cantidad=0.05):
    """
    Agrega ruido aleatorio: Pixeles blancos (sal) y negros (pimienta).
    cantidad: Porcentaje de la imagen a afectar (0.05 = 5%)
    """
    row, col = img.shape[:2]
    # Copia para no dañar original en memoria antes de tiempo
    out = img.copy()
    
    # Sal (Blancos)
    num_salt = np.ceil(cantidad * img.size * 0.5)
    coords = [np.random.randint(0, i - 1, int(num_salt)) for i in img.shape[:2]]
    # Manejo diferente si es gris o color
    if len(img.shape) == 2:
        out[coords[0], coords[1]] = 255
    else:
        out[coords[0], coords[1]] = (255, 255, 255)
        
    # Pimienta (Negros)
    num_pepper = np.ceil(cantidad * img.size * 0.5)
    coords = [np.random.randint(0, i - 1, int(num_pepper)) for i in img.shape[:2]]
    if len(img.shape) == 2:
        out[coords[0], coords[1]] = 0
    else:
        out[coords[0], coords[1]] = (0, 0, 0)
        
    return out

def ruido_gaussiano(img):
    """Agrega ruido con distribución normal (Gaussian)"""
    row, col = img.shape[:2]
    mean = 0
    var = 100 # Varianza ajustable
    sigma = var ** 0.5
    
    if len(img.shape) == 2:
        gauss = np.random.normal(mean, sigma, (row, col))
        gauss = gauss.reshape(row, col)
    else:
        gauss = np.random.normal(mean, sigma, (row, col, 3))
        gauss = gauss.reshape(row, col, 3)
        
    noisy = img + gauss
    # Clip para mantener valores entre 0 y 255 y convertir a uint8
    return np.clip(noisy, 0, 255).astype(np.uint8)

# --- FILTROS PASO BAJAS (SUAVIZADO) ---

def filtro_promedio(img, k_size):
    return cv2.blur(img, (k_size, k_size))

def filtro_promedio_pesado(img, k_size=3):
    # Aproximación gaussiana 3x3 estándar
    kernel = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]]) / 16
    if k_size == 5: # Ejemplo 5x5
        kernel = np.ones((5,5), np.float32) / 25
        # (Podríamos definir uno pesado 5x5 específico, pero usaremos conv estándar)
    return cv2.filter2D(img, -1, kernel)

def filtro_gaussiano(img, k_size):
    # SigmaX=0 deja que OpenCV lo calcule basado en k_size
    return cv2.GaussianBlur(img, (k_size, k_size), 0)

def filtro_bilateral(img, k_size):
    # Bilateral es lento, mantenemos sigmaColor y sigmaSpace fijos moderados
    return cv2.bilateralFilter(img, 9, 75, 75)

# --- FILTROS NO LINEALES ---

def filtro_mediana(img, k_size):
    # k_size debe ser impar
    if k_size % 2 == 0: k_size += 1
    return cv2.medianBlur(img, k_size)

def filtro_maximo(img, k_size):
    # El filtro máximo es equivalente a una DILATACIÓN morfológica
    kernel = np.ones((k_size, k_size), np.uint8)
    return cv2.dilate(img, kernel)

def filtro_minimo(img, k_size):
    # El filtro mínimo es equivalente a una EROSIÓN morfológica
    kernel = np.ones((k_size, k_size), np.uint8)
    return cv2.erode(img, kernel)

def filtro_moda(img, k_size=3):
    # Este es computacionalmente costoso. Usamos scipy.
    # ADVERTENCIA: Puede ser lento en imágenes grandes.
    if len(img.shape) == 3:
        # Procesar canal por canal o convertir a gris
        img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        img_gray = img

    # Definir función para ventana deslizante
    def get_mode(x):
        vals, counts = np.unique(x, return_counts=True)
        return vals[np.argmax(counts)]

    # Aplicar filtro genérico
    res = ndimage.generic_filter(img_gray, get_mode, size=k_size)
    return cv2.cvtColor(res, cv2.COLOR_GRAY2RGB) # Devolver formato compatible

# --- FILTROS PASO ALTAS (BORDES) ---
# Nota: La mayoría de estos funcionan mejor en escala de grises.
# Convertiremos internamente si es necesario.

def preparar_bordes(img):
    if len(img.shape) == 3:
        return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    return img

def filtro_sobel(img):
    gray = preparar_bordes(img)
    # Gradientes X e Y
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    # Magnitud del gradiente
    mag = cv2.magnitude(sobelx, sobely)
    # Normalizar a 0-255
    res = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    return res

def filtro_prewitt(img):
    gray = preparar_bordes(img)
    kernelx = np.array([[1,1,1],[0,0,0],[-1,-1,-1]])
    kernely = np.array([[-1,0,1],[-1,0,1],[-1,0,1]])
    img_prewittx = cv2.filter2D(gray, -1, kernelx)
    img_prewitty = cv2.filter2D(gray, -1, kernely)
    return cv2.addWeighted(img_prewittx, 0.5, img_prewitty, 0.5, 0)

def filtro_roberts(img):
    gray = preparar_bordes(img)
    # Kernels de Roberts (Cruzados 2x2)
    roberts_cross_v = np.array( [[1, 0 ], [0,-1 ]] )
    roberts_cross_h = np.array( [[ 0, 1 ], [ -1, 0 ]] )
    img_roberts_v = cv2.filter2D(gray, -1, roberts_cross_v)
    img_roberts_h = cv2.filter2D(gray, -1, roberts_cross_h)
    return cv2.addWeighted(img_roberts_v, 0.5, img_roberts_h, 0.5, 0)

def filtro_canny(img):
    gray = preparar_bordes(img)
    # Umbrales 100 y 200 son estándar, podrían ser parámetros
    return cv2.Canny(gray, 100, 200)

def filtro_laplaciano(img):
    gray = preparar_bordes(img)
    # Laplaciano es muy sensible al ruido, a veces se suaviza antes
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    res = cv2.normalize(np.abs(lap), None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    return res

def filtro_kirsch(img):
    gray = preparar_bordes(img)
    # Kirsch usa 8 máscaras rotativas (Brújula)
    # Definimos la base y rotamos o definimos manual
    k1 = np.array([[5, 5, 5], [-3, 0, -3], [-3, -3, -3]])
    k2 = np.array([[-3, 5, 5], [-3, 0, 5], [-3, -3, -3]])
    k3 = np.array([[-3, -3, 5], [-3, 0, 5], [-3, -3, 5]])
    k4 = np.array([[-3, -3, -3], [-3, 0, 5], [-3, 5, 5]])
    k5 = np.array([[-3, -3, -3], [-3, 0, -3], [5, 5, 5]])
    k6 = np.array([[-3, -3, -3], [5, 0, -3], [5, 5, -3]])
    k7 = np.array([[5, -3, -3], [5, 0, -3], [5, -3, -3]])
    k8 = np.array([[5, 5, -3], [5, 0, -3], [-3, -3, -3]])
    
    kernels = [k1, k2, k3, k4, k5, k6, k7, k8]
    max_response = np.zeros_like(gray)
    
    for k in kernels:
        resp = cv2.filter2D(gray, -1, k)
        max_response = np.maximum(max_response, resp)
        
    return max_response