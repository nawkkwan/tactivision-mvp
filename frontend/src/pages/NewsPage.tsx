import { TelemetryFrame } from "../components/TelemetryFrame";

interface NewsPageProps { onAnalyze: () => void; }

const cases = [
  ["จังหวะเสียบอล", "ผู้เล่นหกคนมีทางเลือก แต่เส้นใดถูกปิดก่อน?", "แยกพื้นที่ว่างออกจากเส้นทางที่ฝ่ายรับเข้าถึงได้ก่อนบอล"],
  ["การดันแนวรับ", "ความกล้าของกองหลังหรือพื้นที่เสี่ยง?", "วางตำแหน่งทุกคนบนสนามเดียวกันก่อนอภิปรายเรื่องระยะห่าง"],
  ["จังหวะทะลุช่อง", "จุดส่งกับจุดรับเปลี่ยนคำตอบอย่างไร?", "แยกวิถีบอลออกจากตำแหน่งที่ผู้ใช้เลือกให้ผู้รับ"],
];

export function NewsPage({ onAnalyze }: NewsPageProps) {
  return (
    <main className="editorial-page dossier-page">
      <section className="dossier-heading">
        <div><span>จังหวะที่คนเห็นต่างกัน</span><h1>คลังจังหวะถกเถียง ตรวจด้วยพิกัดสนาม</h1><p>นำจังหวะจากการแข่งขันมาเทียบตำแหน่ง ระยะ และเวลา เพื่อช่วยให้การถกเถียงมีข้อมูลที่ตรวจสอบได้</p></div>
        <aside><span>กรณีตัวอย่าง</span><strong>03</strong><small>เลือกเปิดดูและทดลองวิเคราะห์ได้</small></aside>
      </section>
      <div className="dossier-filters"><button type="button" className="active">ทั้งหมด</button><button type="button">จ่ายพลาด</button><button type="button">แทงทะลุช่อง</button><button type="button">แนวรับ</button><button type="button">มุมกล้อง</button></div>
      <section className="featured-case section-rule">
        <span>กรณีตัวอย่าง</span>
        <h2>จังหวะที่ดูเหมือนมีช่องจ่าย อาจปิดลงก่อนบอลเดินทางถึงหรือไม่?</h2>
        <p>เปรียบเทียบสิ่งที่มุมถ่ายทอดทำให้เราเห็น กับตำแหน่งบนสนามและเวลาที่ฝ่ายรับเข้าถึงแนวบอล</p>
        <div className="case-comparison"><TelemetryFrame compact label="ภาพการแข่งขัน" /><div><TelemetryFrame analyzed compact label="หลังเทียบพิกัดสนาม" /><p><strong>สิ่งที่คำนวณได้</strong> การวัดนี้อธิบายระยะและเวลา ส่วนการตัดสินใจยังขึ้นกับบริบทของเกม</p><button type="button" onClick={onAnalyze}>เปิดจังหวะนี้ใน Analysis →</button></div></div>
      </section>
      <section className="case-repository section-rule">
        <div className="section-heading-editorial"><div><span>กรณีตัวอย่าง</span><h2>ลองตรวจจังหวะถกเถียงด้วยพิกัดสนาม</h2></div><small>ผลลัพธ์เป็นการจำลองจากค่าที่กำหนด</small></div>
        <div className="case-grid">{cases.map(([tag, title, body], index) => <article key={tag}><TelemetryFrame compact analyzed={index !== 1} label={tag} /><div><h3>{title}</h3><p>{body}</p><button type="button" onClick={onAnalyze}>ทดลองวิเคราะห์เอง →</button></div></article>)}</div>
      </section>
      <section className="standards-strip"><div><h2>ระบบตรวจจังหวะอย่างไร</h2></div><ol><li><strong>01</strong> เทียบภาพกับสนาม</li><li><strong>02</strong> คำนวณเวลาเคลื่อนที่</li><li><strong>03</strong> เปรียบเทียบทางเลือก</li></ol></section>
      <section className="submit-case"><div><h2>มีจังหวะที่อยากลองตรวจด้วยตัวเอง?</h2><p>อัปโหลดภาพ แล้วเปรียบเทียบทางเลือกด้วยค่าที่คุณกำหนดได้</p></div><button type="button" onClick={onAnalyze}>เริ่มวิเคราะห์</button></section>
    </main>
  );
}
