import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정
st.set_page_config(page_title="Retirement Traveler", layout="wide")

st.title("📊 Retirement Traveler")
st.subheader("S&P 500 실시간 분할매수 시스템")
st.divider()

# 2. 사이드바 설정
st.sidebar.header("💰 나의 투자 설정")
total_budget = st.sidebar.number_input("총 투자 예산 (KRW)", value=80000000, step=1000000)
invest_period = st.sidebar.number_input("매수 기간 (일)", value=180, min_value=1)
base_amount = total_budget / invest_period

# 3. 데이터 로드 함수 (이 부분이 반드시 data = ... 호출보다 위에 있어야 합니다)
@st.cache_data(ttl=600)
def get_safe_market_data():
    try:
        spy = yf.download("^GSPC", period="1y", interval="1d", progress=False)
        vix = yf.download("^VIX", period="5d", interval="1d", progress=False)
        if spy.empty or vix.empty: return None

        if isinstance(spy.columns, pd.MultiIndex):
            spy.columns = spy.columns.get_level_values(0)
        if isinstance(vix.columns, pd.MultiIndex):
            vix.columns = vix.columns.get_level_values(0)

        close = spy['Close'].dropna()
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_val = 100 - (100 / (1 + rs)).iloc[-1]
        peak = close.cummax()
        mdd_val = ((close - peak) / peak * 100).iloc[-1]
        current_price = close.iloc[-1]
        current_vix = vix['Close'].dropna().iloc[-1]

        return {"sp500": float(current_price), "vix": float(current_vix), "mdd": float(mdd_val), "rsi": float(rsi_val)}
    except Exception as e:
        return None

# 4. 가중치 로직
def calculate_weights(v, m, r):
    v_w = 3.0 if v >= 35 else 2.2 if v >= 28 else 1.5 if v >= 22 else 1.0 if v >= 18 else 0.6
    m_w = 5.0 if m <= -20 else 3.5 if m <= -15 else 2.5 if m <= -10 else 1.5 if m <= -5 else 0.8 if m <= -2 else 0.3
    r_w = 4.0 if r <= 25 else 3.0 if r <= 35 else 1.8 if r <= 45 else 1.0 if r <= 55 else 0.6 if r <= 65 else 0.3
    return v_w, m_w, r_w

# 5. 실행 및 출력
data = get_safe_market_data() # 여기서 에러가 났다면 위 함수 정의가 안 된 것입니다.

if data:
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: st.metric("S&P 500", f"{data['sp500']:,.2f}")
    with col_m2: st.metric("VIX", f"{data['vix']:.2f}")
    with col_m3: st.metric("MDD", f"{data['mdd']:.2f}%")
    with col_m4: st.metric("RSI", f"{data['rsi']:.2f}")
    
    v_w, m_w, r_w = calculate_weights(data['vix'], data['mdd'], data['rsi'])
    total_weight = v_w + m_w + r_w
    final_buy = base_amount * total_weight

    st.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 30px; border-radius: 15px; border: 2px solid #EAFF00; text-align: center;">
            <p style="color: white; margin-bottom: 10px;">오늘의 최종 매수액</p>
            <h1 style="color: #EAFF00; font-size: 3rem; margin: 0;">{final_buy:,.0f} 원</h1>
        </div>
    """, unsafe_allow_html=True)
else:
    st.warning("데이터 로딩 중... 잠시만 기다려주세요.")
