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

# 3. 화면 출력
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
