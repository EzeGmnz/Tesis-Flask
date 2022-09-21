import json

import cv2
from PIL import Image


def obtener_imagen():
    '''
    Obtiene la imagen de la region de interés 
    '''

    file_path = r"Flujo\imagen\imagen.jpg"
    image = cv2.imread(file_path)

    return image


def obtener_rdis():
    '''
    Obtiene las regiones de interes ya clasificadas
    '''
    file_path = r"Flujo\rdis\rdis_classified.txt"
    file = open(file_path)

    out = file.read()

    file.close()

    return json.loads(out)


def draw_class_rectangles(image, rdis):
    '''
    Retorna una imagen con las rdi y su clase en la imagen
    '''
    out = image.copy()

#   Style
    color = (36, 255, 12)
    thickness = 3

    for rdi in rdis.values():

        out = cv2.rectangle(
            out,

            (rdi['x'], rdi['y']),
            (rdi['x'] + rdi['width'], rdi['y'] + rdi['height']),

            color,
            thickness
        )

        cv2.putText(
            out,
            rdi['classification']['class'],
            (rdi['x'], rdi['y'] - 15),
            cv2.FONT_HERSHEY_SIMPLEX, 3, color, thickness
        )

        print(rdi['coord_top_left'], rdi['coord_bot_right'])

    return out


def crear_resultado():
    image = obtener_imagen()
    rdis = obtener_rdis()

    image_rectangles = draw_class_rectangles(image.copy(), rdis)

    OUT_PATH = r"C:/D_Drive/Eze/UNS/Tesis/API/Flujo/resultado/imagen_final.jpg"
    cv2.imwrite(OUT_PATH, image_rectangles)

    return OUT_PATH
