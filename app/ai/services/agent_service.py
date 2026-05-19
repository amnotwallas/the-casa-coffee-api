import uuid
import json
import re
import random
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from app.ai.providers.groq_provider import GroqProvider
from app.repositories.product_repo import ProductRepository
from app.schemas.product_schema import Product as ProductSchema
from app.core.logger import get_logger

logger = get_logger(__name__)

class AgentService:
    def __init__(self, ai_provider: GroqProvider, product_repo: ProductRepository):
        self.ai_provider = ai_provider
        self.product_repo = product_repo

    async def _build_system_prompt(self) -> str:
        # Optimización: Solo traer productos disponibles y limitar a los 20 más relevantes
        # En el futuro, esto se reemplazará por búsqueda semántica (RAG)
        products = await self.product_repo.list_all_products(limit=20)
        menu_str = "\n".join([
            f"- {p.nombre}: ${p.precio} MXN (Intensidad: {p.intensidad}/5) | ID: {p.id}" 
            for p in products if p.disponible
        ])
        
        return f"""
        Eres el asistente virtual experto de 'The Casa Chill & Coffe'. Tu objetivo es deleitar a los clientes ayudándoles a elegir su café o snack ideal.
        
        MENÚ DESTACADO:
        {menu_str}
        
        PAUTAS DE COMPORTAMIENTO:
        1. Sé entusiasta, amable y profesional. Usa un tono de experto barista.
        2. Prioriza recomendar los productos del menú anterior.
        3. Si un cliente pide algo que no tenemos, sugiere la alternativa más cercana basándote en la intensidad.
        4. Responde de forma concisa (máximo 3 frases).
        """

    async def process_chat(self, user_message: str) -> str:
        logger.info(f"Processing chat message: {user_message[:50]}...")
        system_prompt = await self._build_system_prompt()
        return self.ai_provider.generate_response(system_prompt, user_message)

    async def stream_chat(self, user_message: str):
        logger.info(f"Streaming chat message: {user_message[:50]}...")
        system_prompt = await self._build_system_prompt()
        for chunk in self.ai_provider.stream_response(system_prompt, user_message):
            yield chunk

    def get_chat_history(self, user_id: str) -> List[dict]:
        return [
            {
                "conversationId": "conv-123",
                "messages": [
                    {"role": "user", "text": "Hola"},
                    {"role": "ai", "text": "¡Hola! Soy tu barista virtual."}
                ],
                "fecha": datetime.now(timezone.utc).isoformat()
            }
        ]

    async def get_personalized_recommendations(self, preferences: List[str]) -> List[dict]:
        """
        Optimización: Recomendaciones Semánticas (Vector Search Ready).
        Nota escolar: Este método simula la búsqueda por similitud usando la columna 'embedding' 
        de la base de datos para encontrar productos que 'significan' lo mismo que las preferencias.
        """
        if not preferences:
            return []
            
        # 1. Traer productos disponibles
        all_products = await self.product_repo.list_all_products(limit=50)
        recs = []
        
        # 2. Simulación de Vector Search:
        # En un sistema real, convertiríamos 'preferences' a un vector (embedding)
        # y haríamos un query: SELECT ... ORDER BY embedding <=> query_vector
        for p in all_products:
            if not p.disponible: continue
            
            for pref in preferences:
                # Buscamos coincidencias semánticas (simuladas aquí con palabras clave mejoradas)
                keyword_match = pref.lower() in p.descripcion.lower() or pref.lower() in p.nombre.lower()
                
                if keyword_match:
                    recs.append({
                        "producto": ProductSchema.model_validate(p), 
                        "razon": f"Basado en tu preferencia semántica por '{pref}'"
                    })
                    break # Siguiente producto
                    
        return recs[:3]

    async def process_quiz(self, answers: dict) -> dict:
        products = await self.product_repo.list_all_products(limit=2)
        return {
            "productos_recomendados": [ProductSchema.model_validate(p) for p in products],
            "explicacion": "Basado en tu preferencia por sabores intensos."
        }

    async def get_welcome_message(self) -> dict:
        """Orquestra una respuesta de bienvenida donde la IA elige qué productos recomendar."""
        logger.info("IA Barista orquestando bienvenida desde DB.")
        
        # Limitar productos para el orquestador
        all_products = await self.product_repo.list_all_products(limit=30)
        menu_context = "\n".join([
            f"ID: {p.id} | Nombre: {p.nombre} | Intensidad: {p.intensidad}/5 | Precio: ${p.precio}"
            for p in all_products if p.disponible
        ])
        
        system_prompt = f"""
        Eres el orquestador experto de 'The Casa Chill & Coffe'.
        Tu tarea es:
        1. Generar un saludo breve (1 frase) y cálido.
        2. Seleccionar exactamente 3 IDs de productos del menú que sean ideales para empezar el día.
        
        MENÚ:
        {menu_context}
        
        RESPONDE ÚNICAMENTE EN ESTE FORMATO JSON:
        {{
            "saludo": "tu mensaje aquí",
            "recomendados": ["id1", "id2", "id3"]
        }}
        """
        
        try:
            ai_decision_raw = self.ai_provider.generate_response(system_prompt, "Inicio de aplicación.")
            json_match = re.search(r'\{.*\}', ai_decision_raw, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
                ai_message = decision.get("saludo", "¡Bienvenido!")
                selected_ids = decision.get("recomendados", [])
            else:
                raise ValueError("AI parsing error")

            recommendations = []
            for pid in selected_ids:
                p_data = await self.product_repo.find_product_by_id(pid)
                if p_data:
                    recommendations.append(ProductSchema.model_validate(p_data))
            
            if not recommendations and all_products:
                recommendations = [ProductSchema.model_validate(p) for p in random.sample(all_products, k=min(3, len(all_products)))]

        except Exception as e:
            logger.error(f"Error AI orchestration: {e}")
            ai_message = "¡Hola! ¿Listo para un café?"
            recommendations = [ProductSchema.model_validate(p) for p in random.sample(all_products, k=min(3, len(all_products)))] if all_products else []

        return {
            "message": ai_message,
            "recommendations": recommendations,
            "conversationId": f"welcome-{str(uuid.uuid4())[:8]}"
        }
