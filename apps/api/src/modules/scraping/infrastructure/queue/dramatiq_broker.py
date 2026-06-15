"""Configuracao compartilhada do broker Dramatiq com Redis."""

import asyncio

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import AsyncIO

from apps.api.src.config.settings import get_settings


# Redis transporta somente mensagens pequenas entre API e worker. O estado do
# scraping continua sendo persistido no PostgreSQL.
broker = RedisBroker(url=get_settings().redis_url)

# Actors Dramatiq sao sincronos por padrao. Este middleware mantem um event
# loop no worker para permitir que nossa task chame casos de uso async.
broker.add_middleware(AsyncIO())

# Dramatiq usa um broker global para registrar actors e enviar mensagens.
# Configura-lo neste modulo garante que API e worker usem a mesma instancia.
dramatiq.set_broker(broker)


async def check_redis_connection() -> bool:
    """Verifica a conexao Redis sem bloquear o event loop da API."""

    return bool(await asyncio.to_thread(broker.client.ping))
