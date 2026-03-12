import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

# 1. ตั้งค่าหน้าเว็บเพจ Dashboard
st.set_page_config(page_title="RMUTI Webometrics Dashboard", page_icon="📊", layout="wide")
st.title("📊 แดชบอร์ดติดตามคะแนน Openness (Webometrics)")
st.subheader("วิเคราะห์แนวโน้มผลงานวิชาการและการอ้างอิง มทร.อีสาน ย้อนหลัง 5 ปี (ฐานข้อมูล OpenAlex)")

# 2. ฟังก์ชันสำหรับดึงข้อมูลจาก API ของ OpenAlex (ใช้ ROR ID)
@st.cache_data # เก็บ Cache ไว้จะได้ไม่ต้องโหลด API ใหม่ทุกครั้งที่รีเฟรชหน้า
def fetch_openalex_data(ror_id):
    url = f"https://api.openalex.org/institutions/{ror_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# ROR ID ของ มทร.อีสาน
ror_id = "https://ror.org/04a2rz655"

with st.spinner('กำลังดึงข้อมูลจาก OpenAlex API...'):
    data = fetch_openalex_data(ror_id)

# 3. ประมวลผลและสร้างกราฟ
if data and 'counts_by_year' in data:
    # นำข้อมูลที่ได้มาจัดรูปแบบใน Pandas DataFrame
    df = pd.DataFrame(data['counts_by_year'])
    
    # กรองเอาเฉพาะข้อมูล 5 ปีย้อนหลัง (ไม่นับปีปัจจุบันที่ยังไม่จบปี)
    current_year = datetime.now().year
    df = df[(df['year'] >= current_year - 6) & (df['year'] < current_year)]
    df = df.sort_values('year')

    # แปลงปีเป็น String เพื่อให้กราฟแสดงผลสวยงาม ไม่เป็นทศนิยม
    df['year'] = df['year'].astype(str)

    # แบ่งหน้าจอเป็น 2 คอลัมน์
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📈 แนวโน้มการถูกอ้างอิง (Citations)")
        st.caption("ข้อมูลนี้ส่งผลโดยตรงต่อคะแนน Openness (10%)")
        fig_cite = px.line(df, x='year', y='cited_by_count', markers=True,
                           labels={'year': 'ปี ค.ศ.', 'cited_by_count': 'จำนวนการถูกอ้างอิง (ครั้ง)'},
                           line_shape='spline')
        fig_cite.update_traces(line_color='#FF4B4B', line_width=3, marker_size=8)
        st.plotly_chart(fig_cite, use_container_width=True)

    with col2:
        st.markdown("### 📝 แนวโน้มการตีพิมพ์ผลงาน (Works)")
        st.caption("จำนวนผลงานวิจัยทั้งหมดของมหาวิทยาลัยในระบบ")
        fig_works = px.bar(df, x='year', y='works_count', text_auto=True,
                           labels={'year': 'ปี ค.ศ.', 'works_count': 'จำนวนผลงาน (ชิ้น)'},
                           color='works_count', color_continuous_scale='Blues')
        st.plotly_chart(fig_works, use_container_width=True)

    st.markdown("---")
    st.info('💡 **ข้อเสนอแนะเชิงกลยุทธ์:** หากกราฟฝั่ง "การตีพิมพ์" สูงขึ้น แต่ "การถูกอ้างอิง" คงที่หรือลดลง มหาวิทยาลัยอาจต้องปรับนโยบายสนับสนุนให้คณาจารย์ตีพิมพ์ในวารสารระดับ Q1/Q2 หรือทำวิจัยร่วมกับเครือข่ายนานาชาติมากขึ้น เพื่อดันยอด Citation')

else:
    st.error("เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล OpenAlex โปรดตรวจสอบอินเทอร์เน็ตหรือลองใหม่อีกครั้ง")
    
    # =====================================================================
# 4. ส่วนเพิ่มเติม: ดึงข้อมูล Top 10 ผลงานวิจัยที่ถูกอ้างอิงสูงสุด
# =====================================================================

@st.cache_data
def fetch_top_works(ror_id):
    # เรียก API ดึงผลงานวิจัย กรองด้วย ROR ID และเรียงลำดับตามยอด Citation จากมากไปน้อย (Top 10)
    url = f"https://api.openalex.org/works?filter=institutions.ror:{ror_id}&sort=cited_by_count:desc&per-page=10"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

