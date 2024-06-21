"""
TICSolver.py

Este script extrae las respuestas correctas de un archivo HTML que contiene los datos de una evaluación o cuestionario.
El formato de los datos en el HTML debe ser similar a 'rowPag' dentro de una etiqueta <script>.
El script guarda las respuestas en un archivo JSON ("correct_answers.json") o las imprime en la consola.
Maneja caracteres especiales UTF-8 y elimina etiquetas HTML de los títulos de las preguntas.
"""

import json
from bs4 import BeautifulSoup


def extract_html_data(archivo_html):
    """Extrae y analiza los datos 'rowPag' de la etiqueta <script> de un archivo HTML."""
    with open(archivo_html, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    for script in soup.find_all('script'):
        if 'rowPag' in script.text:
            try:
                rowpag_data = json.loads(script.text.split('rowPag = ')[1].split('}]}}}};')[0] + '}]}}}}')
                return rowpag_data
            except (json.JSONDecodeError, ValueError):
                return None
    return None


def extract_correct_answers(datos):
    """Extrae las respuestas correctas de los datos 'rowPag'."""

    respuestas_correctas = []
    num_pregunta = 1
    for page_id, page_data in datos.items():
        for question_id, question_data in page_data["questions"].items():
            # Eliminar etiquetas HTML y manejar caracteres especiales en el título
            titulo = BeautifulSoup(question_data["title"], 'html.parser').get_text(separator=" ")

            # Intentar diferentes decodificaciones para manejar caracteres especiales
            for encoding in ['utf-8', 'latin-1', 'windows-1252']:
                try:
                    titulo = titulo.encode('latin-1').decode(encoding)
                    break  # Salir del bucle si la decodificación es exitosa
                except (UnicodeEncodeError, UnicodeDecodeError):
                    pass

            if len(titulo) >= 100:
                titulo = "Pregunta " + str(num_pregunta)

            tipo_pregunta = question_data["type"]
            respuesta_correcta = []
            if tipo_pregunta in ["MUL1R", "MULNR"]:
                respuesta_correcta = [opt["title"] for opt in question_data["options"] if opt.get("correct") == "true"]

            elif tipo_pregunta == "RELLE":
                respuesta_correcta = {opt["orden"]: opt["correct"] for opt in question_data["options"] if
                                      opt["correct"] != "null"}

            elif tipo_pregunta == "RELAC":
                respuesta_correcta = {int(opt["correct"]): opt["title"] for opt in question_data["options"] if
                                      opt["optionType"] == "3"}

            respuestas_correctas.append({"title": titulo, "correct_answer": respuesta_correcta})
            num_pregunta += 1
    return respuestas_correctas


def save_to_json(datos, archivo_json):
    """Guarda los datos extraídos en un archivo JSON, con manejo de errores."""
    while True:
        try:
            with open(archivo_json, 'x') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)  # Evitar problemas con caracteres especiales
            break
        except FileExistsError:
            if input(f"El archivo '{archivo_json}' ya existe. ¿Desea sobrescribirlo? (s/n): ").lower() != 's':
                return False
            else:
                with open(archivo_json, 'w') as f:
                    json.dump(datos, f, indent=4, ensure_ascii=False)
                break
    return True


if __name__ == '__main__':
    ruta_archivo_html = input("Ingrese la ruta al archivo HTML: ")
    ruta_archivo_json = 'correct_answers.txt'  # Nombre por defecto

    # Extraer datos del HTML
    datos_rowpag = extract_html_data(ruta_archivo_html)
    if datos_rowpag:
        # Extraer respuestas correctas
        respuestas = extract_correct_answers(datos_rowpag)

        # Guardar o imprimir resultados
        if input("¿Guardar en JSON? (s/n): ").lower() == 's':
            if not save_to_json(respuestas, ruta_archivo_json):
                print("Datos no guardados.")
            else:
                print(f"Datos guardados en '{ruta_archivo_json}'")
        else:
            if input("¿Imprimir los datos? (s/n): ").lower() == 's':
                print(json.dumps(respuestas, indent=4, ensure_ascii=False))
    else:
        print("No se encontraron datos 'rowPag' en el archivo HTML.")
