import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
import time
import pandas as pd
from datetime import datetime, timedelta
import re
from tqdm import tqdm
from google_play_scraper import app, Sort, reviews
import emoji
import unicodedata
import os
import random
import requests
from bs4 import BeautifulSoup

def clean_text(text):
    """텍스트에서 특수 문자와 제어 문자 제거"""
    if not isinstance(text, str):
        return str(text)
    
    # 유니코드 정규화
    text = unicodedata.normalize('NFKD', text)
    
    # ASCII로 변환 가능한 문자만 유지
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # 기본 문장 부호만 유지하고 나머지 특수 문자 제거
    text = re.sub(r'[^a-zA-Z0-9\s.,!?-]', '', text)
    
    # 중복된 공백 제거
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def scroll_to_element(driver, element):
    """요소가 보이도록 스크롤"""
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    time.sleep(0.5)

def wait_for_element(wait, selector, by=By.CSS_SELECTOR, timeout=10):
    """요소가 나타날 때까지 대기"""
    try:
        return wait.until(EC.presence_of_element_located((by, selector)))
    except TimeoutException:
        return None

def wait_for_elements(wait, selector, by=By.CSS_SELECTOR, timeout=10):
    """여러 요소가 나타날 때까지 대기"""
    try:
        return wait.until(EC.presence_of_all_elements_located((by, selector)))
    except TimeoutException:
        return []

