from datetime import datetime, timezone
from typing import Optional

from fastapi import Query
from pydantic import BaseModel


class CreateCoinflipSettings(BaseModel):
    max_players: int = 5
    max_bet: int = 100
    enabled: bool = False
    haircut: float = 0.0


class CoinflipSettings(BaseModel):
    id: str
    wallet_id: str
    user_id: str
    max_players: int
    max_bet: int
    enabled: bool
    haircut: float


class CreateCoinflip(BaseModel):
    settings_id: Optional[str] = None
    name: str
    number_of_players: int = 0
    buy_in: int = 0


class Coinflip(BaseModel):
    id: Optional[str] = None
    settings_id: Optional[str] = None
    name: str
    number_of_players: int = 0
    buy_in: int = 0
    players: str = ""
    completed: bool = False
    created_at: datetime = datetime.now(timezone.utc)


class JoinCoinflipGame(BaseModel):
    game_id: str = Query(None)
    settings_id: str = Query(None)
    ln_address: str = Query(None)
