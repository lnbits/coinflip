import asyncio
import random

from lnbits.core.models import Payment
from lnbits.core.services import get_pr_from_lnurl, pay_invoice, websocket_updater
from lnbits.tasks import register_invoice_listener
from loguru import logger

from .crud import (
    get_coinflip,
    get_coinflip_settings_from_id,
    update_coinflip,
)


async def wait_for_paid_invoices():
    invoice_queue = asyncio.Queue()
    register_invoice_listener(invoice_queue, "ext_coinflip")

    while True:
        payment = await invoice_queue.get()
        await on_invoice_paid(payment)


async def on_invoice_paid(payment: Payment) -> None:
    if payment.extra.get("tag") != "coinflip":
        return
    ln_address = payment.extra["ln_address"]
    game_id = payment.extra["game_id"]
    # fetch details
    coinflip = await get_coinflip(game_id)
    if not coinflip or not coinflip.settings_id:
        return
    coinflip_settings = await get_coinflip_settings_from_id(coinflip.settings_id)
    if not coinflip_settings:
        return
    # Check they are not trying to scam the system.
    if (payment.amount / 1000) != coinflip.buy_in:
        return
    # If the game is full set as completed and refund the player.
    coinflip_players = []
    if coinflip.players != "":
        coinflip_players = coinflip.players.split(",")
    if len(coinflip_players) > 0 and coinflip_players[0] == "":
        coinflip_players.pop(0)
    if len(coinflip_players) + 1 > coinflip.number_of_players:
        coinflip.completed = True
        coinflip_players.append(ln_address)
        coinflip.players = ",".join(coinflip_players)
        await update_coinflip(coinflip)

        # Calculate the haircut amount
        haircut_amount = coinflip.buy_in * (coinflip_settings.haircut / 100)
        # Calculate the refund amount
        max_sat = int(coinflip.buy_in - haircut_amount)
        try:
            pr = await get_pr_from_lnurl(ln_address, max_sat)
        except Exception as exc:
            logger.error(f"Error getting payment request for refund: {exc!s}")
            return
        await pay_invoice(
            wallet_id=coinflip_settings.wallet_id,
            payment_request=pr,
            max_sat=max_sat,
            description="Refund. Coinflip game was full.",
        )
        await websocket_updater("coinflip" + payment.payment_hash, "refund")
        return

    # Add the player to the game.
    coinflip_players.append(ln_address)
    coinflip.players = ",".join(coinflip_players)
    await update_coinflip(coinflip)
    if len(coinflip_players) == coinflip.number_of_players:
        coinflip.completed = True
        winner = random.choice(coinflip_players)
        coinflip.name = winner
        await update_coinflip(coinflip)
        # Calculate the total amount of winnings
        total_amount = coinflip.buy_in * len(coinflip_players)
        # Calculate the haircut amount
        haircut_amount = total_amount * (coinflip_settings.haircut / 100)
        # Calculate the winnings minus haircut
        max_sat = int(total_amount - haircut_amount)
        try:
            pr = await get_pr_from_lnurl(winner, max_sat)
        except Exception as exc:
            logger.error(f"Error getting payment request for winner: {exc!s}")
            return
        if winner == ln_address:
            await websocket_updater("coinflip" + payment.payment_hash, f"won,{winner}")
            await pay_invoice(
                wallet_id=coinflip_settings.wallet_id,
                payment_request=pr,
                max_sat=max_sat,
                description="You flipping won the coinflip!",
            )
        if winner != ln_address:
            await websocket_updater("coinflip" + payment.payment_hash, f"lost,{winner}")
            await pay_invoice(
                wallet_id=coinflip_settings.wallet_id,
                payment_request=pr,
                max_sat=max_sat,
                description="You flipping won the coinflip!",
            )
        # Pay the tribute to LNbits Inc, because you're nice and like LNbits.
        await pay_tribute(int(haircut_amount), coinflip_settings.wallet_id)
        return
    await websocket_updater("coinflip" + payment.payment_hash, "paid")


async def pay_tribute(haircut_amount: int, wallet_id: str) -> None:
    try:
        tribute = int(2 * (haircut_amount / 100))
        try:
            pr = await get_pr_from_lnurl("lnbits@nostr.com", tribute)
        except Exception as exc:
            logger.error(f"Error getting payment request for tribute: {exc!s}")
            return
        await pay_invoice(
            wallet_id=wallet_id,
            payment_request=pr,
            max_sat=tribute,
            description="Tribut to help support LNbits",
        )
    except Exception:
        pass
    return
