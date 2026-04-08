import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정 및 타이틀
st.set_page_config(page_title="Retirement Traveler", layout="wide")

st.title("📊 Retirement Traveler")
st.subheader("종목별 하이퍼 매트릭스 분할매수 시스템")
st.caption("공식: 종목별 매수액 = 기본 매수액 × (해당종목 RSI 배수 + 해당종목 MDD 배수 + 시장 VIX 배수)")
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
st.info(f"📍 **일일 기본 매수액:** {base_amount:,.0f}원 (종목별 개별 산출 기준)")
st.divider()

# 3. 실시간 데이터 로드 및 지표 계산 함수
@st.cache_data(ttl=600)
def get_market_data():
    try:
        tickers = {
            "vix": "^VIX", 
            "kodex_ndq": "379810.KS", # KODEX 미국나스닥100(A379810)
            "tiger_sp5": "360750.KS"    # TIGER 미국S&P500
        }
        
        data_raw = yf.download(list(tickers.values()), period="1y", interval="1d", progress=False)
        close_data = data_raw['Close'] if isinstance(data_raw.columns, pd.MultiIndex) else data_raw

        def calc_indicators(series):
            series = series.dropna()
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
            peak = series.cummax()
            mdd = ((series - peak) / peak * 100).iloc[-1]
            return float(rsi), float(mdd), float(series.iloc[-1])

        rsi_ndq, mdd_ndq, price_ndq = calc_indicators(close_data[tickers["kodex_ndq"]])
        rsi_sp5, mdd_sp5, price_sp5 = calc_indicators(close_data[tickers["tiger_sp5"]])
        current_vix = float(close_data[tickers["vix"]].dropna().iloc[-1])

        return {
            "vix": current_vix,
            "ndq": {"price": price_ndq, "rsi": rsi_ndq, "mdd": mdd_ndq},
            "sp5": {"price": price_sp5, "rsi": rsi_sp5, "mdd": mdd_sp5}
        }
    except Exception as e:
        st.error(f"데이터 로드 에러: {e}")
        return None

# 4. 하이퍼 매트릭스 로직 함수
def get_matrix_weight_rsi(val, matrix):
    for boundary, weight in matrix:
        if val >= boundary: return weight
    return matrix[-1][1]

def get_matrix_weight_std(val, matrix):
    for boundary, weight in matrix:
        if val <= boundary: return weight
    return matrix[-1][1]

# 5. 실행 및 결과 출력
data = get_market_data()

if data:
    # --- [섹션 1] 시장 공포 지표 ---
    st.markdown("### 🏛️ 시장 변동성 지표")
    st.metric("VIX (공포지수)", f"{data['vix']:.2f}")
    st.divider()

    # 가중치 계산 (VIX는 공통 적용)
    c = get_matrix_weight_std(data['vix'], VIX_MATRIX)

    # --- [섹션 2] 종목별 상세 지표 및 매수액 산출 ---
    col1, col2 = st.columns(2)

    # KODEX 미국나스닥100 계산
    with col1:
        st.info("### 🇰🇷 KODEX 미국나스닥100")
        st.write(f"현재가: **{data['ndq']['price']:,.0f}원**")
        st.write(f"RSI: {data['ndq']['rsi']:.2f} / MDD: {data['ndq']['mdd']:.2f}%")
        
        a_ndq = get_matrix_weight_rsi(data['ndq']['rsi'], RSI_MATRIX)
        b_ndq = get_matrix_weight_std(abs(data['ndq']['mdd']), MDD_MATRIX)
        total_ndq = a_ndq + b_ndq + c
        amount_ndq = base_amount * total_ndq
        
        st.markdown(f"""
            <div style="background-color: #1E1E1E; padding: 20px; border-radius: 10px; border: 2px solid #00CCFF; text-align: center;">
                <p style="color: white; margin-bottom: 5px;">나스닥100 권장 매수액</p>
                <h2 style="color: #00CCFF; margin: 0;">{amount_ndq:,.0f} 원</h2>
                <p style="color: #888; font-size: 0.8rem; margin-top: 5px;">합산 배수: {total_ndq:.2f}배</p>
            </div>
        """, unsafe_allow_html=True)

    # TIGER 미국S&P500 계산
    with col2:
        st.success("### 🇰🇷 TIGER 미국S&P500")
        st.write(f"현재가: **{data['sp5']['price']:,.0f}원**")
        st.write(f"RSI: {data['sp5']['rsi']:.2f} / MDD: {data['sp5']['mdd']:.2f}%")
        
        a_sp5 = get_matrix_weight_rsi(data['sp5']['rsi'], RSI_MATRIX)
        b_sp5 = get_matrix_weight_std(abs(data['sp5']['mdd']), MDD_MATRIX)
        total_sp5 = a_sp5 + b_sp5 + c
        amount_sp5 = base_amount * total_sp5
        
        st.markdown(f"""
            <div style="background-color: #1E1E1E; padding: 20px; border-radius: 10px; border: 2px solid #EAFF00; text-align: center;">
                <p style="color: white; margin-bottom: 5px;">S&P500 권장 매수액</p>
                <h2 style="color: #EAFF00; margin: 0;">{amount_sp5:,.0f} 원</h2>
                <p style="color: #888; font-size: 0.8rem; margin-top: 5px;">합산 배수: {total_sp5:.2f}배</p>
            </div>
        """, unsafe_allow_html=True)

    with st.expander("🔍 상세 가중치 데이터 확인"):
        st.write(f"- 공통 VIX 배수(c): {c}")
        st.write(f"- 나스닥100 배수: RSI(a) {a_ndq} + MDD(b) {b_ndq}")
        st.write(f"- S&P500 배수: RSI(a) {a_sp5} + MDD(b) {b_sp5}")
else:
    st.warning("데이터를 불러오는 중입니다...")
