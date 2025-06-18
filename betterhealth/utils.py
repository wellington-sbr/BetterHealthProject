from .api_client import MutuaApiClient
import logging

logger = logging.getLogger(__name__)


def verificar_mutua_paciente(numero_poliza, nombre_paciente):
    if not numero_poliza or not numero_poliza.strip():
        return {
            'valido': False,
            'datos': {},
            'error': 'Número de póliza no proporcionado'
        }
    try:
        client = MutuaApiClient()
        resultado = client.verificar_pertenencia_mutua(numero_poliza.strip())

        if not isinstance(resultado, dict):
            return {
                'valido': False,
                'datos': {},
                'error': 'Respuesta inválida de la API'
            }

        if resultado.get('success', False):
            datos_paciente = resultado.get('data', {})
            nombre_api = datos_paciente.get('nombre', '').strip().lower()
            nombre_formulario = nombre_paciente.strip().lower()

            if nombre_api == nombre_formulario:
                return {
                    'valido': True,
                    'datos': datos_paciente,
                    'error': None
                }
            else:
                return {
                    'valido': False,
                    'datos': {},
                    'error': 'El nombre no coincide con el número de póliza'
                }
        else:
            return {
                'valido': False,
                'datos': {},
                'error': resultado.get('error', 'Error desconocido')
            }
    except Exception as e:
        logger.error(f"Excepción verificando mutua: {str(e)}")
        return {
            'valido': False,
            'datos': {},
            'error': 'Error al verificar la mutua'
        }
