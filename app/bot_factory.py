from aiogram import Bot

from app.config import settings


def create_bot(**kwargs) -> Bot:
    """Create a Bot instance with proxy configured from settings."""
    if settings.BOT_PROXY_URL and 'session' not in kwargs:
        if settings.BOT_PROXY_URL.startswith('https://'):
            from app.utils.httpx_session import HttpxSession

            kwargs['session'] = HttpxSession(proxy=settings.BOT_PROXY_URL)
        else:
            from aiogram.client.session.aiohttp import AiohttpSession

            kwargs['session'] = AiohttpSession(proxy=settings.BOT_PROXY_URL)
    return Bot(token=settings.BOT_TOKEN, **kwargs)
