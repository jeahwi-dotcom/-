import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정 및 타이틀
st.set_page_config(page_title="Retirement Traveler", layout="wide")

st.title("📊 Retirement Traveler")
st.subheader("S&P 500 실시간 하이퍼 매트릭스 분할매수 시스템")
st.caption("공식: 오늘의 최종 매수액 = 기본 매수액 × (RSI 배수 + MDD 배수 + VIX 배수)")
st.divider()

# --- 하이퍼 매트릭스 데이터 정의 ---
RSI_MATRIX = [
    (75, 0.02), (70, 0.05), (65, 0.08), (60, 0.12), (55, 0.20),
    (52, 0.30), (48, 0.45), (45, 0.65), (42, 0.85), (40, 1.10),
    (38, 1.35), (35, 1.60), (32, 1.90), (30, 2.20), (25, 2.60), (0, 3.20)
]

MDD_MATRIX = [
    (0.5, 0.02), (1, 0.05), (2, 0.10), (3, 0.15), (4, 0.25),
    (5, 0.35), (6, 0.50), (8, 0.75), (10, 1.00), (12, 1.30),
    (14, 1.60), (16, 1.90), (18, 2.30), (20, 2.70), (25, 3.20), (999, 4.00)
]

VIX_MATRIX = [
    (10, 0.02), (12, 0.05), (14, 0.08), (16, 0.12), (18, 0.20),
    (20, 0.30), (22, 0.45), (24, 0.60), (26, 0.80), (28, 1.00),
    (30, 1.30), (33, 1.60), (36, 2.00), (40, 2.50), (45, 3.00), (999, 3.50)
]

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

# 3. 실시간 데이터 로드 함수
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

# 4. 하이퍼 매트릭스 기반 배수 추출 로직
def get_matrix_weight_rsi(val, matrix):
    # RSI용: 내림차순 경계값 확인 (75부터 내려감)
    for boundary, weight in matrix:
        if val >= boundary:
            return weight
    return matrix[-1][1]

def get_matrix_weight_std(val, matrix):
    # MDD, VIX용: 오름차순 경계값 확인 (0.5부터 올라감)
    for boundary, weight in matrix:
        if val <= boundary:
            return weight
    return matrix[-1][1]

# 5. 실행 및 결과 출력
data = get_market_data()

if data:
    # 시장 지표 메트릭 표시
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: st.metric("S&P 500", f"{data['sp500']:,.2f}")
    with col_m2: st.metric("VIX (변동성)", f"{data['vix']:.2f}")
    with col_m3: st.metric("MDD (하락폭)", f"{data['mdd']:.2f}%")
    with col_m4: st.metric("RSI (상대강도)", f"{data['rsi']:.2f}")
    st.divider()

    # 하이퍼 매트릭스 기반 배수 산출
    a = get_matrix_weight_rsi(data['rsi'], RSI_MATRIX)
    b = get_matrix_weight_std(abs(data['mdd']), MDD_MATRIX)
    c = get_matrix_weight_std(data['vix'], VIX_MATRIX)
    
    # [수정된 공식 적용] 나누기 없이 합산 배수를 곱함
    total_multiplier = a + b + c
    final_amount = base_amount * total_multiplier

    st.subheader("📢 하이퍼 매트릭스 최종 산출 결과")
    
    # 결과 시각화 레이아웃
    st.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 40px; border-radius: 20px; border: 3px solid #EAFF00; text-align: center;">
            <p style="color: white; font-size: 1.4rem; margin-bottom: 15px;">최종 매수 금액</p>
            <h1 style="color: #EAFF00; font-size: 4.5rem; margin: 0;">{final_amount:,.0f} 원</h1>
            <p style="color: #888; font-size: 1.1rem; margin-top: 20px;">
                합산 가중치 (a + b + c): <b>{total_multiplier:.2f}배</b><br>
                (RSI {a} + MDD {b} + VIX {c})
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 상세 계산 근거 확인 창
    with st.expander("🔍 지표별 매트릭스 매칭 상세 내역"):
        st.write(f"- **RSI 배수 (a):** {a} (현재 지수: {data['rsi']:.2f})")
        st.write(f"- **MDD 배수 (b):** {b} (현재 지수: {data['mdd']:.2f}%)")
        st.write(f"- **VIX 배수 (c):** {c} (현재 지수: {data['vix']:.2f})")
        st.write("---")
        st.write(f"**최종 계산식:** {base_amount:,.0f}원 × ({a} + {b} + {c}) = {final_amount:,.0f}원")
else:
    st.warning("시장 데이터를 연동하는 중입니다. 잠시만 기다려주세요.")

st.divider()
