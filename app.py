import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정 및 타이틀
st.set_page_config(page_title="Retirement Traveler", layout="wide")

st.title("📊 Retirement Traveler")
st.subheader("S&P 500 하이퍼 매트릭스 & 국내 ETF 개별 지표 시스템")
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

# 3. 실시간 데이터 로드 함수 (개별 지표 계산 로직 추가)
@st.cache_data(ttl=600)
def get_market_data():
    try:
        tickers = {
            "spy": "^GSPC", 
            "vix": "^VIX", 
            "kodex_ndq": "133690.KS", # KODEX 미국나스닥100
            "tiger_sp5": "360750.KS"    # TIGER 미국S&P500
        }
        
        # 데이터 통합 다운로드
        data_raw = yf.download(list(tickers.values()), period="1y", interval="1d", progress=False)
        close_data = data_raw['Close'] if isinstance(data_raw.columns, pd.MultiIndex) else data_raw

        # 지표 계산용 내부 함수
        def calc_indicators(series):
            series = series.dropna()
            # RSI
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
            # MDD
            peak = series.cummax()
            mdd = ((series - peak) / peak * 100).iloc[-1]
            return float(rsi), float(mdd), float(series.iloc[-1])

        # 각 종목별 지표 산출
        rsi_spy, mdd_spy, price_spy = calc_indicators(close_data[tickers["spy"]])
        rsi_ndq, mdd_ndq, price_ndq = calc_indicators(close_data[tickers["kodex_ndq"]])
        rsi_sp5, mdd_sp5, price_sp5 = calc_indicators(close_data[tickers["tiger_sp5"]])
        current_vix = float(close_data[tickers["vix"]].dropna().iloc[-1])

        return {
            "vix": current_vix, "sp500_price": price_spy, "rsi_spy": rsi_spy, "mdd_spy": mdd_spy,
            "ndq_price": price_ndq, "rsi_ndq": rsi_ndq, "mdd_ndq": mdd_ndq,
            "sp5_price": price_sp5, "rsi_sp5": rsi_sp5, "mdd_sp5": mdd_sp5
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
    # --- [섹션 1] 전체 시장 공포 지표 (매수 가이드용) ---
    st.markdown("### 🏛️ 시장 공포 지표 (S&P 500 기준)")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1: st.metric("S&P 500 지수", f"{data['sp500_price']:,.2f}")
    with col_s2: st.metric("VIX (변동성)", f"{data['vix']:.2f}")
    with col_s3: st.metric("S&P 500 RSI", f"{data['rsi_spy']:.2f}")
    with col_s4: st.metric("S&P 500 MDD", f"{data['mdd_spy']:.2f}%")
    st.divider()

    # --- [섹션 2] 국내 상장 ETF 개별 상태 ---
    st.markdown("### 🇰🇷 국내 상장 미국 ETF 개별 지표")
    col_k1, col_k2 = st.columns(2)
    
    with col_k1:
        st.info("**KODEX 미국나스닥100**")
        k_c1, k_c2, k_c3 = st.columns(3)
        k_c1.metric("현재가", f"{data['ndq_price']:,.0f}원")
        k_c2.metric("RSI", f"{data['rsi_ndq']:.2f}")
        k_c3.metric("MDD", f"{data['mdd_ndq']:.2f}%")

    with col_k2:
        st.success("**TIGER 미국S&P500**")
        t_c1, t_c2, t_c3 = st.columns(3)
        t_c1.metric("현재가", f"{data['sp5_price']:,.0f}원")
        t_c2.metric("RSI", f"{data['rsi_sp5']:.2f}")
        t_c3.metric("MDD", f"{data['mdd_sp5']:.2f}%")
    st.divider()

    # 가중치 산출 (기준은 S&P 500 지표 유지)
    a = get_matrix_weight_rsi(data['rsi_spy'], RSI_MATRIX)
    b = get_matrix_weight_std(abs(data['mdd_spy']), MDD_MATRIX)
    c = get_matrix_weight_std(data['vix'], VIX_MATRIX)
    
    total_multiplier = a + b + c
    final_amount = base_amount * total_multiplier

    st.subheader("📢 하이퍼 매트릭스 최종 권장 매수액")
    st.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 40px; border-radius: 20px; border: 3px solid #EAFF00; text-align: center;">
            <p style="color: white; font-size: 1.4rem; margin-bottom: 15px;">오늘의 매수 금액</p>
            <h1 style="color: #EAFF00; font-size: 4.5rem; margin: 0;">{final_amount:,.0f} 원</h1>
            <p style="color: #888; font-size: 1.1rem; margin-top: 20px;">
                합산 가중치 (a + b + c): <b>{total_multiplier:.2f}배</b><br>
                (RSI {a} + MDD {b} + VIX {c})
            </p>
        </div>
    """, unsafe_allow_html=True)

    with st.expander("🔍 매수액 산정 상세 근거"):
        st.write(f"- 기준 지표: **미국 S&P 500 (GSPC)**")
        st.write(f"- RSI 배수: {a} / MDD 배수: {b} / VIX 배수: {c}")
        st.write(f"- 공식: {base_amount:,.0f}원 × {total_multiplier:.2f}배")
else:
    st.warning("시장 데이터를 연동하는 중입니다. 잠시만 기다려주세요.")
