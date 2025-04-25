import streamlit as st
import time
import os
import tempfile

# 필요한 패키지 설치 확인
try:
    import PyPDF2
except ImportError:
    st.warning("PyPDF2 패키지를 설치 중입니다...")
    import subprocess
    subprocess.check_call(["pip", "install", "PyPDF2"])
    import PyPDF2
    st.success("PyPDF2 패키지가 설치되었습니다.")

try:
    import openai
except ImportError:
    st.warning("openai 패키지를 설치 중입니다...")
    import subprocess
    subprocess.check_call(["pip", "install", "openai"])
    import openai
    st.success("openai 패키지가 설치되었습니다.")

# 페이지 기본 설정
st.set_page_config(
    page_title="국회 회의록 분석기",
    page_icon="📚",
    layout="wide"
)

# 제목 및 설명
st.title("📚 국회 회의록 분석 시스템")
st.markdown("""
이 애플리케이션은 국회 회의록 PDF를 분석하여 주요 내용을 구조화된 형태로 요약해줍니다.
""")

# 세션 상태 초기화
if 'OPENAI_API_KEY' not in st.session_state:
    st.session_state.OPENAI_API_KEY = None
if 'SELECTED_MODEL' not in st.session_state:
    st.session_state.SELECTED_MODEL = "gpt-4o"  # 기본 모델

# API 키 입력 및 모델 선택 섹션
with st.sidebar:
    st.header("⚙️ 설정")
    
    # API 키 입력
    api_key = st.text_input("OpenAI API 키를 입력하세요", type="password")
    if api_key:
        st.session_state.OPENAI_API_KEY = api_key
        openai.api_key = api_key
    
    # 모델 선택
    st.subheader("🤖 모델 선택")
    model_options = {
        "GPT-4o": "gpt-4o",
        "GPT-4.1": "gpt-4.1",
        "GPT-4.1 mini": "gpt-4.1-mini"
    }
    selected_model_name = st.radio(
        "분석에 사용할 모델을 선택하세요:",
        options=list(model_options.keys())
    )
    st.session_state.SELECTED_MODEL = model_options[selected_model_name]
    
    # 모델 설명
    st.markdown("---")
    st.markdown("### 📝 모델 설명")
    model_descriptions = {
        "GPT-4o": "가장 빠른 처리 속도와 합리적인 성능을 제공합니다.",
        "GPT-4.1": "최신 모델로, 가장 정확한 분석을 제공합니다.",
        "GPT-4.1 mini": "GPT-4.1의 경량화 버전으로, 빠른 처리와 정확성의 균형을 제공합니다."
    }
    st.info(model_descriptions[selected_model_name])

def extract_text_from_pdf(pdf_file):
    """PDF 파일에서 텍스트를 추출합니다."""
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    except Exception as e:
        st.error(f"PDF 파일 처리 중 오류가 발생했습니다: {e}")
        return None
    return text