with st.spinner('กำลังดึงข้อมูล Top 10 ผลงานวิจัยดาวรุ่งจาก OpenAlex...'):
    top_works_data = fetch_top_works(ror_id)

if top_works_data and 'results' in top_works_data:
    st.markdown("---")
    st.markdown("### 🏆 Top 10 ผลงานวิจัยที่ถูกอ้างอิงสูงสุด (Most Cited Works)")
    st.caption("ข้อมูลส่วนนี้ช่วยชี้เป้า 'งานวิจัยดาวรุ่ง' ของมหาวิทยาลัย เพื่อพิจารณาสนับสนุนทุนต่อยอดและเพิ่มคะแนน Excellence/Openness")
    
    works_list = []
    for work in top_works_data['results']:
        title = work.get('title', 'ไม่มีชื่อเรื่อง')
        year = work.get('publication_year', 'N/A')
        citations = work.get('cited_by_count', 0)
        
        # ดึงชื่อผู้แต่งคนแรก (First Author)
        authorships = work.get('authorships', [])
        first_author = authorships[0]['author']['display_name'] if authorships else 'ไม่ระบุ'
        
        # ดึง URL (DOI) สำหรับคลิกไปดูเปเปอร์ต้นฉบับ
        doi = work.get('doi', '')
        
        works_list.append({
            "ชื่อผลงานวิจัย (Title)": title,
            "ปีที่ตีพิมพ์": str(year),
            "ผู้แต่งหลัก (First Author)": first_author,
            "ยอดอ้างอิง (Citations)": citations,
            "ลิงก์เอกสาร (DOI)": doi
        })
        
    # นำข้อมูลเข้าสู่ Pandas DataFrame เพื่อแสดงผลเป็นตารางสวยงาม
    df_works = pd.DataFrame(works_list)
    
    # ปรับ Index ของตารางให้เริ่มจาก 1 ถึง 10
    df_works.index = df_works.index + 1
    
    # แสดงตารางบน Streamlit (สามารถปรับขนาดและ Sort คอลัมน์ได้ในหน้าเว็บ)
    st.dataframe(
        df_works, 
        use_container_width=True,
        column_config={
            "ลิงก์เอกสาร (DOI)": st.column_config.LinkColumn("ลิงก์เอกสาร (DOI)") # ทำให้ลิงก์สามารถคลิกได้
        }
    )
else:
    st.warning("ไม่สามารถดึงข้อมูลผลงานวิจัยได้ในขณะนี้")
    
# =====================================================================
# 5. ส่วนเพิ่มเติม: ดึงข้อมูลผลงานวิจัย "ทั้งหมด" และ Export เป็น CSV
# =====================================================================

@st.cache_data
def fetch_all_works(ror_id):
    all_works = []
    # ใช้ cursor pagination ของ OpenAlex เพื่อดึงข้อมูลปริมาณมากอย่างเสถียร
    # per-page=200 คือดึงหน้าละ 200 รายการ (สูงสุดที่ API รองรับต่อรอบ)
    url = f"https://api.openalex.org/works?filter=institutions.ror:{ror_id}&sort=cited_by_count:desc&per-page=200&cursor="
    cursor = "*" # กำหนดจุดเริ่มต้น (หน้าแรก)
    
    while cursor:
        current_url = f"{url}{cursor}"
        response = requests.get(current_url)
        
        if response.status_code != 200:
            break
            
        data = response.json()
        results = data.get('results', [])
        
        if not results:
            break # ถ้าไม่มีข้อมูลแล้วให้ออกจากลูป
            
        for work in results:
            title = work.get('title', 'ไม่มีชื่อเรื่อง')
            year = work.get('publication_year', 'N/A')
            citations = work.get('cited_by_count', 0)
            doi = work.get('doi', '')
            
            authorships = work.get('authorships', [])
            first_author = authorships[0]['author']['display_name'] if authorships else 'ไม่ระบุ'
            
            all_works.append({
                "ชื่อผลงานวิจัย (Title)": title,
                "ปีที่ตีพิมพ์": str(year),
                "ผู้แต่งหลัก (First Author)": first_author,
                "ยอดอ้างอิง (Citations)": citations,
                "ลิงก์เอกสาร (DOI)": doi
            })
        
        # อัปเดต cursor เป็นหน้าถัดไปเพื่อรันลูปต่อ
        cursor = data.get('meta', {}).get('next_cursor')
        
    return pd.DataFrame(all_works)

