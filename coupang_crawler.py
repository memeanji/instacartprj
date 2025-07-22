# ✅ 1. coupang_crawler.py (터미널 실행용 - 시트 분할, 수식 적용, 이미지 포함 최종 버전)
import pandas as pd
import time
from urllib.parse import quote
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from openpyxl import load_workbook
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import multiprocessing as mp
import traceback
from time import sleep
import random
import os
from selenium import webdriver


def get_best_products_reviews(category_url, max_pages=10, reviews_per_product=30):
    """
    (구현 예시) section.js_reviewArticleListContainer 기준으로 리뷰 article을 탐색하는 코드 예시만 남기고, 기존 별점 1,2,3점 필터 및 전체 함수는 삭제합니다.
    실제 사용 시 아래 코드를 참고하여 section 기준으로 리뷰를 추출하세요.
    """
    options = uc.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0")
    prefs = {
        "profile.default_content_setting_values.popups": 1,
        "profile.default_content_setting_values.notifications": 1,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "profile.default_content_setting_values.redirects": 1,
        "profile.default_content_setting_values.mixed_script": 1,
        "profile.default_content_setting_values.media_stream": 1
    }
    options.add_experimental_option("prefs", prefs)
    driver = uc.Chrome(options=options)
    all_reviews = []
    try:
        for page in range(1, max_pages+1):
            url = f"{category_url}?sorter=bestAsc&page={page}"
            print(f"페이지 접속 중: {url}")
            driver.get(url)
            time.sleep(2)
            items = driver.find_elements(By.CSS_SELECTOR, "a.search-product-link")
            product_links = [item.get_attribute("href") for item in items if item.get_attribute("href")]
            for link in product_links:
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[1])
                driver.get(link)
                time.sleep(2)
                try:
                    section = driver.find_element(By.CSS_SELECTOR, "section.js_reviewArticleListContainer")
                    reviews = section.find_elements(By.CSS_SELECTOR, "article.sdp-review__article__list")
                    print(f"    > section 내 리뷰 article {len(reviews)}개 발견")
                    for review in reviews:
                        nickname = review.find_element("css selector", "span.sdp-review__article__list__info__user__name").text
                        rating = review.find_element("css selector", "div.sdp-review__article__list__info__product-info__star-orange").get_attribute("data-rating")
                        date = review.find_element("css selector", "div.sdp-review__article__list__info__product-info__reg-date").text
                        content = review.find_element("css selector", "div.sdp-review__article__list__review__content").text
                        print(nickname, rating, date, content)
                except Exception as e:
                    print(f"    > section 또는 article 탐색 실패: {e}")
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
    finally:
        driver.quit()
    return all_reviews


def wait_for_1star_reviews(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, 'article.sdp-review__article__list .sdp-review__article__list__info__product-info__star-orange.js_reviewArticleRatingValue[data-rating="1"]')) > 0
        )
    except:
        pass


def wait_for_any_reviews(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, 'article.sdp-review__article__list')) > 0
        )
    except:
        pass


def get_driver():
    options = uc.ChromeOptions()
    # User-Agent 지정 (실제 브라우저와 유사하게)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    # 팝업/알림/다운로드 등 허용
    prefs = {
        "profile.default_content_setting_values.popups": 1,
        "profile.default_content_setting_values.notifications": 1,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "profile.default_content_setting_values.redirects": 1,
        "profile.default_content_setting_values.mixed_script": 1,
        "profile.default_content_setting_values.media_stream": 1
    }
    options.add_experimental_option("prefs", prefs)
    # 필요시 헤드리스 모드 사용
    # options.add_argument("--headless")
    driver = uc.Chrome(options=options)
    return driver


