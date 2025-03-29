# 학생 설문 분석 MCP

학생들의 수학 수업 관련 설문 데이터를 분석하고 시각화하는 Streamlit 애플리케이션입니다.

## 기능

- 구글 스프레드시트에서 설문 데이터 불러오기
- CSV 파일 업로드를 통한 데이터 분석
- 학생별 개인 설문 결과 확인
- 전체 학생 설문 데이터 분석 및 시각화
- 다양한 차트 유형을 통한 데이터 분석

## 배포 방법

### 1. GitHub 저장소 설정

1. 이 저장소를 GitHub에 push합니다.
2. `credentials.json` 파일은 절대 push하지 마세요.

### 2. Streamlit Cloud 배포

1. [Streamlit Cloud](https://share.streamlit.io/)에 접속합니다.
2. GitHub 계정으로 로그인합니다.
3. "New app" 버튼을 클릭합니다.
4. 저장소, 브랜치, 메인 파일(app.py)을 선택합니다.
5. "Deploy!" 버튼을 클릭합니다.

### 3. Google API 인증 설정

1. Google Cloud Console에서 서비스 계정 키(JSON)를 생성합니다.
2. Streamlit Cloud의 앱 설정에서 "Secrets" 섹션을 찾습니다.
3. 다음 형식으로 secrets를 추가합니다:
   ```toml
   [GOOGLE_CREDENTIALS]
   # 여기에 credentials.json 파일의 전체 내용을 붙여넣습니다
   ```

## 로컬 개발 환경 설정

1. 저장소를 클론합니다:
   ```bash
   git clone [repository-url]
   cd [repository-name]
   ```

2. 가상환경을 생성하고 활성화합니다:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. 필요한 패키지를 설치합니다:
   ```bash
   pip install -r requirements.txt
   ```

4. Google API 인증 정보를 설정합니다:
   - Google Cloud Console에서 서비스 계정 키(JSON)를 다운로드합니다.
   - 프로젝트 루트 디렉토리에 `credentials.json`으로 저장합니다.

5. 앱을 실행합니다:
   ```bash
   streamlit run app.py
   ```

## 주의사항

- Google API 인증 정보는 절대 GitHub에 push하지 마세요.
- 민감한 데이터가 포함된 CSV 파일을 업로드할 때는 주의하세요.
- Streamlit Cloud의 무료 티어에는 리소스 제한이 있을 수 있습니다.

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 

streamlit==1.29.0
pandas==2.1.3
matplotlib==3.8.2
seaborn==0.13.0
google-api-python-client==2.108.0
google-auth-httplib2==0.1.1
google-auth-oauthlib==1.1.0
python-dotenv==1.0.0 