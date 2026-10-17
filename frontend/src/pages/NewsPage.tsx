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
        <span>JAPAN 0–0 SPAIN · 08:14</span>
        <h2>จังหวะแทงช่องด้านซ้าย: พื้นที่ว่างเปิดอยู่จริงนานแค่ไหน?</h2>
        <p>เทียบภาพก่อนจ่ายกับผลวิเคราะห์บนภาพเดียวกัน เพื่อดูระยะทาง เวลาบอลเดินทาง และผู้เล่นฝ่ายรับที่เข้าใกล้แนวบอลที่สุด</p>
        <div className="match-case-comparison">
          <figure>
            <div className="match-case-label"><span>01</span><strong>ภาพจังหวะก่อนจ่าย</strong></div>
            <img src="/spain-japan-through-ball-source.png" alt="จังหวะสเปนครองบอลก่อนแทงช่องในเกมพบญี่ปุ่น" />
            <figcaption>ภาพการแข่งขันก่อนกำหนดผู้ครองบอลและเป้าหมายการจ่าย</figcaption>
          </figure>
          <div className="match-case-analysis">
            <figure>
              <div className="match-case-label"><span>02</span><strong>ผลหลังเลือกพื้นที่เป้าหมาย</strong></div>
              <img src="/spain-japan-through-ball-analysis.png" alt="ผลวิเคราะห์จังหวะแทงช่องของสเปนพร้อมเส้นทางและคะแนนความเสี่ยง" />
              <figcaption>แสดงเส้นทาง จุดเสี่ยงถูกสกัด และรายละเอียดของทางเลือกที่เลือก</figcaption>
            </figure>
            <div className="match-case-summary">
              <p><strong>สิ่งที่คำนวณได้</strong> ทางเลือก A เป็นการจ่ายเข้าพื้นที่ด้านซ้าย ระบบแสดงคะแนนความเสี่ยง ระยะทาง เวลาบอลเดินทาง และผู้เล่นที่อยู่ใกล้แนวบอลที่สุด โดยไม่สรุปแทนผู้ใช้ว่าควรจ่ายหรือไม่</p>
              <div><a href="https://www.youtube.com/watch?v=DtzIyXc56f4" target="_blank" rel="noreferrer">ดูคลิปต้นทาง ↗</a><button type="button" onClick={onAnalyze}>ลองวิเคราะห์จังหวะอื่น →</button></div>
            </div>
          </div>
        </div>
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
