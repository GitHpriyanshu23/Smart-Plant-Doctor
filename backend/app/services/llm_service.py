import logging
import re
import time

from app.config import get_settings

logger = logging.getLogger("uvicorn.error")
settings = get_settings()

# Gemma models only — this API key has no free-tier quota for gemini-2.0-flash (limit: 0).
_DEFAULT_MODEL_CHAIN = [
    "gemma-4-31b-it",
    "gemma-4-4b-it",
    "gemma-4-26b-a4b-it",
]

_SYSTEM_PROMPT = (
    "You are Smart Plant Doctor, an expert plant care assistant powered by AI. "
    "You help users with plant health questions, disease diagnosis advice, watering schedules, "
    "soil & fertilizer recommendations, pest identification, and general gardening tips. "
    "Our AI model detects diseases on 6 plants: Rose, Hibiscus, Aloe Vera, Money Plant, "
    "Chrysanthemum, and Turmeric (29 disease classes total). "
    "Use the sensor and diagnosis context below if available. "
    "Be concise, practical, and friendly. Use bullet points or numbered lists when helpful."
)

_FALLBACK_REPLY = (
    "I'm Smart Plant Doctor! I can help with plant care questions.\n\n"
    "To enable AI-powered responses, add your GEMINI_API_KEY to backend/.env.\n"
    "Get a free key at https://aistudio.google.com/apikey\n\n"
    "In the meantime, here are some general tips:\n"
    "- Water when the top inch of soil feels dry\n"
    "- Most plants prefer 6+ hours of indirect sunlight\n"
    "- Check leaves weekly for spots, yellowing, or wilting\n"
    "- Maintain humidity between 40-60% for tropical plants"
)


def _model_chain() -> list[str]:
    raw = settings.gemini_chat_models.strip()
    if raw:
        return [m.strip() for m in raw.split(",") if m.strip()]
    return _DEFAULT_MODEL_CHAIN


def _build_prompt(context: str, message: str) -> str:
    return f"Context:\n{context}\n\nUser question: {message}"


def _retry_delay_seconds(exc: Exception) -> float:
    match = re.search(r"retry in ([\d.]+)s", str(exc), re.I)
    if match:
        return min(float(match.group(1)) + 0.5, 60.0)
    return 3.0


def _is_rate_limited(exc: Exception) -> bool:
    msg = str(exc)
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower()


def _is_transient(exc: Exception) -> bool:
    msg = str(exc)
    return any(
        token in msg
        for token in ("503", "500", "UNAVAILABLE", "INTERNAL", "high demand")
    )


def _call_model(client, model_id: str, prompt: str) -> str:
    from google.genai import types

    response = client.models.generate_content(
        model=model_id,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=_SYSTEM_PROMPT),
    )
    return response.text or ""


def _generate_with_fallback(client, prompt: str) -> str:
    last_error: Exception | None = None

    for model_id in _model_chain():
        max_attempts = 2 if model_id == _model_chain()[0] else 1
        for attempt in range(max_attempts):
            try:
                text = _call_model(client, model_id, prompt)
                if text.strip():
                    if model_id != _model_chain()[0]:
                        logger.info("Chat reply served by fallback model: %s", model_id)
                    return text
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Model %s failed (attempt %s/%s): %s",
                    model_id,
                    attempt + 1,
                    max_attempts,
                    exc,
                )
                if _is_rate_limited(exc):
                    break
                if _is_transient(exc) and attempt + 1 < max_attempts:
                    time.sleep(_retry_delay_seconds(exc))
                    continue
                break

    if last_error and _is_rate_limited(last_error):
        wait = int(_retry_delay_seconds(last_error))
        return (
            "The AI model is rate-limited right now. "
            f"Please wait about {wait} seconds and try again.\n\n"
            "Your Gemma quota resets automatically — check usage at https://ai.dev/rate-limit"
        )

    return (
        "The AI service is temporarily busy. Please try again in a minute.\n\n"
        "Quick tips while you wait:\n"
        "- Water when the top inch of soil feels dry\n"
        "- Most houseplants prefer bright, indirect light\n"
        "- Yellow leaves often indicate overwatering"
    )


def get_chat_reply(context: str, message: str) -> str:
    if not settings.gemini_api_key:
        return _FALLBACK_REPLY

    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    return _generate_with_fallback(client, _build_prompt(context, message))


def stream_chat_reply(context: str, message: str):
    if not settings.gemini_api_key:
        yield _FALLBACK_REPLY
        return

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = _build_prompt(context, message)
    config = types.GenerateContentConfig(system_instruction=_SYSTEM_PROMPT)

    for model_id in _model_chain():
        try:
            for chunk in client.models.generate_content_stream(
                model=model_id,
                contents=prompt,
                config=config,
            ):
                if chunk.text:
                    yield chunk.text
            return
        except Exception as exc:
            logger.warning("Stream model %s failed: %s", model_id, exc)
            if _is_rate_limited(exc):
                break

    yield "The AI service is temporarily busy. Please try again shortly."
