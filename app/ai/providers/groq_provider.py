from groq import Groq
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

class GroqProvider:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY is not set. AI features will be limited.")
            self.client = None
        else:
            self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    def generate_response(self, system_prompt: str, user_message: str) -> str:
        if not self.client:
            return "El servicio de IA no está configurado actualmente."
        
        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                model=self.model,
                temperature=0.7,
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}", exc_info=True)
            return "Lo siento, hubo un error al procesar tu mensaje."

    def stream_response(self, system_prompt: str, user_message: str):
        if not self.client:
            yield "El servicio de IA no está configurado actualmente."
            return
        
        try:
            stream = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                model=self.model,
                temperature=0.7,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Error calling Groq API (stream): {e}", exc_info=True)
            yield "Lo siento, hubo un error al procesar tu mensaje en streaming."