def scroll_to_bottom(driver, wait_time=1.5):
    """페이지 끝까지 스크롤"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def parse_relative_date(date_text):
    """상대적 날짜를 절대적 날짜로 변환"""
    if not date_text:
        return ''
    
    today = datetime.now()
    
    if 'days ago' in date_text:
        days = int(date_text.split()[0])
        return (today - timedelta(days=days)).strftime('%Y-%m-%d')
    elif 'months ago' in date_text:
        months = int(date_text.split()[0])
        return (today - timedelta(days=months*30)).strftime('%Y-%m-%d')
    elif 'years ago' in date_text:
        years = int(date_text.split()[0])
        return (today - timedelta(days=years*365)).strftime('%Y-%m-%d')
    
    return date_text

def crawl_consumeraffairs_reviews(max_count=100):
    url = "https://www.consumeraffairs.com/food/instacart.html"
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    ]
    proxies = [None]
    reviews = []
    page = 1
    while len(reviews) < max_count:
        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": url
        }
        proxy = random.choice(proxies)
        params = {"page": page}
        try:
            resp = requests.get(url, headers=headers, proxies={"http": proxy, "https": proxy} if proxy else None, params=params, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            review_elements = soup.select(".rvw__cntr")
            if not review_elements:
                break
            for elem in review_elements:
                try:
                    name = elem.select_one(".rvw__inf-nm").get_text(strip=True) if elem.select_one(".rvw__inf-nm") else ""
                    location = elem.select_one(".rvw__inf-lctn").get_text(strip=True) if elem.select_one(".rvw__inf-lctn") else ""
                    rating_elem = elem.select_one(".rvw__rtg.stars-sprt")
                    rating = int(rating_elem["class"][2].split("--p-")[-1]) if rating_elem and len(rating_elem["class"]) > 2 else None
                    date_raw = elem.select_one(".rvw__rvd-dt").get_text(strip=True) if elem.select_one(".rvw__rvd-dt") else ""
                    # 'Reviewed' 또는 'reviewed' 제거
                    date = date_raw.replace('Reviewed', '').replace('reviewed', '').strip()
                    content = elem.select_one(".rvw__bd").get_text(strip=True) if elem.select_one(".rvw__bd") else ""
                    feedback = elem.select_one(".rvw__fdbck").get_text(strip=True) if elem.select_one(".rvw__fdbck") else ""
                    reviews.append({
                        "name": name,
                        "location": location,
                        "rating": rating,
                        "date": date,
                        "review": content,
                        "feedback": feedback
                    })
                    if len(reviews) >= max_count:
                        break
                except Exception:
                    continue
            page += 1
            time.sleep(random.uniform(2, 5))
        except Exception as e:
            print(f"페이지 {page}에서 오류: {e}")
            break
    return reviews

@st.cache_data(ttl=3600)
def fetch_reviews(max_count):
    return crawl_consumeraffairs_reviews(max_count=max_count)

# 데이터 저장을 위한 캐시 함수
@st.cache_data(ttl=3600)
def fetch_reviews(max_count):
    return crawl_consumeraffairs_reviews(max_count=max_count)

# 파일 저장 디렉토리 생성
if not os.path.exists('downloads'):
    os.makedirs('downloads')

# Streamlit 앱 시작
st.set_page_config(page_title="Affairs 리뷰 크롤러", layout="centered", initial_sidebar_state="expanded")
st.title("📊 Affairs 리뷰 수집기")
st.caption("Affairs에서 Instacart 앱 리뷰를 수집합니다.")

# 세션 상태 초기화
if 'collected_data' not in st.session_state:
    st.session_state.collected_data = None
if 'csv_path' not in st.session_state:
    st.session_state.csv_path = None
if 'graph_paths' not in st.session_state:
    st.session_state.graph_paths = {}

# 사이드바에 옵션 추가
st.sidebar.title("크롤링 설정")
max_reviews = st.sidebar.slider("수집할 리뷰 수", min_value=10, max_value=1000, value=970, step=10)

if st.button("크롤링 시작"):
    with st.spinner("리뷰 데이터를 수집하고 있습니다..."):
        # 캐시된 함수를 사용하여 데이터 수집
        results = fetch_reviews(max_count=max_reviews)
        
        if not results:
            st.error("수집된 데이터가 없습니다. 잠시 후 다시 시도해주세요.")
        else:
            # 데이터프레임 생성
            df = pd.DataFrame(results)
            
            # 세션 상태에 데이터 저장
            st.session_state.collected_data = df
            
            # CSV 파일 저장 (백업용)
            csv_filename = f'downloads/instacart_reviews_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            if not os.path.exists('downloads'):
                os.makedirs('downloads')
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            st.session_state.csv_path = csv_filename

            st.write("데이터프레임 shape:", df.shape)  # 데이터 확인용

            # 기본 통계 표시
            st.subheader("📈 기본 통계")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("총 리뷰 수", len(df))
            with col2:
                avg_rating = round(df['rating'].mean(), 2)
                st.metric("평균 별점", f"{avg_rating}점")
            with col3:
                avg_length = round(df['review'].str.len().mean())
                st.metric("평균 리뷰 길이", f"{avg_length}자")
            with col4:
                st.metric("지역 종류 수", df['location'].nunique())

            st.success(f"✅ {len(df)}건의 리뷰 수집 완료!")

            # 다운로드 섹션
            st.subheader("�� 다운로드")
            if not df.empty:
                st.download_button(
                    label="CSV 다운로드",
                    data=df.to_csv(index=False, encoding='utf-8-sig'),
                    file_name=os.path.basename(csv_filename),
                    mime='text/csv'
                )
            else:
                st.warning("저장할 데이터가 없습니다.")

            # 리뷰 필터링 및 정렬 옵션
            st.subheader("🔍 리뷰 필터 및 정렬")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                min_stars = st.select_slider("최소 별점", options=[1,2,3,4,5], value=1)
            with col2:
                min_length = st.number_input("최소 리뷰 길이", min_value=0, value=0)
            with col3:
                location_filter = st.multiselect(
                    "지역 선택",
                    options=sorted(df['location'].unique()),
                    default=sorted(df['location'].unique())
                )
            with col4:
                sort_option = st.selectbox(
                    "정렬 기준",
                    ["최신순", "별점 높은순", "별점 낮은순", "리뷰 길이 긴순"]
                )
            try:
                # 필터링 적용
                filtered_df = df[
                    (df['rating'] >= min_stars) & 
                    (df['review'].str.len() >= min_length) &
                    (df['location'].isin(location_filter))
                ].copy()

                # 정렬 적용
                if sort_option == "최신순":
                    filtered_df = filtered_df.sort_values('date', ascending=False)
                elif sort_option == "별점 높은순":
                    filtered_df = filtered_df.sort_values('rating', ascending=False)
                elif sort_option == "별점 낮은순":
                    filtered_df = filtered_df.sort_values('rating', ascending=True)
                elif sort_option == "리뷰 길이 긴순":
                    filtered_df = filtered_df.sort_values(by='review', key=lambda x: x.str.len(), ascending=False)

                # 리뷰 표시
                st.subheader(f"📋 리뷰 목록 ({len(filtered_df)}건)")
                for idx, row in filtered_df.iterrows():
                    with st.expander(f"⭐{row['rating']} | {row['name']} | {row['location']} | {row['date']}"):
                        # 리뷰 문장별로 나누어 표시
                        review_sentences = [s.strip() for s in row['review'].split('.') if s.strip()]
                        st.markdown("**리뷰 내용:**")
                        for sent in review_sentences:
                            st.write(sent + '.')
                        st.write("---")
                        if row['feedback']:
                            st.markdown(f"<span style='color: #1a73e8; font-weight: bold;'>💬 피드백:</span>", unsafe_allow_html=True)
                            st.info(row['feedback'])
                        else:
                            st.caption("피드백 없음")
                # 데이터프레임 원본 보기 옵션
                if st.checkbox("데이터프레임 원본 보기"):
                    st.dataframe(filtered_df)
            except Exception as e:
                st.error(f"데이터 처리 중 오류 발생: {str(e)}")

