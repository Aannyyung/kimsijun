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
# 페이지 선택
# ---------------------
pages = ["홈", "로그인", "회원가입", "비밀번호 찾기"]
if st.session_state.logged_in:
    pages += ["내 정보", "EDA", "로그아웃"]
selection = st.sidebar.selectbox("📁 메뉴를 선택하세요", pages)

# ---------------------
# 홈
# ---------------------
if selection == "홈":
    st.title("🏠 Home")
    if st.session_state.get("logged_in"):
        st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

    st.markdown("""
    ---
    ### 📘 Population Trends 데이터셋 안내
    - **설명**: 대한민국 연도별 지역 인구, 출생/사망자 수 등의 통계 분석
    - **기능 안내**:
        - 기초 통계, 추이 예측, 지역 분석, 변화량 분석, 시각화
    - 📥 좌측 메뉴에서 'EDA'를 클릭 후 분석 파일 업로드
    """)

# ---------------------
# 로그인
# ---------------------
elif selection == "로그인":
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
            st.experimental_rerun()
        except Exception:
            st.error("로그인 실패")

# ---------------------
# 회원가입
# ---------------------
elif selection == "회원가입":
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
            st.success("회원가입 성공! 로그인 메뉴로 이동해주세요.")
        except Exception:
            st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기
# ---------------------
elif selection == "비밀번호 찾기":
    st.title("🔎 비밀번호 찾기")
    email = st.text_input("이메일")
    if st.button("비밀번호 재설정 메일 전송"):
        try:
            auth.send_password_reset_email(email)
            st.success("비밀번호 재설정 이메일 전송 완료")
        except:
            st.error("이메일 전송 실패")

# ---------------------
# 로그아웃
# ---------------------
elif selection == "로그아웃":
    st.session_state.logged_in = False
    for key in ["user_email", "id_token", "user_name", "user_gender", "user_phone", "profile_image_url"]:
        st.session_state[key] = ""
    st.success("로그아웃 되었습니다.")
    time.sleep(1)
    st.experimental_rerun()

# ---------------------
# 내 정보
# ---------------------
elif selection == "내 정보":
    st.title("👤 사용자 정보")
    email = st.session_state.get("user_email", "")
    name = st.text_input("성명", value=st.session_state.get("user_name", ""))
    gender = st.selectbox("성별", ["선택 안함", "남성", "여성"], index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함")))
    phone = st.text_input("전화번호", value=st.session_state.get("user_phone", ""))

    uploaded = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
    if uploaded:
        path = f"profiles/{email.replace('.', '_')}.jpg"
        storage.child(path).put(uploaded, st.session_state.id_token)
        image_url = storage.child(path).get_url(st.session_state.id_token)
        st.session_state.profile_image_url = image_url
        st.image(image_url, width=150)

    if st.button("저장"):
        firestore.child("users").child(email.replace(".", "_")).update({
            "name": name,
            "gender": gender,
            "phone": phone,
            "profile_image_url": st.session_state.get("profile_image_url", "")
        })
        st.success("저장되었습니다.")

# ---------------------
# EDA
# ---------------------
elif selection == "EDA":
    st.title("📊 인구 데이터 EDA")

    uploaded = st.file_uploader("CSV 파일 업로드 (population_trends.csv)", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)
        df.replace('-', 0, inplace=True)

        tabs = st.tabs(["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

        # 탭 1
        with tabs[0]:
            st.subheader("세종시 통계")
            sejong = df[df['행정구역'].str.contains('세종', na=False)].copy()
            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                sejong[col] = pd.to_numeric(sejong[col], errors='coerce').fillna(0).astype(int)
            st.write(sejong.describe())

        # 탭 2
        with tabs[1]:
            st.subheader("전국 인구 추세 및 2035 예측")
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0).astype(int)
            df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
            national = df[df['지역'] == '전국'].copy()
            recent = national.sort_values('연도', ascending=False).head(3)
            avg_increase = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
            last_year = int(national['연도'].max())
            last_pop = national[national['연도'] == last_year]['인구'].values[0]
            proj = int(last_pop + avg_increase * (2035 - last_year))

            fig, ax = plt.subplots()
            ax.plot(national['연도'], national['인구'], marker='o')
            ax.scatter(2035, proj, color='red')
            ax.text(2035, proj, f"{proj:,}")
            st.pyplot(fig)

        # 탭 3
        with tabs[2]:
            st.subheader("최근 5년 지역별 변화")
            df = df[df['지역'] != '전국']
            df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0).astype(int)
            recent_5 = sorted(df['연도'].unique())[-5:]
            grouped = df[df['연도'].isin(recent_5)].groupby(['지역', '연도'])['인구'].sum().unstack()
            grouped['Change'] = (grouped[recent_5[-1]] - grouped[recent_5[0]]) / 1000
            fig = plt.figure()
            sns.barplot(x='Change', y=grouped.sort_values('Change').index, data=grouped.reset_index(), palette='Blues_d')
            st.pyplot(fig)

        # 탭 4
        with tabs[3]:
            st.subheader("연도별 인구 변화량 Top 100")
            df['증감'] = df.groupby('지역')['인구'].diff().fillna(0).astype(int)
            top = df.reindex(df['증감'].abs().sort_values(ascending=False).index).head(100)
            st.dataframe(top[['연도', '지역', '행정구역', '인구', '증감']])

        # 탭 5
        with tabs[4]:
            st.subheader("누적 스택 영역 그래프")
            df['지역'] = df['지역'].astype(str)
            pivot = df.pivot_table(index='연도', columns='지역', values='인구', aggfunc='sum').fillna(0).sort_index()
            pivot.plot.area(colormap='tab20', figsize=(12, 6))
            st.pyplot(plt.gcf())
    else:
        st.info("CSV 파일을 업로드해주세요")

