import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(
    page_title="한-미 주식 비교 분석기 | 당곡고 학습 도우미",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 제목 및 설명
st.title("📊 한-미 주요 주식 수익률 & 차트 비교 분석기")
st.write(
    "이 웹앱은 한국과 미국의 주요 주식 및 지수 데이터를 가져와 주가 추이와 누적 수익률을 비교할 수 있는 학습용 도구입니다. "
    "직접 주식을 선택하고 기간을 설정하며 데이터의 흐름을 분석해 보세요!"
)

# 3. 사이드바 설정 (사용자 입력)
st.sidebar.header("⚙️ 분석 설정")

# 주식 이름과 yfinance 티커 매핑 사전
stock_dict = {
    "삼성전자 (KS)": "005930.KS",
    "SK하이닉스 (KS)": "000660.KS",
    "현대차 (KS)": "005380.KS",
    "NAVER (KS)": "035420.KS",
    "애플 (US)": "AAPL",
    "마이크로소프트 (US)": "MSFT",
    "테슬라 (US)": "TSLA",
    "엔비디아 (US)": "NVDA",
    "S&P 500 지수 (US)": "^GSPC",
    "코스피 지수 (KS)": "^KS11"
}

# 비교할 주식 다중 선택
selected_stock_names = st.sidebar.multiselect(
    "비교할 주식을 선택하세요 (복수 선택 가능):",
    options=list(stock_dict.keys()),
    default=["삼성전자 (KS)", "애플 (US)", "테슬라 (US)"]
)

# 날짜 범위 설정 (기본값: 최근 1년)
today = datetime.today()
start_date = st.sidebar.date_input("조회 시작일", today - timedelta(days=365))
end_date = st.sidebar.date_input("조회 종료일", today)

if start_date >= end_date:
    st.sidebar.error("시작일은 종료일보다 이전 날짜여야 합니다!")

# 선택된 주식 이름들을 yfinance 티커 목록으로 변환
tickers = [stock_dict[name] for name in selected_stock_names]

# 4. 데이터 불러오기 함수 (캐싱 적용으로 속도 향상)
@st.cache_data
def load_stock_data(tickers, start, end):
    if not tickers:
        return pd.DataFrame()
    # 조정 종가(Adj Close) 기준으로 데이터를 가져옵니다.
    data = yf.download(tickers, start=start, end=end)['Adj Close']
    
    # 만약 하나의 주식만 선택했다면 Series가 반환되므로 DataFrame으로 변환해 줍니다.
    if isinstance(data, pd.Series):
        data = data.to_frame(name=tickers[0])
    return data

# 5. 메인 화면 구현
if tickers:
    with st.spinner("야후 파이낸스에서 데이터를 가져오는 중입니다..."):
        df = load_stock_data(tickers, start_date, end_date)

    if not df.empty:
        # 컬럼명을 티커 기호 대신 보기 쉬운 한글 이름으로 변경합니다.
        ticker_to_name = {v: k for k, v in stock_dict.items()}
        df.columns = [ticker_to_name.get(col, col) for col in df.columns]

        # 결측치 처리 (휴장일 등이 다를 수 있음)
        df = df.ffill().bfill()

        # ---------------- Tabs 구성 ----------------
        tab1, tab2, tab3 = st.tabs(["📈 주가 차트", "🔄 누적 수익률 비교", "📊 요약 통계"])

        with tab1:
            st.subheader("일별 종가 추이")
            st.caption("각 주식이 거래되는 통화(원화 혹은 달러) 기준으로 표시됩니다.")
            fig_price = px.line(df, labels={"value": "주가", "Date": "날짜"})
            st.plotly_chart(fig_price, use_container_width=True)

        with tab2:
            st.subheader("시작일 기준 누적 수익률 (%)")
            st.caption("설정한 시작일의 주가를 0%로 잡고, 이후 주가가 얼마나 변했는지 비율로 비교합니다.")
            
            # 누적 수익률 계산 공식: (현재 가격 / 시작 가격 - 1) * 100
            returns_df = (df / df.iloc[0] - 1) * 100
            
            fig_returns = px.line(returns_df, labels={"value": "누적 수익률 (%)", "Date": "날짜"})
            fig_returns.update_layout(yaxis_tickformat=".1f")
            st.plotly_chart(fig_returns, use_container_width=True)

        with tab3:
            st.subheader("선택 기간 통계 요약")
            summary = pd.DataFrame({
                "시작일 가격": df.iloc[0],
                "마지막일 가격": df.iloc[-1],
                "최고가": df.max(),
                "최저가": df.min(),
                "최종 누적 수익률 (%)": returns_df.iloc[-1]
            })
            st.dataframe(summary.style.format("{:,.2f}"))

        # 💡 스스로 생각하고 탐구해보기 코너
        st.markdown("---")
        st.subheader("💡 스스로 생각해볼까요? (탐구 과제)")
        st.info(
            "1. **단위의 함정**: 그냥 '주가 차트'를 봤을 때와 '누적 수익률 차트'를 봤을 때의 차이점은 무엇인가요? "
            "왜 주식 비교를 할 때는 단순 가격보다 '수익률'을 비교하는 것이 더 합리적일까요?\n\n"
            "2. **시장 지수와의 비교**: 여러분이 선택한 개별 주식의 상승/하락 흐름이 코스피 지수나 S&P 500 지수의 흐름과 얼마나 닮아 있나요? "
            "이것을 금융학에서는 '체계적 위험(시장 변동성)'과 연결지어 설명하곤 합니다.\n\n"
            "3. **환율 효과**: 이 프로그램은 미국 주식은 달러(USD), 한국 주식은 원화(KRW) 기준으로 계산합니다. "
            "만약 환율 변동까지 반영한다면 실제 한국인 투자자의 수익률은 어떻게 달라질까요?"
        )
    else:
        st.error("데이터를 불러오는 데 실패했습니다. 선택한 기간이 너무 짧거나 주식 시장이 열리지 않은 날인지 확인해 주세요.")
else:
    st.info("👈 왼쪽 사이드바에서 비교하고 싶은 주식을 하나 이상 선택해 주세요!")
