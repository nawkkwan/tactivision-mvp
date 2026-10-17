import { TelemetryFrame } from "../components/TelemetryFrame";

interface HomePageProps {
  onAnalyze: () => void;
  onResearch: () => void;
}

const debateRows = [
  ["01", "เห็นช่องจ่าย แต่ยังไม่เห็นเวลาบอลเดินทาง", "ภาพนิ่งช่วยให้เห็นพื้นที่ แต่การถกเถียงมักข้ามระยะทาง ความเร็วบอล และเวลาที่ผู้เล่นแต่ละคนเข้าถึงแนวบอล"],
  ["02", "เห็นกองหลัง แต่เทียบเวลาถึงจุดสกัดได้ยาก", "TactiVision วางบอลและฝ่ายรับบนพิกัดสนามเดียวกัน แล้วเปรียบเทียบเวลาโดยใช้สมมติฐานที่ผู้ใช้ตรวจและแก้ได้"],
  ["03", "ทางเลือกที่ปลอดภัยที่สุด อาจไม่ใช่ทางเลือกที่สร้างเกมที่สุด", "คะแนนต่ำสุดหมายถึงเสี่ยงถูกสกัดต่ำสุดในชุดนั้น ระบบจึงแสดงทางเลือกคู่กันโดยไม่สรุปแทนโค้ชว่าทางใดดีที่สุด"],
];

export function HomePage({ onAnalyze, onResearch }: HomePageProps) {
  return (
    <main className="editorial-page home-page">
      <section className="home-hero">
        <div className="hero-copy">
          <span className="editorial-kicker">วิเคราะห์การจ่ายบอลจากภาพการแข่งขัน</span>
          <h1>จากจังหวะที่ถกเถียง<br />สู่ทางเลือกที่ตรวจสอบได้</h1>
          <p>TactiVision ช่วยให้โค้ชและนักวิเคราะห์เปรียบเทียบเส้นทางการจ่ายบอลจากภาพการแข่งขัน โดยแสดงระยะ เวลา จุดเสี่ยงถูกสกัด และสมมติฐานที่ใช้คำนวณ</p>
          <div className="hero-actions">
            <button type="button" className="flat-primary" onClick={onAnalyze}>ลองวิเคราะห์ภาพ</button>
            <button type="button" className="flat-link" onClick={onResearch}>ดูวิธีทำงาน →</button>
          </div>
        </div>
        <TelemetryFrame label="ภาพตัวอย่างสำหรับเทียบพิกัด" />
        <p className="hero-mandate">เครื่องมือช่วยอธิบายการตัดสินใจ ไม่ใช่คำตัดสินแทนโค้ช</p>
      </section>

      <section className="comparison-section section-rule">
        <div className="section-heading-editorial">
          <div><span>ก่อนและหลังวิเคราะห์</span><h2>เปรียบเทียบภาพการแข่งขัน กับเส้นทางการจ่ายบอลบนพิกัดสนาม</h2></div>
          <small>ภาพตัวอย่างสำหรับอธิบายการแสดงผล</small>
        </div>
        <div className="before-after-grid">
          <TelemetryFrame compact label="ภาพการแข่งขัน" />
          <TelemetryFrame analyzed compact label="หลังวิเคราะห์เส้นทาง" />
        </div>
      </section>

      <section className="debate-section section-rule">
        <div className="debate-intro">
          <div><span>ทำไมคนจึงเห็นต่างกัน</span><h2>ทุกคนเห็นภาพเดียวกัน แต่ไม่ได้ใช้เหตุผลชุดเดียวกัน</h2></div>
          <p>การถกเถียงฟุตบอลมักอาศัยความจำ มุมกล้อง และผลลัพธ์ที่เกิดขึ้นแล้ว ระบบไม่ได้ทำให้ความเห็นต่างหายไป แต่ช่วยให้ทุกคนใช้พิกัด เวลา และสมมติฐานชุดเดียวกัน</p>
        </div>
        <div className="debate-rows">
          {debateRows.map(([number, title, body]) => (
            <article key={number}><strong>{number}</strong><h3>{title}</h3><p>{body}</p></article>
          ))}
        </div>
      </section>

      <section className="case-section">
        <span>จังหวะถกเถียงจากเกมจริง</span>
        <h2>จากกระแสไวรัลออนไลน์ สู่ภาพเวกเตอร์ที่คนหยิบไปคุยต่อได้</h2>
        <p>นำจังหวะที่คนเห็นต่างมาจัดวางบนสนามมาตรฐาน แล้วแยกสิ่งที่ระบบคำนวณออกจากข้อสรุปทางแท็กติกอย่างชัดเจน</p>
        <TelemetryFrame analyzed label="ตัวอย่างการเปรียบเทียบเส้นทาง" />
        <div className="case-opinions">
          <article><h3>จังหวะนี้ควรเล่นปลอดภัยหรือเร่งเกม?</h3><p>ระบบแสดงเส้นทางและเวลาให้เทียบกัน ส่วนคุณค่าทางแท็กติกยังเป็นการตัดสินใจของทีมงาน</p></article>
          <article><h3>คะแนนต่ำกว่า หมายถึงทางเลือกดีกว่าเสมอหรือไม่?</h3><p>ไม่เสมอ คะแนนนี้วัดเฉพาะความเสี่ยงถูกสกัดภายใต้สมมติฐาน ไม่ได้วัดคุณค่าการบุกทั้งหมด</p></article>
        </div>
      </section>

      <section className="boundary-section section-rule">
        <article><h2>ระบบคำนวณอะไร</h2><ol><li>ระยะทางการจ่ายบอล</li><li>เวลาบอลเดินทาง</li><li>เวลาที่ฝ่ายรับเข้าถึงแนวบอล</li><li>จุดเสี่ยงถูกสกัด</li><li>คะแนนความเสี่ยง 0–100</li></ol></article>
        <article><h2>ระบบไม่ได้อ้างว่าอะไร</h2><ul><li>ไม่ใช่เปอร์เซ็นต์ความสำเร็จจากข้อมูลการแข่งขันจริง</li><li>ไม่ได้ตัดสินทางเลือกที่ดีที่สุดทางแท็กติก</li><li>ไม่แทนประสบการณ์ของโค้ช</li><li>ผลลัพธ์ขึ้นกับการเทียบพิกัดและค่าความเร็วที่กำหนด</li></ul></article>
      </section>

      <section className="home-cta">
        <div><h2>มีจังหวะที่ทีมคุณยังถกเถียงกันอยู่หรือไม่?</h2><p>เปลี่ยนภาพหนึ่งจังหวะให้เป็นบทสนทนาที่ตรวจสอบระยะ เวลา และสมมติฐานได้</p></div>
        <button type="button" onClick={onAnalyze}>เริ่มวิเคราะห์</button>
        <button type="button" className="inverse-link" onClick={onResearch}>อ่านวิธีคำนวณ →</button>
      </section>
    </main>
  );
}
