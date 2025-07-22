from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pandas as pd
from google_play_scraper import reviews, Sort

driver = webdriver.Chrome()

url = 'https://play.google.com/store/apps/details?id=com.instacart.client&hl=en&gl=US&showAllReviews=true'
driver.get(url)
print("브라우저에서 reCAPTCHA(로봇이 아닙니다) 인증을 직접 통과하세요.")
input("인증이 끝나면 엔터를 눌러주세요...")

for _ in range(5):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

review_blocks = driver.find_elements(By.CSS_SELECTOR, 'div.d15Mdf.bAhLNe')

results = []

for i in review_blocks:
    try:
        name = i.find_element(By.CLASS_NAME, 'X5PpBb').text
        review = i.find_element(By.CLASS_NAME, 'h3YV2d').text
        date = i.find_element(By.CLASS_NAME, 'bp9Aid').text
        rating_text = i.find_element(By.CLASS_NAME, 'iXRFPc').get_attribute('aria-label')
        rating = rating_text.split(' ')[0]
        try:
            helpful_text = i.find_element(By.CLASS_NAME, 'AJTPZc').text
            if helpful_text:
                helpful = helpful_text.split(' ')[0]
            else:
                helpful = '0'
        except:
            helpful = '0'

        results.append({
            'name': name,
            'date': date,
            'review': review,
            'rating': rating,
            'helpful': helpful
        })
    except Exception as e:
        print(f"오류 발생: {e}")
        continue

# DataFrame으로 변환 및 CSV 저장
df = pd.DataFrame(results)
df.to_csv('instacart_reviews.csv', index=False, encoding='utf-8-sig')
print("instacart_reviews.csv 파일로 저장 완료!")

driver.quit()

result, _ = reviews(
    'com.instacart.client',
    lang='en',
    country='us',
    sort=Sort.MOST_RELEVANT,
    count=200
)

for r in result:
    if r.get('thumbsUp', 0) not in [0, None]:
        print(r['content'])
        print('thumbsUp:', r.get('thumbsUp', 0))
        print('---')