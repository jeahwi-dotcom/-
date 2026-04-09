import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. 앱 설정 및 타이틀
st.set_page_config(page_title="Retirement Traveler", layout="wide")

st.title("📊 Retirement Traveler")
st.subheader("하이퍼 매트릭스 & 코스톨라니 달걀 게이지")
st.divider()

# --- 하이퍼 매트릭스 데이터 정의 (기존 유지) ---
RSI_MATRIX = [(75, 0.02), (70, 0.05), (65, 0.08), (60, 0.12), (55, 0.20), (52, 0.30), (48, 0.45), (45, 0.65), (42, 0.85), (40, 1.10), (38, 1.35), (35, 1.60), (32, 1.90), (30, 2.20), (25, 2.60), (0, 3.20)]
MDD_MATRIX = [(0.5, 0.02), (1, 0.05), (2, 0.10), (3, 0.15), (4, 0.25), (5, 0.35), (6, 0.50), (8, 0.75), (10, 1.00), (12, 1.30), (14, 1.60), (16, 1.90), (18, 2.30), (20, 2.70), (25, 3.20), (999, 4.00)]
VIX_MATRIX = [(10, 0.02), (12, 0.05), (14, 0.08), (16, 0.12), (18, 0.20), (20, 0.30), (22, 0.45), (24, 0.60), (26, 0.80), (28, 1.00), (30, 1.30), (33, 1.60), (36, 2.00), (40, 2.50), (45, 3.00), (999, 3.50)]

# 2. 투자 설정 입력창
with st.sidebar:
    st.header("⚙️ 투자 설정")
    total_budget = st.number_input("총 투자 예산 (KRW)", value=10000000, step=1000000)
    invest_period = st.number_input("매수 기간 (일)", value=100, min_value=1)
    base_amount = total_budget / invest_period
    st.info(f"일일 기본 매수액: {base_amount:,.0f}원")

# 3. 실시간 데이터 로드 함수 (기존 유지)
@st.cache_data(ttl=600)
def get_market_data():
    try:
        tickers = {"spy": "^GSPC", "vix": "^VIX", "ndq": "379810.KS", "sp5": "360750.KS"}
        data_raw = yf.download(list(tickers.values()), period="1y", interval="1d", progress=False)
        close_data = data_raw['Close'] if isinstance(data_raw.columns, pd.MultiIndex) else data_raw
        def calc_indicators(series):
            series = series.dropna()
            delta = series.diff(); gain = (delta.where(delta > 0, 0)).rolling(window=14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]; peak = series.cummax(); mdd = ((series - peak) / peak * 100).iloc[-1]
            return float(rsi), float(mdd), float(series.iloc[-1])
        rsi_spy, mdd_spy, price_spy = calc_indicators(close_data[tickers["spy"]])
        rsi_ndq, mdd_ndq, price_ndq = calc_indicators(close_data[tickers["ndq"]])
        rsi_sp5, mdd_sp5, price_sp5 = calc_indicators(close_data[tickers["sp5"]])
        current_vix = float(close_data[tickers["vix"]].dropna().iloc[-1])
        return {"vix": current_vix, "spy": {"price": price_spy, "rsi": rsi_spy, "mdd": mdd_spy}, "ndq": {"price": price_ndq, "rsi": rsi_ndq, "mdd": mdd_ndq}, "sp5": {"price": price_sp5, "rsi": rsi_sp5, "mdd": mdd_sp5}}
    except: return None

def get_weight_rsi(val, matrix):
    for b, w in matrix:
        if val >= b: return w
    return matrix[-1][1]
def get_weight_std(val, matrix):
    for b, w in matrix:
        if val <= b: return w
    return matrix[-1][1]

# 4. 실행 및 메인 UI
data = get_market_data()
if data:
    # --- [상단 섹션] 시장 지표와 달걀 바늘 ---
    col_stat, col_gauge = st.columns([1, 1])

    with col_stat:
        st.markdown("### 🏛️ 실시간 시장 지표")
        st.metric("S&P 500 지수", f"{data['spy']['price']:,.2f}")
        m1, m2, m3 = st.columns(3)
        m1.metric("VIX", f"{data['vix']:.2f}")
        m2.metric("RSI", f"{data['spy']['rsi']:.1f}")
        m3.metric("MDD", f"{data['spy']['mdd']:.1f}%")

    with col_gauge:
        # 코스톨라니 달걀 바늘 (Plotly Gauge)
        # RSI와 VIX를 조합하여 0(바닥) ~ 100(천장) 지수화
        market_score = (data['spy']['rsi'] + (100 - (data['vix']*2))) / 2 # 단순 예시 로직
        market_score = max(0, min(100, market_score)) # 0~100 제한

        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = market_score,
            title = {'text': "코스톨라니 달걀 위치 (바늘)"},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1},
                'bar': {'color': "white"},
                'steps': [
                    {'range': [0, 25], 'color': "#00CCFF", 'name': "바닥(A1)"},
                    {'range': [25, 50], 'color': "#00FF66", 'name': "상승(A2)"},
                    {'range': [50, 75], 'color': "#FFAA00", 'name': "과열(A3)"},
                    {'range': [75, 100], 'color': "#FF4B4B", 'name': "천장(B1)"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': market_score}
            }
        ))
        fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=0), paper_bgcolor="#0E1117", font={'color': "white"})
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- [하단 섹션] 종목별 권장 매수액 ---
    c = get_weight_std(data['vix'], VIX_MATRIX)
    col1, col2 = st.columns(2)

    with col1:
        st.info("### 🇰🇷 KODEX 미국나스닥100")
        total_ndq = get_weight_rsi(data['ndq']['rsi'], RSI_MATRIX) + get_weight_std(abs(data['ndq']['mdd']), MDD_MATRIX) + c
        st.markdown(f'<div style="background-color:#1E1E1E;padding:30px;border-radius:15px;border:2px solid #00CCFF;text-align:center;"><h1 style="color:#00CCFF;margin:0;">{(base_amount * total_ndq):,.0f} 원</h1><p style="color:#888;">지표 합산: {total_ndq:.2f}배</p></div>', unsafe_allow_html=True)

    with col2:
        st.success("### 🇰🇷 TIGER 미국S&P500")
        total_sp5 = get_weight_rsi(data['sp5']['rsi'], RSI_MATRIX) + get_weight_std(abs(data['sp5']['mdd']), MDD_MATRIX) + c
        st.markdown(f'<div style="background-color:#1E1E1E;padding:30px;border-radius:15px;border:2px solid #EAFF00;text-align:center;"><h1 style="color:#EAFF00;margin:0;">{(base_amount * total_sp5):,.0f} 원</h1><p style="color:#888;">지표 합산: {total_sp5:.2f}배</p></div>', unsafe_allow_html=True)

else:
    st.warning("데이터 로딩 중...")
