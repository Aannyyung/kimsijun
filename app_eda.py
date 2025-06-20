import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # population_trends.csv 데이터셋 소개
        st.markdown("""
        ---
        ### 📘 Population Trends 데이터셋 안내

        - **파일명**: `population_trends.csv`  
        - **설명**: 연도별 지역 인구, 출생/사망자 수 등의 인구 통계 데이터를 기반으로 대한민국의 인구 추세를 분석합니다.

        #### 📊 주요 컬럼 설명:
        - `연도`: 데이터가 측정된 연도
        - `지역`: 전국, 서울, 부산 등 광역시도 단위 지역명
        - `행정구역`: 세부 지역 또는 시군구 단위 행정명
        - `인구`: 해당 지역의 총 인구 수
        - `출생아수(명)`: 해당 연도 출생한 아기 수
        - `사망자수(명)`: 해당 연도 사망자 수

        #### 📈 분석 기능 안내:
        - **기초 통계**: 세종시 데이터를 중심으로 기초 통계, 데이터 구조 확인
        - **연도별 추이**: 전국 인구 변화 및 2035년 예측 시각화
        - **지역별 분석**: 최근 5년간 지역별 인구 변화량 및 비율 분석
        - **변화량 분석**: 연도별 인구 증감 Top 100
        - **시각화**: 지역별 누적 인구 영역 그래프 (Stacked Area Chart)

        > 📥 좌측 메뉴 또는 아래 업로더를 통해 population_trends.csv 파일을 업로드하면, 탭별 분석 결과를 확인할 수 있습니다.
        """)
        

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("👥 Population Trends EDA")

        uploaded_file = st.file_uploader("인구 추세 데이터 업로드 (population_trends.csv)", type=["csv"])
        if not uploaded_file:
            st.info("CSV 파일을 업로드해주세요.")
            return

        df = pd.read_csv(uploaded_file)
        df.replace('-', 0, inplace=True)

        tabs = st.tabs(["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

        # -----------------------
        # 탭 1: 기초 통계 (세종시 중심 전처리)
        with tabs[0]:
        st.subheader("세종시 데이터 전처리 및 통계")

        if '행정구역' in df.columns:
            sejong_df = df[df['행정구역'].astype(str).str.contains('세종', na=False)].copy()
            sejong_df.replace('-', 0, inplace=True)

            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                sejong_df[col] = pd.to_numeric(sejong_df[col], errors='coerce').fillna(0).astype(int)

            st.dataframe(sejong_df)

            st.subheader("요약 통계 (describe)")
            st.write(sejong_df.describe())

            st.subheader("데이터프레임 구조 (info)")
            buffer = io.StringIO()
            sejong_df.info(buf=buffer)
            info_str = buffer.getvalue()
            st.text(info_str)

        

        # -----------------------
        # 탭 2: 연도별 추이 + 2035 예측
        # -----------------------
        with tabs[1]:
            st.subheader("전국 인구 추세 및 2035년 예측")

            df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0).astype(int)
            df['출생아수(명)'] = pd.to_numeric(df['출생아수(명)'], errors='coerce').fillna(0).astype(int)
            df['사망자수(명)'] = pd.to_numeric(df['사망자수(명)'], errors='coerce').fillna(0).astype(int)
            df['연도'] = pd.to_numeric(df['연도'], errors='coerce')

            national_df = df[df['지역'] == '전국'].copy()

            recent_years = national_df.sort_values('연도', ascending=False).head(3)
            recent_avg_increase = (recent_years['출생아수(명)'] - recent_years['사망자수(명)']).mean()

            last_year = int(national_df['연도'].max())
            last_population = national_df[national_df['연도'] == last_year]['인구'].values[0]
            projected_population = int(last_population + recent_avg_increase * (2035 - last_year))

            plt.figure(figsize=(10, 5))
            plt.plot(national_df['연도'], national_df['인구'], marker='o', label='Actual')
            plt.scatter(2035, projected_population, color='red', label='Projected (2035)')
            plt.text(2035, projected_population, f'{projected_population:,}', ha='left', va='bottom')
            plt.title("Population Trend and 2035 Projection")
            plt.xlabel("Year")
            plt.ylabel("Population")
            plt.legend()
            plt.grid(True)

            st.pyplot(plt.gcf())

        # -----------------------
        # 탭 3: 지역별 분석 (최근 5년)
        # -----------------------
        with tabs[2]:
            st.subheader("최근 5년간 지역별 인구 변화량 및 변화율")

            df = df[df['지역'] != '전국'].copy()
            df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0).astype(int)

            recent_years = sorted(df['연도'].unique())[-5:]
            df_recent = df[df['연도'].isin(recent_years)]

            grouped = df_recent.groupby(['지역', '연도'])['인구'].sum().unstack()
            grouped['Change'] = (grouped[recent_years[-1]] - grouped[recent_years[0]]) / 1000
            grouped['Rate (%)'] = ((grouped[recent_years[-1]] - grouped[recent_years[0]]) / grouped[recent_years[0]]) * 100

            region_translation = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }
            grouped.index = grouped.index.map(region_translation)

            # 변화량 시각화
            change_df = grouped.sort_values('Change', ascending=False)
            plt.figure(figsize=(10, 7))
            ax = sns.barplot(x='Change', y=change_df.index, data=change_df, palette='viridis')
            for i, value in enumerate(change_df['Change']):
                ax.text(value + 1, i, f"{value:.1f}", va='center')
            plt.title("Population Change Over 5 Years (Thousands)")
            st.pyplot(plt.gcf())

            # 변화율 시각화
            rate_df = grouped.sort_values('Rate (%)', ascending=False)
            plt.figure(figsize=(10, 7))
            ax2 = sns.barplot(x='Rate (%)', y=rate_df.index, data=rate_df, palette='coolwarm')
            for i, value in enumerate(rate_df['Rate (%)']):
                ax2.text(value + 0.1, i, f"{value:.1f}%", va='center')
            plt.title("Population Growth Rate Over 5 Years (%)")
            st.pyplot(plt.gcf())

        # -----------------------
        # 탭 4: 변화량 분석 (Top 100)
        # -----------------------
        with tabs[3]:
            st.subheader("Top 100 Year-over-Year Population Changes")

            df['증감'] = df.groupby('지역')['인구'].diff().fillna(0).astype(int)
            top_changes = df.reindex(df['증감'].abs().sort_values(ascending=False).index).head(100).copy()

            top_changes['인구'] = top_changes['인구'].apply(lambda x: f"{x:,}")
            top_changes['증감'] = top_changes['증감'].apply(lambda x: f"{x:,}")

            def highlight_change(val):
                val_int = int(val.replace(",", ""))
                if val_int > 0:
                    return 'background-color: #cce5ff'
                elif val_int < 0:
                    return 'background-color: #f8d7da'
                return ''

            styled_df = top_changes.style.applymap(highlight_change, subset=['증감'])
            st.dataframe(styled_df, use_container_width=True)

        # -----------------------
        # 탭 5: 누적 영역 시각화
        # -----------------------
        with tabs[4]:
            st.subheader("연도별 지역별 누적 인구 스택 영역 그래프")

            df['지역'] = df['지역'].map(region_translation)
            pivot_df = df.pivot_table(index='연도', columns='지역', values='인구', aggfunc='sum').fillna(0).sort_index()

            plt.figure(figsize=(12, 6))
            pivot_df.plot.area(colormap='tab20', alpha=0.9)
            plt.title("Population Trend by Region (Stacked Area)")
            plt.xlabel("Year")
            plt.ylabel("Population")
            plt.legend(title="Region", loc='upper left', bbox_to_anchor=(1.0, 1.0))
            plt.tight_layout()

            st.pyplot(plt.gcf())




# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
