import json
import os

import cv2
import numpy as np
import tensorflow as tf
from PIL import Image

MODEL_PATH = r"model_custom_xception_preproc"
model = tf.keras.models.load_model(MODEL_PATH)


def recuperar_rdis():
    '''
    Recupera las regiones de interés de la imagen a partir del archivo metadata
    '''
    rdi_file_path = r"Flujo/rdis/rdis.txt"

    data = {}
    with open(rdi_file_path) as file:
        data = json.loads(file.read())

    return data


def clasificar_rdis(rdis, rdis_images_path):
    '''
    Clasifica morfológicamente las regiones de interés y retorna el resultado
    junto con la confianza del resultado obtenido
    '''

    classes = ['de canto', 'eliptica', 'en fusion', 'espiral']

    out = rdis['rdis']
    rdis_count = int(rdis['rdis_total'])

    input_image_dim = (124, 124)
    for i in range(1, rdis_count + 1):
        rdi_image_path = rdis_images_path.format(i)
        rdi_image = cv2.imread(rdi_image_path)

        #   resize image
        rdi_image = cv2.resize(rdi_image, input_image_dim)

        #   model input is of shape [batch_size, image_width, image_height, number_of_channels]
        rdi_image_expanded = np.expand_dims(rdi_image, axis=0)

        #   predicting image class
        result = model.predict(rdi_image_expanded)
        result_class = result.argmax(axis=-1)
        confidence = result[-1][result_class][0]*100

        out[str(i - 1)]['classification'] = {
            'class': classes[result_class[0]],
            'confidence': confidence
        }

    return out


def guardar_resultado_clasificacion(resultado):
    '''
    Guarda el resultado de la clasificación en un archivo
    '''
    file_path = r"Flujo/rdis/rdis_classified.txt"

    with open(file_path, 'w') as file:
        file.write(json.dumps(resultado))


def clasificar():
    rdis_data = recuperar_rdis()

    rdis_count = int(rdis_data['rdis_total'])
    rdis_images_path = r"Flujo/rdis/rdi_{}.jpg"

    clasificacion = clasificar_rdis(rdis_data, rdis_images_path)

    guardar_resultado_clasificacion(clasificacion)
