from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import pandas as pd
import re
import os
import ssl
import chromedriver_autoinstaller

class NaverCafeCrawler:
    def __init__(self, cafe_name, club_id, menu_id, period_days, debug_mode):
        self.cafe_name = cafe_name
        self.club_id = club_id
        self.menu_id = menu_id
        self.period_days = period_days
        self.debug_mode = debug_mode
        self.base_url = "https://cafe.naver.com"
        
        ssl._create_default_https_context = ssl._create_unverified_context
        
        self.driver = self._setup_driver()
        self.target_date = datetime.now() - timedelta(days=period_days)

        # --- ▼ 키워드 리스트를 클래스 속성으로 정의 ▼ --- 
        self.keywords = {
            '우리약제': ['바벤시오', '아벨루맙', '젬시스', '젬카보', '젬시타빈', '유지요법'],
            '경쟁약제': ['키트루다', '파드셉', '임핀지', '옵디보', 'EV+P', 'EVP'],
            '부작용': ['부작용', '폐렴', '신경', '피부', '발진', '설사', '피로', '구내염', '수포', '당뇨'],
            '삶의질': ['불안', '재발 걱정', '약값', '보험']
        }
        # --- ▲ 키워드 리스트 정의 완료 ▲ --- 
        
    def _setup_driver(self):
        chrome_options = webdriver.ChromeOptions()
        if not self.debug_mode:
            chrome_options.add_argument('--headless')
            
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--allow-insecure-localhost')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        chromedriver_autoinstaller.install()
        return webdriver.Chrome(options=chrome_options)

    def login(self, id, password):
        """네이버 로그인"""
        try:
            print("로그인 시도 중...")
            self.driver.get("https://nid.naver.com/nidlogin.login")
            
            if self.debug_mode:
                print("디버그 모드: 수동 로그인을 위해 대기 중...")
                input("로그인을 완료한 후 Enter 키를 눌러주세요...")
            else:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, 'id'))
                ).send_keys(id)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, 'pw'))
                ).send_keys(password)
                
                self.driver.find_element(By.ID, "log.login").click()
                
                WebDriverWait(self.driver, 10).until(
                    EC.url_changes(self.driver.current_url)
                )
            
            print("로그인 완료")
            return True
        except Exception as e:
            print(f"로그인 실패: {str(e)}")
            return False

    def parse_date(self, date_str):
        """날짜 문자열 파싱"""
        try:
            now = datetime.now()
            if ':' in date_str:  # 오늘 날짜 (HH:MM)
                hour, minute = map(int, date_str.split(':'))
                return datetime(now.year, now.month, now.day, hour, minute)
            else:  # YYYY.MM.DD. 형식
                date_str = date_str.rstrip('.')
                return datetime.strptime(date_str, '%Y.%m.%d')
        except Exception as e:
            print(f"날짜 파싱 에러: {e}, 입력값: {date_str}")
            return None

    def get_article_content(self, article_id):
        """게시글 상세 내용과 댓글을 iframe 내부에서 추출"""
        print(f"--- 게시글 {article_id} 상세 내용 추출 시작 ---")

        try:
            # 1. 게시글 URL 접속
            article_url = f"{self.base_url}/f-e/cafes/{self.club_id}/articles/{article_id}?menuid={self.menu_id}"
            print(f"1. URL 접속 시도: {article_url}")
            self.driver.get(article_url)
            print("1. URL 접속 완료.")
            
            # 2. iframe으로 전환
            print("2. iframe 전환 대기 중 (최대 10초)...")
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, 'cafe_main'))
                )
                print("2. iframe 전환 성공.")
            except TimeoutException:
                print("2. iframe을 찾지 못했습니다. 게시글 본문이 iframe 안에 없을 수 있습니다.")
                return {'content': "", 'comments': []}
            
            # 3. 본문 및 댓글 컨테이너 로드 대기
            print("3. 본문 및 댓글 컨테이너 로드 대기 중 (최대 10초)...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.se-main-container, .CommentBox, .article_container, .content-container'))
            )
            print("3. 컨테이너 로드 완료.")
            
            # 4. 페이지 소스 파싱 (iframe 내부)
            print("4. 페이지 소스 파싱 시작...")
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            print("4. 페이지 소스 파싱 완료.")
            
            # 5. 본문 내용 추출
            print("5. 본문 내용 추출 시작...")
            content = ""
            main_content = soup.select_one('.se-main-container, .article_container, .content-container')
            
            if main_content:
                content = main_content.get_text(strip=True)
                print("5. 본문 내용 추출 완료.")
                print(f"   - 추출된 본문: {content[:50]}...")
            else:
                print("5. 본문 내용을 찾을 수 없습니다.")

            # 6. 댓글 추출 (iframe 내부)
            print("6. 댓글 추출 시작...")
            comments = []
            comment_elements = soup.select('ul.comment_list > li.CommentItem')

            if comment_elements:
                print(f"6. 총 {len(comment_elements)}개의 댓글 요소를 찾았습니다.")
                for comment_el in comment_elements:
                    author_el = comment_el.select_one('.comment_nickname')
                    comment_text_el = comment_el.select_one('.text_comment')

                    author = author_el.get_text(strip=True) if author_el else "작성자 정보 없음"
                    comment_text = comment_text_el.get_text(strip=True) if comment_text_el else "댓글 내용 없음"

                    comments.append({'author': author, 'text': comment_text})
                print("6. 댓글 추출 완료.")
            else:
                print("6. 댓글을 찾을 수 없습니다. (선택자 문제 또는 댓글 없음)")

            # 원래 프레임으로 복귀하는 코드는 제거함 (댓글이 iframe 안에 있다는 가정 하에)
            return {'content': content, 'comments': comments}
                
        except Exception as e:
            print(f"--- 게시글 {article_id} 상세 내용 추출 실패! ---")
            print(f"   - 실패 원인: {e}")
            # 오류 발생 시에만 원래 프레임으로 돌아가도록 처리
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return {'content': "", 'comments': []}
        
        finally:
            print(f"--- 게시글 {article_id} 처리 종료 ---")


    def crawl_articles(self):
        """게시글 크롤링 실행"""
        articles = []
        page = 1
        continue_crawling = True
        
        while continue_crawling:
            try:
                print(f"\n페이지 {page} 크롤링 중...")
                
                page_url = f"{self.base_url}/f-e/cafes/{self.club_id}/menus/{self.menu_id}?page={page}"
                self.driver.get(page_url)
                
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'table.article-table'))
                )
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                all_rows = soup.select('table.article-table > tbody > tr')
                
                if not all_rows:
                    print("더 이상 게시글이 없습니다.")
                    break

                article_rows = [row for row in all_rows if not 'board-notice' in row.get('class', [])]
                print(f"발견된 일반 게시글 수: {len(article_rows)}")
                
                found_articles_on_page = False
                for row in article_rows:
                    try:
                        title_element = row.select_one('a.article')
                        if not title_element:
                            continue
                            
                        title = title_element.get_text(strip=True)
                        href = title_element['href']
                        article_id_str = href.split('/')[-1].split('?')[0]
                        
                        if not article_id_str.isdigit():
                            continue
                            
                        author_element = row.select_one('.nickname')
                        date_element = row.select_one('.type_date')
                        view_element = row.select_one('.type_readCount')
                        
                        if not author_element or not date_element or not view_element:
                            continue
                            
                        author = author_element.get_text(strip=True)
                        date_str = date_element.text.strip()
                        views = view_element.text.strip()
                        
                        post_date = self.parse_date(date_str)
                        if not post_date:
                            continue
                            
                        if post_date < self.target_date:
                            print(f"기간 초과: {date_str}")
                            continue_crawling = False
                            break
                        
                        content_data = self.get_article_content(article_id_str)
                        
                        # --- ▼ 키워드 분석 로직 추가 ▼ ---
                        found_keywords = self.analyze_keywords(title, content_data['content'], content_data['comments'])
                        
                        article_data = {
                            'article_id': article_id_str,
                            '제목': title,
                            '본문': content_data['content'],
                            '작성일': post_date,
                            '작성자': author,
                            'URL/ID': href,
                            '조회수': views,
                            **found_keywords  # 키워드 분석 결과 딕셔너리를 직접 병합
                        }
                        
                        articles.append(article_data)
                        # --- ▲ 키워드 분석 로직 추가 완료 ▲ ---
                        
                        found_articles_on_page = True
                        print(f"게시글 추출 완료: {title} ({date_str}, 조회수: {views})")
                        
                    except Exception as e:
                        print(f"게시글 처리 중 에러: {e}")
                        continue
                
                if not found_articles_on_page or not continue_crawling:
                    break
                
                page += 1
                time.sleep(1)
            
            except Exception as e:
                print(f"페이지 처리 중 에러: {e}")
                if self.debug_mode:
                    print("상세 에러:", e)
                    print("현재 URL:", self.driver.current_url)
                break
        
        return articles

    def analyze_keywords(self, title, content, comments):
        """제목, 본문, 댓글에서 키워드 언급 횟수 집계"""
        # 모든 텍스트를 하나의 문자열로 합치기
        all_text = f"{title} {content}"
        for comment in comments:
            all_text += f" {comment['text']}"
        
        # 띄어쓰기, 대소문자 무시를 위해 텍스트를 전처리
        processed_text = all_text.lower().replace(" ", "")
        
        keyword_counts = {}
        for category, keyword_list in self.keywords.items():
            for keyword in keyword_list:
                # 키워드도 띄어쓰기 제거
                processed_keyword = keyword.replace(" ", "")
                # 정규식을 사용해 언급 횟수 집계
                count = len(re.findall(re.escape(processed_keyword), processed_text, re.IGNORECASE))
                
                # 엑셀 열 이름에 맞게 키-값 쌍 생성
                keyword_counts[f'{keyword}'] = count
                
        return keyword_counts

    def save_to_excel(self, articles, filename):
        """크롤링 결과를 엑셀로 저장"""
        if not articles:
            print("저장할 게시글이 없습니다.")
            return
            
        try:
            # article_data 딕셔너리를 사용하여 DataFrame 생성
            df = pd.DataFrame(articles)
            
            df = df.sort_values('작성일', ascending=False)
            df['작성일'] = df['작성일'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            if not os.path.exists('results'):
                os.makedirs('results')
            
            output_path = os.path.join('results', filename)
            df.to_excel(output_path, index=False)
            print(f"결과가 {output_path}에 저장되었습니다.")
            
        except Exception as e:
            print(f"엑셀 저장 중 에러: {e}")

    def close(self):
        """크롤러 종료"""
        if self.debug_mode:
            input("크롤러를 종료하려면 Enter 키를 눌러주세요...")
        self.driver.quit()