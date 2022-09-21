import json

import cv2 as cv
import numpy as np
import requests
from src.input.imagen import (Coordenada, calcular_distancia_arc_sec,
                              obtener_coordenada_centro,
                              obtener_dimensiones_imagen,
                              obtener_imagen_de_url, obtener_url_api)


def obtener_contornos(imagen):
    '''
    Función para detectar y obtener los contornos en una imagen
    '''
    imgray = cv.cvtColor(
        imagen, cv.COLOR_BGR2GRAY)  # Convertimos la imagen a una escala de grises

    max_val = 255
    # Todo píxel que supere este valor sera considerado como blanco (max_val)
    threshold = 50

    ret, thresh = cv.threshold(imgray, threshold, max_val, cv.THRESH_BINARY)
    contours, _ = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    return contours


def obtener_rectangulo_de_contorno(contorno):
    '''
    Función que obtiene el rectángulo o bounding box a partir de un contorno que contiene a un objeto 
    de OpenCV
    '''

    # x e y son las coordenadas del extremo superior izq.
    return cv.boundingRect(contorno)


def traducir_escala(maximo_px, maximo_grados, minimo_grados, punto_px):
    '''
    Traduce un punto en una rango en píxeles (0, max_px)
    a su correspondiente punto en un rango en grados (min_grados, max_grados)
    '''

    return maximo_grados - (punto_px * abs(maximo_grados - minimo_grados) / maximo_px)


def punto_a_coord_eq(coord1_limite, coord2_limite, x, y, w_imagen, h_imagen):
    '''
    Traduce un punto en px a coordenadas ecuatoriales
    basandose en los limites de la imagen

    ra = x
    dec = y
    '''

    limite_sup_ra = max(coord1_limite.ra, coord2_limite.ra)
    limite_inf_ra = min(coord1_limite.ra, coord2_limite.ra)

    limite_arriba_dec = min(coord1_limite.dec, coord2_limite.dec)
    limite_abajo_dec = max(coord1_limite.dec, coord2_limite.dec)

    return Coordenada(
        traducir_escala(w_imagen, limite_sup_ra, limite_inf_ra,  x),
        traducir_escala(h_imagen, limite_abajo_dec, limite_arriba_dec, y)
    )


def obtener_coordenadas():
    archivo_metadata = open(r"Flujo/imagen/imagen.txt")
    json_metadata = json.load(archivo_metadata)

    coord1 = Coordenada(
        json_metadata['coord1']['ra'],
        json_metadata['coord1']['dec']
    )

    coord2 = Coordenada(
        json_metadata['coord2']['ra'],
        json_metadata['coord2']['dec']
    )

    return coord1, coord2


def obtener_coordenadas_rdi(rdi):
    '''
    Obtiene las coordenadas superior izquierda e inferior derecha 
    de la región de interés
    '''

    coord1, coord2 = obtener_coordenadas()

    _, ancho_imagen, alto_imagen = obtener_dimensiones_imagen(
        coord1,
        coord2
    )

    x_rdi, y_rdi, w_rdi, h_rdi = rdi

    coord_sup_izq = punto_a_coord_eq(
        coord1, coord2, x_rdi, y_rdi, ancho_imagen, alto_imagen)

    coord_inf_der = punto_a_coord_eq(
        coord1, coord2, x_rdi + w_rdi, y_rdi + h_rdi, ancho_imagen, alto_imagen)

    return coord_sup_izq, coord_inf_der


def filtrar_rdis_por_distancia(rdis):
    '''
    Función que filtra los contornos que tengan un área mas chica que un umbral
    '''
    MIN_DISTANCIA_ARC_SEC = 13

    indices_rdis = []

    for index, rdi in enumerate(rdis):
        coord_sup_izq, coord_inf_der = obtener_coordenadas_rdi(
            rdi
        )
        distancia_rdi = calcular_distancia_arc_sec(
            coord_sup_izq, coord_inf_der)

        if distancia_rdi > MIN_DISTANCIA_ARC_SEC:
            indices_rdis.append(index)

    return indices_rdis


def obtener_objetos_cercanos(coordenada, radio_arc_min):
    url = "http://skyserver.sdss.org/dr16/SkyServerWS/SearchTools/RadialSearch?ra={}&dec={}&radius={}&whichway=equatorial&limit=10&format=json&fp=none&whichquery=imaging"
    url = url.format(coordenada.ra, coordenada.dec, radio_arc_min)

    print(url)
    r = requests.get(url)

    return json.loads(r.content)[0]['Rows']


