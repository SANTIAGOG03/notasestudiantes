from flask import Flask, jsonify, abort
import mysql.connector
import os

app = Flask(__name__)

from dotenv import load_dotenv
load_dotenv()

# Configuración de la base de datos
DB_HOST = os.getenv('DB_HOST', 'sql.freedb.tech')
DB_USER = os.getenv('DB_USER', 'freedb_santiago')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME', 'freedb_alfonsito')
DB_PORT = int(os.getenv('DB_PORT', '3306'))


def conectar_db():
   
    try:
        conexion = mysql.connector.connect(host=DB_HOST,
                                           user=DB_USER,
                                           password=DB_PASSWORD,
                                           database=DB_NAME,
                                           port=DB_PORT)
        return conexion
    except mysql.connector.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        abort(500, "No se pudo conectar a la base de datos"
              )  # Error 500: Internal Server Error


def obtener_notas_estudiante(estudiante_id):
  
    conexion = conectar_db()
    cursor = conexion.cursor(
        dictionary=True)  # Para obtener los resultados como diccionarios
    try:
        # Primero, obtener el nombre del estudiante
        cursor.execute("SELECT nombre FROM estudiantes WHERE id = %s",
                       (estudiante_id, ))
        estudiante = cursor.fetchone()
        if not estudiante:
            return None  # Estudiante no encontrado

        # Luego, obtener las notas del estudiante
        cursor.execute(
            """
            SELECT m.materia, m.nota
            FROM notas AS m
            WHERE m.estudiante_id = %s
            """,
            (estudiante_id, ),
        )
        notas = cursor.fetchall()

        # Calcular el promedio
        promedio = sum(nota["nota"]
                       for nota in notas) / len(notas) if notas else 0

        # Formatear la respuesta
        resultado = {
            "nombre": estudiante["nombre"],
            "notas": notas,
            "promedio": promedio
        }
        return resultado

    except mysql.connector.Error as e:
        print(f"Error al obtener las notas del estudiante: {e}")
        return None  # Indica que hubo un error
    finally:
        cursor.close()
        conexion.close()


def obtener_notas_todos_estudiantes():
  
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, nombre FROM estudiantes")
        estudiantes = cursor.fetchall()
        resultados = {}
        for estudiante in estudiantes:
            estudiante_id = estudiante["id"]
            cursor.execute(
                """
                SELECT m.materia, m.nota
                FROM notas AS m
                WHERE m.estudiante_id = %s
                """,
                (estudiante_id, ),
            )
            notas = cursor.fetchall()
            promedio = sum(nota["nota"]
                           for nota in notas) / len(notas) if notas else 0
            resultados[estudiante_id] = {
                "nombre": estudiante["nombre"],
                "notas": notas,
                "promedio": promedio
            }
        return resultados
    except mysql.connector.Error as e:
        print(f"Error al obtener las notas de todos los estudiantes: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()


@app.route("/", methods=["GET"])
def index():
    """Root endpoint that shows available API endpoints."""
    return jsonify({
        "endpoints": {
            "get_student_grades": "/estudiantes/<id>/notas",
            "get_all_grades": "/estudiantes/notas"
        }
    })

@app.route("/estudiantes/<int:estudiante_id>/notas", methods=["GET"])
def obtener_notas_estudiante_api(estudiante_id):
    """
    Endpoint de la API para obtener las notas de un estudiante específico.
    """
    resultado = obtener_notas_estudiante(estudiante_id)
    if resultado:
        return jsonify(resultado)
    elif resultado is None:  #cambiado para que el error 404 solo se active cuando la función retorna None
        abort(404, description="Estudiante no encontrado")
    else:
        abort(500, "Error al obtener las notas del estudiante"
              )  #error 500 si hubo un error interno


@app.route("/estudiantes/notas", methods=["GET"])
def obtener_notas_todos_estudiantes_api():

    resultados = obtener_notas_todos_estudiantes()
    if resultados:
        return jsonify(resultados)
    else:
        abort(500, "Error al obtener las notas de los estudiantes")


@app.errorhandler(404)
def estudiante_no_encontrado(error):
    """Manejador de error para el código 404."""
    return jsonify({"error": str(error)}), 404


@app.errorhandler(500)
def error_interno_servidor(error):
    """Manejador de error para el código 500."""
    return jsonify({"error": str(error)}), 500


if __name__ == "__main__":
    # Obtiene el puerto del entorno o usa el puerto 5000 por defecto
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
