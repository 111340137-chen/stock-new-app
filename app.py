import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os
from zoneinfo import ZoneInfo

# =========================
# 0) Streamlit 基本設定
# =========================
st.set_page_config(page_title="我的資產儀表板", layout="wide")
st.title("💰 媽媽狩獵者 的資產儀表板")

DATA_FILE = "cash_data.json"

# =========================
# 1) 讀寫設定
# =========================
def load_settings():
    default_data = {
        "twd_bank": 84000, "twd_physical": 0, "twd_max": 20335, "usd": 1,195,
        "btc": 0.012498, "btc_cost": 79905.3,
        "eth": 0.0536, "eth_cost": 2961.40,
        "sol": 4.209, "sol_cost": 131.0,
        "realized_profit_twd": 98966,
        "realized_profit_us_stock": -64,
        "realized_profit_crypto": 0.0
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            return {**default_data, **saved}
        except:
            return default_data
    return default_data

def save_settings(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# =========================
# 2) 你的持股
# =========================
tw_portfolio = [
    {"code": "2317.TW", "name": "鴻海", "shares": 160, "cost": 166.84},
    {"code": "2330.TW", "name": "台積電", "shares": 44, "cost": 1013.12},
]

us_portfolio = [
    {"code": "GRAB", "shares": 50, "cost": 5.125},
    {"code": "NVDA", "shares": 9.78414, "cost": 173.7884},
    {"code": "PLTR", "shares": 2.2357, "cost": 148.96006},
    {"code": "SOFI", "shares": 80.3943, "cost": 24.419},
    {"code": "ORCL", "shares": 4.20742, "cost": 169.68324},
    {"code": "QQQI", "shares": 9, "cost": 52.3771},
    {"code": "TSLA", "shares": 6, "cost": 414.13667},
]

# =========================
# 3) 側邊欄
# =========================
st.sidebar.header("⚙️ 資產設定")
saved = load_settings()

with st.sidebar.expander("💰 已實現損益 (落袋為安)", expanded=True):
    realized_twd = st.number_input("🇹🇼 台股已實現獲利 (TWD)", value=float(saved.get("realized_profit_twd", 97747)), step=100.0)
    realized_us_stock = st.number_input("🇺🇸 美股已實現獲利 (USD)", value=float(saved.get("realized_profit_us_stock", -45)), step=10.0)
    realized_crypto = st.number_input("🪙 加密貨幣已實現獲利 (USD)", value=float(saved.get("realized_profit_crypto", 0.0)), step=10.0)

st.sidebar.subheader("💵 法幣現金")
cash_twd_bank = st.sidebar.number_input("🏦 銀行存款 (TWD)", value=float(saved.get("twd_bank", 0.0)), step=10000.0)
cash_twd_physical = st.sidebar.number_input("🧧 實體現鈔 (TWD)", value=float(saved.get("twd_physical", 0.0)), step=1000.0)
cash_twd_max = st.sidebar.number_input("🟣 MAX 交易所 (TWD)", value=float(saved.get("twd_max", 0.0)), step=1000.0)
cash_usd = st.sidebar.number_input("🇺🇸 美金 (USD)", value=float(saved.get("usd", 0.0)), step=100.0)

st.sidebar.markdown("---")
st.sidebar.subheader("🪙 加密貨幣持倉")
c1, c2 = st.sidebar.columns(2)
btc_qty = c1.number_input("BTC 顆數", value=float(saved.get("btc", 0.0)), step=0.00000001, format="%.8f")
btc_cost = c2.number_input("BTC 均價(USD)", value=float(saved.get("btc_cost", 0.0)), step=100.0, format="%.2f")

c3, c4 = st.sidebar.columns(2)
eth_qty = c3.number_input("ETH 顆數", value=float(saved.get("eth", 0.0)), step=0.00000001, format="%.8f")
eth_cost = c4.number_input("ETH 均價(USD)", value=float(saved.get("eth_cost", 0.0)), step=10.0, format="%.2f")

c5, c6 = st.sidebar.columns(2)
sol_qty = c5.number_input("SOL 顆數", value=float(saved.get("sol", 0.0)), step=0.00000001, format="%.8f")
sol_cost = c6.number_input("SOL 均價(USD)", value=float(saved.get("sol_cost", 0.0)), step=1.0, format="%.2f")

current = {
    "twd_bank": cash_twd_bank, "twd_physical": cash_twd_physical, "twd_max": cash_twd_max, "usd": cash_usd,
    "btc": btc_qty, "btc_cost": btc_cost, "eth": eth_qty, "eth_cost": eth_cost, "sol": sol_qty, "sol_cost": sol_cost,
    "realized_profit_twd": realized_twd,
    "realized_profit_us_stock": realized_us_stock,
    "realized_profit_crypto": realized_crypto
}
if current != saved:
    save_settings(current)

# =========================
# 4) 匯率
# =========================
@st.cache_data(ttl=120)
def get_usdtwd():
    candidates = ["TWD=X", "USDTWD=X"]
    for c in candidates:
        try:
            ticker = yf.Ticker(c)
            df = ticker.history(period="5d", interval="1d")
            if not df.empty and "Close" in df.columns:
                s = df["Close"].dropna()
                if len(s) > 0:
                    return float(s.iloc[-1]), c
        except:
            pass
    return 32.5, "fallback(32.5)"

# =========================
# 5) 新的抓價方式與表格構建
# =========================
@st.cache_data(ttl=30)
def fetch_prev_close_and_live(code: str, market_tz: str):
    ticker = yf.Ticker(code)
    
    df_d = ticker.history(period="1mo", interval="1d")
    if df_d.empty or "Close" not in df_d.columns:
        raise ValueError(f"無法取得日K資料")
        
    dclose = df_d["Close"].dropna()
    if len(dclose) >= 2:
        prev_close = float(dclose.iloc[-2])
        last_daily_close = float(dclose.iloc[-1])
    elif len(dclose) == 1:
        prev_close = float(dclose.iloc[-1])
        last_daily_close = prev_close
    else:
        raise ValueError("日K的 Close 欄位無有效數據")

    live_price = last_daily_close
    live_ts_local = None
    live_date_local = None
    has_live_today = False

    try:
        df_i = ticker.history(period="5d", interval="1m")
        if not df_i.empty and "Close" in df_i.columns:
            iclose = df_i["Close"].dropna()
            if len(iclose) > 0:
                live_price = float(iclose.iloc[-1])
                ts = iclose.index[-1]
                
                if ts.tzinfo is None:
                    ts = ts.tz_localize("UTC")
                
                ts_local = ts.tz_convert(ZoneInfo(market_tz))
                live_ts_local = ts_local
                live_date_local = ts_local.date()

                today_local = pd.Timestamp.now(tz=ZoneInfo(market_tz)).date()
                has_live_today = (live_date_local == today_local)
    except Exception:
        pass

    return {
        "prev_close": prev_close,
        "last_daily_close": last_daily_close,
        "live_price": live_price,
        "live_ts_local": live_ts_local,
        "live_date_local": live_date_local,
        "has_live_today": has_live_today
    }

@st.cache_data(ttl=60)
def fetch_last_two_closes_with_date(codes):
    out = {}
    errors = []
    for code in codes:
        try:
            ticker = yf.Ticker(code)
            df = ticker.history(period="15d", interval="1d")
            if not df.empty and "Close" in df.columns:
                s = df["Close"].dropna()
                if len(s) >= 2:
                    last_close = float(s.iloc[-1])
                    prev_close = float(s.iloc[-2])
                    last_date = s.index[-1].date()
                    out[code] = (last_close, prev_close, last_date)
                elif len(s) == 1:
                    last_close = float(s.iloc[-1])
                    last_date = s.index[-1].date()
                    out[code] = (last_close, last_close, last_date)
                else:
                    errors.append(f"{code}：無有效收盤價")
            else:
                errors.append(f"{code}：無法取得歷史資料")
        except Exception as e:
            errors.append(f"{code} 抓價失敗：{str(e)}")
    return out, errors

@st.cache_data(ttl=60)
def build_df(tw_portfolio, us_portfolio, crypto_inputs):
    errors = []
    rate, rate_src = get_usdtwd()

    rows = []

    # -------------------------
    # 台股
    # -------------------------
    for it in tw_portfolio:
        code = it["code"]
        try:
            q = fetch_prev_close_and_live(code, "Asia/Taipei")
        except Exception as e:
            errors.append(f"台股抓不到：{code} ({e})")
            continue

        prev_close = q["prev_close"]
        last_daily_close = q["last_daily_close"]
        live_price = q["live_price"]
        has_live_today = q["has_live_today"]

        prev_change = last_daily_close - prev_close
        prev_change_pct = (prev_change / prev_close * 100) if prev_close else 0.0

        today_change = (live_price - prev_close) if has_live_today else 0.0
        today_pnl_twd = today_change * it["shares"]

        mkt_status = "盤中/今日已更新" if has_live_today else "休市/非今日盤中資料"

        mv = live_price * it["shares"]
        cost = it["cost"] * it["shares"]
        unreal = mv - cost
        unreal_pct = (unreal / cost * 100) if cost else 0.0

        quote_day = q["live_date_local"] if q["live_date_local"] is not None else pd.Timestamp.now(tz=ZoneInfo("Asia/Taipei")).date()

        rows.append({
            "代號": it["name"],
            "類型": "台股",
            "幣別": "TWD",
            "現價": live_price,
            "上一交易日漲跌": prev_change,
            "上一交易日幅度%": prev_change_pct,
            "報價日": str(quote_day),
            "市場狀態": mkt_status,
            "今日損益(TWD)": today_pnl_twd,
            "市值(TWD)": mv,
            "未實現損益(TWD)": unreal,
            "未實現報酬%": unreal_pct,
        })

    # -------------------------
    # 美股
    # -------------------------
    for it in us_portfolio:
        code = it["code"]
        try:
            q = fetch_prev_close_and_live(code, "America/New_York")
        except Exception as e:
            errors.append(f"美股抓不到：{code} ({e})")
            continue

        prev_close = q["prev_close"]
        last_daily_close = q["last_daily_close"]
        live_price = q["live_price"]
        has_live_today = q["has_live_today"]

        prev_change = last_daily_close - prev_close
        prev_change_pct = (prev_change / prev_close * 100) if prev_close else 0.0

        today_change_usd = (live_price - prev_close) if has_live_today else 0.0
        today_pnl_twd = (today_change_usd * it["shares"]) * rate

        mkt_status = "盤中/今日已更新" if has_live_today else "休市/非今日盤中資料"

        mv_usd = live_price * it["shares"]
        cost_usd = it["cost"] * it["shares"]
        unreal_usd = mv_usd - cost_usd
        unreal_pct = (unreal_usd / cost_usd * 100) if cost_usd else 0.0

        quote_day = q["live_date_local"] if q["live_date_local"] is not None else pd.Timestamp.now(tz=ZoneInfo("America/New_York")).date()

        rows.append({
            "代號": code,
            "類型": "美股",
            "幣別": "USD",
            "現價": live_price,
            "上一交易日漲跌": prev_change,
            "上一交易日幅度%": prev_change_pct,
            "報價日": str(quote_day),
            "市場狀態": mkt_status,
            "今日損益(TWD)": today_pnl_twd,
            "市值(TWD)": mv_usd * rate,
            "未實現損益(TWD)": unreal_usd * rate,
            "未實現報酬%": unreal_pct,
        })

    # -------------------------
    # 幣圈
    # -------------------------
    crypto_codes = list(crypto_inputs.keys())
    cr_prices, cr_err = fetch_last_two_closes_with_date(crypto_codes)
    errors += cr_err

    for code, info in crypto_inputs.items():
        qty = float(info["qty"])
        cost = float(info["cost"])
        if qty <= 0:
            continue
        if code not in cr_prices:
            errors.append(f"幣圈抓不到：{code}")
            continue

        last_close, prev_close, last_date = cr_prices[code]

        change = last_close - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0.0

        mv_usd = last_close * qty
        cost_usd = cost * qty
        unreal_usd = mv_usd - cost_usd
        unreal_pct = (unreal_usd / cost_usd * 100) if cost_usd else 0.0

        rows.append({
            "代號": code.replace("-USD", ""),
            "類型": "Crypto(24h)",
            "幣別": "USD",
            "現價": last_close,
            "上一交易日漲跌": change,
            "上一交易日幅度%": change_pct,
            "報價日": str(last_date),
            "市場狀態": "24h",
            "今日損益(TWD)": (change * qty) * rate,
            "市值(TWD)": mv_usd * rate,
            "未實現損益(TWD)": unreal_usd * rate,
            "未實現報酬%": unreal_pct,
        })

    df = pd.DataFrame(rows)
    return df, rate, rate_src, errors

# =========================
# 6) 執行計算
# =========================
st.write("🔄 正在取得最新報價...")

crypto_inputs = {
    "BTC-USD": {"qty": btc_qty, "cost": btc_cost},
    "ETH-USD": {"qty": eth_qty, "cost": eth_cost},
    "SOL-USD": {"qty": sol_qty, "cost": sol_cost},
}

df, rate, rate_src, errors = build_df(tw_portfolio, us_portfolio, crypto_inputs)

# 現金（統一 TWD）
cash_total_twd = cash_twd_bank + cash_twd_physical + cash_twd_max + (cash_usd * rate)

# 市值 & 總資產
stock_crypto_total = float(df["市值(TWD)"].sum()) if not df.empty else 0.0
total_assets = stock_crypto_total + cash_total_twd

# ⭐ 新增：投資的資產總額 
# 邏輯：總資產 減去 銀行台幣、MAX台幣、實體現鈔 (保留所有持倉與美金券商餘額)
invested_assets = total_assets - cash_twd_bank - cash_twd_max - cash_twd_physical

# 未實現
unreal_tw = float(df[df["類型"] == "台股"]["未實現損益(TWD)"].sum()) if not df.empty else 0.0
unreal_us = float(df[df["類型"] == "美股"]["未實現損益(TWD)"].sum()) if not df.empty else 0.0
unreal_crypto = float(df[df["類型"].str.contains("Crypto")]["未實現損益(TWD)"].sum()) if not df.empty else 0.0

# 已實現（USD -> TWD）
real_tw_twd = float(realized_twd)
real_us_twd = float(realized_us_stock) * rate
real_crypto_twd = float(realized_crypto) * rate

profit_tw_total = unreal_tw + real_tw_twd
profit_us_total = unreal_us + real_us_twd
profit_crypto_total = unreal_crypto + real_crypto_twd
total_profit = profit_tw_total + profit_us_total + profit_crypto_total

# 近似報酬率（保留你的邏輯）
invested_approx = total_assets - total_profit
return_rate_approx = (total_profit / invested_approx * 100) if invested_approx > 0 else 0.0

# 今日/24h 變動
today_change = float(df["今日損益(TWD)"].sum()) if not df.empty else 0.0
today_change_pct = (today_change / total_assets * 100) if total_assets else 0.0

# 佔比
if not df.empty and total_assets > 0:
    df["佔比%"] = df["市值(TWD)"] / total_assets * 100
else:
    if not df.empty:
        df["佔比%"] = 0.0

# =========================
# 7) 指標區
# =========================
# ⭐ 這裡拆成 5 格：保留總資產，旁邊放投資總額
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🏆 總資產(TWD)", f"${total_assets:,.0f}")
c2.metric("🎯 投資總額(TWD)", f"${invested_assets:,.0f}")
c3.metric("💰 總獲利(含已實現)", f"${total_profit:,.0f}", delta=f"{return_rate_approx:.2f}% (近似)")
c4.metric("📅 今日/24h變動", f"${today_change:,.0f}", delta=f"{today_change_pct:.2f}%")
c5.metric("💱 USD/TWD", f"{rate:.2f}", delta=rate_src)

st.markdown("---")

# =========================
# 8) 損益結構
# =========================
st.subheader("📊 損益結構分析 (TWD)")
a, b, c = st.columns(3)
with a:
    st.info(f"**🇹🇼 台股總損益**\n\n### ${profit_tw_total:,.0f}")
    st.write(f"- 未實現：${unreal_tw:,.0f}")
    st.write(f"- 已實現：${real_tw_twd:,.0f}")
with b:
    st.info(f"**🇺🇸 美股總損益**\n\n### ${profit_us_total:,.0f}")
    st.write(f"- 未實現：${unreal_us:,.0f}")
    st.write(f"- 已實現：${real_us_twd:,.0f}")
with c:
    st.info(f"**🪙 幣圈總損益**\n\n### ${profit_crypto_total:,.0f}")
    st.write(f"- 未實現：${unreal_crypto:,.0f}")
    st.write(f"- 已實現：${real_crypto_twd:,.0f}")

st.divider()

# =========================
# 9) 圓餅圖 + 明細表
# =========================
left, right = st.columns([0.35, 0.65])

with left:
    st.subheader("🍰 資產配置圓餅圖")

    chart_rows = []
    if not df.empty:
        for _, r in df.iterrows():
            chart_rows.append({"項目": r["代號"], "市值": r["市值(TWD)"]})

    if cash_twd_bank > 0: chart_rows.append({"項目": "銀行存款", "市值": cash_twd_bank})
    if cash_twd_physical > 0: chart_rows.append({"項目": "實體現鈔", "市值": cash_twd_physical})
    if cash_twd_max > 0: chart_rows.append({"項目": "MAX 交易所", "市值": cash_twd_max})
    if cash_usd > 0: chart_rows.append({"項目": "美金存款(折台)", "市值": cash_usd * rate})

    chart_df = pd.DataFrame(chart_rows)
    if chart_df.empty:
        st.warning("目前沒有可顯示的資產。")
    else:
        fig = px.pie(chart_df, values="市值", names="項目", hole=0.4, title=f"總資產: ${total_assets:,.0f} TWD")
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("📋 持倉詳細行情（市值/損益以 TWD 統一）")

    if df.empty:
        st.warning("沒有抓到任何行情資料（可能是網路或代碼問題）。")
    else:
        show = df[[
            "代號", "類型", "幣別",
            "現價", "上一交易日漲跌", "上一交易日幅度%",
            "市值(TWD)", "佔比%",
            "今日損益(TWD)",
            "未實現報酬%", "未實現損益(TWD)",
            "報價日", "市場狀態"
        ]].copy()

        def color_style(v):
            if isinstance(v, (int, float)):
                if v > 0: return "color: #FF4B4B; font-weight: bold"
                if v < 0: return "color: #00C853; font-weight: bold"
                return "color: gray"
            return ""

        styled = (
            show.style
            .map(color_style, subset=["上一交易日漲跌", "上一交易日幅度%", "今日損益(TWD)", "未實現報酬%", "未實現損益(TWD)"])
            .format({
                "現價": "{:.2f}",
                "上一交易日漲跌": "{:+.2f}",
                "上一交易日幅度%": "{:+.2f}%",
                "市值(TWD)": "${:,.0f}",
                "佔比%": "{:.1f}%",
                "今日損益(TWD)": "${:,.0f}",
                "未實現報酬%": "{:+.2f}%",
                "未實現損益(TWD)": "${:,.0f}",
            })
        )
        st.dataframe(styled, use_container_width=True, height=520, hide_index=True)

# =========================
# 10) 抓價錯誤區
# =========================
if errors:
    with st.expander("⚠️ 抓價/資料警告（點開看哪些代碼抓不到）", expanded=False):
        for e in errors:
            st.write("-", e)
