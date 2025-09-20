````markdown
# 🚀 Crawl_Naver-Cafe-for-bladder_cancer

네이버 카페에서 방광암 관련 게시글과 댓글을 수집하고, 특정 키워드에 대한 언급 횟수를 분석하여 엑셀 파일로 저장하는 크롤러입니다. 환자분들의 경험과 치료 과정에 대한 인사이트를 얻는 데 활용될 수 있습니다.

## 주요 기능

- 네이버 카페 게시판 크롤링
- **게시글 본문 및 댓글** 수집
- **'키트루다', '바벤시오'** 등 특정 항암제 및 부작용, 삶의 질 관련 키워드 언급 횟수 분석
- 공지사항 제외 및 기간 설정을 통한 선택적 수집
- 엑셀 파일로 결과 저장

---

## 🏗️ 크롤러 동작 로직

이 크롤러는 다음과 같은 단계로 동작하여 데이터를 수집하고 분석합니다.

### 1. 로그인 및 페이지 접속

먼저 **Selenium**을 이용해 네이버에 로그인합니다. 이후 설정 파일에 지정된 카페 및 게시판 URL에 자동으로 접속합니다.

### 2. 게시글 목록 순회

게시판의 첫 페이지부터 시작하여 게시글 목록을 순서대로 읽습니다. 각 게시글의 **작성일**을 확인하여 설정된 기간(`PERIOD_DAYS`) 내의 게시글인지 검증합니다. 기간을 벗어나는 게시글이 발견되면 크롤링을 중단하고 다음 단계로 넘어갑니다.

### 3. 게시글 상세 페이지 진입 및 데이터 추출

기간 내의 게시글을 발견하면, 해당 게시글의 상세 페이지로 이동하여 **본문**과 **댓글**을 추출합니다. 이 과정은 다음과 같이 진행됩니다.

- **`iframe` 전환**: 게시글 본문은 `cafe_main`이라는 별도의 `iframe` 안에 있습니다. 크롤러는 이 프레임으로 전환하여 본문 내용을 추출합니다.
- **프레임 복귀**: 댓글은 메인 페이지에 위치하므로, 본문 추출 후에는 원래의 메인 프레임으로 복귀합니다.
- **댓글 추출**: 복귀한 메인 프레임에서 댓글 섹션을 찾아 댓글 내용을 추출합니다.

### 4. 키워드 분석 및 데이터 저장

수집한 **게시글 제목, 본문, 댓글**의 모든 텍스트를 조합하여 사전에 정의된 키워드(예: '키트루다', '부작용' 등)가 각각 몇 번 언급되었는지 집계합니다. 모든 정보(제목, 본문, 작성일, 조회수, 키워드 언급 횟수)는 구조화된 데이터 형태로 정리되어 최종적으로 `results` 폴더에 엑셀 파일로 저장됩니다.

이러한 로직을 통해 방대한 게시글 데이터 속에서 필요한 정보를 효율적으로 추출하고, 분석 가능한 형태로 가공할 수 있습니다.

---

## 필요 사항

- Python 3.7 이상
- Chrome 브라우저

---

## 설치 방법

1.  저장소 클론

    ```bash
    git clone [repository_url]
    cd BladderCancerInsights
    ```

2.  가상환경 생성 및 활성화

    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    ```

3.  필요한 패키지 설치
    ```bash
    pip install -r requirements.txt
    ```

---

## 설정 방법

1.  `.config.example` 파일을 `.config`로 복사합니다.

    ```bash
    cp .config.example .config
    ```

2.  `.config` 파일을 열어 아래 설정값을 채워주세요.
    ```ini
    CAFE_NAME=카페이름
    CLUB_ID=카페ID
    MENU_ID=게시판ID
    PERIOD_DAYS=30
    NAVER_ID=네이버아이디
    NAVER_PASSWORD=네이버비밀번호
    ```

### 설정값 설명

- `CAFE_NAME`: 카페 URL의 도메인 이름 (예: cancer.naver.com -> cancer)
- `CLUB_ID`: 카페의 고유 ID (URL에서 `clubid=숫자` 부분)
- `MENU_ID`: 게시판의 고유 ID (URL에서 `menuid=숫자` 부분)
- `PERIOD_DAYS`: 크롤링할 기간 (오늘로부터 과거로 n일)
- `NAVER_ID`: 네이버 로그인 아이디
- `NAVER_PASSWORD`: 네이버 로그인 비밀번호

---

## 사용 방법

1.  터미널에서 프로그램을 실행합니다.

    ```bash
    python main.py
    ```

2.  **결과 확인:**
    - 크롤링된 데이터는 `results` 폴더에 엑셀 파일로 저장됩니다.
    - 파일명 형식: `naver_cafe_articles_YYYYMMDD_HHMMSS.xlsx`

---

## 주의사항

- **로그인 및 권한:** 네이버 카페 회원 로그인이 필요하며, 해당 게시판의 읽기 권한이 있어야 합니다.
- **서버 부하:** 과도한 크롤링은 서버에 부담을 줄 수 있으니 적절한 간격을 두고 사용해주세요.
- **윤리적 사용:** 크롤링한 데이터의 저작권과 개인정보 보호에 유의해주세요. 이 도구는 연구 및 분석 목적으로만 활용되어야 합니다.

---

## 파일 구조
````

.
├── README.md
├── requirements.txt
├── .config.example
├── .gitignore
├── main.py
├── naver_cafe_crawler.py
└── results/
    └── naver_cafe_articles\_[timestamp].xlsx

```

---

## 라이선스

MIT License

---

## 문의사항

문의사항이나 개선 제안은 [GitHub Issues](https://github.com/your-username/BladderCancerInsights/issues)를 통해 남겨주세요.
```
