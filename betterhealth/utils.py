from .api_client import MutuaApiClient
import logging
from .models import Service

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

def solicitar_autorizacion_mutua(numero_poliza, servicio_id, fecha_cita, nombre_paciente):
    if not numero_poliza or not numero_poliza.strip():
        return {
            'autorizado': False,
            'numero_autorizacion': None,
            'motivo': 'Número de póliza no proporcionado',
            'error': 'Datos incompletos'
        }
    try:
        servicio = Service.objects.get(id=servicio_id)
        client = MutuaApiClient()
        datos_autorizacion = {
            'numero_poliza': numero_poliza.strip(),
            'nombre_paciente': nombre_paciente.strip(),
            'servicio_codigo': servicio.service_type,
            'servicio_nombre': servicio.name,
            'fecha_cita': fecha_cita.strftime('%Y-%m-%d'),
            'importe': float(servicio.price)
        }
        resultado = client.solicitar_autorizacion_mutua(datos_autorizacion)

        if not isinstance(resultado, dict):
            return {
                'autorizado': False,
                'numero_autorizacion': None,
                'motivo': 'Respuesta inválida de la API',
                'error': 'Error técnico'
            }

        if resultado.get('success', False):
            datos_respuesta = resultado.get('data', {})
            return {
                'autorizado': datos_respuesta.get('autorizado', False),
                'numero_autorizacion': datos_respuesta.get('numero_autorizacion'),
                'motivo': datos_respuesta.get('motivo', 'Autorización procesada'),
                'error': None
            }
        else:
            return {
                'autorizado': False,
                'numero_autorizacion': None,
                'motivo': resultado.get('error', 'Servicio no autorizado por la mutua'),
                'error': None
            }
    except Service.DoesNotExist:
        logger.error(f"Servicio con ID {servicio_id} no encontrado")
        return {
            'autorizado': False,
            'numero_autorizacion': None,
            'motivo': 'Servicio no encontrado',
            'error': 'Error interno'
        }
    except Exception as e:
        logger.error(f"Excepción solicitando autorización mutua: {str(e)}")
        return {
            'autorizado': False,
            'numero_autorizacion': None,
            'motivo': 'Error técnico al procesar la autorización',
            'error': 'Error al conectar con la mutua'
        }
