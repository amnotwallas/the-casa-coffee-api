import uuid
import json
import re
import random
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from app.ai.providers.groq_provider import GroqProvider
from app.repositories.product_repo import ProductRepository
from app.core.logger import get_logger

logger = get_logger(__name__)

class AgentService:
    def __init__(self, ai_provider: GroqProvider, product_repo: ProductRepository):
        self.ai_provider = ai_provider
        self.product_repo = product_repo

    async def _build_system_prompt(self) -> str:
        products = await self.product_repo.list_all_products(limit=50)
        menu_str = "\n".join([
            f"- {p.nombre}: ${p.precio} MXN (Intensidad: {p.intensidad}/5)" 
            for p in products
        ])
        
        return f"""
        Eres el asistente virtual experto de 'The Casa Chill & Coffe'. Tu objetivo es deleitar a los clientes ayudándoles a elegir su café o snack ideal.
        
        MENÚ DISPONIBLE:
        {menu_str}
        
        PAUTAS DE COMPORTAMIENTO:
        1. Sé entusiasta, amable y profesional. Usa un tono de experto barista.
        2. Solo recomienda productos que estén en el menú anterior.
        3. Si un cliente pide algo que no tenemos, sugiere la alternativa más cercana del menú.
        4. Menciona la intensidad del café si el cliente busca algo fuerte o suave.
        5. Responde de forma concisa pero atractiva.
        """

    async def process_chat(self, user_message: str) -> str:
        logger.info(f"Processing chat message: {user_message[:50]}...")
        system_prompt = await self._build_system_prompt()
        return self.ai_provider.generate_response(system_prompt, user_message)

    async def stream_chat(self, user_message: str):
        logger.info(f"Streaming chat message: {user_message[:50]}...")
        system_prompt = await self._build_system_prompt()
        # Nota: GroqProvider.stream_response es un generador síncrono o asíncrono?
        # Por ahora lo mantenemos asumiendo que es un generador síncrono envuelto en async
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
        all_products = await self.product_repo.list_all_products(limit=100)
        recs = []
        for pref in preferences:
            for p in all_products:
                if pref.lower() in p.descripcion.lower():
                    recs.append({"producto": p.model_dump(), "razon": f"Basado en tu gusto por {pref}"})
        return recs[:3]

    async def process_quiz(self, answers: dict) -> dict:
        products = await self.product_repo.list_all_products(limit=2)
        return {
            "productos_recomendados": [p.model_dump() for p in products],
            "explicacion": "Basado en tu preferencia por sabores intensos."
        }

    async def get_welcome_message(self) -> dict:
        """Orquestra una respuesta de bienvenida donde la IA elige qué productos recomendar."""
        logger.info("IA Barista orquestando bienvenida desde DB.")
        
        all_products = await self.product_repo.list_all_products(limit=50)
        menu_context = "\n".join([
            f"ID: {p.id} | Nombre: {p.nombre} | Intensidad: {p.intensidad}/5 | Precio: ${p.precio}"
            for p in all_products
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
                    recommendations.append(p_data.model_dump())
            
            if not recommendations and all_products:
                recommendations = [p.model_dump() for p in random.sample(all_products, k=min(3, len(all_products)))]

        except Exception as e:
            logger.error(f"Error AI orchestration: {e}")
            ai_message = "¡Hola! ¿Listo para un café?"
            recommendations = [p.model_dump() for p in random.sample(all_products, k=min(3, len(all_products)))] if all_products else []

        return {
            "message": ai_message,
            "recommendations": recommendations,
            "conversationId": f"welcome-{str(uuid.uuid4())[:8]}"
        }
