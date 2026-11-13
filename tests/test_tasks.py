from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from lnbits.core.models import Payment, PaymentState

from .. import tasks
from ..models import Coinflip, CoinflipSettings


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def game_payment(monkeypatch):
    game = Coinflip(
        id="game-one",
        settings_id="settings-one",
        name="Game",
        number_of_players=2,
        buy_in=1000,
    )
    settings = CoinflipSettings(
        id="settings-one",
        wallet_id="game-wallet",
        user_id="operator",
        max_players=5,
        max_bet=10_000,
        enabled=True,
        haircut=1,
    )
    payment = Payment(
        checking_id="invoice-one",
        payment_hash="hash-one",
        wallet_id=settings.wallet_id,
        amount=1_000_000,
        fee=0,
        bolt11="invoice",
        status=PaymentState.SUCCESS,
        extra={
            "tag": "coinflip",
            "game_id": game.id,
            "ln_address": "player@example.com",
        },
    )
    monkeypatch.setattr(tasks, "get_coinflip", AsyncMock(return_value=game))
    monkeypatch.setattr(
        tasks, "get_coinflip_settings_from_id", AsyncMock(return_value=settings)
    )
    update = AsyncMock()
    resolve = AsyncMock(return_value="payout-invoice")
    pay = AsyncMock()
    notify = AsyncMock()
    tribute = AsyncMock()
    monkeypatch.setattr(tasks, "update_coinflip", update)
    monkeypatch.setattr(tasks, "get_pr_from_lnurl", resolve)
    monkeypatch.setattr(tasks, "pay_invoice", pay)
    monkeypatch.setattr(tasks, "websocket_updater", notify)
    monkeypatch.setattr(tasks, "pay_tribute", tribute)
    return SimpleNamespace(
        game=game,
        settings=settings,
        payment=payment,
        update=update,
        resolve=resolve,
        pay=pay,
        notify=notify,
        tribute=tribute,
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "players", ["", "first@example.com", "first@example.com,second@example.com"]
)
async def test_payment_for_another_wallet_leaves_game_unchanged(game_payment, players):
    case = game_payment
    case.game.players = players
    case.game.completed = players.count(",") == 1
    before = case.game.model_dump()
    case.payment.wallet_id = "another-wallet"

    await tasks.on_invoice_paid(case.payment)

    assert case.game.model_dump() == before
    case.update.assert_not_awaited()
    case.resolve.assert_not_awaited()
    case.pay.assert_not_awaited()
    case.notify.assert_not_awaited()
    case.tribute.assert_not_awaited()


@pytest.mark.anyio
async def test_matching_wallet_adds_player(game_payment):
    case = game_payment
    await tasks.on_invoice_paid(case.payment)

    assert case.game.players == "player@example.com"
    assert not case.game.completed
    case.update.assert_awaited_once_with(case.game)
    case.notify.assert_awaited_once_with("coinfliphash-one", "paid")
    case.pay.assert_not_awaited()


@pytest.mark.anyio
@pytest.mark.parametrize("winner", ["first@example.com", "player@example.com"])
async def test_matching_wallet_completes_game(game_payment, monkeypatch, winner):
    case = game_payment
    case.game.players = "first@example.com"
    monkeypatch.setattr(tasks.random, "choice", lambda players: winner)

    await tasks.on_invoice_paid(case.payment)

    assert case.game.completed
    assert case.game.name == winner
    assert case.game.players == "first@example.com,player@example.com"
    case.resolve.assert_awaited_once_with(winner, 1_980_000)
    case.pay.assert_awaited_once_with(
        wallet_id=case.settings.wallet_id,
        payment_request="payout-invoice",
        max_sat=1980,
        description="You flipping won the coinflip!",
    )
    case.tribute.assert_awaited_once_with(20, case.settings.wallet_id)


@pytest.mark.anyio
async def test_matching_wallet_refunds_full_game(game_payment):
    case = game_payment
    case.game.players = "first@example.com,second@example.com"
    case.game.completed = True

    await tasks.on_invoice_paid(case.payment)

    case.resolve.assert_awaited_once_with("player@example.com", 990_000)
    case.pay.assert_awaited_once_with(
        wallet_id=case.settings.wallet_id,
        payment_request="payout-invoice",
        max_sat=990,
        description="Refund. Coinflip game was full.",
    )
    case.notify.assert_awaited_once_with("coinfliphash-one", "refund")
    case.tribute.assert_not_awaited()


@pytest.mark.anyio
@pytest.mark.parametrize("amount", [999_000, 1_001_000])
async def test_matching_wallet_still_requires_buy_in(game_payment, amount):
    case = game_payment
    case.payment.amount = amount

    await tasks.on_invoice_paid(case.payment)

    assert case.game.players == ""
    case.update.assert_not_awaited()
    case.pay.assert_not_awaited()
