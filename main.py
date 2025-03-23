from fastapi import FastAPI
import os
import requests
import yfinance as yf

app = FastAPI()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ALERTS = os.getenv("STOCK_ALERTS", "")  # z. B. "AAPL<160,TSLA>800,NVDA<700"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Telegram-Fehler: {e}")

def parse_alerts(raw):
    alerts = []
    for entry in raw.split(","):
        entry = entry.strip()
        if "<" in entry:
            symbol, value = entry.split("<")
            alerts.append({ "symbol": symbol.upper(), "below": float(value) })
        elif ">" in entry:
            symbol, value = entry.split(">")
            alerts.append({ "symbol": symbol.upper(), "above": float(value) })
    return alerts

def check_prices():
    results = []
    alerts = parse_alerts(ALERTS)
    for alert in alerts:
        symbol = alert["symbol"]
        try:
            stock = yf.Ticker(symbol)
            price = stock.fast_info["lastPrice"]
            if "below" in alert and price < alert["below"]:
                msg = f"🔔 {symbol} unter {alert['below']} USD gefallen → Aktuell: {price:.2f} USD"
                send_telegram_message(msg)
                results.append(msg)
            elif "above" in alert and price > alert["above"]:
                msg = f"🚀 {symbol} über {alert['above']} USD gestiegen → Aktuell: {price:.2f} USD"
                send_telegram_message(msg)
                results.append(msg)
        except Exception as e:
            results.append(f"Fehler bei {symbol}: {e}")
    return results

@app.get("/check")
def run_check():
    results = check_prices()
    print("Preisalarm ausgeführt:", results)
    return { "checked": len(results), "status": "OK" }