def analyze_minutes_with_openai(minutes_text):
    """OpenAI API를 사용하여 회의록 텍스트를 분석하고 요약합니다."""
    analysis_prompt = """
당신은 대한민국 국회의 회의록을 정리하는 전문가입니다. 아래의 구조와 지침에 따라 회의 내용을 Markdown 형식으로 구조화하여 요약하세요.
---
## 📥 입력: 회의록 전체 텍스트 또는 PDF
---
## 📤 출력: Markdown 기반 구조화 요약
---
### 1. 🗂 회의 메타정보
```markdown
## 🗂 회의 개요
- 회의명: 
- 일시: 
- 장소: 
- 위원장:
- 수석전문위원 및 주요 발언자:
- 담당 부처:
- 상정된 전체 안건 수:
- 실제 논의된 안건 수: (의사일정 제X항, …)
```
---
### 2. 📌 논의된 안건별 구조화 요약  
**논의 시간이 길고 쟁점이 다층적으로 이어질 경우, 발언자 순서 및 흐름을 따라 단계적으로 정리합니다.**  
```markdown
## 📌 [안건 제목]
- 법안명:
- 의안번호:
- 대표발의:
### 🧾 주요 개정 내용
- (개정 내용 요약)
### 🧩 토론 쟁점 요약
#### ▫️ 1단계 쟁점: (예: 제도 정의 및 용어 해석)
- 김승원 위원: '최선집행의무' 주체에 혼란 → 정부에 명확한 설명 요구
- 금융위 박민우 국장: 규정 구조 해석 제시
#### ▫️ 2단계 쟁점: (예: 제도 운영 방식과 영향)
- 유동수 위원: ATS의 거래시간과 기존 거래소 간 영향 분석 요청
- 김현정 위원: 국민 대상 홍보 부족 문제 제기
#### ▫️ 3단계 쟁점: (예: 정책 방향성 및 제도적 타당성)
- 박상혁 위원: 해외 사례 비교 및 향후 복수 ATS 도입 가능성 질의
- 강명구 위원: 복수거래소 체제에서 불공정거래 감시 가능성 질의
💬 [감정 및 태도 분석]
- 김승원 위원: 반복 질의 → 구조적 혼란과 신중함이 혼재
- 강민국 위원: 정부 답변에 불만, 압박성 발언 사용
- 김현정 위원: 국민 이해 부족에 대한 적극적 문제 제기
### 🏢 [기업 관련 분석]
- 기업명: (예: 넥스트레이드 ATS)
- 언급 맥락: 대체시장으로서 법적 지위 및 제도적 영향
### 🧠 [분석]
- 논의 흐름에 따라 법안의 제도적 위치 및 정책적 파급력 분석
- 다단계 쟁점 정리를 통해 중간 맥락 손실 없이 전체 구조 반영
### 💬 [의견]
- (위원별 정책 제언 또는 구조적 우려 중심)
### ✅ 의결 결과
- (예: 원안 의결, 수정가결, 대안 마련 후 전체회의 보고 등)
```
---
### 3. 📝 언급된 법안
```markdown
## 📝 언급만 된 법안
- 전자상거래법 일부개정법률안(의안번호 XXXX, 박상혁 의원 대표발의)
```
---
### ⚠️ 유의사항
- ❌ 논의되지 않은 안건은 제외. 단순 언급은 목록으로만 기록
- ✅ **쟁점이 길게 이어질 경우, 쟁점별 논의 단계를 나누어 정리**  
- ✅ 발언 순서를 따라 구조화하되, **질문 → 해석 → 반론 → 합의/보류 흐름**을 유지
- ✅ [감정 및 태도 분석]은 발언자의 태도 변화 또는 긴장 포인트를 서술
- ✅ Markdown 포맷과 논리 흐름을 철저히 유지
"""
    
    full_prompt = f"{analysis_prompt}\n\n--- 회의록 텍스트 ---\n{minutes_text}"
    
    try:
        # 모델별 설정
        model_settings = {
            "gpt-4o": {"temperature": 0.3},
            "gpt-4.1": {"temperature": 0.2},
            "gpt-4.1-mini": {"temperature": 0.4}
        }
        
        # 선택된 모델이 설정에 없으면 기본값 사용
        current_model = st.session_state.SELECTED_MODEL
        if current_model not in model_settings:
            st.warning(f"모델 '{current_model}'에 대한 설정이 없습니다. 기본 설정을 사용합니다.")
            settings = {"temperature": 0.3}
        else:
            settings = model_settings[current_model]
        
        # API 호출
        try:
            response = openai.chat.completions.create(
                model=current_model,
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                temperature=settings["temperature"]
            )
            return response.choices[0].message.content
        except Exception as api_error:
            st.error(f"OpenAI API 호출 중 오류가 발생했습니다: {api_error}")
            st.info("모델 이름이 올바른지 확인해 주세요.")
            return None
            
    except Exception as e:
        st.error(f"예상치 못한 오류가 발생했습니다: {e}")
        return None

# 메인 애플리케이션 로직
def main():
    if not st.session_state.OPENAI_API_KEY:
        st.warning("👈 사이드바에서 OpenAI API 키를 입력해주세요.")
        return

    # 파일 업로드
    uploaded_file = st.file_uploader("회의록 PDF 파일을 업로드하세요", type=['pdf'])
    
    if uploaded_file:
        with st.spinner("PDF 파일을 처리 중입니다..."):
            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name

            # PDF 텍스트 추출
            with open(tmp_file_path, 'rb') as pdf_file:
                minutes_text = extract_text_from_pdf(pdf_file)
            
            # 임시 파일 삭제
            os.unlink(tmp_file_path)

            if minutes_text:
                st.success("PDF 텍스트 추출이 완료되었습니다.")
                
                # 현재 선택된 모델 정보 표시
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"📌 선택된 모델: **{st.session_state.SELECTED_MODEL}**")
                with col2:
                    model_display_name = next((k for k, v in model_options.items() if v == st.session_state.SELECTED_MODEL), "알 수 없음")
                    st.info(f"📋 모델 설명: {model_descriptions.get(model_display_name, '정보 없음')}")
                
                # 분석 시작 버튼
                if st.button("회의록 분석 시작"):
                    with st.spinner(f"OpenAI {st.session_state.SELECTED_MODEL} 모델을 통해 회의록을 분석 중입니다..."):
                        # 분석 시작 시간 기록
                        start_time = time.time()
                        
                        summary = analyze_minutes_with_openai(minutes_text)
                        
                        # 분석 완료 시간 계산
                        end_time = time.time()
                        analysis_time = round(end_time - start_time, 1)
                        
                        if summary:
                            st.success(f"✅ 분석 완료! (소요 시간: {analysis_time}초)")
                            st.markdown("## 📊 분석 결과")
                            st.markdown(summary)
                            
                            # 분석 결과 다운로드 버튼
                            st.download_button(
                                label="분석 결과 다운로드",
                                data=summary,
                                file_name="회의록_분석결과.md",
                                mime="text/markdown"
                            )
                        else:
                            st.error("분석 중 오류가 발생했습니다. 다른 모델을 선택하거나 API 키를 확인해 주세요.")

if __name__ == "__main__":
    main()