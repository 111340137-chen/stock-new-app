import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, os
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# 0) Streamlit 基本設定
# =========================
st.set_page_config(page_title="我的資產儀表板", layout="wide")
st.title("💰 媽媽狩獵者 的資產儀表板")

DATA_FILE = "cash_data.json"
HISTORY_FILE = "asset_history.json"

# =========================
# 1) 讀寫設定
# =========================
DEFAULT_DATA = {
    "twd_bank": 48619,
    "twd_physical": 0,
    "twd_max": 20335,
    "usd": 1014.77,
    "btc": 0.012498, "btc_cost": 79905.3,
    "eth": 0.0536,   "eth_cost": 2961.40,
    "sol": 4.209,    "sol_cost": 131.0,
    "realized_profit_twd": 98966,
    "realized_profit_us_stock": -64,
    "realized_profit_crypto": 0.0,
    "tw_portfolio": [
        {"code": "2317.TW", "name": "鴻海",    "shares": 160,     "cost": 166.84},
        {"code": "2330.TW", "name": "台積電",  "shares": 44,      "cost": 1013.12},
        {"code": "4958.TW", "name": "臻鼎-KY", "shares": 60,      "cost": 209.21},
        {"code": "3376.TW", "name": "新日興", "shares": 67,      "cost":  197.4},
    ],
    "us_portfolio": [
        {"code": "GRAB",  "shares": 50,       "cost": 5.125},
        {"code": "NVDA",  "shares": 9.78414,  "cost": 173.7884},
        {"code": "PLTR",  "shares": 2.2357,   "cost": 148.96006},
        {"code": "SOFI",  "shares": 80.3943,  "cost": 24.419},
        {"code": "ORCL",  "shares": 4.20742,  "cost": 169.68324},
        {"code": "QQQI",  "shares": 9,        "cost": 52.3771},
        {"code": "TSLA",  "shares": 6.5,      "cost": 409.93846},
    ],
}

def load_settings():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # 深層合併，確保新欄位有預設值
            merged = {**DEFAULT_DATA, **saved}
            # portfolio 若存在就用存檔的
            if "tw_portfolio" not in saved:
                merged["tw_portfolio"] = DEFAULT_DATA["tw_portfolio"]
            if "us_portfolio" not in saved:
                merged["us_portfolio"] = DEFAULT_DATA["us_portfolio"]
            return merged
        except Exception:
            pass
    return dict(DEFAULT_DATA)

