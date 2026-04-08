import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정 (최대한 깔끔하게)
st.set_page_config(page_title="Retirement Traveler", layout="centered")

# 커스텀 스타일: 폰트 크기 및 박스 가독성 향상
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: bold; }
    .buy-box { padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 은퇴여행자 매수 가이드")
st.caption("실시간 VIX 및 하이퍼 매트릭스 기반")

# --- 데이터 정의 (기존 데이터 유지) ---
RSI_MATRIX = [(75, 0.02), (70, 0.05), (65, 0.08), (60, 0.12), (55, 0.20), (52, 0.30), (48, 0.45), (45, 0.65), (42, 0.85), (40, 1.10), (38, 1.35), (35, 1.60), (32, 1.90), (30, 2.20), (25, 2.60), (0, 3.20)]
MDD_MATRIX = [(0.5, 0.02), (1, 0.05), (2, 0.10), (3, 0.15), (4, 0.25), (5, 0.35), (6, 0.50), (8, 0.75), (10, 1.00), (12, 1.30), (14, 1.60), (16, 1.90), (18, 2.30), (20, 2.70), (25, 3.20), (999, 4.00)]
VIX_MATRIX = [(10, 0.02), (12, 0.05), (14, 0.08), (16, 0.12), (18, 0.20), (20, 0.30), (22, 0.45), (24, 0.60), (26, 0.80), (28, 1.00), (30, 1.30), (33, 1.60), (36, 2.00), (40, 2.50), (45, 3.00), (999, 3.50)]

# 2. 투자 설정 (사이드바로 숨겨서 메인 화면을 심플하게 유지)
with st.sidebar:
    st.header("⚙️ 설정")
    total_budget = st.number_input("총 예산 (원)", value=80000000, step=1000000)
    invest_period = st.number_input("매수 기간 (일)", value=180, min_value=1)
    base_amount = total_budget / invest_period
    st.write(f"일일 기본액: {base_amount:,.0f}원")

# 3. 데이터 로드 함수
@st.cache_data(ttl=600)
def get_market_data():
    try:
        tickers = {"spy": "^GSPC", "vix": "^VIX", "ndq": "379810.KS", "sp5": "360750.KS"}
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

        rsi_spy, mdd_spy, price_spy = calc_indicators(close_data[tickers["spy"]])
        rsi_ndq, mdd_ndq, price_ndq = calc_indicators(close_data[tickers["ndq"]])
        rsi_sp5, mdd_sp5, price_sp5 = calc_indicators(close_data[tickers["sp5"]])
        current_vix = float(close_data[tickers["vix"]].dropna().iloc[-1])

        return {"vix": current_vix, "spy": {"rsi": rsi_spy, "mdd": mdd_spy}, "ndq": {"price": price_ndq, "rsi": rsi_ndq, "mdd": mdd_ndq}, "sp5": {"price": price_sp5, "rsi": rsi_sp5, "mdd": mdd_sp5}}
    except: return None

def get_weight(val, matrix, mode="rsi"):
    if mode == "rsi":
        for b, w in matrix:
            if val >= b: return w
    else:
        for b, w in matrix:
            if val <= b: return w
    return matrix[-1][1]

# 4. 메인 화면 구성
data = get_market_data()

if data:
    # 시장 지표 요약 (간결하게 3개만)
    col1, col2, col3 = st.columns(3)
    col1.metric("시장 공포(VIX)", f"{data['vix']:.1f}")
    col2.metric("나스닥 RSI", f"{data['ndq']['rsi']:.1f}")
    col3.metric("S&P500 RSI", f"{data['sp5']['rsi']:.1f}")
    
    st.divider()

    # 공통 VIX 배수 계산
    c = get_weight(data['vix'], VIX_MATRIX, "std")

    # 결과 표시
    st.markdown("### 💰 오늘의 권장 매수액")
    
    # KODEX 미국나스닥100
    a_ndq = get_weight(data['ndq']['rsi'], RSI_MATRIX, "rsi")
    b_ndq = get_weight(abs(data['ndq']['mdd']), MDD_MATRIX, "std")
    total_ndq = a_ndq + b_ndq + c
    
    st.markdown(f"""
        <div class="buy-box" style="border: 2px solid #00CCFF; background-color: #002233;">
            <span style="color: #00CCFF; font-size: 1.2rem; font-weight: bold;">KODEX 미국나스닥100</span><br>
            <span style="color: white; font-size: 2.8rem; font-weight: bold;">{(base_amount * total_ndq):,.0f} 원</span><br>
            <span style="color: #888; font-size: 0.9rem;">지표 합계: {total_ndq:.2f}배 (현재가 {data['ndq']['price']:,.0f}원)</span>
        </div>
        """, unsafe_allow_html=True)

    # TIGER 미국S&P500
    a_sp5 = get_weight(data['sp5']['rsi'], RSI_MATRIX, "rsi")
    b_sp5 = get_weight(abs(data['sp5']['mdd']), MDD_MATRIX, "std")
    total_sp5 = a_sp5 + b_sp5 + c

    st.markdown(f"""
        <div class="buy-box" style="border: 2px solid #EAFF00; background-color: #222200;">
            <span style="color: #EAFF00; font-size: 1.2rem; font-weight: bold;">TIGER 미국S&P500</span><br>
            <span style="color: white; font-size: 2.8rem; font-weight: bold;">{(base_amount * total_sp5):,.0f} 원</span><br>
            <span style="color: #888; font-size: 0.9rem;">지표 합계: {total_sp5:.2f}배 (현재가 {data['sp5']['price']:,.0f}원)</span>
        </div>
        """, unsafe_allow_html=True)

    # 상세 정보는 하단에 숨김
    with st.expander("ℹ️ 계산 근거 및 상세 지표"):
        st.write(f"**공통 VIX 가중치:** {c}")
        st.write(f"**나스닥100:** RSI 배수 {a_ndq} + MDD 배수 {b_ndq}")
        st.write(f"**S&P500:** RSI 배수 {a_sp5} + MDD 배수 {b_sp5}")
else:
    st.error("데이터를 가져올 수 없습니다. 인터넷 연결을 확인하세요.")
