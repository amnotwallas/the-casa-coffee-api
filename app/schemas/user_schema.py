from pydantic import BaseModel, EmailStr, Field, model_validator
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
    model_config = {"from_attributes": True}

class UserPreferences(BaseModel):
    notificacionesPush: bool = True
    tipoLecheFavorita: Optional[str] = "Almendra"
    idioma: str = "es"

class UserProfile(BaseModel):
    id: str
    firebase_uid: str
    nombre: str
    email: EmailStr
    is_admin: bool = False
    telefono: Optional[str] = None
    foto: Optional[str] = None
    direcciones: Optional[List[Address]] = None
    preferencias: Optional[UserPreferences] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def map_user_relational_data(cls, data: any):
        """Mapea relaciones de BD (direcciones, preferencias) a campos JSON."""
        if hasattr(data, "__dict__"):
            data_dict = data.__dict__.copy()
            
            # Mapear Direcciones
            data_dict["direcciones"] = getattr(data, "direcciones", None)
            
            # Mapear Preferencias
            pref = getattr(data, "preferencias", None)
            if pref:
                data_dict["preferencias"] = {
                    "notificacionesPush": pref.notificacionesPush,
                    "tipoLecheFavorita": pref.tipoLecheFavorita,
                    "idioma": pref.idioma
                }
            else:
                data_dict["preferencias"] = None
            
            return data_dict
        return data

# --- SCHEMAS DE AUTENTICACIÓN ---

class FirebaseAuthRequest(BaseModel):
    firebase_token: str
    nombre: Optional[str] = None
    telefono: Optional[str] = None

class AuthResponse(BaseModel):
    user: UserProfile
    # El token real lo gestiona Firebase en el cliente, 
    # pero podemos retornar el perfil confirmado.
