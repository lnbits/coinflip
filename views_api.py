from http import HTTPStatus

from fastapi import APIRouter, Depends
from lnbits.core.crud import get_user
from lnbits.core.models import WalletTypeInfo
from lnbits.core.services import create_invoice
from lnbits.decorators import require_admin_key, require_invoice_key
from starlette.exceptions import HTTPException

from .crud import (
    create_coinflip,
    create_coinflip_settings,
    get_coinflip,
    get_coinflip_settings,
    get_coinflip_settings_from_id,
    update_coinflip_settings,
)
from .helpers import get_pr
from .models import (
    CoinflipSettings,
    CreateCoinflip,
    CreateCoinflipSettings,
    JoinCoinflipGame,
)

coinflip_api_router = APIRouter()


@coinflip_api_router.get("/api/v1/coinflip/settings", status_code=HTTPStatus.OK)
async def api_get_coinflip_settings(
    key_info: WalletTypeInfo = Depends(require_admin_key),
):
    user = await get_user(key_info.wallet.user)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="unable to chnage settings"
        )
    settings = await get_coinflip_settings(user.id)
    if not settings:
        settings = await create_coinflip_settings(
            key_info.wallet.id,
            key_info.wallet.user,
            CreateCoinflipSettings(),
        )
    return settings


@coinflip_api_router.post("/api/v1/coinflip/settings", status_code=HTTPStatus.CREATED)
async def api_create_coinflip_settings(
    coinflip_settings: CreateCoinflipSettings,
    key_info: WalletTypeInfo = Depends(require_admin_key),
) -> CoinflipSettings:
    user = await get_user(key_info.wallet.user)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="unable to change settings"
        )
    return await create_coinflip_settings(
        key_info.wallet.id, user.id, coinflip_settings
    )


@coinflip_api_router.put("/api/v1/coinflip/settings", status_code=HTTPStatus.CREATED)
async def api_update_coinflip_settings(
    coinflip_settings: CoinflipSettings,
    key_info: WalletTypeInfo = Depends(require_admin_key),
) -> CoinflipSettings:
    user = await get_user(key_info.wallet.user)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="unable to change settings"
        )
    settings = await update_coinflip_settings(coinflip_settings)
    return settings


@coinflip_api_router.post("/api/v1/coinflip", status_code=HTTPStatus.OK)
async def api_create_coinflip(
    data: CreateCoinflip, key_info: WalletTypeInfo = Depends(require_invoice_key)
):
    coinflip_settings = await get_coinflip_settings(key_info.wallet.user)
    if not coinflip_settings:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Couldnt load settings"
        )
    if coinflip_settings.max_bet < data.buy_in:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Buy in to high")
    if coinflip_settings.max_players < data.number_of_players:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Number of plaers is too high"
        )
    if coinflip_settings.id != data.settings_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Settings ID is wrong"
        )
    coinflip = await create_coinflip(data)
    return coinflip.id


@coinflip_api_router.post("/api/v1/coinflip/join/", status_code=HTTPStatus.OK)
async def api_join_coinflip(data: JoinCoinflipGame):
    coinflip_settings = await get_coinflip_settings_from_id(data.settings_id)
    coinflip_game = await get_coinflip(data.game_id)
    if not coinflip_game:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="No game found")
    if not coinflip_settings:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Coinflip settings missing"
        )
    if coinflip_game.completed:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="This game is already full"
        )
    if not coinflip_settings.enabled:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="This game is disabled"
        )
    pay_req = await get_pr(data.ln_address, coinflip_game.buy_in)
    if not pay_req:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="lnaddress check failed"
        )
    payment = await create_invoice(
        wallet_id=coinflip_settings.wallet_id,
        amount=coinflip_game.buy_in,
        memo=f"Coinflip {coinflip_game.name} for {data.ln_address}",
        extra={
            "tag": "coinflip",
            "ln_address": data.ln_address,
            "game_id": data.game_id,
        },
    )
    return {"payment_hash": payment.payment_hash, "payment_request": payment.bolt11}


@coinflip_api_router.get(
    "/api/v1/coinflip/coinflip/{coinflip_id}", status_code=HTTPStatus.OK
)
async def api_get_coinflip(coinflip_id: str):
    return await get_coinflip(coinflip_id)
