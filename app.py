import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정
st.set_page_config(page_title="Retirement Traveler", layout="wide")

st.title("📊 Retirement Traveler")
st.subheader("S&P 500 실시간 시장 지표 상황")
st.caption("외부 라이브러리 충돌을 제거한 초정밀 실시간 연동 시스템")
st.divider()

# 2. 사이드바: 투자 설정
st.sidebar.header("💰 나의 투자 설정")
total_budget = st.sidebar.number_input("총 투자 예산 (KRW)", value=80000000, step=1000000)
invest_period = st.sidebar.number_input("매수 기간 (일)", value=180, min_value=1)
base_amount = total_budget / invest_period

st.sidebar.divider()
st.sidebar.write(f"📍 **일일 기본 매수액:** {base_amount:,.0f}원")

# 3.  데이터 호출 및 지표 산출 함수
@st.cache_data(ttl=600) # 10분마다 자동 갱신
def get_safe_metrics():
    try:
        # 데이터 다운로드 (최신 yfinance 구조 대응)
        spy = yf.download("^GSPC", period="1y", interval="1d", progress=False)
        vix = yf.download("^VIX", period="5d", interval="1d", progress=False)

        if spy.empty or vix.empty:
            return None

        # [중요] Multi-index 컬럼을 단일 컬럼으로 강제 변환 (에러 방지 핵심)
        if isinstance(spy.columns, pd.MultiIndex):
            spy.columns = spy.columns.get_level_values(0)
        if isinstance(vix.columns, pd.MultiIndex):
            vix.columns = vix.columns.get_level_values(0)

        close = spy['Close'].dropna()
        
        # --- 지표 직접 연동 (계산 오차 최소화) ---
        
        # 1. RSI 직접 산출 (웹 지표와 동일 로직)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_val = 100 - (100 / (1 + rs)).iloc[-1]

        # 2. MDD 산출 (전고점 대비 현재가)
        peak = close.cummax()
        mdd_val = ((close - peak) / peak * 100).iloc[-1]

        # 3. 실시간 가격 및 VIX
        current_price = close.iloc[-1]
        current_vix = vix['Close'].dropna().iloc[-1]

        return {
            "sp500": float(current_price),
            "vix": float(current_vix),
            "mdd": float(mdd_val),
            "rsi": float(rsi_val)
        }
    except Exception as e:
        # 에러 발생 시 화면에 상세 원인 출력 (디버깅용)
        st.sidebar.error(f"시스템 로그: {e}")
        return None

# 4. 화면 출력
data = get_safe_metrics()

if data:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("S&P 500 (현재가)", f"{data['sp500']:,.2f}")
    
    with col2:
        st.metric("VIX (공포지수)", f"{data['vix']:.2f}")
        
    with col3:
        st.metric("MDD (최대낙폭)", f"{data['mdd']:.2f}%")
        
    with col4:
        st.metric("RSI (과매도지표)", f"{data['rsi']:.2f}")
    
    st.info("💡 데이터는 Yahoo Finance 실시간 시세를 기반으로 10분마다 자동 갱신됩니다.")
else:
    st.warning("⚠️ 현재 시장 데이터를 가져오는 중입니다. 잠시 후 [Reboot] 혹은 새로고침을 해주세요.")

st.divider()

# 5. 가중치 로직 함수
def calculate_weights(v, m, r):
    # VIX 가중치
    if v >= 35: v_w = 3.0
    elif v >= 28: v_w = 2.2
    elif v >= 22: v_w = 1.5
    elif v >= 18: v_w = 1.0
    else: v_w = 0.6

    # MDD 가중치
    if m <= -20: m_w = 5.0
    elif m <= -15: m_w = 3.5
    elif m <= -10: m_w = 2.5
    elif m <= -5: m_w = 1.5
    elif m <= -2: m_w = 0.8
    else: m_w = 0.3

    # RSI 가중치
    if r <= 25: r_w = 4.0
    elif r <= 35: r_w = 3.0
    elif r <= 45: r_w = 1.8
    elif r <= 55: r_w = 1.0
    elif r <= 65: r_w = 0.6
    else: r_w = 0.3
    
    return v_w, m_w, r_w

# 데이터 호출 및 대시보드 출력
data = get_safe_market_data()

if data:
    # --- 상단 실시간 지표 대시보드 ---
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: st.metric("S&P 500", f"{data['sp500']:,.2f}")
    with col_m2: st.metric("VIX (공포지수)", f"{data['vix']:.2f}")
    with col_m3: st.metric("MDD (낙폭)", f"{data['mdd']:.2f}%")
    with col_m4: st.metric("RSI (강도)", f"{data['rsi']:.2f}")
    st.divider()

    # --- 최종 매수액 계산 ---
    v_w, m_w, r_w = calculate_weights(data['vix'], data['mdd'], data['rsi'])
    total_weight = v_w + m_w + r_w
    final_buy_amount = base_amount * total_weight

    st.subheader("📢 오늘의 권장 매수 안내")
    
    # 강조 상자 디자인
    st.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 30px; border-radius: 15px; border: 2px solid #EAFF00; text-align: center;">
            <p style="color: white; font-size: 1.2rem; margin-bottom: 10px;">오늘의 최종 매수액</p>
            <h1 style="color: #EAFF00; font-size: 3.5rem; margin: 0;">{final_buy_amount:,.0f} 원</h1>
            <p style="color: #888; font-size: 1rem; margin-top: 10px;">적용된 총 가중치 배수: <b>{total_weight:.2f}배</b></p>
        </div>
    """, unsafe_allow_html=True)

    # 세부 내역 확인
    with st.expander("🔍 가중치 산정 상세 내역"):
        st.write(f"- 기본 일일 매수액: {base_amount:,.0f}원")
        st.write(f"- VIX 가중치 (+): {v_w}")
        st.write(f"- MDD 가중치 (+): {m_w}")
        st.write(f"- RSI 가중치 (+): {r_w}")
        st.info("공식: 기본 매수액 × (VIX 가중치 + MDD 가중치 + RSI 가중치)")
else:
    st.warning("⚠️ 시장 데이터를 불러오는 중입니다. 잠시 후 새로고침(F5)을 해주세요.")

