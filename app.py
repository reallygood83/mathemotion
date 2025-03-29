import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os.path
import numpy as np
import base64
from io import BytesIO
import json
import matplotlib.font_manager as fm

# 페이지 설정
st.set_page_config(page_title="학생 설문 분석 MCP", layout="wide")

# 커스텀 CSS 스타일
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700&display=swap');

.main-title {
    font-family: 'Nanum Gothic', sans-serif !important;
    font-size: 2.5rem;
    color: #7D5A50;
    background: linear-gradient(45deg, #FF8C61, #F9C784);
    padding: 0.5rem 1rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.stButton>button {
    font-family: 'Nanum Gothic', sans-serif !important;
    background-color: #F8A978;
    color: white;
    font-weight: bold;
    border-radius: 10px;
    border: none;
    padding: 0.5rem 1rem;
    transition: all 0.3s;
}

.stButton>button:hover {
    background-color: #FF8C61;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

/* 모든 텍스트에 나눔고딕 적용 */
* {
    font-family: 'Nanum Gothic', sans-serif !important;
}

/* Streamlit 기본 스타일 오버라이드 */
.stMarkdown, .stText, .stSelectbox, .stRadio, .stNumberInput, .stTextInput, .stFileUploader {
    font-family: 'Nanum Gothic', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

def set_korean_font():
    """시스템에 설치된 한글 폰트를 찾아 설정합니다."""
    try:
        # 시스템에 설치된 모든 폰트 찾기
        font_list = fm.findSystemFonts(fontpaths=None, fontext='ttf')
        
        # 한글 폰트 목록 (우선순위 순)
        korean_fonts = [
            'NanumGothic',
            'Malgun',
            'AppleGothic',
            'Noto Sans CJK KR',
            'Noto Sans KR',
            'NanumMyeongjo',
            'NanumGothicCoding'
        ]
        
        # 설치된 한글 폰트 찾기
        found_font = None
        for font_name in korean_fonts:
            matching_fonts = [f for f in font_list if font_name in f]
            if matching_fonts:
                found_font = matching_fonts[0]
                break
        
        if found_font:
            # 폰트 설정
            font_prop = fm.FontProperties(fname=found_font)
            plt.rcParams['font.family'] = font_prop.get_name()
            plt.rcParams['axes.unicode_minus'] = False
            st.success(f"한글 폰트가 적용되었습니다: {font_prop.get_name()}")
            return font_prop
        else:
            # 한글 폰트를 찾지 못한 경우 기본 폰트 사용
            plt.rcParams['font.family'] = 'DejaVu Sans'
            plt.rcParams['axes.unicode_minus'] = False
            st.warning("한글 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")
            return fm.FontProperties(family='DejaVu Sans')
            
    except Exception as e:
        st.error(f"폰트 설정 중 오류 발생: {str(e)}")
        return fm.FontProperties(family='DejaVu Sans')

# Google Sheets API 설정
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def get_google_sheets_service():
    """구글 스프레드시트 서비스 객체를 생성합니다."""
    try:
        # Streamlit Cloud 환경에서 실행 중인 경우
        if 'GOOGLE_CREDENTIALS' in st.secrets:
            credentials_json = st.secrets['GOOGLE_CREDENTIALS']
            st.success("Streamlit Cloud 환경에서 인증 정보를 성공적으로 로드했습니다.")
        else:
            # 로컬 환경에서 실행 중인 경우
            credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
            
            # 직접 경로 지정 (개발 환경용)
            if not credentials_path:
                # 기본 경로 시도
                if os.path.exists('credentials.json'):
                    credentials_path = 'credentials.json'
                    st.info("현재 디렉토리의 credentials.json 파일을 사용합니다.")
                else:
                    # 인증 파일 업로드 기능으로 설정된 경우
                    if 'google_credentials' in st.session_state:
                        credentials_json = st.session_state['google_credentials']
                        credentials = service_account.Credentials.from_service_account_info(
                            json.loads(credentials_json), scopes=SCOPES)
                        service = build('sheets', 'v4', credentials=credentials)
                        return service
                    else:
                        st.error("Google API 인증 정보가 설정되지 않았습니다.")
                        st.info("다음 방법 중 하나로 Google API 인증 정보를 설정해주세요:")
                        st.info("1. 환경 변수 GOOGLE_CREDENTIALS_PATH에 인증 파일 경로 설정")
                        st.info("2. 프로젝트 루트 디렉토리에 credentials.json 파일 위치시키기")
                        st.info("3. 사이드바에서 인증 파일 업로드")
                        st.info("4. Streamlit Cloud를 사용하는 경우 st.secrets에 GOOGLE_CREDENTIALS 설정")
                        return None
            
            with open(credentials_path, 'r') as f:
                credentials_json = f.read()
            st.success(f"{credentials_path}에서 인증 정보를 성공적으로 로드했습니다.")
        
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(credentials_json), scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except FileNotFoundError:
        st.error(f"인증 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
        return None
    except json.JSONDecodeError:
        st.error("인증 파일이 올바른 JSON 형식이 아닙니다.")
        return None
    except Exception as e:
        st.error(f"구글 스프레드시트 서비스 생성 중 오류가 발생했습니다: {str(e)}")
        return None

def get_sheet_data(service, spreadsheet_id, range_name):
    """구글 스프레드시트에서 데이터를 가져옵니다."""
    try:
        # 스프레드시트 ID와 범위가 뒤바뀐 경우를 확인
        if '!' in spreadsheet_id and not '!' in range_name:
            spreadsheet_id, range_name = range_name, spreadsheet_id
            st.info("스프레드시트 ID와 범위가 교정되었습니다.")
        
        # 시트 이름에 특수 문자가 있는 경우 작은따옴표로 감싸기
        if '!' in range_name:
            sheet_name, cell_range = range_name.split('!', 1)
            if ('.' in sheet_name or ' ' in sheet_name) and not (sheet_name.startswith("'") and sheet_name.endswith("'")):
                sheet_name = f"'{sheet_name}'"
            range_name = f"{sheet_name}!{cell_range}"
        
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        
        if not values:
            st.warning("데이터가 없습니다.")
            return None
            
        # 헤더 행 가져오기
        headers = values[0]
        
        # 실제 데이터 행 가져오기
        data = values[1:]
        
        # 데이터프레임 생성
        df = pd.DataFrame(data)
        
        # 컬럼 수가 맞지 않는 경우 처리
        if len(headers) > len(df.columns):
            # 부족한 컬럼 추가
            for i in range(len(df.columns), len(headers)):
                df[i] = None
        elif len(headers) < len(df.columns):
            # 초과 컬럼 제거
            df = df.iloc[:, :len(headers)]
        
        # 컬럼명 설정
        df.columns = headers
        
        # 설문 문항 컬럼명 정리 (기존 컬럼명과 새로운 컬럼명 매핑)
        survey_columns = {
            '타임스탬프': '타임스탬프',
            '📌 학생 번호를 선택하세요.': '학번',
            '🧑‍🎓 학생 이름을 입력하세요.': '학생 이름',
            '🤩 오늘 수학 수업이 기대돼요. (1점: 전혀 기대되지 않아요 ~ 5점: 매우 기대돼요)': '수업 기대도',
            '😨 오늘 수학 수업이 좀 긴장돼요. (1점: 전혀 긴장되지 않아요 ~ 5점: 매우 긴장돼요)': '긴장도',
            '🎲 오늘 배우는 수학 내용이 재미있을 것 같아요. (1점: 전혀 재미없을 것 같아요 ~ 5점: 매우 재미있을 것 같아요)': '재미 예상도',
            '💪 오늘 수업을 잘 해낼 자신이 있어요. (1점: 전혀 자신 없어요 ~ 5점: 매우 자신 있어요)': '자신감',
            '🎯 지금 수업에 집중하고 있어요. (1점: 전혀 집중하지 못해요 ~ 5점: 완전히 집중하고 있어요)': '집중도',
            '😆 지금 수업이 즐거워요. (1점: 전혀 즐겁지 않아요 ~ 5점: 매우 즐거워요)': '즐거움',
            '🌟 이제 수학 공부에 자신감이 더 생겼어요. (1점: 전혀 그렇지 않아요 ~ 5점: 매우 그래요)': '자신감 변화',
            '🎉 수업 후에 수학이 전보다 더 재미있어졌어요. (1점: 전혀 그렇지 않아요 ~ 5점: 매우 그래요)': '재미 변화',
            '😌 수업 후에는 수학 시간에 전보다 덜 긴장돼요. (1점: 전혀 그렇지 않아요 ~ 5점: 매우 그래요)': '긴장도 변화',
            '🧠 오늘 수업 내용을 잘 이해했어요. (1점: 전혀 이해하지 못했어요 ~ 5점: 매우 잘 이해했어요)': '이해도',
            '📋 ✏️ 오늘 배운 수학 내용을 한 줄로 요약해 보세요.': '수업 요약',
            '📋 💭 오늘 수업에서 스스로 잘한 점이나 아쉬운 점을 한 문장으로 적어 보세요.': '자기 평가'
        }
        
        # 컬럼명 매핑
        mapped_columns = {}
        for orig_col in df.columns:
            if orig_col in survey_columns:
                mapped_columns[orig_col] = survey_columns[orig_col]
            else:
                # 매핑되지 않은 컬럼은 원래 이름 유지
                mapped_columns[orig_col] = orig_col
        
        # 컬럼명 변경
        df = df.rename(columns=mapped_columns)
        
        # 숫자형 데이터 변환
        numeric_columns = ['수업 기대도', '긴장도', '재미 예상도', '자신감', '집중도', 
                         '즐거움', '자신감 변화', '재미 변화', '긴장도 변화', '이해도']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 컬럼 존재 여부 확인 및 경고
        missing_columns = [col for col in numeric_columns if col not in df.columns]
        if missing_columns:
            st.warning(f"다음 컬럼을 찾을 수 없습니다: {', '.join(missing_columns)}")
            st.info("사용 가능한 컬럼 목록:")
            st.write(df.columns.tolist())
        
        return df
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {str(e)}")
        return None

def load_example_data():
    """예제 데이터를 생성합니다."""
    # 학생 이름 리스트
    student_names = ["김철수", "이영희", "박민준", "정서연", "최준호", 
                     "강지민", "윤지현", "장현우", "한소희", "송민석"]
    
    # 날짜 생성
    dates = pd.date_range(start="2025-03-20", periods=1, freq='D')
    
    # 빈 데이터프레임 생성
    rows = []
    
    # 각 학생별 데이터 생성
    for student_name in student_names:
        for date in dates:
            # 랜덤 데이터 생성
            row = {
                '타임스탬프': date.strftime('%Y-%m-%d %H:%M:%S'),
                '학번': np.random.randint(1, 31),
                '학생 이름': student_name,
                '수업 기대도': np.random.randint(1, 6),
                '긴장도': np.random.randint(1, 6),
                '재미 예상도': np.random.randint(1, 6),
                '자신감': np.random.randint(1, 6),
                '집중도': np.random.randint(1, 6),
                '즐거움': np.random.randint(1, 6),
                '자신감 변화': np.random.randint(1, 6),
                '재미 변화': np.random.randint(1, 6),
                '긴장도 변화': np.random.randint(1, 6),
                '이해도': np.random.randint(1, 6),
                '수업 요약': '오늘은 이차방정식의 근의 공식에 대해 배웠습니다.',
                '자기 평가': '집중해서 들었지만 계산 과정에서 실수했습니다.'
            }
            rows.append(row)
    
    # 데이터프레임 생성
    df = pd.DataFrame(rows)
    return df

def create_visualization(df, chart_type, student_name=None):
    """지정된 차트 유형에 따라 시각화를 생성하고 base64로 인코딩된 이미지를 반환합니다."""
    if df is None:
        return None, "데이터를 찾을 수 없습니다."
    
    # 필요한 컬럼 목록
    required_columns = ['수업 기대도', '긴장도', '재미 예상도', '자신감', '집중도', 
                     '즐거움', '자신감 변화', '재미 변화', '긴장도 변화', '이해도']
    
    # 누락된 컬럼 확인
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return None, f"다음 컬럼을 찾을 수 없습니다: {', '.join(missing_columns)}"
    
    # 한글 폰트 설정
    korean_font = set_korean_font()
    
    # 그래프 초기화
    plt.clf()
    plt.close('all')
    
    # 그래프 생성
    fig = plt.figure(figsize=(12, 8), dpi=100)
    
    try:
        if chart_type == '학생별 설문 응답':
            if student_name is None:
                return None, "학생 이름을 지정해주세요."
            
            student_data = df[df['학생 이름'] == student_name]
            if student_data.empty:
                return None, f"'{student_name}' 학생을 찾을 수 없습니다."
            
            survey_items = ['수업 기대도', '긴장도', '재미 예상도', '자신감', '집중도', 
                        '즐거움', '자신감 변화', '재미 변화', '긴장도 변화', '이해도']
            
            # 결측값 처리
            values = student_data[survey_items].iloc[0].fillna(0)
            
            ax = fig.add_subplot(111)
            bars = ax.bar(range(len(survey_items)), values)
            
            # 한글 폰트 적용
            ax.set_title(f'{student_name} 학생의 설문 응답', fontsize=16, fontweight='bold', fontproperties=korean_font)
            ax.set_xticks(range(len(survey_items)))
            ax.set_xticklabels(survey_items, rotation=45, ha='right', fontsize=10, fontproperties=korean_font)
            ax.set_ylabel('점수 (1-5)', fontsize=12, fontproperties=korean_font)
            ax.set_ylim(0, 5)
            
            # 막대 위에 값 표시
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontproperties=korean_font)
            
            # 자기 평가 정보 추가
            if '수업 요약' in student_data.columns and '자기 평가' in student_data.columns:
                evaluation_text = f"\n수업 요약: {student_data['수업 요약'].iloc[0]}\n"
                evaluation_text += f"자기 평가: {student_data['자기 평가'].iloc[0]}"
                plt.figtext(0.02, 0.02, evaluation_text, fontsize=10, wrap=True, fontproperties=korean_font)
        
        elif chart_type == '문항별 평균 점수':
            survey_items = ['수업 기대도', '긴장도', '재미 예상도', '자신감', '집중도', 
                        '즐거움', '자신감 변화', '재미 변화', '긴장도 변화', '이해도']
            
            # 결측값 처리
            means = df[survey_items].fillna(0).mean()
            stds = df[survey_items].fillna(0).std()
            
            ax = fig.add_subplot(111)
            bars = ax.bar(range(len(survey_items)), means, yerr=stds, capsize=5)
            
            ax.set_title('문항별 평균 점수 (오차 막대: 표준편차)', fontsize=16, fontweight='bold', fontproperties=korean_font)
            ax.set_xticks(range(len(survey_items)))
            ax.set_xticklabels(survey_items, rotation=45, ha='right', fontsize=10, fontproperties=korean_font)
            ax.set_ylabel('평균 점수 (1-5)', fontsize=12, fontproperties=korean_font)
            ax.set_ylim(0, 5)
            
            # 막대 위에 값 표시
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}',
                    ha='center', va='bottom', fontproperties=korean_font)
        
        elif chart_type == '학생별 변화 추이':
            if student_name is None:
                return None, "학생 이름을 지정해주세요."
            
            student_data = df[df['학생 이름'] == student_name]
            if student_data.empty:
                return None, f"'{student_name}' 학생을 찾을 수 없습니다."
            
            changes = ['자신감 변화', '재미 변화', '긴장도 변화']
            # 결측값 처리
            values = student_data[changes].iloc[0].fillna(0)
            
            ax = fig.add_subplot(111)
            bars = ax.bar(range(len(changes)), values)
            
            ax.set_title(f'{student_name} 학생의 수업 전후 변화', fontsize=16, fontweight='bold', fontproperties=korean_font)
            ax.set_xticks(range(len(changes)))
            ax.set_xticklabels(changes, rotation=45, ha='right', fontsize=12, fontproperties=korean_font)
            ax.set_ylabel('변화 점수 (1-5)', fontsize=12, fontproperties=korean_font)
            ax.set_ylim(0, 5)
            
            # 막대 위에 값 표시
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontproperties=korean_font)
        
        elif chart_type == '문항별 상관관계':
            survey_items = ['수업 기대도', '긴장도', '재미 예상도', '자신감', '집중도', 
                        '즐거움', '자신감 변화', '재미 변화', '긴장도 변화', '이해도']
            
            # 결측값 처리
            correlation_matrix = df[survey_items].fillna(0).corr()
            ax = fig.add_subplot(111)
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f', ax=ax)
            
            ax.set_title('문항별 상관관계', fontsize=16, fontweight='bold', fontproperties=korean_font)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=10, fontproperties=korean_font)
            ax.set_yticklabels(ax.get_yticklabels(), fontsize=10, fontproperties=korean_font)
        
        # 여백 조정
        plt.tight_layout(pad=3.0)
        
        # 그래프를 base64로 인코딩
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=300, facecolor='white')
        buf.seek(0)
        img_str = base64.b64encode(buf.getvalue()).decode()
        plt.close()
        
        return img_str, None
    except Exception as e:
        return None, f"시각화 생성 중 오류가 발생했습니다: {str(e)}"

