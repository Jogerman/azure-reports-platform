# backend/apps/authentication/services.py
import logging
import requests
import msal
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decouple import config
import uuid

logger = logging.getLogger(__name__)
User = get_user_model()

class MicrosoftAuthService:
    """
    Servicio para autenticación con Microsoft OAuth usando MSAL
    """
    
    def __init__(self, request=None):
        self.request = request
        self.client_id = config('MICROSOFT_CLIENT_ID', default='')
        self.client_secret = config('MICROSOFT_CLIENT_SECRET', default='')
        self.tenant_id = config('MICROSOFT_TENANT_ID', default='common')
        self.redirect_uri = config('MICROSOFT_REDIRECT_URI', default='http://localhost:8000/api/auth/microsoft/callback/')
        
        # Scopes para obtener información del usuario
        self.scopes = [
            'openid',
            'profile',
            'email',
            'User.Read'
        ]
        
        # URLs de Microsoft
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.graph_endpoint = "https://graph.microsoft.com/v1.0/me"
    
    def is_configured(self):
        """Verificar si Microsoft OAuth está configurado correctamente"""
        try:
            required_settings = [
                self.client_id,
                self.client_secret,
            ]
            
            configured = all(setting and setting != 'your-client-id' for setting in required_settings)
            
            if not configured:
                logger.warning("Microsoft OAuth no está completamente configurado")
                return False
            
            # Verificar que MSAL esté disponible
            return True
            
        except Exception as e:
            logger.error(f"Error verificando configuración Microsoft OAuth: {e}")
            return False
    
    def get_authorization_url(self, state=None):
        """Generar URL de autorización de Microsoft"""
        try:
            if not self.is_configured():
                raise ValidationError("Microsoft OAuth no está configurado")
            
            # Crear aplicación MSAL
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority
            )
            
            # Generar state si no se proporciona
            if not state:
                state = str(uuid.uuid4())
            
            # Construir URL de autorización
            auth_url = app.get_authorization_request_url(
                scopes=self.scopes,
                state=state,
                redirect_uri=self.redirect_uri
            )
            
            logger.info(f"URL de autorización generada para Microsoft OAuth")
            return auth_url, state
            
        except Exception as e:
            logger.error(f"Error generando URL de autorización: {e}")
            raise ValidationError(f"Error en Microsoft OAuth: {str(e)}")
    
    def get_token_from_code(self, authorization_code, state=None):
        """Intercambiar código de autorización por tokens"""
        try:
            if not self.is_configured():
                raise ValidationError("Microsoft OAuth no está configurado")
            
            # Crear aplicación MSAL
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority
            )
            
            # Intercambiar código por token
            result = app.acquire_token_by_authorization_code(
                code=authorization_code,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            if 'error' in result:
                error_msg = result.get('error_description', result.get('error', 'Error desconocido'))
                logger.error(f"Error obteniendo token: {error_msg}")
                raise ValidationError(f"Error de autenticación: {error_msg}")
            
            logger.info("Token obtenido exitosamente de Microsoft")
            return result
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error intercambiando código por token: {e}")
            raise ValidationError(f"Error en autenticación Microsoft: {str(e)}")
    
    def get_user_info(self, access_token):
        """Obtener información del usuario usando el token de acceso"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Llamar a Microsoft Graph API
            response = requests.get(
                self.graph_endpoint,
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Error llamando Graph API: {response.status_code} - {response.text}")
                raise ValidationError("Error obteniendo información del usuario")
            
            user_data = response.json()
            
            # Normalizar datos del usuario
            normalized_data = {
                'id': user_data.get('id'),
                'email': user_data.get('mail') or user_data.get('userPrincipalName'),
                'first_name': user_data.get('givenName', ''),
                'last_name': user_data.get('surname', ''),
                'display_name': user_data.get('displayName', ''),
                'tenant_id': user_data.get('tenant_id', self.tenant_id),
                'raw_data': user_data
            }
            
            logger.info(f"Información de usuario obtenida: {normalized_data.get('email')}")
            return normalized_data
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo información del usuario: {e}")
            raise ValidationError(f"Error obteniendo datos del usuario: {str(e)}")
    
    def validate_tenant(self, user_info):
        """Validar que el usuario pertenezca al tenant autorizado"""
        try:
            # Si no hay restricción de tenant, permitir cualquiera
            if self.tenant_id == 'common' or not self.tenant_id:
                return True
            
            # Validar tenant específico
            user_tenant = user_info.get('tenant_id', '')
            
            if user_tenant and user_tenant != self.tenant_id:
                logger.warning(f"Usuario de tenant no autorizado: {user_tenant}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validando tenant: {e}")
            return False
    
    def create_or_update_user(self, user_info):
        """Crear o actualizar usuario basado en información de Microsoft"""
        try:
            email = user_info.get('email')
            if not email:
                raise ValidationError("Email requerido para crear usuario")
            
            # Buscar usuario existente
            try:
                user = User.objects.get(email=email)
                
                # Actualizar información existente
                user.first_name = user_info.get('first_name', user.first_name)
                user.last_name = user_info.get('last_name', user.last_name)
                
                # Actualizar último método de login si el campo existe
                if hasattr(user, 'last_login_provider'):
                    user.last_login_provider = 'microsoft'
                
                user.save()
                logger.info(f"Usuario actualizado: {email}")
                
            except User.DoesNotExist:
                # Crear nuevo usuario
                username = email.split('@')[0]  # Usar parte local del email como username
                
                # Asegurar username único
                counter = 1
                original_username = username
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=user_info.get('first_name', ''),
                    last_name=user_info.get('last_name', ''),
                    is_active=True
                )
                
                # Configurar último método de login si el campo existe
                if hasattr(user, 'last_login_provider'):
                    user.last_login_provider = 'microsoft'
                    user.save()
                
                logger.info(f"Nuevo usuario creado: {email}")
            
            return user
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creando/actualizando usuario: {e}")
            raise ValidationError(f"Error procesando usuario: {str(e)}")
    
    def refresh_token(self, refresh_token):
        """Renovar token de acceso usando refresh token"""
        try:
            if not self.is_configured():
                raise ValidationError("Microsoft OAuth no está configurado")
            
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority
            )
            
            # Intentar renovar token
            result = app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=self.scopes
            )
            
            if 'error' in result:
                error_msg = result.get('error_description', result.get('error', 'Error renovando token'))
                logger.error(f"Error renovando token: {error_msg}")
                raise ValidationError(f"Error renovando token: {error_msg}")
            
            logger.info("Token renovado exitosamente")
            return result
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error renovando token: {e}")
            raise ValidationError(f"Error renovando token: {str(e)}")


class MicrosoftGraphService:
    """
    Servicio adicional para interactuar con Microsoft Graph API
    """
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.graph_base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def get_user_profile(self):
        """Obtener perfil completo del usuario"""
        try:
            response = requests.get(
                f"{self.graph_base_url}/me",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error obteniendo perfil: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error en Graph API: {e}")
            return None
    
    def get_user_photo(self):
        """Obtener foto del usuario"""
        try:
            response = requests.get(
                f"{self.graph_base_url}/me/photo/$value",
                headers={'Authorization': f'Bearer {self.access_token}'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.content
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo foto: {e}")
            return None