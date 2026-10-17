import { TelemetryFrame } from "../components/TelemetryFrame";

interface NewsPageProps { onAnalyze: () => void; }

const cases = [
  ["CASE 02 · TURNOVER", "จังหวะเสียบอล: ผู้เล่นหกคนมีทางเลือก แต่เส้นใดถูกปิดก่อน?", "แยกพื้นที่ว่างออกจากเส้นทางที่ฝ่ายรับเข้าถึงได้ก่อนบอล"],
  ["CASE 03 · DEFENSE", "จังหวะดันไลน์: ความกล้าของกองหลังหรือพื้นที่เสี่ยง?", "วางตำแหน่งทุกคนบนสนามเดียวกันก่อนอภิปรายเรื่องระยะห่าง"],
  ["CASE 04 · OFFSIDE", "จังหวะทะลุช่อง: จุดส่งกับจุดรับเปลี่ยนคำตอบอย่างไร?", "แยกวิถีบอลออกจากตำแหน่งอนาคตที่ผู้ใช้เลือกให้ผู้รับ"],
];

export function NewsPage({ onAnalyze }: NewsPageProps) {
  return (
    <main className="editorial-page dossier-page">
      <section className="dossier-heading">
        <div><span>DOSSIER NO. 24 · TACTICAL CONTROVERSY & VIRAL INCIDENT REVIEW</span><h1>คลังจังหวะถกเถียง และการตรวจข้ออ้างด้วยพิกัดสนาม</h1><p>รวบรวมจังหวะจากการแข่งขันและบทสนทนาออนไลน์ เพื่อแยกมุมมองเชิงแท็กติกออกจากสิ่งที่แบบจำลองคิเนมาติกส์คำนวณได้จริง</p></div>
        <aside><span>PUBLIC CASE INDEX</span><strong>03</strong><small>DEMO DOSSIERS</small></aside>
      </section>
      <div className="dossier-filters"><button type="button" className="active">ทั้งหมด</button><button type="button">จ่ายพลาด</button><button type="button">แทงทะลุช่อง</button><button type="button">แนวรับ</button><button type="button">มุมกล้อง</button></div>
      <section className="featured-case section-rule">
        <span>COVER CASE 01 · HIGH CONTROVERSY</span>
        <h2>จังหวะที่ดูเหมือนมีช่องจ่าย อาจปิดลงก่อนบอลเดินทางถึงหรือไม่?</h2>
        <p>เปรียบเทียบสิ่งที่มุมถ่ายทอดทำให้เราเห็น กับตำแหน่งบนสนามและเวลาที่ฝ่ายรับเข้าถึงแนวบอล</p>
        <div className="case-comparison"><TelemetryFrame compact label="PERSPECTIVE 01 · TV BROADCAST" /><div><TelemetryFrame analyzed compact label="PERSPECTIVE 02 · PITCH CALIBRATION" /><p><strong>GEOMETRICAL VERDICT</strong> การวัดนี้อธิบายระยะและเวลาเท่านั้น ข้อสรุปว่าควรเสี่ยงหรือไม่ยังขึ้นกับบริบทของเกม</p><button type="button" onClick={onAnalyze}>เปิดจังหวะนี้ใน Analysis →</button></div></div>
      </section>
      <section className="case-repository section-rule">
        <div className="section-heading-editorial"><div><span>CASE REPOSITORIES</span><h2>คดีถกเถียงยอดนิยม: พิสูจน์ด้วยเรขาคณิตสนาม</h2></div><small>DEMO CASES · NO CLAIM OF GROUND TRUTH</small></div>
        <div className="case-grid">{cases.map(([tag, title, body], index) => <article key={tag}><TelemetryFrame compact analyzed={index !== 1} label={tag} /><div><h3>{title}</h3><p>{body}</p><button type="button" onClick={onAnalyze}>ทดลองวิเคราะห์เอง →</button></div></article>)}</div>
      </section>
      <section className="standards-strip"><div><span>RIGOROUS STANDARDS</span><h2>ขั้นตอนตรวจสอบของ TactiVision</h2></div><ol><li><strong>01</strong> PITCH HOMOGRAPHY</li><li><strong>02</strong> KINEMATIC VELOCITY</li><li><strong>03</strong> DETERMINISTIC CONES</li></ol></section>
      <section className="submit-case"><div><span>COMMUNITY PIPELINE</span><h2>มีจังหวะที่เป็นข้อถกเถียงในเกมล่าสุดหรือไม่?</h2><p>เปิดหน้า Analysis เพื่ออัปโหลดภาพและตรวจทางเลือกด้วยค่าที่คุณกำหนดเอง</p></div><button type="button" onClick={onAnalyze}>START ANALYSIS</button></section>
    </main>
  );
}
