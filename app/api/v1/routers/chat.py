from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import json
from typing import List, Optional
from app.ai.services.agent_service import AgentService
from app.api.dependencies import get_agent_service, get_current_user_required, get_admin_repo, get_user_repo
from app.repositories.admin_repo import AdminRepository
from app.repositories.user_repo import UserRepository
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.schemas.welcome_schema import WelcomeResponse
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["AI Chat"])

@router.post("/message")
async def chat_message(
    request: ChatRequest,
    agent_service: AgentService = Depends(get_agent_service),
    current_user: dict = Depends(get_current_user_required),
    admin_repo: AdminRepository = Depends(get_admin_repo)
):
    """Procesa un mensaje de chat con el Barista AI con streaming. REQUIERE LOGIN."""
    
    # Generar notificación para el administrador
    try:
        user_name = current_user.get("nombre", "Cliente")
        await admin_repo.create_notification(
            type="support",
            title="Nueva interacción de chat",
            body=f"El cliente {user_name} ha enviado un mensaje al asistente virtual."
        )
    except Exception as e:
        logger.error(f"Error al crear notificación de chat: {e}")

    async def event_generator():
        # Enviar metadata inicial
        metadata = {
            "conversationId": request.conversationId or "new-session",
            "suggestions": ["¿Qué me recomiendas?", "Ver el menú", "Horarios"]
        }
        yield f"data: {json.dumps(metadata)}\n\n"
        
        # Enviar el stream de la respuesta
        # stream_chat ahora es async generator
        async for chunk in agent_service.stream_chat(request.message):
            if chunk:
                yield f"data: {chunk}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@router.get("/welcome", response_model=WelcomeResponse)
async def get_welcome(
    agent_service: AgentService = Depends(get_agent_service)
):
    """Genera un mensaje de bienvenida de IA y recomendaciones. PÚBLICO."""
    return await agent_service.get_welcome_message()

@router.get("/history")
async def get_chat_history(
    agent_service: AgentService = Depends(get_agent_service),
    current_user_id: str = Depends(get_current_user_required)
):
    """Obtiene el historial de conversaciones. REQUIERE LOGIN."""
    return agent_service.get_chat_history(current_user_id)

@router.post("/recommendations")
async def get_recommendations(
    preferences: List[str],
    agent_service: AgentService = Depends(get_agent_service),
    current_user_id: str = Depends(get_current_user_required)
):
    """Obtiene recomendaciones personalizadas basadas en gustos. REQUIERE LOGIN."""
    return await agent_service.get_personalized_recommendations(preferences)

@router.post("/recommendations/quiz")
async def process_recommendation_quiz(
    answers: dict,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Procesa un quiz para recomendar productos. PÚBLICO."""
    return await agent_service.process_quiz(answers)
