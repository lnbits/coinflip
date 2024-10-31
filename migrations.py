async def m001_add_coinflip_settings(db):
    """
    Creates a hash check table.
    """
    await db.execute(
        """
        CREATE TABLE coinflip.settings (
            id TEXT PRIMARY KEY,
            wallet_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            haircut INTEGER NOT NULL,
            max_players INTEGER NOT NULL,
            max_bet INTEGER NOT NULL,
            enabled BOOLEAN NOT NULL
        );
        """
    )


async def m002_add_coinflip(db):
    """
    Creates a hash check table.
    """
    await db.execute(
        f"""
        CREATE TABLE coinflip.coinflip (
            id TEXT PRIMARY KEY,
            settings_id TEXT NOT NULL,
            name TEXT NOT NULL,
            number_of_players INTEGER NOT NULL,
            buy_in INTEGER NOT NULL,
            players TEXT NOT NULL,
            completed BOOLEAN,
            created_at TIMESTAMP NOT NULL DEFAULT {db.timestamp_now}
        );
        """
    )
