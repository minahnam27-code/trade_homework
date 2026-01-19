import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="K-Trade 품목별 통계 분석기", page_icon="📈", layout="wide")

# 2. 데이터 로드 및 전처리 (인코딩 및 경로 확인)
@st.cache_data
def load_data():
    # 파일 경로를 본인의 환경에 맞게 수정하세요 (예: 'data.csv' 또는 전체 경로)
    file_path = '품목별_수출액__수입액_20260119092646.csv'
    
    # 한국어 인코딩 적용 (cp949)
    df = pd.read_csv(file_path, encoding='cp949')
    
    # 숫자형 변환 및 결측치 처리
    for col in ['수출액 (천달러)', '수입액 (천달러)']:
        df[col] = pd.to_numeric(df[col].replace('-', '0'), errors='coerce').fillna(0)
    
    # 무역수지 계산
    df['무역수지'] = df['수출액 (천달러)'] - df['수입액 (천달러)']
    # 시점 정렬을 위해 문자열 유지
    df['시점'] = df['시점'].astype(str)
    return df

try:
    df = load_data()

    # --- 사이드바 필터 ---
    st.sidebar.header("🔍 분석 조건 설정")
    
    # 품목 선택 (총액 제외)
    all_categories = df[df['품목별(1)'] != '총액']['품목별(1)'].unique()
    selected_cats = st.sidebar.multiselect("분석할 품목(대분류) 선택", 
                                          options=all_categories, 
                                          default=all_categories[:3])
    
    # 기간 선택
    all_periods = sorted(df['시점'].unique())
    selected_period = st.sidebar.select_slider("분석 기준월 선택", options=all_periods, value=all_periods[-1])

    # --- 메인 화면 ---
    st.title("🛳️ 품목별 수출입 통계 대시보드")
    st.caption("관세청 수출입무역통계를 기반으로 작성된 분석 도구입니다.")
    
    # 탭 나누기
    tab1, tab2 = st.tabs(["📊 당월 실적 요약", "📈 월별 추이 분석"])

    with tab1:
        # 데이터 필터링 (선택된 달 + 선택된 품목 + 대분류 소계 데이터)
        cur_df = df[(df['시점'] == selected_period) & 
                    (df['품목별(1)'].isin(selected_cats)) & 
                    (df['품목별(2)'] == '소계')]
        
        # 상단 지표 (KPI)
        exp_sum = cur_df['수출액 (천달러)'].sum()
        imp_sum = cur_df['수입액 (천달러)'].sum()
        bal_sum = exp_sum - imp_sum
        
        c1, c2, c3 = st.columns(3)
        c1.metric("총 수출액", f"${exp_sum:,.0f}K")
        c2.metric("총 수입액", f"${imp_sum:,.0f}K")
        # 무역수지: 흑자면 초록색(+), 적자면 빨간색(-) 자동 표시
        c3.metric("무역수지", f"${bal_sum:,.0f}K", delta=float(bal_sum))

        st.divider()

        # 차트 영역
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("품목별 수출/수입 비교")
            fig_bar = px.bar(cur_df, x='품목별(1)', y=['수출액 (천달러)', '수입액 (천달러)'],
                             barmode='group', height=400,
                             color_discrete_sequence=['#1f77b4', '#ef553b'])
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_right:
            st.subheader("세부 품목(중분류) 비중")
            # 선택된 대분류 내의 중분류 데이터 필터링
            sub_df = df[(df['시점'] == selected_period) & 
                        (df['품목별(1)'].isin(selected_cats)) & 
                        (df['품목별(2)'] != '소계') & 
                        (df['품목별(3)'] == '소계')]
            fig_pie = px.sunburst(sub_df, path=['품목별(1)', '품목별(2)'], values='수출액 (천달러)',
                                  color='무역수지', color_continuous_scale='RdBu')
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        st.subheader("주요 품목별 월별 수출 추이")
        # 시계열 데이터 필터링
        trend_df = df[(df['품목별(1)'].isin(selected_cats)) & (df['품목별(2)'] == '소계')]
        
        fig_line = px.line(trend_df, x='시점', y='수출액 (천달러)', color='품목별(1)',
                           markers=True, line_shape='linear',
                           title="선택 품목의 수출액 변화 흐름")
        st.plotly_chart(fig_line, use_container_width=True)
        
        st.info("💡 2025년 9월부터 11월까지의 데이터 흐름을 확인할 수 있습니다.")

    # 하단 상세 데이터 섹션
    with st.expander("📝 전체 데이터 표 보기"):
        st.dataframe(df, use_container_width=True)

except FileNotFoundError:
    st.error("CSV 파일을 찾을 수 없습니다. 파일 경로와 이름을 확인해 주세요.")
except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")