def save_settings(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# =========================
# 2) 歷史快照
# =========================
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_snapshot(total_twd: float, invested_twd: float, profit_twd: float):
    history = load_history()
    today = datetime.now().strftime("%Y-%m-%d")
    # 同一天只保留最新一筆
    history = [h for h in history if h["date"] != today]
    history.append({
        "date": today,
        "total": round(total_twd),
        "invested": round(invested_twd),
        "profit": round(profit_twd),
    })
    # 只保留最近 365 天
    history = sorted(history, key=lambda x: x["date"])[-365:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# =========================
# 3) 側邊欄
# =========================
st.sidebar.header("⚙️ 資產設定")
saved = load_settings()

# ── 現金 ──
with st.sidebar.expander("💵 法幣現金", expanded=True):
    cash_twd_bank     = st.number_input("🏦 銀行存款 (TWD)",   value=float(saved["twd_bank"]),     step=10000.0)
    cash_twd_physical = st.number_input("🧧 實體現鈔 (TWD)",   value=float(saved["twd_physical"]), step=1000.0)
    cash_twd_max      = st.number_input("🟣 MAX 交易所 (TWD)", value=float(saved["twd_max"]),      step=1000.0)
    cash_usd          = st.number_input("🇺🇸 美金 (USD)",       value=float(saved["usd"]),          step=100.0)

# ── 加密貨幣 ──
with st.sidebar.expander("🪙 加密貨幣持倉", expanded=False):
    c1, c2 = st.sidebar.columns(2)
    btc_qty  = c1.number_input("BTC 顆數",    value=float(saved["btc"]),      step=0.00000001, format="%.8f")
    btc_cost = c2.number_input("BTC 均價(USD)",value=float(saved["btc_cost"]), step=100.0,     format="%.2f")
    c3, c4 = st.sidebar.columns(2)
    eth_qty  = c3.number_input("ETH 顆數",    value=float(saved["eth"]),      step=0.00000001, format="%.8f")
    eth_cost = c4.number_input("ETH 均價(USD)",value=float(saved["eth_cost"]), step=10.0,      format="%.2f")
    c5, c6 = st.sidebar.columns(2)
    sol_qty  = c5.number_input("SOL 顆數",    value=float(saved["sol"]),      step=0.00000001, format="%.8f")
    sol_cost = c6.number_input("SOL 均價(USD)",value=float(saved["sol_cost"]), step=1.0,       format="%.2f")

# ── 已實現損益 ──
with st.sidebar.expander("💰 已實現損益", expanded=False):
    realized_twd      = st.number_input("🇹🇼 台股已實現獲利 (TWD)", value=float(saved["realized_profit_twd"]),      step=100.0)
    realized_us_stock = st.number_input("🇺🇸 美股已實現獲利 (USD)", value=float(saved["realized_profit_us_stock"]), step=10.0)
    realized_crypto   = st.number_input("🪙 加密已實現獲利 (USD)",  value=float(saved["realized_profit_crypto"]),   step=10.0)

# ── 台股持倉編輯 ──
with st.sidebar.expander("🇹🇼 台股持倉（可編輯）", expanded=False):
    st.caption("格式：代號,名稱,股數,均價  每行一筆")
    tw_default_text = "\n".join(
        f"{r['code']},{r['name']},{r['shares']},{r['cost']}"
        for r in saved["tw_portfolio"]
    )
    tw_text = st.text_area("台股清單", value=tw_default_text, height=160)

    tw_portfolio = []
    for line in tw_text.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 4:
            try:
                tw_portfolio.append({
                    "code": parts[0], "name": parts[1],
                    "shares": float(parts[2]), "cost": float(parts[3])
                })
            except ValueError:
                pass

# ── 美股持倉編輯 ──
with st.sidebar.expander("🇺🇸 美股持倉（可編輯）", expanded=False):
    st.caption("格式：代號,股數,均價  每行一筆")
    us_default_text = "\n".join(
        f"{r['code']},{r['shares']},{r['cost']}"
        for r in saved["us_portfolio"]
    )
    us_text = st.text_area("美股清單", value=us_default_text, height=200)

    us_portfolio = []
    for line in us_text.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 3:
            try:
                us_portfolio.append({
                    "code": parts[0],
                    "shares": float(parts[1]), "cost": float(parts[2])
                })
            except ValueError:
                pass

# ── 儲存 ──
current = {
    "twd_bank": cash_twd_bank, "twd_physical": cash_twd_physical,
    "twd_max": cash_twd_max,   "usd": cash_usd,
    "btc": btc_qty,  "btc_cost": btc_cost,
    "eth": eth_qty,  "eth_cost": eth_cost,
    "sol": sol_qty,  "sol_cost": sol_cost,
    "realized_profit_twd": realized_twd,
    "realized_profit_us_stock": realized_us_stock,
    "realized_profit_crypto": realized_crypto,
    "tw_portfolio": tw_portfolio,
    "us_portfolio": us_portfolio,
}
if current != saved:
    save_settings(current)

# =========================
# 4) 匯率（批次 + fallback）
# =========================
@st.cache_data(ttl=120)
def get_usdtwd():
    for code in ["TWD=X", "USDTWD=X"]:
        try:
            df = yf.Ticker(code).history(period="5d", interval="1d")
            if not df.empty:
                s = df["Close"].dropna()
                if len(s) > 0:
                    return float(s.iloc[-1]), code
        except Exception:
            pass
    return 32.5, "fallback(32.5)"

# =========================
# 5) 批次抓股票行情（核心改善）
# =========================
@st.cache_data(ttl=60)
def batch_fetch_stocks(codes_tw: tuple, codes_us: tuple):
    """
    一次性批次下載台股 + 美股的日K，
    再各別補抓 1m 分鐘K 以取得盤中即時價。
    回傳 dict[code] = {prev_close, live_price, has_live_today, live_date_local}
    """
    all_codes = list(codes_tw) + list(codes_us)
    result = {}
    errors = []

    if not all_codes:
        return result, errors

    # ── 日K 批次下載 ──
    try:
        raw = yf.download(
            all_codes,
            period="1mo",
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
    except Exception as e:
        errors.append(f"批次日K下載失敗：{e}")
        return result, errors

    def _extract_daily(code):
        try:
            if len(all_codes) == 1:
                df = raw
            else:
                df = raw[code] if code in raw.columns.get_level_values(0) else pd.DataFrame()
            if df is None or df.empty:
                return None, None
            s = df["Close"].dropna()
            if len(s) >= 2:
                return float(s.iloc[-2]), float(s.iloc[-1])
            elif len(s) == 1:
                v = float(s.iloc[-1])
                return v, v
        except Exception:
            pass
        return None, None

    # ── 分鐘K（各別，但只取最後一筆）──
    def _get_live(code, tz_str):
        try:
            df_i = yf.Ticker(code).history(period="2d", interval="1m")
            if df_i.empty:
                return None, None, False
            s = df_i["Close"].dropna()
            if s.empty:
                return None, None, False
            live_price = float(s.iloc[-1])
            ts = s.index[-1]
            if ts.tzinfo is None:
                ts = ts.tz_localize("UTC")
            ts_local = ts.tz_convert(tz_str)
            live_date = ts_local.date()
            today = pd.Timestamp.now(tz=tz_str).date()
            return live_price, live_date, (live_date == today)
        except Exception:
            return None, None, False

    for code in codes_tw:
        prev_close, last_daily = _extract_daily(code)
        if prev_close is None:
            errors.append(f"台股日K抓不到：{code}")
            continue
        live_price, live_date, has_live = _get_live(code, "Asia/Taipei")
        result[code] = {
            "prev_close":     prev_close,
            "live_price":     live_price if live_price else last_daily,
            "last_daily":     last_daily,
            "has_live_today": has_live,
            "live_date":      live_date,
            "tz":             "Asia/Taipei",
        }

    for code in codes_us:
        prev_close, last_daily = _extract_daily(code)
        if prev_close is None:
            errors.append(f"美股日K抓不到：{code}")
            continue
        live_price, live_date, has_live = _get_live(code, "America/New_York")
        result[code] = {
            "prev_close":     prev_close,
            "live_price":     live_price if live_price else last_daily,
            "last_daily":     last_daily,
            "has_live_today": has_live,
            "live_date":      live_date,
            "tz":             "America/New_York",
        }

    return result, errors

@st.cache_data(ttl=60)
def batch_fetch_crypto(codes: tuple):
    """批次抓加密貨幣日K（yfinance 支援 BTC-USD 等）"""
    out = {}
    errors = []
    if not codes:
        return out, errors
    try:
        raw = yf.download(
            list(codes),
            period="5d",
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
    except Exception as e:
        errors.append(f"加密貨幣批次下載失敗：{e}")
        return out, errors

    for code in codes:
        try:
            df = raw[code] if len(codes) > 1 else raw
            s = df["Close"].dropna()
            if len(s) >= 2:
                out[code] = (float(s.iloc[-1]), float(s.iloc[-2]), s.index[-1].date())
            elif len(s) == 1:
                v = float(s.iloc[-1])
                out[code] = (v, v, s.index[-1].date())
            else:
                errors.append(f"{code}：無有效收盤價")
        except Exception as e:
            errors.append(f"{code} 解析失敗：{e}")
    return out, errors

# =========================
# 6) 組成 DataFrame
# =========================
@st.cache_data(ttl=60)
def build_df(
    tw_portfolio_tuple,   # tuple of frozen dicts (hashable)
    us_portfolio_tuple,
    crypto_tuple,         # tuple of (code, qty, cost)
    rate: float,
):
    tw_portfolio = [dict(r) for r in tw_portfolio_tuple]
    us_portfolio = [dict(r) for r in us_portfolio_tuple]

    codes_tw = tuple(r["code"] for r in tw_portfolio)
    codes_us = tuple(r["code"] for r in us_portfolio)

    prices, errors = batch_fetch_stocks(codes_tw, codes_us)

    crypto_codes = tuple(c for c, _, _ in crypto_tuple)
    cr_prices, cr_err = batch_fetch_crypto(crypto_codes)
    errors += cr_err

    rows = []

    # ── 台股 ──
    for it in tw_portfolio:
        code = it["code"]
        if code not in prices:
            continue
        q = prices[code]
        prev_close = q["prev_close"]
        live_price = q["live_price"]
        has_live   = q["has_live_today"]
        live_date  = q["live_date"]

        prev_change     = q["last_daily"] - prev_close
        prev_change_pct = (prev_change / prev_close * 100) if prev_close else 0.0
        today_change    = (live_price - prev_close) if has_live else 0.0
        today_pnl       = today_change * it["shares"]
        mv              = live_price * it["shares"]
        cost            = it["cost"] * it["shares"]
        unreal          = mv - cost
        unreal_pct      = (unreal / cost * 100) if cost else 0.0
        quote_day       = str(live_date) if live_date else "—"
        mkt_status      = "盤中✅" if has_live else "收盤"

        rows.append({
            "代號": it["name"], "類型": "台股", "幣別": "TWD",
            "現價": live_price,
            "上一交易日漲跌": prev_change, "上一交易日幅度%": prev_change_pct,
            "報價日": quote_day, "市場狀態": mkt_status,
            "今日損益(TWD)": today_pnl,
            "市值(TWD)": mv,
            "未實現損益(TWD)": unreal, "未實現報酬%": unreal_pct,
        })

    # ── 美股 ──
    for it in us_portfolio:
        code = it["code"]
        if code not in prices:
            continue
        q = prices[code]
        prev_close = q["prev_close"]
        live_price = q["live_price"]
        has_live   = q["has_live_today"]
        live_date  = q["live_date"]

        prev_change     = q["last_daily"] - prev_close
        prev_change_pct = (prev_change / prev_close * 100) if prev_close else 0.0
        today_change    = (live_price - prev_close) if has_live else 0.0
        today_pnl       = today_change * it["shares"] * rate
        mv_usd          = live_price * it["shares"]
        cost_usd        = it["cost"] * it["shares"]
        unreal_usd      = mv_usd - cost_usd
        unreal_pct      = (unreal_usd / cost_usd * 100) if cost_usd else 0.0
        quote_day       = str(live_date) if live_date else "—"
        mkt_status      = "盤中✅" if has_live else "收盤"

        rows.append({
            "代號": code, "類型": "美股", "幣別": "USD",
            "現價": live_price,
            "上一交易日漲跌": prev_change, "上一交易日幅度%": prev_change_pct,
            "報價日": quote_day, "市場狀態": mkt_status,
            "今日損益(TWD)": today_pnl,
            "市值(TWD)": mv_usd * rate,
            "未實現損益(TWD)": unreal_usd * rate, "未實現報酬%": unreal_pct,
        })

    # ── 加密貨幣 ──
    for code, qty, cost_per in crypto_tuple:
        if qty <= 0 or code not in cr_prices:
            if code not in cr_prices:
                errors.append(f"幣圈抓不到：{code}")
            continue
        last_close, prev_close, last_date = cr_prices[code]
        change     = last_close - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0.0
        mv_usd     = last_close * qty
        cost_usd   = cost_per  * qty
        unreal_usd = mv_usd - cost_usd
        unreal_pct = (unreal_usd / cost_usd * 100) if cost_usd else 0.0

        rows.append({
            "代號": code.replace("-USD", ""), "類型": "Crypto(24h)", "幣別": "USD",
            "現價": last_close,
            "上一交易日漲跌": change, "上一交易日幅度%": change_pct,
            "報價日": str(last_date), "市場狀態": "24h",
            "今日損益(TWD)": (change * qty) * rate,
            "市值(TWD)": mv_usd * rate,
            "未實現損益(TWD)": unreal_usd * rate, "未實現報酬%": unreal_pct,
        })

    df = pd.DataFrame(rows)
    return df, errors

# =========================
# 7) 執行計算
# =========================
st.write("🔄 正在批次取得最新報價（速度已最佳化）...")

rate, rate_src = get_usdtwd()

crypto_tuple = (
    ("BTC-USD", btc_qty, btc_cost),
    ("ETH-USD", eth_qty, eth_cost),
    ("SOL-USD", sol_qty, sol_cost),
)

# 把 portfolio 轉成 hashable tuple of tuple
tw_hashable = tuple(tuple(sorted(r.items())) for r in tw_portfolio)
us_hashable = tuple(tuple(sorted(r.items())) for r in us_portfolio)

df, errors = build_df(tw_hashable, us_hashable, crypto_tuple, rate)

# ── 計算匯總 ──
cash_total_twd   = cash_twd_bank + cash_twd_physical + cash_twd_max + (cash_usd * rate)
stock_crypto_total = float(df["市值(TWD)"].sum()) if not df.empty else 0.0
total_assets     = stock_crypto_total + cash_total_twd
invested_assets  = total_assets - cash_twd_bank - cash_twd_max - cash_twd_physical

unreal_tw     = float(df[df["類型"] == "台股"]["未實現損益(TWD)"].sum())          if not df.empty else 0.0
unreal_us     = float(df[df["類型"] == "美股"]["未實現損益(TWD)"].sum())          if not df.empty else 0.0
unreal_crypto = float(df[df["類型"].str.contains("Crypto")]["未實現損益(TWD)"].sum()) if not df.empty else 0.0

real_tw_twd     = float(realized_twd)
real_us_twd     = float(realized_us_stock) * rate
real_crypto_twd = float(realized_crypto)   * rate

profit_tw_total     = unreal_tw     + real_tw_twd
profit_us_total     = unreal_us     + real_us_twd
profit_crypto_total = unreal_crypto + real_crypto_twd
total_profit        = profit_tw_total + profit_us_total + profit_crypto_total

invested_approx    = total_assets - total_profit
return_rate_approx = (total_profit / invested_approx * 100) if invested_approx > 0 else 0.0

today_change     = float(df["今日損益(TWD)"].sum()) if not df.empty else 0.0
today_change_pct = (today_change / total_assets * 100) if total_assets else 0.0

if not df.empty and total_assets > 0:
    df["佔比%"] = df["市值(TWD)"] / total_assets * 100
else:
    if not df.empty:
        df["佔比%"] = 0.0

# ── 儲存每日快照 ──
save_snapshot(total_assets, invested_assets, total_profit)

# =========================
# 8) 指標區
# =========================
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🏆 總資產(TWD)",        f"${total_assets:,.0f}")
c2.metric("🎯 投資總額(TWD)",      f"${invested_assets:,.0f}")
c3.metric("💰 總獲利(含已實現)",   f"${total_profit:,.0f}", delta=f"{return_rate_approx:.2f}% (近似)")

# 今日變動：休市時顯示灰色說明
if today_change == 0:
    c4.metric("📅 今日/24h變動", "$0", delta="休市中（無盤中資料）")
else:
    c4.metric("📅 今日/24h變動", f"${today_change:,.0f}", delta=f"{today_change_pct:.2f}%")

c5.metric("💱 USD/TWD", f"{rate:.2f}", delta=rate_src)

st.markdown("---")

# =========================
# 9) 損益結構
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
# 10) 圓餅圖 + 明細表
# =========================
left, right = st.columns([0.35, 0.65])

with left:
    st.subheader("🍰 資產配置圓餅圖")

    chart_rows = []
    if not df.empty:
        for _, r in df.iterrows():
            chart_rows.append({"項目": r["代號"], "市值": r["市值(TWD)"]})
    if cash_twd_bank     > 0: chart_rows.append({"項目": "銀行存款",    "市值": cash_twd_bank})
    if cash_twd_physical > 0: chart_rows.append({"項目": "實體現鈔",    "市值": cash_twd_physical})
    if cash_twd_max      > 0: chart_rows.append({"項目": "MAX 交易所",  "市值": cash_twd_max})
    if cash_usd          > 0: chart_rows.append({"項目": "美金(折台)",   "市值": cash_usd * rate})

    chart_df = pd.DataFrame(chart_rows)
    if chart_df.empty:
        st.warning("目前沒有可顯示的資產。")
    else:
        fig = px.pie(
            chart_df, values="市值", names="項目", hole=0.4,
            title=f"總資產: ${total_assets:,.0f} TWD"
        )
        # 小切片只顯示百分比，hover 再顯示名稱，避免 label 重疊
        fig.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate="<b>%{label}</b><br>市值: $%{value:,.0f}<br>佔比: %{percent}<extra></extra>",
        )
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("📋 持倉明細（市值/損益統一 TWD）")

    if df.empty:
        st.warning("沒有抓到任何行情資料。")
    else:
        show = df[[
            "代號", "類型", "幣別", "現價",
            "上一交易日漲跌", "上一交易日幅度%",
            "市值(TWD)", "佔比%",
            "今日損益(TWD)",
            "未實現報酬%", "未實現損益(TWD)",
            "報價日", "市場狀態"
        ]].copy()

        def color_style(v):
            if isinstance(v, (int, float)):
                if v > 0: return "color: #FF4B4B; font-weight: bold"   # 紅=漲（台灣習慣）
                if v < 0: return "color: #00C853; font-weight: bold"   # 綠=跌
                return "color: gray"
            return ""

        # 休市時「今日損益」顯示為灰色，避免誤解
        def today_pnl_style(v):
            if isinstance(v, (int, float)):
                if v == 0: return "color: gray"
                return color_style(v)
            return ""

        styled = (
            show.style
            .map(color_style, subset=["上一交易日漲跌", "上一交易日幅度%", "未實現報酬%", "未實現損益(TWD)"])
            .map(today_pnl_style, subset=["今日損益(TWD)"])
            .format({
                "現價":           "{:.2f}",
                "上一交易日漲跌":  "{:+.2f}",
                "上一交易日幅度%": "{:+.2f}%",
                "市值(TWD)":      "${:,.0f}",
                "佔比%":          "{:.1f}%",
                "今日損益(TWD)":  "${:,.0f}",
                "未實現報酬%":    "{:+.2f}%",
                "未實現損益(TWD)":"${:,.0f}",
            })
        )
        st.dataframe(styled, use_container_width=True, height=520, hide_index=True)

st.divider()

# =========================
# 11) 歷史資產走勢圖（新增）
# =========================
st.subheader("📈 歷史資產走勢")

history = load_history()
if len(history) < 2:
    st.info("資料累積中…每天開啟儀表板會自動記錄一筆快照，累積 2 天後即可看到走勢圖。")
else:
    hist_df = pd.DataFrame(history)
    hist_df["date"] = pd.to_datetime(hist_df["date"])

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=hist_df["date"], y=hist_df["total"],
        name="總資產", mode="lines+markers",
        line=dict(color="#4C9BE8", width=2),
        hovertemplate="%{x|%Y-%m-%d}<br>總資產: $%{y:,.0f}<extra></extra>",
    ))
    fig2.add_trace(go.Scatter(
        x=hist_df["date"], y=hist_df["profit"],
        name="累積獲利", mode="lines+markers",
        line=dict(color="#FF4B4B", width=2, dash="dot"),
        hovertemplate="%{x|%Y-%m-%d}<br>累積獲利: $%{y:,.0f}<extra></extra>",
    ))
    fig2.update_layout(
        xaxis_title="日期",
        yaxis_title="TWD",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=380,
    )
    st.plotly_chart(fig2, use_container_width=True)

# =========================
# 12) 抓價錯誤區
# =========================
if errors:
    with st.expander("⚠️ 抓價/資料警告", expanded=False):
        for e in errors:
            st.write("-", e)
