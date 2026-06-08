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

# 4. 데이터 불러오기 함수 (예외 처리를 대폭 강화한 버전)
@st.cache_data
def load_stock_data(tickers, start, end):
    if not tickers:
        return pd.DataFrame()
    
    try:
        # auto_adjust=False를 설정하여 'Adj Close' 컬럼을 안전하게 가져오도록 시도합니다.
        raw_data = yf.download(tickers, start=start, end=end, auto_adjust=False)
        
        if raw_data.empty:
            return pd.DataFrame()
        
        # 1) 컬럼에서 'Adj Close'가 있는지 확인하고 가져옵니다.
        # 만약 없으면 일반 'Close'를 가져오는 예외처리를 추가해 KeyError를 원천 차단합니다.
        if 'Adj Close' in raw_data.columns:
            data = raw_data['Adj Close']
        elif 'Close' in raw_data.columns:
            data = raw_data['Close']
        else:
            # 둘 다 없는 극단적인 상황에는 전체 데이터 프레임을 반환합니다.
            data = raw_data
            
        # 2) 만약 주식이 딱 1개만 선택되었을 때, Series가 반환되는 현상을 방지하고 DataFrame으로 규격화합니다.
        if isinstance(data, pd.Series):
            data = data.to_frame(name=tickers[0])
            
        return data

    except Exception as e:
        # 어떤 에러가 발생했는지 웹 화면에 일시적으로 띄워줍니다.
        st.error(f"데이터를 다운로드하는 중 에러가 발생했습니다: {e}")
        return pd.DataFrame()

# 5. 메인 화면 구현
if tickers:
    with st.spinner("야후 파이낸스에서 데이터를 가져오는 중입니다..."):
        df = load_stock_data(tickers, start_date, end_date)

    if not df.empty:
        # 데이터프레임 복사본 생성
        df_cleaned = df.copy()

        # 만약 컬럼이 MultiIndex(여러 층으로 구성)라면, 마지막 층(티커명)만 남기고 단순화합니다.
        if isinstance(df_cleaned.columns, pd.MultiIndex):
            df_cleaned.columns = df_cleaned.columns.get_level_values(-1)

        # 컬럼명을 티커 기호 대신 보기 쉬운 한글 이름으로 변경합니다.
        ticker_to_name = {v: k for k, v in stock_dict.items()}
        df_cleaned.columns = [ticker_to_name.get(col, col) for col in df_cleaned.columns]

        # 결측치 처리 (휴장일 등이 다를 수 있으므로 앞뒤 데이터로 채워줍니다)
        df_cleaned = df_cleaned.ffill().bfill()

        # ---------------- Tabs 구성 ----------------
        tab1, tab2, tab3 = st.tabs(["📈 주가 차트", "🔄 누적 수익률 비교", "📊 요약 통계"])

        with tab1:
            st.subheader("일별 종가 추이")
            st.caption("각 주식이 거래되는 통화(원화 혹은 달러) 기준으로 표시됩니다.")
            fig_price = px.line(df_cleaned, labels={"value": "주가", "Date": "날짜"})
            st.plotly_chart(fig_price, use_container_width=True)

        with tab2:
            st.subheader("시작일 기준 누적 수익률 (%)")
            st.caption("설정한 시작일의 주가를 0%로 잡고, 이후 주가가 얼마나 변했는지 비율로 비교합니다.")
            
            # 누적 수익률 계산 공식: (현재 가격 / 시작 가격 - 1) * 100
            returns_df = (df_cleaned / df_cleaned.iloc[0] - 1) * 100
            
            fig_returns = px.line(returns_df, labels={"value": "누적 수익률 (%)", "Date": "날짜"})
            fig_returns.update_layout(yaxis_tickformat=".1f")
            st.plotly_chart(fig_returns, use_container_width=True)

        with tab3:
            st.subheader("선택 기간 통계 요약")
            summary = pd.DataFrame({
                "시작일 가격": df_cleaned.iloc[0],
                "마지막일 가격": df_cleaned.iloc[-1],
                "최고가": df_cleaned.max(),
                "최저가": df_cleaned.min(),
                "최종 누적 수익률 (%)": returns_df.iloc[-1]
            })
            st.dataframe(summary.style.format("{:,.2f}"))

        # 💡 스스로 생각하고 탐구해보기 코너
        st.markdown("---")
        st.subheader("💡 스스로 생각해볼까요? (탐구 과제)")
        st.info(
            "1. **예외 처리의 중요성**: 우리가 겪은 `KeyError`처럼, 외부 API(야후 파이낸스)가 전달해 주는 데이터 형식은 언제든 변할 수 있습니다. "
            "이에 대비하는 '예외 처리(Exception Handling)' 코딩 습관이 왜 중요한지 직접 에러를 해결해 보며 느낀 점을 적어보세요!\n\n"
            "2. **누적 수익률의 유용성**: 원화 단위인 한국 주식과 달러 단위인 미국 주식을 하나의 차트에서 직접 비교하는 것이 왜 어려우며, "
            "이를 '누적 수익률'로 변환했을 때 어떤 분석이 가능해지는지 탐구해 보세요."
        )
    else:
        st.error("데이터를 불러오는 데 실패했습니다. 선택한 기간이 너무 짧거나 주식 시장이 열리지 않은 날인지 확인해 주세요.")
else:
    st.info("👈 왼쪽 사이드바에서 비교하고 싶은 주식을 하나 이상 선택해 주세요!")
