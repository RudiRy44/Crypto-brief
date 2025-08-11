import os, requests, datetime as dt

# ---- Timezone: Asia/Shanghai (CST) ----
TZ = dt.timezone(dt.timedelta(hours=8))
now = dt.datetime.now(TZ)

# ---- Telegram ----
BOT = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ["TELEGRAM_CHAT_ID"]
TG_URL = f"https://api.telegram.org/bot{BOT}/sendMessage"

def send(text):
    # Telegram message limit ~4096 chars; keep margin
    requests.post(TG_URL, data={"chat_id": CHAT, "parse_mode":"HTML", "text": text[:4000]})

# ---- Free data via CoinGecko (no key) ----
def prices_watchlist():
    ids = "bitcoin,ethereum,solana,ripple,cosmos"
    r = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={
            "ids": ids,
            "vs_currencies":"usd",
            "include_24hr_change":"true",
            "include_24hr_vol":"true"
        },
        timeout=20
    )
    r.raise_for_status()
    return r.json()

def price_spike_alerts():
    # NOTE: for true 15m/1h spikes we’ll upgrade later with candle data.
    data = prices_watchlist()
    msgs = []
    def row(id_, sym):
        chg = data[id_].get("usd_24h_change", 0.0)
        if id_ in ("bitcoin","ethereum"):
            if abs(chg) >= 5:
                return f"{sym}: ~{chg:.2f}% (24h) — large move. (Proxy for 1h spike)"
        else:
            if abs(chg) >= 7:
                return f"{sym}: ~{chg:.2f}% (24h) — large move. (Proxy for 1h spike)"
        return None
    for id_, sym in [("bitcoin","BTC"),("ethereum","ETH"),("solana","SOL"),("ripple","XRP"),("cosmos","ATOM")]:
        m = row(id_, sym)
        if m: msgs.append(m)
    return msgs

def daily_brief():
    px = prices_watchlist()
    def line(id_, label):
        p = px[id_]["usd"]; chg = px[id_].get("usd_24h_change", 0.0)
        return f"{label}: ${p:,.0f} ({chg:+.2f}% 24h)"
    return (
        f"🚀 <b>Daily Crypto Intel Brief</b> — {now:%Y-%m-%d %H:%M} CST\n"
        f"{line('bitcoin','BTC')}\n"
        f"{line('ethereum','ETH')}\n"
        f"{line('solana','SOL')}\n"
        f"{line('ripple','XRP')}\n"
        f"{line('cosmos','ATOM')}\n\n"
        "What to watch (next upgrade hooks):\n"
        "• Whale inflows/outflows & exchange deposits (Nansen/Arkham APIs)\n"
        "• DEX momentum on new pairs (<72h) via GeckoTerminal API\n"
        "• Social/political narrative spikes (X/Reddit/News)\n"
    )

def within_alert_hours():
    return 6 <= now.hour <= 18  # Intraday window Beijing time

if now.hour == 8 and now.minute == 0:
    send(daily_brief())
else:
    if within_alert_hours():
        spikes = price_spike_alerts()
        if spikes:
            send("⚡ <b>Price-Move Alerts</b>\n" + "\n".join(f"• {s}" for s in spikes))
