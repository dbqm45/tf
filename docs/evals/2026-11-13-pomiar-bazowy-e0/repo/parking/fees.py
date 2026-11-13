"""Parking fee rules. Amounts are in grosze (1 zł = 100 gr)."""

FREE_MINUTES = 30
HOURLY_RATE = 400
DAILY_CAP = 4000
MINUTES_PER_DAY = 24 * 60


def fee(minutes: int) -> int:
    """Fee for a stay of `minutes`. The first 30 minutes are free, then every started hour costs 4 zł.
    One day never costs more than 40 zł."""
    if minutes < 0:
        raise ValueError("minutes must not be negative")
    days, rest = divmod(minutes, MINUTES_PER_DAY)
    return days * DAILY_CAP + _day_fee(rest)


def _day_fee(minutes: int) -> int:
    if minutes <= FREE_MINUTES:
        return 0
    hours = -(-minutes // 60)
    return min(hours * HOURLY_RATE, DAILY_CAP)
