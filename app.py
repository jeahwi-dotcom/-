import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정 및 타이틀
st.set_page_config(page_title="Retirement Traveler", layout="wide")

st.title("📊 Retirement Traveler")
st.subheader("S&P 500 실시간 분할매수 시스템")
st.caption("공식: 오늘의 최종 매수액 = 기본 매수액 × (VIX 가중치 + MDD 가중치 + RSI 가중치)")
st.divider()

# 2. 투자 설정 입력창 (메인 상단)
st.markdown("### 💰 나의 투자 설정")
col_input1, col_input2 = st.columns(2)

with col_input1:
    total_budget = st.number_input("총 투자 예산 (KRW)", value=80000000, step=1000000)

with col_input2:
    invest_period = st.number_input("매수 기간 (일)", value=180, min_value=1)

base_amount = total_budget / invest_period
st.info(f"📍 **일일 기본 매수액:** {base_amount:,.0f}원")
st.divider()

# 3. 실시간 데이터 로드 함수 (안정성 강화 버전)
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
        
        # 최신 가격 및 VIX
        current_vix = vix['Close'].dropna().iloc[-1]
        current_sp = close.iloc[-1]

        return {"vix": float(current_vix), "mdd": float(mdd_val), "rsi": float(rsi_val), "sp500": float(current_sp)}
    except:
        return None

# 4. 요청하신 정밀 가중치 테이블 로직
def get_weights(v, m, r):
    # [Table 1: VIX 가중치]
    if v >= 35: v_w = 3.0
    elif v >= 28: v_w = 2.2
    elif v >= 22: v_w = 1.5
    elif v >= 18: v_w = 1.0
    else: v_w = 0.6

    # [Table 2: MDD 가중치]
    if m <= -20: m_w = 5.0
    elif m <= -15: m_w = 3.5
    elif m <= -10: m_w = 2.5
    elif m <= -5: m_w = 1.5
    elif m <= -2: m_w = 0.8
    else: m_w = 0.3

    # [Table 3: RSI 가중치]
    if r <= 25: r_w = 4.0
    elif r <= 35: r_w = 3.0
    elif r <= 45: r_w = 1.8
    elif r <= 55: r_w = 1.0
    elif r <= 65: r_w = 0.6
    else: r_w = 0.3
    
    return v_w, m_w, r_w

# 5. 실행 및 결과 출력
data = get_market_data()

if data:
    # 시장 지표 표시
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: st.metric("S&P 500", f"{data['sp500']:,.2f}")
    with col_m2: st.metric("VIX", f"{data['vix']:.2f}")
    with col_m3: st.metric("MDD", f"{data['mdd']:.2f}%")
    with col_m4: st.metric("RSI", f"{data['rsi']:.2f}")
    st.divider()

    # 가중치 산출 및 최종 합산 공식 적용
    v_w, m_w, r_w = get_weights(data['vix'], data['mdd'], data['rsi'])
    
    # 공식: 오늘의 최종 매수액 = 기본 매수액 × (VIX + MDD + RSI)
    total_multiplier = v_w + m_w + r_w
    final_amount = base_amount * total_multiplier

    st.subheader("📢 오늘의 최종 매수액 산출 결과")
    
    # 강조 레이아웃
    st.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 40px; border-radius: 20px; border: 3px solid #EAFF00; text-align: center;">
            <p style="color: white; font-size: 1.4rem; margin-bottom: 15px;">최종 매수 금액</p>
            <h1 style="color: #EAFF00; font-size: 4.5rem; margin: 0;">{final_amount:,.0f} 원</h1>
            <p style="color: #888; font-size: 1.1rem; margin-top: 20px;">
                적용된 합산 가중치: <b>{total_multiplier:.1f}배</b><br>
                (VIX {v_w} + MDD {m_w} + RSI {r_w})
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 상세 근거
    with st.expander("🔍 가중치 산정 상세 근거 확인"):
        st.write(f"1. **VIX ({data['vix']:.2f}):** {v_w} 적용")
        st.write(f"2. **MDD ({data['mdd']:.2f}%):** {m_w} 적용")
        st.write(f"3. **RSI ({data['rsi']:.2f}):** {r_w} 적용")
        st.write("---")
        st.write(f"**최종 계산:** {base_amount:,.0f}원 × ({v_w} + {m_w} + {r_w}) = {final_amount:,.0f}원")
else:
    st.warning("시장 데이터를 불러오는 중입니다. 잠시 후 새로고침 해주세요.")

st.divider()
