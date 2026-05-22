import streamlit as st
import random
import os
import glob
from datetime import datetime
import pandas as pd
from weasyprint import HTML

# [단어장 표준화 파싱 엔진]
def process_dataframe(df, filename, words_list):
    filename_lower = filename.lower()
    if "뜯어먹는" in filename_lower or "1800" in filename_lower:
        headers = [str(h).strip() for h in df.columns]
        if len(headers) >= 5:
            w1, m1 = headers[2], headers[4]
            if w1 and m1 and "unnamed" not in w1.lower() and "unnamed" not in m1.lower(): words_list.append((w1, m1))
        if len(headers) >= 10:
            w2, m2 = headers[7], headers[9]
            if w2 and m2 and "unnamed" not in w2.lower() and "unnamed" not in m2.lower(): words_list.append((w2, m2))
        for _, row in df.iterrows():
            if len(row) >= 5:
                w1, m1 = str(row.iloc[2]).strip(), str(row.iloc[4]).strip()
                if w1 and m1 and w1 != 'nan' and m1 != 'nan' and not w1.isdigit(): words_list.append((w1, m1))
            if len(row) >= 10:
                w2, m2 = str(row.iloc[7]).strip(), str(row.iloc[9]).strip()
                if w2 and m2 and w2 != 'nan' and m2 != 'nan' and not w2.isdigit(): words_list.append((w2, m2))
        return
    cols = [str(c).strip() for c in df.columns]
    if any('어휘' in c for c in cols) and any('뜻' in c for c in cols):
        for i in range(len(cols)):
            if '어휘' in cols[i]:
                for j in range(i + 1, min(i + 3, len(cols))):
                    if '뜻' in cols[j]:
                        col_w, col_m = df.iloc[:, i], df.iloc[:, j]
                        for w, m in zip(col_w, col_m):
                            if pd.notna(w) and pd.notna(m):
                                w_str, m_str = str(w).strip(), str(m).strip()
                                if w_str and m_str and w_str != 'nan' and m_str != 'nan' and "어휘" not in w_str: words_list.append((w_str, m_str))
        return
    df.columns = cols
    if '단어' in cols and '뜻' in cols:
        df = df.dropna(subset=['단어', '뜻'])
        for _, row in df.iterrows(): words_list.append((str(row['단어']).strip(), str(row['뜻']).strip()))
    elif '영단어' in cols and '한글 뜻' in cols:
        df = df.dropna(subset=['영단어', '한글 뜻'])
        for _, row in df.iterrows(): words_list.append((str(row['영단어']).strip(), str(row['한글 뜻']).strip()))
    elif 'English' in cols and '의미' in cols:
        df = df.dropna(subset=['English', '의미'])
        for _, row in df.iterrows(): words_list.append((str(row['English']).strip(), str(row['의미']).strip()))
    else:
        ncol = df.shape[1]
        for col_idx in range(0, ncol - 1, 3):
            if col_idx + 2 < ncol:
                col_w, col_m = df.iloc[:, col_idx + 1], df.iloc[:, col_idx + 2]
                for w, m in zip(col_w, col_m):
                    if pd.notna(w) and pd.notna(m):
                        w_str, m_str = str(w).strip(), str(m).strip()
                        if w_str and m_str and not w_str.isdigit() and len(w_str) > 1 and "day" not in w_str.lower() and "단어" not in w_str.lower(): words_list.append((w_str, m_str))

