from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

# --- SCHEMAS DE USUARIO ---

class AddressBase(BaseModel):
    calle: str
    ciudad: str
    codigoPostal: str
    referencia: Optional[str] = None
    esDefault: bool = False

class Address(AddressBase):
    id: str

class UserPreferences(BaseModel):
    notificacionesPush: bool = True
    tipoLecheFavorita: Optional[str] = "Almendra"
    idioma: str = "es"

class UserProfile(BaseModel):
    id: str
    firebase_uid: str
    nombre: str
    email: EmailStr
    telefono: Optional[str] = None
    foto: Optional[str] = None
    direcciones: List[Address] = []
    preferencias: UserPreferences = UserPreferences()

# --- SCHEMAS DE AUTENTICACIÓN ---

class FirebaseAuthRequest(BaseModel):
    firebase_token: str
    nombre: Optional[str] = None
    telefono: Optional[str] = None

class AuthResponse(BaseModel):
    user: UserProfile
    # El token real lo gestiona Firebase en el cliente, 
    # pero podemos retornar el perfil confirmado.
