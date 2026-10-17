import { MatchComparison, MatchStories } from "../components/MatchStories";

interface HomePageProps {
  onAnalyze: () => void;
  onResearch: () => void;
  onNews: () => void;
}

const debateRows = [
  ["01", "เห็นช่องจ่าย แต่ยังไม่เห็นเวลาบอลเดินทาง", "ภาพนิ่งช่วยให้เห็นพื้นที่ แต่การถกเถียงมักข้ามระยะทาง ความเร็วบอล และเวลาที่ผู้เล่นแต่ละคนเข้าถึงแนวบอล"],
  ["02", "เห็นกองหลัง แต่เทียบเวลาถึงจุดสกัดได้ยาก", "TactiVision วางบอลและฝ่ายรับบนพิกัดสนามเดียวกัน แล้วเปรียบเทียบเวลาโดยใช้สมมติฐานที่ผู้ใช้ตรวจและแก้ได้"],
  ["03", "ทางเลือกที่ปลอดภัยที่สุด อาจไม่ใช่ทางเลือกที่สร้างเกมที่สุด", "คะแนนต่ำสุดหมายถึงเสี่ยงถูกสกัดต่ำสุดในชุดนั้น ระบบจึงแสดงทางเลือกคู่กันโดยไม่สรุปแทนโค้ชว่าทางใดดีที่สุด"],
];

export function HomePage({ onAnalyze, onResearch, onNews }: HomePageProps) {
  return (
    <main className="editorial-page home-page">
      <section className="home-hero">
        <div className="hero-copy">
          <span className="editorial-kicker">TACTICAL PASS ANALYSIS</span>
          <h1>จากจังหวะที่ถกเถียง <span>สู่ทางเลือกที่ตรวจสอบได้</span></h1>
          <p>เปรียบเทียบเส้นทางการจ่ายบอลจากภาพการแข่งขัน ด้วยพิกัดสนาม ระยะทาง เวลาเดินทาง และจุดเสี่ยงถูกสกัดที่ตรวจสอบย้อนกลับได้</p>
          <ul className="hero-features" aria-label="ข้อมูลที่ระบบใช้วิเคราะห์">
            <li>พิกัดสนาม</li>
            <li>เวลาบอลเดินทาง</li>
            <li>จุดเสี่ยงถูกสกัด</li>
          </ul>
          <div className="hero-actions">
            <button type="button" className="flat-primary" onClick={onAnalyze}>เริ่มวิเคราะห์ภาพ</button>
            <button type="button" className="flat-link" onClick={onResearch}>อ่านวิธีคำนวณ</button>
          </div>
        </div>
        <figure className="hero-match-frame">
          <div className="hero-match-header"><span>ภาพจากการแข่งขัน</span><span>ตรวจพบผู้เล่นและลูกบอล</span></div>
          <img src="/match-analysis.png" alt="ภาพการแข่งขันฟุตบอลที่ระบบตรวจจับผู้เล่นและลูกบอลแล้ว" />
          <figcaption><strong>เริ่มจากภาพจริง</strong><span>นำตำแหน่งที่ตรวจพบไปเทียบกับพิกัดสนามเพื่อวิเคราะห์เส้นทางการจ่ายบอล</span></figcaption>
        </figure>
        <p className="hero-mandate"><span>ขอบเขตการใช้งาน</span> เครื่องมือนี้ช่วยอธิบายข้อมูลประกอบการตัดสินใจ โดยไม่ตัดสินแทนโค้ช</p>
      </section>

      <section className="comparison-section section-rule">
        <div className="section-heading-editorial">
          <div><span>ก่อนและหลังวิเคราะห์</span><h2>เปรียบเทียบภาพการแข่งขัน กับเส้นทางการจ่ายบอลบนพิกัดสนาม</h2></div>
          <small>ภาพตัวอย่างสำหรับอธิบายการแสดงผล</small>
        </div>
        <MatchComparison />
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
        <span>COMMUNITY DEBATES · NEWS & BREAKDOWNS</span>
        <h2>จากจังหวะที่คนเห็นต่าง สู่ภาพวิเคราะห์ที่หยิบไปคุยต่อได้</h2>
        <p>ดูภาพก่อนและหลังวิเคราะห์ พร้อมคลิปต้นทางของทั้งสองจังหวะ</p>
        <MatchStories onAnalyze={onAnalyze} />
        <button className="stories-link" type="button" onClick={onNews}>อ่านข่าวและจังหวะวิเคราะห์ทั้งหมด →</button>
      </section>

      <section className="boundary-section section-rule">
        <article><header><h2>ระบบคำนวณอะไร</h2><span>DETERMINISTIC METRICS</span></header><p>ข้อมูลสำหรับเปรียบเทียบเส้นทาง ภายใต้ตำแหน่งและสมมติฐานที่กำหนด</p><ol>
          <li><strong>ระยะทางการจ่ายบอล:</strong> คำนวณจากพิกัดสนามที่เทียบกับภาพ</li>
          <li><strong>เวลาบอลเดินทาง:</strong> ประมาณจากระยะทางและความเร็วบอล</li>
          <li><strong>เวลาที่ฝ่ายรับเข้าถึงแนวบอล:</strong> อิงความเร็วและเวลาตอบสนอง</li>
          <li><strong>จุดเสี่ยงถูกสกัด:</strong> ตำแหน่งบนเส้นทางที่ฝ่ายรับอาจเข้าถึงบอล</li>
          <li><strong>คะแนนความเสี่ยง 0–100:</strong> ใช้เปรียบเทียบทางเลือกภายใต้ค่าชุดเดียวกัน</li>
        </ol></article>
        <article><header><h2>ระบบไม่ได้อ้างว่าอะไร</h2><span>METHOD BOUNDARIES</span></header><p>ข้อจำกัดที่ควรใช้ประกอบการอ่านผล</p><ul>
          <li><strong>ไม่ใช่เปอร์เซ็นต์ความสำเร็จจริง:</strong> คะแนนไม่ได้ผ่านการปรับเทียบจากผลการจ่ายบอลจริง</li>
          <li><strong>ไม่ได้ตัดสินทางเลือกที่ดีที่สุด:</strong> ความเสี่ยงต่ำอาจไม่ใช่ทางเลือกที่สร้างโอกาสบุกมากที่สุด</li>
          <li><strong>ไม่แทนประสบการณ์ของโค้ช:</strong> บริบทเกมและแผนทีมยังเป็นส่วนสำคัญ</li>
          <li><strong>ผลขึ้นกับภาพและค่าที่กำหนด:</strong> การเทียบพิกัดและสมมติฐานความเร็วส่งผลต่อคะแนน</li>
        </ul></article>
      </section>

      <section className="home-cta">
        <div><span>READY TO MAP YOUR SQUAD?</span><h2>มีจังหวะที่ทีมคุณยังถกเถียงกันอยู่หรือไม่?</h2><p>เปลี่ยนภาพหนึ่งจังหวะให้เป็นบทสนทนาที่ตรวจสอบระยะ เวลา และสมมติฐานได้</p></div>
        <button type="button" onClick={onAnalyze}>เริ่มวิเคราะห์</button>
        <button type="button" className="inverse-link" onClick={onNews}>อ่านข่าวและบทวิเคราะห์ →</button>
      </section>
    </main>
  );
}
