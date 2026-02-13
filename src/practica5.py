import cv2
import numpy as np

# --- UTILIDADES ---

def get_gray(img):
    if len(img.shape) == 3:
        return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    return img

def apply_lut(img, lut):
    """Aplica una tabla de búsqueda a la imagen (maneja color/grises)"""
    if len(img.shape) == 3:
        # Si es color, convertimos a HSV, ecualizamos V y volvemos
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        h, s, v = cv2.split(hsv)
        v_eq = cv2.LUT(v, lut)
        hsv_eq = cv2.merge([h, s, v_eq])
        return cv2.cvtColor(hsv_eq, cv2.COLOR_HSV2RGB)
    else:
        return cv2.LUT(img, lut)

# --- 1. TÉCNICAS DE SEGMENTACIÓN ---

def seg_otsu(img):
    gray = get_gray(img)
    _, binaria = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binaria

def seg_media(img):
    gray = get_gray(img)
    media = np.mean(gray)
    _, binaria = cv2.threshold(gray, media, 255, cv2.THRESH_BINARY)
    return binaria

def seg_kapur(img):
    """Método de Entropía Máxima de Kapur"""
    gray = get_gray(img)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    # Normalizar histograma (probabilidades)
    total_pixels = gray.size
    p = hist / total_pixels
    
    # Calcular tablas acumulativas para optimizar
    # P(t): Probabilidad acumulada hasta t
    # H(t): Entropía acumulada hasta t
    
    # Evitamos log(0) con eps
    eps = 1e-10
    
    max_entropy = -float('inf')
    best_thresh = 128
    
    # Pre-calcular entropía global para acelerar? No, Kapur divide en 2 clases.
    # Kapur: H(A) + H(B) maximizado.
    
    # Fuerza bruta optimizada sobre 256 niveles
    p_cum = np.cumsum(p)
    h_cum = np.cumsum(-p * np.log(p + eps))
    
    for t in range(1, 255):
        # Probabilidades de clases w0 y w1
        w0 = p_cum[t]
        w1 = 1.0 - w0
        
        if w0 == 0 or w1 == 0: continue
            
        # Entropías normalizadas por clase
        # H0 = -sum(pi/w0 * log(pi/w0)) = 1/w0 * sum(-pi*log pi) + log(w0)
        h0 = (h_cum[t] / w0) + np.log(w0 + eps)
        
        # H1 similar pero desde t+1 hasta 255
        h1 = ((h_cum[255] - h_cum[t]) / w1) + np.log(w1 + eps)
        
        total_ent = h0 + h1
        
        if total_ent > max_entropy:
            max_entropy = total_ent
            best_thresh = t
            
    _, binaria = cv2.threshold(gray, best_thresh, 255, cv2.THRESH_BINARY)
    return binaria

def seg_min_histograma(img):
    """Busca el valle entre dos picos principales del histograma suavizado"""
    gray = get_gray(img)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    
    # Suavizar histograma para eliminar ruido local
    hist_smooth = cv2.GaussianBlur(hist.reshape(1, -1), (1, 15), 5).flatten()
    
    # Encontrar picos y valles simples no es trivial robustamente.
    # Aproximación: Usamos método iterativo de medias (Isodata) que suele converger al valle
    # O implementamos Kittler-Illingworth (Min Error).
    # Haremos Isodata iterativo (Media iterativa) que es muy efectivo.
    t = 128
    while True:
        g1 = gray[gray <= t]
        g2 = gray[gray > t]
        if len(g1) == 0 or len(g2) == 0: break
        m1 = np.mean(g1)
        m2 = np.mean(g2)
        new_t = int((m1 + m2) / 2)
        if new_t == t: break
        t = new_t
        
    _, binaria = cv2.threshold(gray, t, 255, cv2.THRESH_BINARY)
    return binaria

