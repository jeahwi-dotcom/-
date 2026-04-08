import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정 및 타이틀
st.set_page_config(page_title="Retirement Traveler", layout="wide")

st.title("📊 Retirement Traveler")
st.subheader("S&P 500 실시간 분할매수 시스템")
st.caption("공식: 오늘의 최종 매수액 = 기본 매수액 × (RSI 배수 + MDD 배수 + VIX 배수)")
st.divider()

# 2. 투자 설정 입력창
st.markdown("### 💰 나의 투자 설정")
col_input1, col_input2 = st.columns(2)

with col_input1:
    total_budget = st.number_input("총 투자 예산 (KRW)", value=80000000, step=1000000)

with col_input2:
    invest_period = st.number_input("매수 기간 (일)", value=180, min_value=1)

base_amount = total_budget / invest_period
st.info(f"📍 **일일 기본 매수액:** {base_amount:,.0f}원")
st.divider()

# 3. 실시간 데이터 로드 함수 (안정성 유지)
@st.cache_data(ttl=600)
def get_market_data():
    try:
        spy = yf.download("^GSPC", period="1y", interval="1d", progress=False)
        vix = yf.download("^VIX", period="5d", interval="1d", progress=False)
        
        if spy.empty or vix.empty: return None

        if isinstance(spy.columns, pd.MultiIndex): spy.columns = spy.columns.get_level_values(0)
        if isinstance(vix.columns, pd.MultiIndex): vix.columns = vix.columns.get_level_values(0)

        close = spy['Close'].dropna()
        
        # RSI 직접 계산
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_val = 100 - (100 / (1 + rs)).iloc[-1]
        
        # MDD 직접 계산
        peak = close.cummax()
        mdd_val = ((close - peak) / peak * 100).iloc[-1]
        
        current_vix = vix['Close'].dropna().iloc[-1]
        current_sp = close.iloc[-1]

        return {"vix": float(current_vix), "mdd": float(mdd_val), "rsi": float(rsi_val), "sp500": float(current_sp)}
    except:
        return None

# 4. 요청하신 새로운 구간별 배수 로직 (a, b, c)
def get_custom_weights(rsi, mdd, vix):
    # --- 1. RSI 배수 (a) ---
    if rsi >= 60:
        a = 0.1
    elif 50 <= rsi < 60:
        a = 0.3
    elif 45 <= rsi < 50:
        a = 0.7
    elif 35 <= rsi < 45:
        a = 1.3
    else: # 35 미만
        a = 2.0

    # --- 2. MDD 배수 (b) ---
    mdd_val = abs(mdd) # 음수를 양수로 변환하여 비교
    if mdd_val <= 2:
        b = 0.1
    elif 2 < mdd_val <= 5:
        b = 0.3
    elif 5 < mdd_val <= 10:
        b = 0.8
    elif 10 < mdd_val <= 15:
        b = 1.5
    else: # 15% 초과 하락 시
        b = 2.5

    # --- 3. VIX 배수 (c) ---
    if vix < 15:
        c = 0.1
    elif 15 <= vix < 20:
        c = 0.3
    elif 20 <= vix < 25:
        c = 0.5
    elif 25 <= vix < 35:
        c = 1.2
    else: # 35 초과
        c = 2.5
        
    return a, b, c

# 5. 실행 및 결과 출력
data = get_market_data()

if data:
    # 시장 지표 메트릭
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: st.metric("S&P 500", f"{data['sp500']:,.2f}")
    with col_m2: st.metric("VIX", f"{data['vix']:.2f}")
    with col_m3: st.metric("MDD", f"{data['mdd']:.2f}%")
    with col_m4: st.metric("RSI", f"{data['rsi']:.2f}")
    st.divider()

    # 새 수식 적용
    a, b, c = get_custom_weights(data['rsi'], data['mdd'], data['vix'])
    total_sum_weight = a + b + c
    final_amount = base_amount * total_sum_weight

    st.subheader("📢 오늘의 최종 매수액 산출 결과")
    
    # 강조 레이아웃
    st.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 40px; border-radius: 20px; border: 3px solid #EAFF00; text-align: center;">
            <p style="color: white; font-size: 1.4rem; margin-bottom: 15px;">최종 매수 금액</p>
            <h1 style="color: #EAFF00; font-size: 4.5rem; margin: 0;">{final_amount:,.0f} 원</h1>
            <p style="color: #888; font-size: 1.1rem; margin-top: 20px;">
                합산 배수 (a+b+c): <b>{total_sum_weight:.2f}배</b><br>
                (RSI {a} + MDD {b} + VIX {c})
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 상세 계산 근거
    with st.expander("🔍 지표별 배수 상세 확인"):
        st.write(f"- **RSI ({data['rsi']:.2f}):** a = {a}")
        st.write(f"- **MDD ({data['mdd']:.2f}%):** b = {b}")
        st.write(f"- **VIX ({data['vix']:.2f}):** c = {c}")
        st.write("---")
        st.write(f"**최종 계산:** {base_amount:,.0f}원 × ({a} + {b} + {c}) = {final_amount:,.0f}원")
else:
    st.warning("데이터를 불러오는 중입니다. 잠시만 기다려주세요.")

st.divider()
