from typing import Optional

from lnbits.db import Database
from lnbits.helpers import urlsafe_short_hash
from loguru import logger

from .models import Coinflip, CoinflipSettings, CreateCoinflip, CreateCoinflipSettings

db = Database("ext_coinflip")


# Coinflip Settings
async def create_coinflip_settings(
    wallet_id: str, user_id: str, data: CreateCoinflipSettings
) -> CoinflipSettings:
    settings = CoinflipSettings(
        **data.dict(), wallet_id=wallet_id, user_id=user_id, id=urlsafe_short_hash()
    )
    await db.insert("coinflip.settings", settings)
    return settings


async def update_coinflip_settings(settings: CoinflipSettings) -> CoinflipSettings:
    await db.update("coinflip.settings", settings)
    return settings


async def get_coinflip_settings(
    user_id: str,
) -> Optional[CoinflipSettings]:
    logger.debug(user_id)
    return await db.fetchone(
        "SELECT * FROM coinflip.settings WHERE user_id = :user_id",
        {"user_id": user_id},
        CoinflipSettings,
    )


async def get_coinflip_settings_from_id(settings_id: str) -> Optional[CoinflipSettings]:
    return await db.fetchone(
        "SELECT * FROM coinflip.settings WHERE id = :id",
        {"id": settings_id},
        CoinflipSettings,
    )


# Coinflips
async def create_coinflip(data: CreateCoinflip) -> Coinflip:
    coinflip = Coinflip(**data.dict(), id=urlsafe_short_hash())
    logger.debug(coinflip)
    await db.insert("coinflip.coinflip", coinflip)
    return coinflip


async def update_coinflip(coinflip: Coinflip) -> Coinflip:
    await db.update("coinflip.coinflip", coinflip)
    return coinflip


async def get_coinflip(coinflip_id: str) -> Optional[Coinflip]:
    logger.debug("coinflip_id")
    return await db.fetchone(
        "SELECT * FROM coinflip.coinflip WHERE id = :id",
        {"id": coinflip_id},
        Coinflip,
    )


async def get_latest_coinflip(page_id: str) -> Optional[Coinflip]:
    return await db.fetchone(
        "SELECT * FROM coinflip.coinflip WHERE page_id = :id ORDER BY created_at DESC",
        {"page_id": page_id},
        Coinflip,
    )
