from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer

from .crud import get_coinflip, get_coinflip_settings_from_id

coinflip_generic_router: APIRouter = APIRouter()


def coinflip_renderer():
    return template_renderer(["coinflip/templates"])


@coinflip_generic_router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(check_user_exists)):
    return coinflip_renderer().TemplateResponse(
        "coinflip/index.html", {"request": request, "user": user.json()}
    )


@coinflip_generic_router.get(
    "/coinflip/{coinflip_settings_id}/{game}", response_class=HTMLResponse
)
async def display_coinflip(request: Request, coinflip_settings_id: str, game: str):
    coinflip_settings = await get_coinflip_settings_from_id(coinflip_settings_id)
    if not coinflip_settings:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Coinflip game does not exist."
        )
    winner = None
    if game:
        coinflip = await get_coinflip(game)
        if not coinflip:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Coinflip game does not exist."
            )
        if coinflip.completed:
            winner = coinflip.players
    return coinflip_renderer().TemplateResponse(
        "coinflip/coinflip.html",
        {
            "request": request,
            "coinflipHaircut": coinflip_settings.haircut,
            "coinflipMaxPlayers": coinflip_settings.max_players,
            "coinflipMaxBet": coinflip_settings.max_bet,
            "coinflipPageId": coinflip_settings.id,
            "coinflipGameId": game,
            "coinflipWinner": winner,
        },
    )