def gather_all_vocabulary():
    words_list = []
    # 구글 드라이브 대신 현재 웹 서버 창고 내부의 파일들을 다이렉트로 탐색
    files_pool = glob.glob('./*.csv') + glob.glob('./*.xlsx')
    for f in files_pool:
        filename = os.path.basename(f)
        ext = os.path.splitext(filename)[1].lower()
        try:
            if ext == '.xlsx':
                xl = pd.ExcelFile(f)
                for sheet_name in xl.sheet_names:
                    skip = 1 if "basic" in filename.lower() or "basic" in sheet_name.lower() else 0
                    df = pd.read_excel(f, sheet_name=sheet_name, skiprows=skip)
                    process_dataframe(df, filename, words_list)
            elif ext == '.csv':
                skip = 1 if "basic" in filename.lower() else 0
                for enc in ['utf-8', 'cp949', 'utf-8-sig', 'euc-kr']:
                    try:
                        df = pd.read_csv(f, skiprows=skip, encoding=enc)
                        process_dataframe(df, filename, words_list)
                        break
                    except UnicodeDecodeError: continue
        except Exception: pass
    unique_map = {}
    for w, m in words_list:
        if w.strip() and not w.strip().isdigit() and len(w.strip()) > 1:
            if w.strip().lower() not in unique_map: unique_map[w.strip().lower()] = (w.strip(), m.strip())
    return list(unique_map.values())

def make_html_page_section(words_chunk, start_no, show_answers=False):
    left, right = words_chunk[:25], words_chunk[25:]
    html = '<table class="layout-table"><tr><td class="layout-cell"><table class="word-table"><thead><tr><th style="width:12%;">No</th><th style="width:44%;">단어 (Word)</th><th style="width:44%;">뜻 (Meaning)</th></tr></thead><tbody>'
    for i, (w, m) in enumerate(left):
        ans = m if show_answers else ""
        html += f'<tr><td class="center">{start_no + i}</td><td class="word-cell">{w}</td><td class="meaning-cell answer-text">{ans}</td></tr>'
    html += '</tbody></table></td><td class="layout-spacer"></td><td class="layout-cell"><table class="word-table"><thead><tr><th style="width:12%;">No</th><th style="width:44%;">단어 (Word)</th><th style="width:44%;">뜻 (Meaning)</th></tr></thead><tbody>'
    for i, (w, m) in enumerate(right):
        ans = m if show_answers else ""
        html += f'<tr><td class="center">{start_no + 25 + i}</td><td class="word-cell">{w}</td><td class="meaning-cell answer-text">{ans}</td></tr>'
    html += '</tbody></table></td></tr></table>'
    return html

# --- 🌐 여기부터 스트림릿 웹 화면 디자인 파트 ---
st.set_page_config(page_title="수능 영단어 마스터", page_icon="🎯", layout="centered")
st.title("🎯 수능 영단어 프리미엄 무한 생성기")
st.write("아이패드 굿노트 필기에 완전 최적화된 일주일치(7세트/700문항) 패키지를 즉석에서 조립합니다.")

# 실시간 단어 창고 인벤토리 스캔
vocab_pool = gather_all_vocabulary()
st.metric(label="현재 웹 서버에 연동된 총 고유 어휘량", value=f"{len(vocab_pool):,} 단어")

st.markdown("---")
st.write("아래 버튼을 누르면 일주일 동안 단 한 단어도 겹치지 않는 700문항짜리 28페이지 PDF 책자가 생성됩니다.")