# ใช้ st.spinner แจ้งเตือนผู้ใช้ระหว่างที่ระบบกำลังวนลูปดึงข้อมูล
with st.spinner('กำลังดึงข้อมูลผลงานวิจัยทั้งหมดของมหาวิทยาลัย (อาจใช้เวลาสักครู่เนื่องจากมีปริมาณมาก)...'):
    df_all_works = fetch_all_works(ror_id)

# =====================================================================
# 6. ส่วนแสดงผลตารางผลงานทั้งหมด พร้อมระบบ Sidebar Filters
# =====================================================================

if not df_all_works.empty:
    st.markdown("---")
    st.markdown("### 📚 ข้อมูลผลงานวิจัยทั้งหมดของมหาวิทยาลัย")
    
    # --- สร้างเมนูตัวกรองด้านข้าง (Sidebar) ---
    st.sidebar.header("🔍 ค้นหาและกรองข้อมูล")
    st.sidebar.markdown("ใช้เครื่องมือด้านล่างเพื่อค้นหาผลงานวิจัยเฉพาะเจาะจง")
    
    # 1. ตัวกรองปีที่ตีพิมพ์ (Year Filter)
    # ดึงรายการปีทั้งหมดที่มีในข้อมูล (ตัดค่า N/A ออก) แล้วเรียงจากปีล่าสุดลงไป
    available_years = sorted(df_all_works[df_all_works['ปีที่ตีพิมพ์'] != 'N/A']['ปีที่ตีพิมพ์'].unique().tolist(), reverse=True)
    selected_years = st.sidebar.multiselect("📅 เลือกปีที่ตีพิมพ์:", options=available_years, default=available_years)
    
    # 2. ค้นหาจากชื่อผู้แต่ง (Author Search)
    search_author = st.sidebar.text_input("👤 ค้นหาชื่อผู้แต่งหลัก (ภาษาอังกฤษ):", "")
    
    # 3. ค้นหาจากชื่อผลงานวิจัย (Title Search)
    search_title = st.sidebar.text_input("📝 ค้นหาคีย์เวิร์ดในชื่อผลงานวิจัย:", "")
    
    # --- นำเงื่อนไขมากรองข้อมูล (Apply Filters) ---
    filtered_df = df_all_works.copy()
    
    if selected_years:
        filtered_df = filtered_df[filtered_df['ปีที่ตีพิมพ์'].isin(selected_years)]
        
    if search_author:
        # ใช้ str.contains เพื่อค้นหาแบบบางส่วน (Partial Match) และไม่สนตัวพิมพ์เล็ก-ใหญ่ (case=False)
        filtered_df = filtered_df[filtered_df['ผู้แต่งหลัก (First Author)'].str.contains(search_author, case=False, na=False)]
        
    if search_title:
        filtered_df = filtered_df[filtered_df['ชื่อผลงานวิจัย (Title)'].str.contains(search_title, case=False, na=False)]
    
    # --- แสดงผลข้อมูลที่ผ่านการกรองแล้ว ---
    st.caption(f"แสดงผลข้อมูลจำนวน **{len(filtered_df):,}** ชิ้น จากทั้งหมด {len(df_all_works):,} ชิ้น (เรียงตามยอดอ้างอิงสูงสุด)")
    
    # รีเซ็ต Index ให้เริ่มจาก 1 ใหม่เสมอ เพื่อความสวยงามของตาราง
    filtered_df.reset_index(drop=True, inplace=True)
    filtered_df.index = filtered_df.index + 1
    
    # แสดงตารางบน Dashboard
    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=400, 
        column_config={
            "ลิงก์เอกสาร (DOI)": st.column_config.LinkColumn("ลิงก์เอกสาร (DOI)")
        }
    )
    
    # แปลงข้อมูลเฉพาะส่วนที่ "กรองแล้ว" เป็น CSV
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    
    # ปุ่มดาวน์โหลด
    st.download_button(
        label="📥 ดาวน์โหลดข้อมูลที่กรองแล้ว (Excel/CSV)",
        data=csv,
        file_name='rmuti_filtered_works.csv',
        mime='text/csv',
    )
