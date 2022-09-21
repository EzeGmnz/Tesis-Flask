import json
import os
import shutil
import urllib.request

from astropy import coordinates
from astropy.coordinates import Angle
from PIL import Image


class Coordenada:
    def __init__(self, ra, dec):
        self.ra = ra
        self.dec = dec

    def __str__(self):
        return str(self.ra) + ', ' + str(self.dec)


def grados_a_segundos_arc(grados):
    return grados * 3600


def radianes_a_segundos_arc(radianes):
    return radianes * 206264.806247


def calcular_distancia_arc_sec(coord1, coord2):
    '''
    Calcula la distancia entre dos puntos en la esfera celeste
    utilizando el sistema de coordenadas ecuatorial absoluto

    Utilizando radianes
    '''
    distancia_rad = coordinates.angular_separation(
        Angle('{}d'.format(coord1.ra)),
        Angle('{}d'.format(coord1.dec)),
        Angle('{}d'.format(coord2.ra)),
        Angle('{}d'.format(coord2.dec)),
    )

    return radianes_a_segundos_arc(distancia_rad.value)


def obtener_dimensiones_imagen(coord1, coord2):
    '''
    Calcula las dimensiones y la escala de la imagen necesarias
    para obtener una imagen delimitada por las coordenadas de entrada
    '''

    distancia_ra = calcular_distancia_arc_sec(
        Coordenada(coord1.ra, coord1.dec),
        Coordenada(coord2.ra, coord1.dec)
    )

    distancia_dec = calcular_distancia_arc_sec(
        Coordenada(coord1.ra, coord1.dec),
        Coordenada(coord1.ra, coord2.dec)
    )

    limite_sup = 2048
    limite_inf = 64

    ra_primero = distancia_ra > distancia_dec

    if ra_primero:
        w = limite_sup
        s = distancia_ra / w
        h = int(distancia_dec / s)

    else:
        h = limite_sup
        s = distancia_dec / h
        w = int(distancia_ra / s)

    return s, w, h


def obtener_coordenada_centro(coord1, coord2):
    '''
    Obtiene la coordenada central a partir de dos coordenadas
    '''

    centro_ra = (coord1.ra + coord2.ra) / 2
    centro_dec = (coord1.dec + coord2.dec) / 2
    print(centro_ra, centro_dec)
    return Coordenada(centro_ra, centro_dec)


def obtener_url_api(coord, escala, ancho, alto):
    '''

    Construye y retorna la dirección URL para obtener una imágen de la API a partir de los parámetros
    coord: coordenada central
    escala: valor indicando los segundos de arco por píxel

    '''

    optionals = ''

    return 'http://skyserver.sdss.org/dr16/SkyServerWS/ImgCutout/getjpeg?ra={}&dec={}&width={}&height={}&opt={}&scale={}' \
        .format(
            coord.ra,
            coord.dec,
            ancho,
            alto,
            optionals,
            escala
        )


def obtener_imagen_de_url(url, dest):
    '''
    Descarga una imagen desde una URL hacia un arachivo destino
    '''

    print('Obteniendo imagen...')
    urllib.request.urlretrieve(url, dest)
    print('Imagen Obtenida')

    return Image.open(dest)


def guardar_metadata_imagen(coordenada_centro, coord1, coord2, scale, width, height, url):
    metadata = r"Flujo/imagen/imagen.txt"

    data = {'url': url, 'coord1': {'ra': coord1.ra, 'dec': coord1.dec}, 'coord2': {'ra': coord2.ra, 'dec': coord2.dec}, 'coordenada_centro': {'ra': coordenada_centro.ra,
                                                                                                                                              'dec': coordenada_centro.dec}, 'width': width, 'height': height, 'scale': scale, }

    with open(metadata, 'w') as f:
        f.write(json.dumps(data))


def limpiar_directorio(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def limpiar_directorios_flujo():

    limpiar_directorio(r"Flujo/imagen")
    limpiar_directorio(r"Flujo/rdis")
    limpiar_directorio(r"Flujo/resultado")


def obtener_imagen(coord1, coord2):
    limpiar_directorios_flujo()

    s, w, h = obtener_dimensiones_imagen(
        coord1,
        coord2
    )

    coordenada_centro = obtener_coordenada_centro(
        coord1,
        coord2
    )

    url = obtener_url_api(
        coordenada_centro,
        s,
        w,
        h
    )

    guardar_metadata_imagen(
        coordenada_centro,
        coord1,
        coord2,
        s,
        w,
        h,
        url
    )

    dest_file = r"Flujo/imagen/imagen.jpg"
    image = obtener_imagen_de_url(url, dest_file)
