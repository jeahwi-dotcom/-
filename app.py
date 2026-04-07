import streamlit as st
import yfinance as yf

# 1. 앱 타이틀 및 브랜딩
st.title("📊 Retirement Traveler")
st.subheader("S&P 500 실시간 투자 가이드")
st.caption("어머니의 안정적인 노후를 위한 정밀 분할매수 시스템")
st.divider()

# 2. 실시간 데이터 로드 함수
@st.cache_data(ttl=3600) # 1시간마다 갱신
def get_status_metrics():
    # 데이터 다운로드 (S&P 500 지수 및 VIX 지수)
    spy = yf.download("^GSPC", period="1y", interval="1d", progress=False)
    vix = yf.download("^VIX", period="5d", interval="1d", progress=False)
    
    close = spy['Close']
    
    # RSI 직접 계산
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi_val = 100 - (100 / (1 + rs)).iloc[-1]
    
    # MDD 계산
    rolling_max = close.cummax()
    mdd_val = ((close - rolling_max) / rolling_max * 100).iloc[-1]
    
    # 최신 수치 추출
    current_sp500 = close.iloc[-1]
    current_vix = vix['Close'].iloc[-1]
    
    return current_sp500, current_vix, mdd_val, rsi_val

# 3. 데이터 호출 및 화면 표시
try:
    sp500, vix_val, mdd_val, rsi_val = get_status_metrics()

    # 4분할 레이아웃 구성
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("S&P 500", f"{sp500:,.2f}")

    with col2:
        st.metric("VIX (공포지수)", f"{vix_val:.2f}")

    with col3:
        # MDD는 하락폭이므로 음수로 표시
        st.metric("MDD (낙폭)", f"{mdd_val:.2f}%")

    with col4:
        st.metric("RSI (강도)", f"{rsi_val:.2f}")

except Exception as e:
    st.error("실시간 데이터를 불러오는 중 오류가 발생했습니다.")

st.divider()
