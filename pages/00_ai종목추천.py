import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 페이지 및 테마 설정
st.set_page_config(
    page_title="AI 밸류체인 비교 연구기 | 당곡고 학습 도우미",
    layout="wide"
)

st.title("🤖 AI 산업 밸류체인별 대표 기업 데이터 분석기")
st.write(
    "이 프로그램은 글로벌 AI 생태계를 구성하는 **하드웨어**, **클라우드**, **소프트웨어** 세 가지 도메인의 "
    "주요 기업들의 주가 흐름과 누적 수익률을 비교하여 어떤 세부 산업이 AI 패러다임을 주도하고 있는지 탐구하는 교육 도구입니다."
)

# 2. 밸류체인별 분석 대상 사전 정의
ai_sectors = {
    "🛠️ 하드웨어/반도체": {
        "엔비디아 (NVIDIA)": "NVDA",
        "TSMC (파운드리)": "TSM",
        "SK하이닉스 (HBM)": "000660.KS"
    },
    "☁️ 클라우드/인프라": {
        "마이크로소프트 (MSFT)": "MSFT",
        "아마존 (AMZN)": "AMZN",
        "구글 (GOOGL)": "GOOGL"
    },
    "💻 소프트웨어/서비스": {
        "팔란티어 (PLTR)": "PLTR",
        "서비스나우 (NOW)": "NOW",
        "세일즈포스 (CRM)": "CRM"
    }
}

# 3. 사이드바 설정 (밸류체인 단계별 주식 선택)
st.sidebar.header("📂 분석 대상 선택")

selected_tickers = {}
for sector, stocks in ai_sectors.items():
    st.sidebar.subheader(sector)
    selected = st.sidebar.multiselect(
        f"{sector} 내 분석 대상:",
        options=list(stocks.keys()),
        default=list(stocks.keys())[0] # 기본값으로 각 분류별 첫 번째 종목 선택
    )
    for name in selected:
        selected_tickers[name] = stocks[name]

# 날짜 범위 설정 (기본값: 최근 1년)
today = datetime.today()
start_date = st.sidebar.date_input("조회 시작일", today - timedelta(days=365))
end_date = st.sidebar.date_input("조회 종료일", today)

# 4. 데이터 수집 함수
@st.cache_data
def get_ai_data(ticker_dict, start, end):
    if not ticker_dict:
        return pd.DataFrame()
    
    tickers = list(ticker_dict.values())
    raw_data = yf.download(tickers, start=start, end=end, auto_adjust=False)
    
    if raw_data.empty:
        return pd.DataFrame()
    
    # 안전하게 종가(Close) 혹은 조정 종가(Adj Close) 추출
    data = raw_data['Adj Close'] if 'Adj Close' in raw_data.columns else raw_data['Close']
    
    if isinstance(data, pd.Series):
        data = data.to_frame(name=tickers[0])
        
    return data

# 5. 데이터 시각화 및 분석
if selected_tickers:
    with st.spinner("야후 파이낸스로부터 AI 밸류체인 데이터를 실시간 분석 중입니다..."):
        df_raw = get_ai_data(selected_tickers, start_date, end_date)
        
    if not df_raw.empty:
        df_cleaned = df_raw.copy()
        
        # 다중 인덱스 처리
        if isinstance(df_cleaned.columns, pd.MultiIndex):
            df_cleaned.columns = df_cleaned.columns.get_level_values(-1)
            
        # 컬럼명을 한글 이름으로 변경
        reverse_dict = {v: k for k, v in selected_tickers.items()}
        df_cleaned.columns = [reverse_dict.get(col, col) for col in df_cleaned.columns]
        
        # 휴장일 보정
        df_cleaned = df_cleaned.ffill().bfill()
        
        # 누적 수익률 계산
        returns_df = (df_cleaned / df_cleaned.iloc[0] - 1) * 100
        
        tab1, tab2, tab3 = st.tabs(["📈 누적 수익률 비교", "📊 원본 가격 변동", "📋 요약 데이터"])
        
        with tab1:
            st.subheader("💡 밸류체인별 누적 수익률 (%)")
            st.caption("동일한 시작 시점에서 어떤 영역(하드웨어 vs 인프라 vs 소프트웨어)이 가장 폭발적으로 성장했는지 비교해 보세요.")
            fig_returns = px.line(returns_df, labels={"value": "누적 수익률 (%)", "Date": "날짜"})
            st.plotly_chart(fig_returns, use_container_width=True)
            
        with tab2:
            st.subheader("💵 일별 개별 가격 흐름")
            st.caption("주의: 미국 주식은 달러($), 한국 주식은 원화(₩) 기준입니다.")
            fig_price = px.line(df_cleaned, labels={"value": "주가", "Date": "날짜"})
            st.plotly_chart(fig_price, use_container_width=True)
            
        with tab3:
            st.subheader("📝 분석 리포트 요약")
            summary = pd.DataFrame({
                "시작 가격": df_cleaned.iloc[0],
                "최종 가격": df_cleaned.iloc[-1],
                "최종 수익률 (%)": returns_df.iloc[-1]
            })
            st.dataframe(summary.style.format("{:,.2f}"))
            
    else:
        st.error("데이터 로드에 실패했습니다. 조회 기간이나 종목 선택을 다시 확인해 주세요.")
else:
    st.info("👈 왼쪽 사이드바에서 분석해보고 싶은 AI 밸류체인 기업들을 선택해 주세요!")

# 💡 스스로 생각하고 탐구해보기 코너
st.markdown("---")
st.subheader("💡 경제 및 정보 교과 융합 탐구 활동 가이드")
st.info(
    "1. **성장의 순서(수혜의 시차) 분석**: AI 패러다임이 시작되었을 때 가장 먼저 급상승한 것은 어떤 밸류체인(예: 하드웨어)이었나요? "
    "시간이 지나며 클라우드나 소프트웨어 기업들의 수익률 추이는 어떻게 변화하고 있나요? '선행성과 후행성'의 개념으로 탐구해 보세요.\n\n"
    "2. **독점과 경쟁 구도**: 하드웨어 분야(예: TSMC, 엔비디아)가 클라우드나 소프트웨어 분야보다 독점력이 높은 이유를 기술적/경제적 진입장벽 관점에서 분석해 보세요.\n\n"
    "3. **사회적 영향 연구**: AI 소프트웨어 시장이 커짐에 따라 인간의 일자리는 어떻게 변화할지, 이러한 소프트웨어 기업들의 매출 성장률과 연결지어 보고서를 작성해 보세요."
)