else:
    st.warning("ไม่พบข้อมูลหรือเกิดข้อผิดพลาดในการดึงข้อมูลทั้งหมด")
# =====================================================================
# 7. ส่วนเพิ่มเติม: สรุปผู้บริหาร (Executive Summary)
# =====================================================================

st.markdown("---")
st.header("📌 สรุปผู้บริหาร (Executive Summary)")
st.caption("สรุปแนวโน้มการเติบโตย้อนหลัง 5 ปี และข้อเสนอแนะเชิงกลยุทธ์เพื่อยกระดับ Webometrics")

# ตรวจสอบว่าตัวแปร df (ข้อมูล 5 ปีจากกราฟด้านบน) มีอยู่และไม่ว่างเปล่า
if 'df' in locals() and not df.empty:
    # คำนวณสถิติ 5 ปีย้อนหลัง
    total_works_5yrs = df['works_count'].sum()
    total_citations_5yrs = df['cited_by_count'].sum()
    
    # ดึงข้อมูลปีแรกสุดและปีล่าสุดในกรอบ 5 ปี มาเปรียบเทียบการเติบโต
    first_year_data = df.iloc[0]
    latest_year_data = df.iloc[-1]
    
    works_growth = latest_year_data['works_count'] - first_year_data['works_count']
    citations_growth = latest_year_data['cited_by_count'] - first_year_data['cited_by_count']
    
    # แสดงผลตัวเลขแบบ Metric Box 3 กล่อง
    col1, col2, col3 = st.columns(3)
    col1.metric("รวมผลงานวิชาการ (5 ปีหลัง)", f"{total_works_5yrs:,} ชิ้น", f"{works_growth:+} จากปี {first_year_data['year']}")
    col2.metric("รวมการถูกอ้างอิง (5 ปีหลัง)", f"{total_citations_5yrs:,} ครั้ง", f"{citations_growth:+} จากปี {first_year_data['year']}")
    col3.metric("สถานะฐานข้อมูลสถาบัน", "ROR: 04a2rz655", "เชื่อมต่อ OpenAlex สำเร็จ", delta_color="normal")

st.markdown("""
### **บทวิเคราะห์และข้อเสนอแนะเชิงกลยุทธ์ด้านสารสนเทศ:**

**1. การปรับตัวรับเกณฑ์ใหม่ของ Webometrics (รอบมกราคม 2026):** ตัวชี้วัด Openness (น้ำหนัก 10%) ได้ยกเลิกการใช้ข้อมูลจาก Google Scholar และเปลี่ยนมาประเมินจากฐานข้อมูล **OpenAlex** ผ่านรหัสสถาบัน **ROR ID** แดชบอร์ดนี้จึงถูกพัฒนาขึ้นอย่างเร่งด่วนเพื่อมอนิเตอร์สถานะตัวตนทางดิจิทัลของมหาวิทยาลัยให้สอดคล้องกับ Methodology ล่าสุด

**2. ทิศทางการเติบโตของข้อมูล 5 ปีย้อนหลัง:** ภาพรวมปริมาณผลงานวิชาการและการถูกอ้างอิง (Citation) เป็นตัวบ่งชี้สำคัญที่ส่งผลโดยตรงต่อคะแนน Excellence (40%) และ Openness (10%) การติดตามแนวโน้มนี้อย่างใกล้ชิดจะช่วยให้เห็นประสิทธิภาพของนโยบายส่งเสริมการวิจัยในภาพรวม

**3. กลยุทธ์ขับเคลื่อนระยะต่อไปสำหรับฝ่ายเทคโนโลยีสารสนเทศ:**
* **Data Standardization:** ควรประสานงานกับสถาบันวิจัยฯ เพื่อออกแนวปฏิบัติให้คณาจารย์จากทุกวิทยาเขต ระบุชื่อหน่วยงาน (Affiliation Name) ในผลงานวิจัยให้เป็นมาตรฐานเดียวกัน และกระตุ้นให้ผูกบัญชี ORCID เพื่อลดปัญหาการตกหล่นของข้อมูลคะแนนในระบบของ OpenAlex
* **Data-Driven Funding:** นำข้อมูลรายชื่อ "Top 10 ผลงานวิจัยดาวรุ่ง" ที่ได้จากระบบ ไปใช้ประกอบการพิจารณาจัดสรรทุนอุดหนุนการตีพิมพ์ (Page Charge) หรือทำการประชาสัมพันธ์ (PR) เพื่อดันยอดอ้างอิงให้ถึงเกณฑ์กลุ่ม Top 10% ของโลก
* **EdPex Alignment:** สามารถนำแดชบอร์ดติดตามข้อมูลชุดนี้ ไปผนวกเป็นส่วนหนึ่งของระบบสารสนเทศเพื่อการบริหาร (MIS) เพื่อรองรับการประเมินคุณภาพองค์กรในหมวดที่ 4 (การวัด การวิเคราะห์ และการจัดการความรู้) ได้อย่างเป็นรูปธรรม
""")
# =====================================================================
# 8. ส่วนเพิ่มเติม: เปรียบเทียบคู่แข่ง (Competitor Comparison)
# =====================================================================

