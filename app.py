import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정 및 타이틀
st.set_page_config(page_title="Retirement Traveler", layout="wide")

st.title("📊 Retirement Traveler")
st.subheader("S&P 500 실시간 분할매수 시스템")
st.caption("어머니의 은퇴 자산 운용을 위한 실시간 지표 연동형 가이드")
st.divider()

# 2. 투자 설정 입력창 (메인 화면 상단 배치)
st.markdown("### 💰 나의 투자 설정")
col_input1, col_input2 = st.columns(2)

with col_input1:
    total_budget = st.number_input("총 투자 예산 (KRW)", value=80000000, step=1000000, help="전체 투자하실 금액을 입력하세요.")

with col_input2:
    invest_period = st.number_input("매수 기간 (일)", value=180, min_value=1, help="며칠 동안 나누어 매수하실지 입력하세요.")

base_amount = total_budget / invest_period
st.info(f"📍 **일일 기본 매수액:** {base_amount:,.0f}원 (가중치 1.0 기준)")
st.divider()

# 3. 데이터 로드 함수 (캐싱 및 에러 방지)
@st.cache_data(ttl=600)
def get_safe_market_data():
    try:
        spy = yf.download("^GSPC", period="1y", interval="1d", progress=False)
        vix = yf.download("^VIX", period="5d", interval="1d", progress=False)
        
        if spy.empty or vix.empty:
            return None

        # Multi-index 컬럼 대응
        if isinstance(spy.columns, pd.MultiIndex):
            spy.columns = spy.columns.get_level_values(0)
        if isinstance(vix.columns, pd.MultiIndex):
            vix.columns = vix.columns.get_level_values(0)

        close = spy['Close'].dropna()
        
        # 지표 계산
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_val = 100 - (100 / (1 + rs)).iloc[-1]
        
        peak = close.cummax()
        mdd_val = ((close - peak) / peak * 100).iloc[-1]
        
        current_price = close.iloc[-1]
        current_vix = vix['Close'].dropna().iloc[-1]

        return {
            "sp500": float(current_price),
            "vix": float(current_vix),
            "mdd": float(mdd_val),
            "rsi": float(rsi_val)
        }
    except Exception as e:
        return None

# 4. 가중치 로직 함수
def calculate_weights(v, m, r):
    v_w = 3.0 if v >= 35 else 2.2 if v >= 28 else 1.5 if v >= 22 else 1.0 if v >= 18 else 0.6
    m_w = 5.0 if m <= -20 else 3.5 if m <= -15 else 2.5 if m <= -10 else 1.5 if m <= -5 else 0.8 if m <= -2 else 0.3
    r_w = 4.0 if r <= 25 else 3.0 if r <= 35 else 1.8 if r <= 45 else 1.0 if r <= 55 else 0.6 if r <= 65 else 0.3
    return v_w, m_w, r_w

# 5. 데이터 호출 및 결과 출력
data = get_safe_market_data()

if data:
    # 실시간 지표 대시보드
    st.markdown("### 📈 실시간 시장 지표")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: st.metric("S&P 500", f"{data['sp500']:,.2f}")
    with col_m2: st.metric("VIX (공포지수)", f"{data['vix']:.2f}")
    with col_m3: st.metric("MDD (낙폭)", f"{data['mdd']:.2f}%")
    with col_m4: st.metric("RSI (강도)", f"{data['rsi']:.2f}")
    st.divider()

    # 최종 매수액 계산
    v_w, m_w, r_w = calculate_weights(data['vix'], data['mdd'], data['rsi'])
    total_weight = v_w + m_w + r_w
    final_buy_amount = base_amount * total_weight

    st.subheader("📢 오늘의 권장 매수 안내")
    st.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 40px; border-radius: 20px; border: 3px solid #EAFF00; text-align: center; margin-bottom: 20px;">
            <p style="color: white; font-size: 1.4rem; margin-bottom: 15px;">오늘의 최종 매수액</p>
            <h1 style="color: #EAFF00; font-size: 4.5rem; margin: 0;">{final_buy_amount:,.0f} 원</h1>
            <p style="color: #888; font-size: 1.1rem; margin-top: 15px;">현재 합산 가중치: <b>{total_weight:.2f}배</b> (VIX:{v_w} + MDD:{m_w} + RSI:{r_w})</p>
        </div>
    """, unsafe_allow_html=True)

    with st.expander("ℹ️ 가중치 산정 기준 보기"):
        st.write("시장 공포(VIX), 전고점 대비 하락폭(MDD), 과매도 상태(RSI)를 합산하여 매수 강도를 결정합니다.")
        st.write(f"- 기본 매수액: {base_amount:,.0f}원 × {total_weight:.2f}배")
else:
    st.warning("⚠️ 시장 데이터를 불러오는 중입니다. 잠시 후 새로고침 해주세요.")
