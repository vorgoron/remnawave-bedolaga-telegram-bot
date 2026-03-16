from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, cast

import httpx
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramNetworkError
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType


if TYPE_CHECKING:
    from aiogram.client.bot import Bot
    from aiogram.types import InputFile


class HttpxSession(BaseSession):
    """aiogram session using httpx — supports HTTPS (TLS-wrapped) proxies."""

    def __init__(self, proxy: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._proxy = proxy
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            init_kwargs: dict[str, Any] = {}
            if self._proxy:
                init_kwargs['proxy'] = self._proxy
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                **init_kwargs,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def make_request(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: int | None = None,
    ) -> TelegramType:
        client = await self._get_client()
        url = self.api.api_url(token=bot.token, method=method.__api_method__)

        input_files: dict[str, InputFile] = {}
        data: dict[str, str] = {}
        for key, value in method.model_dump(warnings=False).items():
            prepared = self.prepare_value(value, bot=bot, files=input_files)
            if not prepared:
                continue
            data[key] = prepared

        files: dict[str, tuple[str, bytes]] = {}
        for key, input_file in input_files.items():
            content = b''.join([chunk async for chunk in input_file.read(bot)])
            files[key] = (input_file.filename or key, content)

        req_timeout = httpx.Timeout(float(timeout)) if timeout is not None else None

        try:
            if files:
                response = await client.post(url, data=data, files=files, timeout=req_timeout)
            else:
                response = await client.post(url, data=data, timeout=req_timeout)
        except httpx.TimeoutException as e:
            raise TelegramNetworkError(method=method, message='Request timeout error') from e
        except httpx.RequestError as e:
            raise TelegramNetworkError(method=method, message=f'{type(e).__name__}: {e}') from e

        result = self.check_response(
            bot=bot,
            method=method,
            status_code=response.status_code,
            content=response.text,
        )
        return cast('TelegramType', result.result)

    async def stream_content(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes]:
        if headers is None:
            headers = {}
        client = await self._get_client()
        async with client.stream('GET', url, headers=headers, timeout=timeout) as response:
            if raise_for_status:
                response.raise_for_status()
            async for chunk in response.aiter_bytes(chunk_size):
                yield chunk