def analyze_survey_data(spreadsheet_id, range_name, chart_type, student_name=None):
    """구글 스프레드시트에서 데이터를 가져와서 시각화를 생성합니다."""
    try:
        service = get_google_sheets_service()
        if service is None:
            return None, "구글 스프레드시트 서비스를 초기화할 수 없습니다. 인증 정보를 확인해주세요."
        
        df = get_sheet_data(service, spreadsheet_id, range_name)
        if df is None:
            return None, "데이터를 가져오는데 실패했습니다. 스프레드시트 ID와 범위를 확인해주세요."
        
        img_str, error = create_visualization(df, chart_type, student_name)
        if error:
            return None, error
        
        return img_str, None
    except Exception as e:
        return None, f"분석 중 오류가 발생했습니다: {str(e)}"

def main():
    # 앱 제목 표시
    st.markdown('<h1 class="main-title">📊 학생 설문 분석 MCP</h1>', unsafe_allow_html=True)
    
    # 한글 폰트 설정
    korean_font = set_korean_font()
    
    # 사이드바 설정
    st.sidebar.title('🌈 설정')
    
    # Google API 인증 설정 섹션
    with st.sidebar.expander("🔐 Google API 인증", expanded=False):
        st.markdown("""
        ### 인증 방법
        다음 중 한 가지 방법으로 Google API 인증 정보를 설정하세요:
        1. 환경 변수 `GOOGLE_CREDENTIALS_PATH`에 인증 파일 경로 설정
        2. 프로젝트 루트 디렉토리에 `credentials.json` 파일 위치시키기
        3. 아래 업로더를 통해 인증 파일 직접 업로드
        4. Streamlit Cloud를 사용하는 경우 `st.secrets`에 `GOOGLE_CREDENTIALS` 설정
        """)
        
        # 인증 파일 업로드 기능
        uploaded_cred_file = st.file_uploader("Google API 인증 파일 업로드", type=['json'])
        if uploaded_cred_file is not None:
            try:
                # 세션 상태에 파일 내용 저장
                st.session_state['google_credentials'] = uploaded_cred_file.getvalue().decode()
                # 파일을 임시로 저장
                with open('credentials.json', 'wb') as f:
                    f.write(uploaded_cred_file.getbuffer())
                st.success("인증 파일이 성공적으로 업로드되었습니다. ✅")
            except Exception as e:
                st.error(f"인증 파일 처리 중 오류 발생: {str(e)}")
    
    # 데이터 입력 방식 선택
    data_input_method = st.sidebar.radio(
        "데이터 입력 방식", 
        ["📊 구글 스프레드시트 사용", "📋 CSV 파일 업로드", "🧪 예제 데이터 사용"]
    )
    
    # 데이터 로드
    df = None
    spreadsheet_id = None
    range_name = None
    
    if data_input_method == "📊 구글 스프레드시트 사용":
        st.sidebar.header('📋 스프레드시트 설정')
        spreadsheet_id = st.sidebar.text_input('📝 스프레드시트 ID를 입력하세요')
        range_name = st.sidebar.text_input('📍 데이터 범위를 입력하세요 (예: Sheet1!A1:F100)')
        
        if spreadsheet_id and range_name:
            service = get_google_sheets_service()
            if service:
                with st.spinner('구글 스프레드시트에서 데이터를 가져오는 중...'):
                    df = get_sheet_data(service, spreadsheet_id, range_name)
                    if df is not None:
                        st.sidebar.success("스프레드시트에서 데이터를 성공적으로 가져왔습니다. ✅")
                    else:
                        st.sidebar.error("데이터를 가져오는데 실패했습니다. 스프레드시트 ID와 범위를 확인해주세요.")
            else:
                st.sidebar.error("구글 스프레드시트 서비스 초기화에 실패했습니다. 인증 정보를 확인해주세요.")
        else:
            st.sidebar.warning("스프레드시트 ID와 범위를 모두 입력해주세요.")
            
    elif data_input_method == "📋 CSV 파일 업로드":
        uploaded_file = st.sidebar.file_uploader("설문 데이터 CSV 업로드", type=['csv'])
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.sidebar.success("파일이 성공적으로 업로드되었습니다. ✅")
            except Exception as e:
                st.sidebar.error(f"파일 로드 중 오류가 발생했습니다: {str(e)}")
    else:  # 예제 데이터 사용
        df = load_example_data()
        st.sidebar.success("예제 데이터가 로드되었습니다. ✅")
    
    # 데이터가 로드된 경우에만 탭 표시
    if df is not None:
        # 탭 생성: 학생용 / 교사용
        tab1, tab2 = st.tabs(["👨‍🎓 학생용", "👨‍🏫 교사용"])
        
        # 학생 데이터 분석 (학생용 탭)
        with tab1:
            st.header("🧩 내 설문 데이터 확인하기")
            
            # 학생 이름 선택
            if '학생 이름' in df.columns:
                student_options = sorted(df['학생 이름'].unique().tolist())
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    student_name = st.selectbox('👨‍🎓 내 이름 선택하기', options=[""] + student_options)
                with col2:
                    show_data = st.button('📊 내 데이터 보기', use_container_width=True)
                
                if student_name and show_data:
                    # 학생별 설문 응답 차트
                    with st.spinner('데이터를 분석하는 중...'):
                        if data_input_method == "📊 구글 스프레드시트 사용" and spreadsheet_id and range_name:
                            # 구글 스프레드시트 데이터 분석
                            img_str, error = analyze_survey_data(spreadsheet_id, range_name, '학생별 설문 응답', student_name)
                        else:
                            # 로컬 데이터 분석
                            img_str, error = create_visualization(df, '학생별 설문 응답', student_name)
                            
                        if img_str:
                            st.success(f'"{student_name}" 학생의 설문 응답 분석이 완료되었습니다!')
                            st.image(f"data:image/png;base64,{img_str}", use_container_width=True)
                            
                            # 변화 추이 차트
                            if data_input_method == "📊 구글 스프레드시트 사용" and spreadsheet_id and range_name:
                                img_str2, error2 = analyze_survey_data(spreadsheet_id, range_name, '학생별 변화 추이', student_name)
                            else:
                                img_str2, error2 = create_visualization(df, '학생별 변화 추이', student_name)
                                
                            if img_str2:
                                st.subheader("📈 수업 전후 변화")
                                st.image(f"data:image/png;base64,{img_str2}", use_container_width=True)
                        else:
                            st.error(error)
            else:
                st.error("데이터에 '학생 이름' 컬럼이 없습니다.")
        
        # 전체 데이터 분석 (교사용 탭)
        with tab2:
            st.header("📊 전체 학생 설문 분석")
            
            # 분석 유형 선택
            chart_options = ['문항별 평균 점수', '문항별 상관관계', '모든 학생 응답 비교']
            chart_type = st.selectbox('📈 분석 유형 선택', chart_options)
            
            # 분석 버튼
            if st.button('✨ 분석 실행', use_container_width=True):
                with st.spinner('데이터를 분석하는 중...'):
                    if chart_type == '모든 학생 응답 비교':
                        # 모든 학생의 데이터를 한 페이지에 표시
                        if '학생 이름' in df.columns:
                            students = sorted(df['학생 이름'].unique().tolist())
                            
                            # 학생별 응답을 그리드 형태로 표시
                            st.subheader(f"📋 전체 {len(students)}명의 학생 응답")
                            
                            survey_items = ['수업 기대도', '긴장도', '재미 예상도', '자신감', '집중도', 
                                        '즐거움', '자신감 변화', '재미 변화', '긴장도 변화', '이해도']
                            
                            # 모든 학생 데이터를 하나의 큰 차트로 시각화
                            try:
                                fig = plt.figure(figsize=(12, 8), dpi=100)
                                ax = fig.add_subplot(111)
                                
                                # 각 학생별로 다른 색상 사용
                                colors = plt.cm.tab20(np.linspace(0, 1, len(students)))
                                
                                for i, student in enumerate(students):
                                    student_data = df[df['학생 이름'] == student]
                                    values = []
                                    for item in survey_items:
                                        if item in student_data.columns:
                                            val = student_data[item].iloc[0]
                                            values.append(float(val) if pd.notna(val) else 0)
                                        else:
                                            values.append(0)
                                            
                                    # 각 학생의 데이터를 선 그래프로 표시
                                    ax.plot(range(len(survey_items)), values, marker='o', 
                                           color=colors[i], label=student, linewidth=2, alpha=0.7)
                                
                                # 차트 설정
                                ax.set_title('모든 학생의 설문 응답 비교', fontsize=16, fontweight='bold', fontproperties=korean_font)
                                ax.set_xticks(range(len(survey_items)))
                                ax.set_xticklabels(survey_items, rotation=45, ha='right', fontsize=10, fontproperties=korean_font)
                                ax.set_ylabel('점수 (1-5)', fontsize=12, fontproperties=korean_font)
                                ax.set_ylim(0, 5)
                                ax.grid(True, linestyle='--', alpha=0.7)
                                
                                # 범례 추가
                                ax.legend(title='학생 이름', bbox_to_anchor=(1.05, 1), loc='upper left', 
                                          prop=korean_font, fontsize=9)
                                
                                # 여백 조정
                                plt.tight_layout(pad=3.0)
                                
                                # 그래프를 base64로 인코딩
                                buf = BytesIO()
                                plt.savefig(buf, format='png', bbox_inches='tight', dpi=300, facecolor='white')
                                buf.seek(0)
                                img_str = base64.b64encode(buf.getvalue()).decode()
                                plt.close()
                                
                                # 이미지 표시
                                st.image(f"data:image/png;base64,{img_str}", use_container_width=True)
                                
                                # 평균값도 함께 표시
                                st.subheader("📌 문항별 평균 점수")
                                if data_input_method == "📊 구글 스프레드시트 사용" and spreadsheet_id and range_name:
                                    avg_img_str, _ = analyze_survey_data(spreadsheet_id, range_name, '문항별 평균 점수')
                                else:
                                    avg_img_str, _ = create_visualization(df, '문항별 평균 점수')
                                
                                if avg_img_str:
                                    st.image(f"data:image/png;base64,{avg_img_str}", use_container_width=True)
                                
                            except Exception as e:
                                st.error(f"시각화 중 오류가 발생했습니다: {str(e)}")
                        else:
                            st.error("데이터에 '학생 이름' 컬럼이 없습니다.")
                    else:
                        # 기존 차트 타입 (평균 점수, 상관관계)
                        if data_input_method == "📊 구글 스프레드시트 사용" and spreadsheet_id and range_name:
                            img_str, error = analyze_survey_data(spreadsheet_id, range_name, chart_type)
                        else:
                            img_str, error = create_visualization(df, chart_type)
                            
                        if img_str:
                            st.success('분석이 완료되었습니다!')
                            st.image(f"data:image/png;base64,{img_str}", use_container_width=True)
                        else:
                            st.error(error)
    else:
        if data_input_method == "📊 구글 스프레드시트 사용":
            st.info("👈 사이드바에서 스프레드시트 ID와 범위를 입력한 후 데이터를 불러와주세요.")
        elif data_input_method == "📋 CSV 파일 업로드":
            st.info("👈 사이드바에서 CSV 파일을 업로드해주세요.")
        else:
            st.error("예제 데이터를 로드하는 중 오류가 발생했습니다.")
    
    # 앱 사용법 안내
    with st.expander("📚 앱 사용 안내", expanded=False):
        st.markdown("""
        <div style="background-color: #FFF1E6; padding: 20px; border-radius: 10px; border-left: 5px solid #F8A978;">
        <h3 style="color: #7D5A50;">🚀 사용 방법</h3>
        <ol style="color: #5B4B49;">
            <li><b>데이터 입력 방식 선택</b>: 구글 스프레드시트, CSV 파일 업로드, 또는 예제 데이터 중 선택</li>
            <li><b>구글 스프레드시트 사용 시</b>: 스프레드시트 ID와 데이터 범위를 입력하고 Google API 인증 설정</li>
            <li><b>학생용</b>: 자신의 이름을 선택하여 개인 설문 결과를 확인</li>
            <li><b>교사용</b>: 다양한 분석 유형을 통해 전체 학생의 설문 데이터를 분석</li>
        </ol>
        
        <h3 style="color: #7D5A50;">🔑 인증 파일 얻는 방법</h3>
        <ol style="color: #5B4B49;">
            <li><a href="https://console.cloud.google.com/" target="_blank">Google Cloud Console</a>에 접속</li>
            <li>프로젝트를 선택하거나 새 프로젝트를 생성</li>
            <li>Google Sheets API를 사용 설정</li>
            <li>사용자 인증 정보 > 서비스 계정 > 키 만들기를 선택</li>
            <li>JSON 형식의 키를 다운로드</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)

if __name__ == '__main__':
    main()