st.markdown("---")
st.header("📊 เปรียบเทียบสมรรถนะกับสถาบันอื่น (Benchmarking)")
st.caption("เปรียบเทียบแนวโน้มผลงานวิชาการและการถูกอ้างอิงย้อนหลัง 5 ปี ระหว่าง มทร.อีสาน, ม.อุบลราชธานี และ ม.แม่โจ้")

@st.cache_data
def fetch_competitor_data():
    # กำหนดรายชื่อมหาวิทยาลัยและ ROR ID
    institutions = {
        "ม.บูรพา (อันดับ 3 ในกลุ่ม 2)(Burapha University)": "https://ror.org/01ff74m36",
        "ม.อุบลราชธานี (อันดับ 4 ในกลุ่ม 2)(UBU)": "https://ror.org/045nemn19",
        "ม.แม่โจ้ (อันดับ 5 ในกลุ่ม 2)(MJU)": "https://ror.org/03c7s1f64",   
        "มทร.อีสาน (อันดับ 6 ในกลุ่ม 2)(RMUTI)": "https://ror.org/04a2rz655",
        "ม.ทักษิณ (อันดับ 7 ในกลุ่ม 2) (Thaksin University)": "https://ror.org/00t2prd39"
    }
    
    all_data = []
    current_year = datetime.now().year
    
    for name, ror in institutions.items():
        url = f"https://api.openalex.org/institutions/{ror}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'counts_by_year' in data:
                temp_df = pd.DataFrame(data['counts_by_year'])
                # กรองข้อมูล 5 ปีย้อนหลัง
                temp_df = temp_df[(temp_df['year'] >= current_year - 6) & (temp_df['year'] < current_year)]
                temp_df['University'] = name
                all_data.append(temp_df)
                
    if all_data:
        # นำข้อมูลของทุกมหาวิทยาลัยมารวมกันเป็นตารางเดียว
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df['year'] = combined_df['year'].astype(str)
        return combined_df.sort_values('year')
    return pd.DataFrame()

with st.spinner('กำลังดึงข้อมูลเปรียบเทียบจาก OpenAlex...'):
    comp_df = fetch_competitor_data()

if not comp_df.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 เปรียบเทียบยอดการถูกอ้างอิง (Citations)")
        fig_comp_cite = px.line(comp_df, x='year', y='cited_by_count', color='University', markers=True,
                                labels={'year': 'ปี ค.ศ.', 'cited_by_count': 'จำนวนการถูกอ้างอิง (ครั้ง)', 'University': 'มหาวิทยาลัย'},
                                line_shape='spline')
        fig_comp_cite.update_traces(line_width=3, marker_size=8)
        # ปรับตำแหน่ง Legend ให้อยู่ด้านบนจะได้ไม่บังพื้นที่กราฟ
        fig_comp_cite.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_comp_cite, use_container_width=True)

    with col2:
        st.markdown("### 📝 เปรียบเทียบยอดการตีพิมพ์ผลงาน (Works)")
        fig_comp_works = px.bar(comp_df, x='year', y='works_count', color='University', barmode='group',
                                labels={'year': 'ปี ค.ศ.', 'works_count': 'จำนวนผลงาน (ชิ้น)', 'University': 'มหาวิทยาลัย'})
        fig_comp_works.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_comp_works, use_container_width=True)
else:
    st.error("ไม่สามารถดึงข้อมูลเปรียบเทียบได้ในขณะนี้")
