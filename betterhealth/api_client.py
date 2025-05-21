import requests
import json
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Union
from django.conf import settings
from django.core.cache import cache


class MutuaApiClient:
    """
    Cliente para la API de la Mutua
    """
    CACHE_KEY = 'mutua_api_token'
    TOKEN_EXPIRY = 3600  # 1 hora en segundos

    def __init__(self):
        self.base_url = settings.MUTUA_API['BASE_URL']
        self.username = settings.MUTUA_API['USERNAME']
        self.password = settings.MUTUA_API['PASSWORD']

    def _format_date(self, date_obj: Optional[Union[date, str]]) -> Optional[str]:
        """Formatea un objeto date o string para las peticiones API"""
        if not date_obj:
            return None

        if isinstance(date_obj, date):
            return date_obj.isoformat()
        return date_obj  # Ya es un string

    def login(self) -> Dict[str, Any]:
        """Obtiene un token de autenticación usando las credenciales del .env"""
        url = f"{self.base_url}/token"

        payload = {
            'grant_type': 'password',
            'username': self.username,
            'password': self.password
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            response = requests.post(url, data=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            token = data.get('access_token')

            # Guardar token en caché
            cache.set(self.CACHE_KEY, token, self.TOKEN_EXPIRY)

            return {
                'success': True,
                'token': token,
                'data': data
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'response': getattr(e, 'response', None)
            }

    def get_token(self) -> Optional[str]:
        """Obtiene el token desde caché o genera uno nuevo"""
        token = cache.get(self.CACHE_KEY)
        if not token:
            result = self.login()
            if result['success']:
                token = result['token']
            else:
                return None
        return token

    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict[str, Any]:
        """Realiza una petición a la API con manejo de token"""
        token = self.get_token()
        if not token:
            return {
                'success': False,
                'error': 'No se pudo obtener el token de autenticación'
            }

        url = f"{self.base_url}{endpoint}"

        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                headers['Content-Type'] = 'application/json'
                response = requests.post(url, headers=headers, params=params, json=data)
            else:
                return {
                    'success': False,
                    'error': f'Método HTTP no soportado: {method}'
                }

            response.raise_for_status()

            return {
                'success': True,
                'data': response.json() if response.content else {}
            }
        except requests.exceptions.RequestException as e:
            # Si el error es 401 (no autorizado), intentar renovar el token
            if hasattr(e, 'response') and e.response and e.response.status_code == 401:
                cache.delete(self.CACHE_KEY)  # Borrar token inválido
                # Reintentar con nuevo token
                return self._make_request(method, endpoint, params, data)

            return {
                'success': False,
                'error': str(e),
                'response': getattr(e, 'response', None)
            }

    # ENDPOINTS DE SERVICIOS CLÍNICA MUTUA

    def get_servicios_mutua(self) -> Dict[str, Any]:
        """
        Obtiene la lista de servicios del catálogo incluidos en la mutua.

        Returns:
            Dict con 'success' y 'data' o 'error'
        """
        return self._make_request('GET', '/servicios-clinica/mutua')

    # ENDPOINTS DE AUTORIZACIONES

    def autorizar_tratamiento(self, id_paciente: int, id_tratamiento: int, comentarios: str = None) -> Dict[str, Any]:
        """
        Autoriza un tratamiento o servicio solicitado para un paciente.

        Args:
            id_paciente: ID del paciente
            id_tratamiento: ID del tratamiento
            comentarios: Comentarios opcionales sobre la autorización

        Returns:
            Dict con 'success' y 'data' o 'error'
        """
        params = {
            'id_paciente': id_paciente,
            'id_tratamiento': id_tratamiento
        }

        if comentarios:
            params['comentarios'] = comentarios

        return self._make_request('POST', '/autorizaciones/', params=params)

    def consultar_historial_autorizaciones(self, id_paciente: int) -> Dict[str, Any]:
        """
        Consulta el historial de autorizaciones previas de un paciente.

        Args:
            id_paciente: ID del paciente

        Returns:
            Dict con 'success' y 'data' (lista de autorizaciones) o 'error'
        """
        return self._make_request('GET', f'/autorizaciones/paciente/{id_paciente}')

    # ENDPOINTS DE SERVICIOS

    def solicitar_informe_servicios(self, id_paciente: int,
                                    fecha_inicio: Optional[Union[date, str]] = None,
                                    fecha_fin: Optional[Union[date, str]] = None) -> Dict[str, Any]:
        """
        Solicita un informe de servicios utilizados por un paciente en un período determinado.

        Args:
            id_paciente: ID del paciente
            fecha_inicio: Fecha de inicio del período (opcional)
            fecha_fin: Fecha de fin del período (opcional)

        Returns:
            Dict con 'success' y 'data' (informe de servicios) o 'error'
        """
        params = {}

        if fecha_inicio:
            params['fecha_inicio'] = self._format_date(fecha_inicio)

        if fecha_fin:
            params['fecha_fin'] = self._format_date(fecha_fin)

        return self._make_request('GET', f'/servicios/informe/{id_paciente}', params=params)

    # ENDPOINTS DE REFERENCIA

    def listar_pacientes(self) -> Dict[str, Any]:
        """
        Lista todos los pacientes registrados (para referencia).

        Returns:
            Dict con 'success' y 'data' (lista de pacientes) o 'error'
        """
        return self._make_request('GET', '/pacientes/')

    def listar_servicios(self) -> Dict[str, Any]:
        """
        Lista todos los servicios disponibles en la mutua (para referencia).

        Returns:
            Dict con 'success' y 'data' (lista de servicios) o 'error'
        """
        return self._make_request('GET', '/servicios/')

    # ENDPOINTS DE PACIENTES

    def verificar_pertenencia_mutua(self, afiliado: str) -> Dict[str, Any]:
        """
        Verifica si un paciente pertenece a la mutua.

        Args:
            afiliado: Número de afiliado del paciente

        Returns:
            Dict con 'success' y 'data' o 'error'
        """
        return self._make_request('GET', f'/pacientes/verificar/{afiliado}')

    # ENDPOINTS DE USUARIOS

    def get_current_user(self) -> Dict[str, Any]:
        """
        Obtiene información del usuario autenticado actualmente.

        Returns:
            Dict con 'success' y 'data' (información de usuario) o 'error'
        """
        return self._make_request('GET', '/users/me')