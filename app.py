import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정 및 타이틀
st.set_page_config(page_title="Retirement Traveler", layout="wide")

# CSS로 달걀 모델 시각화 스타일 정의
st.markdown("""
    <style>
    .egg-container { display: flex; justify-content: space-around; align-items: center; background-color: #1e1e1e; padding: 20px; border-radius: 20px; margin: 10px 0; border: 1px solid #444; }
    .egg-phase { text-align: center; padding: 10px; border-radius: 10px; flex: 1; margin: 0 5px; border: 2px solid transparent; opacity: 0.4; }
    .active-phase { opacity: 1; border-color: #EAFF00; background-color: #333300; transform: scale(1.05); transition: all 0.3s; }
    .phase-title { font-weight: bold; font-size: 1.1rem; margin-bottom: 5px; }
    .phase-desc { font-size: 0.8rem; color: #ccc; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Retirement Traveler")
st.subheader("실시간 지표 & 코스톨라니 달걀 시계 대시보드")
st.divider()

# --- 하이퍼 매트릭스 데이터 정의 (기존 유지) ---
RSI_MATRIX = [(75, 0.02), (70, 0.05), (65, 0.08), (60, 0.12), (55, 0.20), (52, 0.30), (48, 0.45), (45, 0.65), (42, 0.85), (40, 1.10), (38, 1.35), (35, 1.60), (32, 1.90), (30, 2.20), (25, 2.60), (0, 3.20)]
MDD_MATRIX = [(0.5, 0.02), (1, 0.05), (2, 0.10), (3, 0.15), (4, 0.25), (5, 0.35), (6, 0.50), (8, 0.75), (10, 1.00), (12, 1.30), (14, 1.60), (16, 1.90), (18, 2.30), (20, 2.70), (25, 3.20), (999, 4.00)]
VIX_MATRIX = [(10, 0.02), (12, 0.05), (14, 0.08), (16, 0.12), (18, 0.20), (20, 0.30), (22, 0.45), (24, 0.60), (26, 0.80), (28, 1.00), (30, 1.30), (33, 1.60), (36, 2.00), (40, 2.50), (45, 3.00), (999, 3.50)]

# 2. 투자 설정 입력창
st.markdown("### 💰 나의 투자 설정")
col_input1, col_input2 = st.columns(2)
with col_input1: total_budget = st.number_input("총 투자 예산 (KRW)", value=80000000, step=1000000)
with col_input2: invest_period = st.number_input("매수 기간 (일)", value=180, min_value=1)
base_amount = total_budget / invest_period

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

# 4. 하이퍼 매트릭스 로직 (기존 유지)
def get_weight_rsi(val, matrix):
    for b, w in matrix:
        if val >= b: return w
    return matrix[-1][1]
def get_weight_std(val, matrix):
    for b, w in matrix:
        if val <= b: return w
    return matrix[-1][1]

# 5. 실행 및 결과 출력
data = get_market_data()
if data:
    # --- [섹션 1] S&P 500 시장 지표 가로 배치 ---
    st.markdown("### 🏛️ 미국 시장 종합 지표")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("S&P 500 지수", f"{data['spy']['price']:,.2f}")
    m2.metric("실시간 VIX", f"{data['vix']:.2f}")
    m3.metric("S&P 500 RSI", f"{data['spy']['rsi']:.1f}")
    m4.metric("S&P 500 MDD", f"{data['spy']['mdd']:.2f}%")
    
    # --- [섹션 2] 코스톨라니 달걀 모델 시계형 시각화 ---
    st.markdown("### 🥚 코스톨라니 달걀 시계 (시장 국면)")
    rsi = data['spy']['rsi']
    vix = data['vix']
    
    # 국면 판단 logic
    active = [False] * 6 # A1, A2, A3, B1, B2, B3 순서
    if rsi <= 30 or vix >= 35: active[0] = True   # A1: 수정기 (바닥)
    elif rsi <= 45: active[1] = True            # A2: 동행기 (매집)
    elif rsi <= 60: active[2] = True            # A3: 과장기 (상승강화)
    elif rsi >= 75: active[3] = True            # B1: 수정기 (고점)
    elif rsi >= 65: active[4] = True            # B2: 동행기 (매도중)
    else: active[5] = True                      # B3: 과장기 (침체시작)

    st.markdown(f"""
        <div class="egg-container">
            <div class="egg-phase {'active-phase' if active[0] else ''}">
                <div class="phase-title">A1 수정기</div><div class="phase-desc">바닥 / 소신파 매수</div>
            </div>
            <div class="egg-phase {'active-phase' if active[1] else ''}">
                <div class="phase-title">A2 동행기</div><div class="phase-desc">거래량 증가 / 보유</div>
            </div>
            <div class="egg-phase {'active-phase' if active[2] else ''}">
                <div class="phase-title">A3 과장기</div><div class="phase-desc">과열 / 부화뇌동 매수</div>
            </div>
            <div class="egg-phase {'active-phase' if active[3] else ''}">
                <div class="phase-title">B1 수정기</div><div class="phase-desc">고점 / 소신파 매도</div>
            </div>
            <div class="egg-phase {'active-phase' if active[4] else ''}">
                <div class="phase-title">B2 동행기</div><div class="phase-desc">거래량 감소 / 현금화</div>
            </div>
            <div class="egg-phase {'active-phase' if active[5] else ''}">
                <div class="phase-title">B3 과장기</div><div class="phase-desc">폭락 / 공포 투매</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.divider()

    # --- [섹션 3] 종목별 매수액 산출 ---
    c = get_weight_std(data['vix'], VIX_MATRIX)
    col1, col2 = st.columns(2)

    with col1:
        st.info("### 🇰🇷 KODEX 미국나스닥100")
        a_ndq = get_weight_rsi(data['ndq']['rsi'], RSI_MATRIX)
        b_ndq = get_weight_std(abs(data['ndq']['mdd']), MDD_MATRIX)
        total_ndq = a_ndq + b_ndq + c
        st.markdown(f'<div style="background-color:#1E1E1E;padding:20px;border-radius:15px;border:2px solid #00CCFF;text-align:center;"><h2 style="color:#00CCFF;margin:0;">{(base_amount * total_ndq):,.0f} 원</h2><p style="color:#888;margin:5px 0 0 0;">나스닥 RSI: {data["ndq"]["rsi"]:.1f}</p></div>', unsafe_allow_html=True)

    with col2:
        st.success("### 🇰🇷 TIGER 미국S&P500")
        a_sp5 = get_weight_rsi(data['sp5']['rsi'], RSI_MATRIX)
        b_sp5 = get_weight_std(abs(data['sp5']['mdd']), MDD_MATRIX)
        total_sp5 = a_sp5 + b_sp5 + c
        st.markdown(f'<div style="background-color:#1E1E1E;padding:20px;border-radius:15px;border:2px solid #EAFF00;text-align:center;"><h2 style="color:#EAFF00;margin:0;">{(base_amount * total_sp5):,.0f} 원</h2><p style="color:#888;margin:5px 0 0 0;">S&P500 RSI: {data["sp5"]["rsi"]:.1f}</p></div>', unsafe_allow_html=True)

    with st.expander("🔍 상세 데이터 확인"):
        st.write(f"공통 VIX 배수: {c} | 나스닥 가중치: {total_ndq:.2f}배 | S&P500 가중치: {total_sp5:.2f}배")
else:
    st.warning("데이터 연동 중...")