if st.button("🔥 일주일치(700단어) 마스터 패키지 PDF 굽기", type="primary"):
    if len(vocab_pool) < 700:
        st.error("창고에 단어가 부족합니다. 파일이 정상적으로 올라갔는지 확인해주세요.")
    else:
        with st.spinner("단어장에서 중복을 걷어내고 700문제를 고르는 중... 잠시만 기다려주세요!"):
            weekly_sampled_words = random.sample(vocab_pool, 700)
            current_date = datetime.now().strftime("%Y년 %m월 %d일")
            
            # 인쇄 레이아웃 CSS 탑재
            full_html_content = """
            <!DOCTYPE html><html><head><meta charset="utf-8"><style>
                @page { size: A4; margin: 12mm 14mm; } * { box-sizing: border-box; }
                body { font-family: 'NanumGothic', sans-serif; color: #333333; margin: 0; }
                .header { border-bottom: 2px solid #2d3748; padding-bottom: 1mm; margin-bottom: 4mm; }
                .title { font-size: 15pt; font-weight: bold; text-align: center; margin: 0 0 2mm 0; }
                .info { width: 100%; font-size: 9pt; color: #4a5568; margin-bottom: 1mm; }
                .layout-table { width: 100%; border-collapse: collapse; }
                .layout-cell { width: 48.5%; vertical-align: top; } .layout-spacer { width: 3%; }
                .word-table { width: 100%; border-collapse: collapse; }
                .word-table th { background-color: #f7fafc; border: 1px solid #cbd5e0; font-size: 9pt; padding: 5px 2px; text-align: center; font-weight: bold; }
                .word-table td { border: 1px solid #cbd5e0; font-size: 9.5pt; padding: 2px 6px; height: 8.5mm; vertical-align: middle; }
                .center { text-align: center; color: #718096; font-size: 8.5pt; font-weight: bold; }
                .word-cell { font-weight: 600; color: #1a202c; } .answer-text { color: #2b6cb0; font-weight: bold; }
                .score-box { border: 1px solid #cbd5e0; padding: 2px 10px; font-weight: bold; } .page-break { page-break-before: always; }
                .set-badge { background-color: #2d3748; color: white; padding: 2px 8px; font-size: 10pt; font-weight: bold; border-radius: 4px; }
            </style></head><body>
            """
            
            for set_no in range(1, 8):
                day_words = weekly_sampled_words[(set_no-1)*100 : set_no*100]
                part1_words, part2_words = day_words[:50], day_words[50:]
                prefix_break = "class='page-break'" if set_no > 1 else ""
                
                # 시험지 지면 렌더링
                full_html_content += f"""
                <div {prefix_break}>
                    <div class="header"><h1 class="title"><span class="set-badge">SET {set_no}</span> 수능 영단어 프리미엄 테스트 (시험지 1/2)</h1>
                    <table class="info"><tr><td>출행일시: {current_date}</td><td style="text-align: right;">이름: _______________ &nbsp;&nbsp;&nbsp; 점수: <span class="score-box">&nbsp;&nbsp;&nbsp;&nbsp; / 100</span></td></tr></table></div>
                    {make_html_page_section(part1_words, start_no=1, show_answers=False)}
                </div>
                <div class="page-break">
                    <div class="header"><h1 class="title"><span class="set-badge">SET {set_no}</span> 수능 영단어 프리미엄 테스트 (시험지 2/2)</h1><table class="info"><tr><td>애플펜슬로 크게크게 글씨를 써내려가세요!</td><td style="text-align: right;">이름: _______________</td></tr></table></div>
                    {make_html_page_section(part2_words, start_no=51, show_answers=False)}
                </div>
                """
                # 정답지 지면 렌더링
                full_html_content += f"""
                <div class="page-break">
                    <div class="header"><h1 class="title"><span class="set-badge">SET {set_no} 정답</span> 수능 영단어 프리미엄 테스트 (정답지 1/2)</h1><table class="info"><tr><td>★ 채점용 정답지입니다.</td><td style="text-align: right;">총 문항수: 100문항</td></tr></table></div>
                    {make_html_page_section(part1_words, start_no=1, show_answers=True)}
                </div>
                <div class="page-break">
                    <div class="header"><h1 class="title"><span class="set-badge">SET {set_no} 정답</span> 수능 영단어 프리미엄 테스트 (정답지 2/2)</h1><table class="info"><tr><td>★ 오답 처리는 1등급의 지름길입니다.</td><td style="text-align: right;">총 문항수: 100문항</td></tr></table></div>
                    {make_html_page_section(part2_words, start_no=51, show_answers=True)}
                </div>
                """
            full_html_content += "</body></html>"
            
            # PDF 빌드 연산 수행
            HTML(string=full_html_content).write_pdf("weekly_package.pdf")
            
            with open("weekly_package.pdf", "rb") as pdf_file:
                st.download_button(
                    label="📥 아이패드에 일주일치 28페이지 PDF 즉시 다운로드",
                    data=pdf_file,
                    file_name=f"수능영단어_일주일치_7세트_{datetime.now().strftime('%m%d')}.pdf",
                    mime="application/pdf",
                    type="secondary"
                )
            st.success("🎉 단어장 생성이 완료되었습니다! 위 다운로드 단추를 누르세요!")