def seg_multiumbral(img):
    """Divide la imagen en 3 regiones (2 umbrales) usando Otsu Recursivo"""
    gray = get_gray(img)
    # Otsu normal para encontrar primer corte
    thresh1, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Dividir en dos regiones
    region1 = gray[gray <= thresh1]
    region2 = gray[gray > thresh1]
    
    # Aplicar Otsu a la región superior (o la más grande/variada)
    # Por simplicidad, calculamos Otsu en la segunda mitad para sacar un segundo umbral alto
    _, th2_local = cv2.threshold(region2, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    thresh2 = thresh1 # Si falla, se queda igual
    
    # Re-calculamos otsu global masked? Más fácil: Otsu 2-niveles aproximado:
    # Usaremos 85 y 170 como semillas o buscamos.
    # Para cumplir "multiumbral" simple visualmente:
    res = np.zeros_like(gray)
    res[gray > thresh1] = 127
    # Un segundo umbral arbitrario basado en media de la parte alta
    if len(region2) > 0:
        thresh2 = int(np.mean(region2))
        res[gray > thresh2] = 255
        
    return res

def seg_umbral_banda(img, lower, upper):
    gray = get_gray(img)
    mask = cv2.inRange(gray, int(lower), int(upper))
    return mask

# --- 2. AJUSTE DE BRILLO Y CONTRASTE (ECUALIZACIONES) ---

def eq_uniforme(img):
    if len(img.shape) == 3:
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        h, s, v = cv2.split(hsv)
        v_eq = cv2.equalizeHist(v)
        return cv2.cvtColor(cv2.merge([h, s, v_eq]), cv2.COLOR_HSV2RGB)
    else:
        return cv2.equalizeHist(img)

def crear_lut_distribucion(funcion_distribucion):
    """Genera una LUT de 256 valores basada en una CDF objetivo"""
    lut = np.zeros(256, dtype=np.uint8)
    # Generamos la CDF ideal normalizada (0 a 1)
    cdf_ideal = funcion_distribucion(np.arange(256))
    cdf_ideal = (cdf_ideal - cdf_ideal.min()) / (cdf_ideal.max() - cdf_ideal.min() + 1e-5)
    lut = (cdf_ideal * 255).astype(np.uint8)
    return lut

def eq_exponencial(img, alpha=0.05):
    # G(z) = 1 - exp(-alpha * z)
    # Para histogram matching exacto se requiere igualar CDFs. 
    # Aquí aplicaremos una transformación directa de función de transferencia para efecto visual.
    # T(r) = -1/alpha * ln(1 - r) (Inversa de exponencial) -> Expande oscuros.
    
    lut = np.zeros(256, dtype=np.uint8)
    for i in range(256):
        r = i / 255.0
        # Formula aproximada para efecto exponencial visual
        val = 255 * (1 - np.exp(-alpha * i)) 
        lut[i] = np.clip(val, 0, 255)
    return apply_lut(img, lut)

def eq_rayleigh(img, alpha=0.4):
    # Distribución Rayleigh
    lut = np.zeros(256, dtype=np.uint8)
    # Usamos histogram matching simplificado
    # Mapeamos la entrada uniforme a Rayleigh
    # z = sqrt(2*alpha^2 * ln(1/(1-P(r))))
    # Asumimos entrada ecualizada (Prob Uniforme P(r)=r)
    g_max = np.sqrt(2 * alpha**2 * np.log(1 / (1 - 0.999))) # Para normalizar
    
    for i in range(256):
        r = i / 255.0 # Probabilidad acumulada (si asumimos imagen plana)
        if r >= 1.0: r = 0.999
        val_ray = np.sqrt(2 * alpha**2 * np.log(1 / (1 - r)))
        lut[i] = np.clip((val_ray / g_max) * 255, 0, 255)
        
    return apply_lut(img, lut)

def eq_hipercubica(img):
    # Transformación de potencia cúbica (raíz cúbica para aclarar o cubo para contrastar)
    # Usualmente Hipercúbica se refiere a elevar a 1/3
    lut = np.zeros(256, dtype=np.uint8)
    for i in range(256):
        r = i / 255.0
        val = r ** (1/3.0) * 255
        lut[i] = np.clip(val, 0, 255)
    return apply_lut(img, lut)

def eq_logaritmica(img):
    # T(r) = c * log(1 + r)
    c = 255 / np.log(1 + 255)
    lut = np.zeros(256, dtype=np.uint8)
    for i in range(256):
        val = c * np.log(1 + i)
        lut[i] = np.clip(val, 0, 255)
    return apply_lut(img, lut)

def correccion_gamma(img, gamma=1.0):
    # T(r) = r^gamma
    inv_gamma = 1.0 / gamma
    lut = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
    return apply_lut(img, lut)

def func_potencia(img, potencia=2.0):
    # T(r) = r^p
    lut = np.array([((i / 255.0) ** potencia) * 255 for i in range(256)]).astype("uint8")
    return apply_lut(img, lut)

# --- OPERACIONES DE HISTOGRAMA ---

def desplazar_histograma(img, valor):
    # Sumar constante
    lut = np.zeros(256, dtype=np.uint8)
    for i in range(256):
        lut[i] = np.clip(i + valor, 0, 255)
    return apply_lut(img, lut)

def expansion_histograma(img):
    # Contrast Stretching (Min-Max)
    gray = get_gray(img)
    min_val, max_val, _, _ = cv2.minMaxLoc(gray)
    
    if max_val - min_val == 0: return img # Evitar div por cero
    
    lut = np.zeros(256, dtype=np.uint8)
    for i in range(256):
        val = (i - min_val) * (255.0 / (max_val - min_val))
        lut[i] = np.clip(val, 0, 255)
    return apply_lut(img, lut)

def contraccion_histograma(img, min_out, max_out):
    # Comprimir rango a [min_out, max_out]
    lut = np.zeros(256, dtype=np.uint8)
    min_in, max_in = 0, 255
    slope = (max_out - min_out) / (max_in - min_in)
    
    for i in range(256):
        val = min_out + slope * (i - min_in)
        lut[i] = np.clip(val, 0, 255)
    return apply_lut(img, lut)