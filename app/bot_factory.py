from aiogram import Bot

from app.config import settings


def create_bot(**kwargs) -> Bot:
    """Create a Bot instance with proxy configured from settings."""
    from aiogram.client.session.aiohttp import AiohttpSession

    if settings.BOT_PROXY_URL and 'session' not in kwargs:
        kwargs['session'] = AiohttpSession(proxy=settings.BOT_PROXY_URL)
    return Bot(token=settings.BOT_TOKEN, **kwargs)
