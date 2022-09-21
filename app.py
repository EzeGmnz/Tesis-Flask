from flask import Flask, request, send_file, jsonify

from src.clasificacion.clasificacion import clasificar
from src.input.imagen import (Coordenada, obtener_coordenada_centro,
                              obtener_dimensiones_imagen, obtener_imagen,
                              obtener_url_api, obtener_imagen_de_url)
from src.input.rdis import rdis
from src.resultado.resultado import crear_resultado
from flask_cors import CORS, cross_origin
import time
from os import path

app = Flask(__name__)


app.debug = True
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/')
def index():

    if not validateQueryParams():
        return 'Missing query params. Params must be ra1, dec1, ra2, dec2', 422

    coordenada1 = Coordenada(float(request.args.get('ra1')),
                             float(request.args.get('dec1')))

    coordenada2 = Coordenada(float(request.args.get('ra2')),
                             float(request.args.get('dec2')))

    mock = int(request.args.get('mock'))

    if mock > 0 and path.exists('C:/D_Drive/Eze/UNS/Tesis/API/mock/{}/imagen_final.jpg'.format(mock)):

        image_path = 'C:/D_Drive/Eze/UNS/Tesis/API/mock/{}/imagen_final.jpg'.format(
            mock)

        sleep_time_seconds = 10
        time.sleep(sleep_time_seconds)

        return send_file(image_path)
    else:
        _, w, h = obtener_dimensiones_imagen(
            coordenada1,
            coordenada2
        )

        obtener_imagen(coordenada1, coordenada2)
        rdis()
        clasificar()

        image_path = crear_resultado()

        return send_file(image_path)


def validateQueryParams():

    if not request.args.get('ra1') or not request.args.get('dec1') or not request.args.get('ra2') or not request.args.get('dec2'):
        return False

    return True


@app.route('/image-url')
def image_url():

    if not validateQueryParams():
        return 'Missing query params. Params must be ra1, dec1, ra2, dec2', 422

    coordenada1 = Coordenada(float(request.args.get('ra1')),
                             float(request.args.get('dec1')))

    coordenada2 = Coordenada(float(request.args.get('ra2')),
                             float(request.args.get('dec2')))

    s, w, h = obtener_dimensiones_imagen(
        coordenada1,
        coordenada2
    )

    coordenada_centro = obtener_coordenada_centro(
        coordenada1,
        coordenada2
    )

    url = obtener_url_api(
        coordenada_centro,
        s,
        w,
        h
    )

    return jsonify(url=url)
