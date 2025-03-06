import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from datetime import datetime


def generate_check_sheet():
    # Datos de ejemplo - deberías reemplazarlos con datos reales de tu proyecto
    categorias = ['Calidad del Código', 'Documentación', 'Pruebas', 'Interfaz', 'Rendimiento']

    # Elementos a verificar para cada categoría
    elementos = {
        'Calidad del Código': ['Sigue guía de estilo', 'Sin código duplicado', 'Diseño modular', 'Manejo de errores'],
        'Documentación': ['README actualizado', 'Comentarios en código', 'Documentación API', 'Guía de usuario'],
        'Pruebas': ['Pruebas unitarias', 'Pruebas de integración', 'Cobertura > 80%', 'Casos límite'],
        'Interfaz': ['Diseño responsive', 'Accesibilidad', 'Estilo consistente', 'Feedback al usuario'],
        'Rendimiento': ['Tiempo de carga < 3s', 'Uso de memoria', 'Utilización CPU', 'Optimización de consultas']
    }

    # Resultados (aprobado/fallido/no aplicable)
    # 1 = aprobado, 0 = fallido, -1 = no aplicable
    resultados = {
        'Calidad del Código': [1, 0, 1, 0],
        'Documentación': [1, 1, 0, -1],
        'Pruebas': [1, 0, 0, 1],
        'Interfaz': [1, 0, 1, 1],
        'Rendimiento': [0, 1, 1, -1]
    }

    # Crear una figura con subgráficos para cada categoría
    fig, axes = plt.subplots(len(categorias), 1, figsize=(10, 3 * len(categorias)))
    fig.suptitle('Hoja de Verificación de Calidad del Proyecto', fontsize=16)

    # Para el caso de una sola categoría
    if len(categorias) == 1:
        axes = [axes]

    # Graficar cada categoría
    for i, categoria in enumerate(categorias):
        items = elementos[categoria]
        res = resultados[categoria]

        # Crear mapa de colores
        colores = ['red' if x == 0 else 'green' if x == 1 else 'gray' for x in res]

        # Crear las marcas de verificación
        axes[i].barh(items, [1] * len(items), color=colores)
        axes[i].set_title(categoria)
        axes[i].set_xlim(0, 1.5)
        axes[i].set_xticks([])

        # Añadir indicadores de texto
        for j, item in enumerate(items):
            estado = "✓" if res[j] == 1 else "✗" if res[j] == 0 else "N/A"
            axes[i].text(1.1, j, estado, va='center', fontsize=12)

    plt.tight_layout()

    # Crear directorio de salida si no existe
    os.makedirs('artifacts', exist_ok=True)

    # Generar marca de tiempo para el nombre del archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"artifacts/checksheet_{timestamp}.png"

    # Guardar la figura
    plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
    plt.close()

    return nombre_archivo


if __name__ == "__main__":
    archivo_salida = generate_check_sheet()
    print(f"Hoja de verificación generada: {archivo_salida}")