def es_galaxia_API(coordenada, radio_arc_min):
    '''
    Determina si una coordenada tiene una galaxia según los datos de SDSS

    SDSS:  Galaxy type is 3 
            Known object is 5
    '''

    objetos_cercanos = obtener_objetos_cercanos(coordenada, radio_arc_min)

    for fila in objetos_cercanos:
        print(fila['type'])

    for fila in objetos_cercanos:
        tipo = fila['type']

        if tipo in [3, 5]:
            return True

    return False


def filtrar_por_API(contornos):
    '''
    Filtrar por API las regiones de interés
    '''
    out = []

    coord1, coord2 = obtener_coordenadas()

    for contorno in contornos:

        M = cv.moments(contorno)
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])

        _, ancho_imagen, alto_imagen = obtener_dimensiones_imagen(
            coord1,
            coord2
        )

        coordenada_moment = punto_a_coord_eq(
            coord1, coord2, cx, cy, ancho_imagen, alto_imagen)
        rectangulo = obtener_rectangulo_de_contorno(contorno)

        coord_sup_izq, coord_inf_der = obtener_coordenadas_rdi(rectangulo)
        distancia = calcular_distancia_arc_sec(coord_sup_izq, coord_inf_der)

        radio_arc_min = (distancia / 7.5) / 60

        print(coordenada_moment.ra, coordenada_moment.dec, radio_arc_min)
        if es_galaxia_API(coordenada_moment, radio_arc_min):
            out.append(rectangulo)

    return out


def obtener_url_imagen_rdi(rdi):
    coord_sup_izq, coord_inf_der = obtener_coordenadas_rdi(
        rdi
    )

    s, w, h = obtener_dimensiones_imagen(coord_sup_izq, coord_inf_der)

    # Dejamos un poco de margen en la imagen de la rdi
    s += 0.02

    if w > h:
        h = w
    else:
        w = h

    url = obtener_url_api(
        obtener_coordenada_centro(coord_sup_izq, coord_inf_der),
        s,
        w,
        h
    )

    return url


def obtener_imagen_rdi(rdi, index):
    '''
    Obtiene una imagen cercana de la región de interés
    '''
    url = obtener_url_imagen_rdi(rdi)
    imagen = obtener_imagen_de_url(
        url, r"Flujo/rdis/rdi_{}.jpg".format(index))

    imagen = cv.imread(
        r"Flujo/rdis/rdi_{}.jpg".format(index))
    imagen = cv.fastNlMeansDenoisingColored(imagen, None, 10, 10, 7, 21)
    cv.imwrite(
        r"Flujo/rdis/rdi_{}.jpg".format(index), imagen)

    return imagen


def guardar_metadata_rdis(rdis):
    '''
    Guarda la información de las regiones de interés obtenidas
    '''

    archivo = open(r"Flujo/rdis/rdis.txt", 'w')
    data = {}

    data['rdis_total'] = str(len(rdis))
    data['rdis'] = {}

    for index, rdi in enumerate(rdis):
        x, y, w, h = rdi
        coord_top_left, coord_bot_right = obtener_coordenadas_rdi(
            rdi
        )

        data['rdis'][str(index)] = {
            'url': obtener_url_imagen_rdi(rdi),
            'x': x,
            'y': y,
            'width': w,
            'height': h,
            'coord_top_left': [coord_top_left.ra, coord_top_left.dec],
            'coord_bot_right': [coord_bot_right.ra, coord_bot_right.dec],
        }

    archivo.write(json.dumps(data))
    archivo.close()


def rdis():
    img_path = r"Flujo/imagen/imagen.jpg"
    img = cv.imread(img_path)
    original = img.copy()

    contornos = obtener_contornos(img)
    cv.imwrite(r"Flujo/imagen/imagen_contornos.jpg",
               cv.drawContours(img, contornos, -1, (0, 255, 0), 3))

    # Obtenemos todas las bounding boxes
    rdis = [obtener_rectangulo_de_contorno(x) for x in contornos]

    indices_rdis = filtrar_rdis_por_distancia(rdis)
    contornos_filtrados = [contornos[i] for i in indices_rdis]

    rdis_filtradas = filtrar_por_API(contornos_filtrados)

    dest_file = r"Flujo/imagen/imagen.jpg"
    image = cv.imread(r"Flujo/imagen/imagen.jpg")
    cv.imwrite(r"Flujo/imagen/imagen_bbox.jpg", image)

    guardar_metadata_rdis(rdis_filtradas)

    for index, rdi in enumerate(rdis_filtradas, 1):
        imagen = obtener_imagen_rdi(rdi, index)