def get_product_and_reviews(category_url, review_pages_per_product=10):
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time
    import pandas as pd

    options = uc.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = uc.Chrome(options=options)
    all_data = []

    try:
        driver.get(category_url)
        time.sleep(2)
        items = driver.find_elements(By.CSS_SELECTOR, "li.search-product")
        print(f"상품 {len(items)}개 발견")

        for item_idx, item in enumerate(items):
            try:
                # 로켓프레시 뱃지 확인
                if not item.find_elements(By.CSS_SELECTOR, "span.rocket-fresh"):
                    continue

                product_name = item.find_element(By.CSS_SELECTOR, "div.name").text
                link = item.find_element(By.CSS_SELECTOR, "a.search-product-link").get_attribute("href")
                print(f"\n[{item_idx+1}] 상품명: {product_name}")
                print(f"링크: {link}")

                # 상세페이지를 새 탭에 바로 띄움
                driver.execute_script(f"window.open('{link}');")
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(2)

                # "상품평" 탭 클릭
                try:
                    review_tab = driver.find_element(By.XPATH, "//a[contains(text(), '상품평')]")
                    review_tab.click()
                    time.sleep(2)
                except Exception as e:
                    print("상품평 탭 클릭 실패:", e)

                # 리뷰 10페이지 반복
                for page in range(1, review_pages_per_product + 1):
                    try:
                        if page > 1:
                            page_btn = driver.find_element(
                                By.XPATH,
                                f"//button[contains(@class, 'js_reviewArticlePageBtn') and text()='{page}']"
                            )
                            page_btn.click()
                            time.sleep(2)

                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.js_reviewArticleListContainer"))
                        )

                        review_articles = driver.find_elements(
                            By.CSS_SELECTOR, "div.js_reviewArticleListContainer article.sdp-review__article__list"
                        )
                        for article in review_articles:
                            try:
                                content = article.find_element(
                                    By.CSS_SELECTOR, "div.sdp-review__article__list__review__content"
                                ).text
                                nickname = article.find_element(
                                    By.CSS_SELECTOR, "span.sdp-review__article__list__info__user__name"
                                ).text
                                rating = article.find_element(
                                    By.CSS_SELECTOR, "div.sdp-review__article__list__info__product-info__star-orange"
                                ).get_attribute("data-rating")
                                date = article.find_element(
                                    By.CSS_SELECTOR, "div.sdp-review__article__list__info__product-info__reg-date"
                                ).text
                                all_data.append({
                                    "상품명": product_name,
                                    "상품링크": link,
                                    "유저닉네임": nickname,
                                    "유저별별점": rating,
                                    "리뷰본문": content,
                                    "리뷰작성일": date
                                })
                            except Exception as e:
                                continue
                    except Exception as e:
                        break

                # 새 탭 닫고, 원래 탭으로 복귀
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except Exception as e:
                print("상품 리뷰 수집 중 에러:", e)
                continue
    finally:
        driver.quit()

    df = pd.DataFrame(all_data)
    return df


def patch_uc_once():
    options = uc.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0")
    driver = uc.Chrome(options=options)
    driver.quit()


def make_url(keyword, page=1):
    return f"https://www.coupang.com/np/search?q={quote(keyword)}&sorter=saleCountDesc&page={page}"


def get_coupang_search(keyword):
    # 크롬 옵션 설정 (브라우저 창 안 띄우고 싶으면 options.add_argument("--headless") 추가)
    options = Options()
    # options.add_argument("--headless")  # 필요시 주석 해제

    # 크롬 드라이버 경로 지정 (chromedriver.exe가 PATH에 있으면 생략 가능)
    driver = webdriver.Chrome(options=options)

    try:
        # 키워드 인코딩 및 URL 생성
        keyword = "신선 리프레시 " + keyword
        url = f"https://www.coupang.com/np/search?component=&q={quote(keyword)}&channel=user"
        driver.get(url)
        time.sleep(3)  # 페이지 로딩 대기

        # 로켓프레시 상품만 추출
        products = driver.find_elements(By.CSS_SELECTOR, "li.search-product")
        for product in products:
            try:
                # 로켓프레시 뱃지 확인
                badge = product.find_elements(By.CSS_SELECTOR, "span.rocket-fresh")
                if not badge:
                    continue  # 로켓프레시 아니면 패스

                name = product.find_element(By.CSS_SELECTOR, "div.name").text
                if "라즈베리" in name:
                    link = product.find_element(By.CSS_SELECTOR, "a.search-product-link").get_attribute("href")
                    print(f"상품명: {name}")
                    print(f"링크: {link}")

                    # 상세페이지 새 탭에서 열기
                    driver.execute_script("window.open(arguments[0]);", link)
                    driver.switch_to.window(driver.window_handles[1])
                    time.sleep(2)

                    # (1) "상품평" 탭 클릭
                    try:
                        review_tab = driver.find_element(By.XPATH, "//a[contains(text(), '상품평')]")
                        review_tab.click()
                        time.sleep(2)
                    except Exception as e:
                        print("상품평 탭 클릭 실패:", e)

                    # (2) 리뷰 컨테이너 대기
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.js_reviewArticleListContainer"))
                        )
                    except:
                        print("리뷰 컨테이너 로딩 실패")
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        continue

                    # (3) 리뷰 추출
                    review_articles = driver.find_elements(By.CSS_SELECTOR, "div.js_reviewArticleListContainer article.sdp-review__article__list")
                    print(f"리뷰 개수: {len(review_articles)}")
                    for article in review_articles:
                        try:
                            content = article.find_element(By.CSS_SELECTOR, "div.sdp-review__article__list__review__content").text
                            print("리뷰:", content)
                            print("="*30)
                        except Exception as e:
                            print("리뷰 본문 추출 실패:", e)
                            continue

                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    break  # 첫 번째 로켓프레시 라즈베리 상품만
            except Exception as e:
                print("에러:", e)
                continue
    finally:
        driver.quit()


if __name__ == "__main__":
    driver = get_driver()
    driver.get("https://www.coupang.com/np/search?component=&q=라즈베리&channel=user")
    time.sleep(2)
    keyword = "라즈베리"
    url = f"https://www.coupang.com/np/search?component=&q={keyword}&channel=user"
    df = get_product_and_reviews(url, review_pages_per_product=10)
    print(df.head())
    # df.to_excel("쿠팡_라즈베리_리뷰.xlsx", index=False)
