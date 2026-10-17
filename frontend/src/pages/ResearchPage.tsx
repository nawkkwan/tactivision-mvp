import { TelemetryFrame } from "../components/TelemetryFrame";

const papers = [
  { code: "PAPER 01 · AVAILABILITY", title: "Who can receive the pass? A computational model for quantifying availability in soccer", detail: "แนวคิดเปรียบเทียบเวลาที่ผู้รับและฝ่ายรับเข้าถึงตำแหน่งบนแนวบอล", source: "Brefeld et al. (2022)", url: "https://doi.org/10.1007/s10618-022-00827-2" },
  { code: "PAPER 02 · PASS SEQUENCES", title: "Validation of a defensive disruptiveness model to evaluate passing sequences", detail: "หลักฐานด้านการวัดผลของลำดับการจ่ายบอลและการรบกวนแนวรับ", source: "Forcher et al. (2021)", url: "https://doi.org/10.3390/e23121607" },
  { code: "PAPER 03 · CALIBRATION", title: "TVCalib: Camera Calibration for Sports Field Registration in Soccer", detail: "การประมาณ camera pose และพิกัดสนามด้วยเส้นและจุดอ้างอิงจากภาพถ่ายทอด", source: "Theiner & Ewerth (2023)", url: "https://openaccess.thecvf.com/content/WACV2023/html/Theiner_TVCalib_Camera_Calibration_for_Sports_Field_Registration_in_Soccer_WACV_2023_paper.html" },
  { code: "PAPER 04 · FIELD LOCALIZATION", title: "Sports Field Localization via Deep Structured Models", detail: "การใช้ semantic cues ของพื้นสนาม เส้น และวงกลมเพื่อระบุตำแหน่งสนามจากภาพ", source: "Homayounfar et al. (2017)", url: "https://openaccess.thecvf.com/content_cvpr_2017/html/Homayounfar_Sports_Field_Localization_CVPR_2017_paper.html" },
  { code: "PAPER 05 · BALL FLIGHT", title: "Measurements of the flight trajectory of a spinning soccer ball", detail: "ข้อจำกัดของการประมาณลูกโค้งเมื่อยังไม่มีข้อมูลความเร็วต้น สปิน และแรงต้าน", source: "Hong et al. (2020)", url: "https://www.mdpi.com/2504-3900/49/1/88" },
];

export function ResearchPage() {
  return (
    <main className="editorial-page research-page">
      <section className="research-heading">
        <div><span>ARCHIVE · ISSN TACTIVISION RESEARCH & WORKING PAPERS</span><h1>คลังงานวิจัยและระเบียบวิธีฟุตบอล<br /><strong>RESEARCH & TECHNICAL WORKING PAPERS</strong></h1><p>รวมหลักฐานที่รองรับการจำลองพาส การเคลื่อนที่ของผู้เล่น และการเทียบพิกัดสนาม พร้อมแยกสิ่งที่มีงานวิจัยรองรับออกจากสมมติฐานของ MVP</p></div>
        <aside><span>REPOSITORY AUDIT STATUS</span><strong>7</strong><small>PRIMARY REFERENCES IN PROJECT DOCS</small></aside>
      </section>

      <section className="lead-paper section-rule">
        <TelemetryFrame label="FEATURED METHOD · 2D PITCH HOMOGRAPHY" />
        <article><span>WORKING PAPER 01</span><h2>การปรับระนาบกล้อง 2D Homography จากภาพถ่ายทอด เพื่อคำนวณเวกเตอร์ส่งบอลแบบตรวจสอบได้</h2><p>ระบบแปลงตำแหน่งจากพิกเซลภาพไปยังสนามมาตรฐาน 105 × 68 เมตร จากนั้นจึงคำนวณเวลาเดินทางของบอลและเวลาที่ผู้เล่นเข้าถึงแนวบอล</p><p>เวอร์ชันปัจจุบันใช้ Auto-first และเปิด Manual Calibration เมื่อภาพไม่เหมาะกับการประมาณอัตโนมัติ ทุกค่าความเร็วและเวลาตอบสนองยังคงปรับได้โดยผู้ใช้</p><a href="https://openaccess.thecvf.com/content/WACV2023/html/Theiner_TVCalib_Camera_Calibration_for_Sports_Field_Registration_in_Soccer_WACV_2023_paper.html" target="_blank" rel="noreferrer">อ่านงาน TVCalib ต้นทาง ↗</a></article>
      </section>

      <section className="paper-index section-rule">
        <div className="section-heading-editorial"><div><span>INDEXED LITERATURE</span><h2>คลังเอกสารวิชาการแยกตามหมวดหมู่</h2></div><small>OPEN REPOSITORIES & EXTERNAL JOURNALS</small></div>
        <div>{papers.map((paper) => <article key={paper.code}><span>{paper.code}</span><div><h3>{paper.title}</h3><p>{paper.detail}</p><small>{paper.source}</small></div><a href={paper.url} target="_blank" rel="noreferrer">เปิดแหล่งอ้างอิง ↗</a></article>)}</div>
      </section>

      <section className="research-boundaries section-rule">
        <article><span>OPEN DATA INFRASTRUCTURE</span><h2>แหล่งข้อมูลและมาตรฐานที่เชื่อมต่อ</h2><ul><li>SoccerNet Camera Calibration</li><li>FIFA Research & Standards Hub</li><li>งานวิจัย Tracking และ pass availability แบบเปิด</li></ul></article>
        <article><span>TRANSPARENCY STANDARD</span><h2>นโยบายตรวจสอบความถูกต้อง</h2><ol><li>ใช้สมการแบบกำหนดแน่นอนและแสดงตัวแปร</li><li>แยกผลจำลองออกจากข้อสรุปทางแท็กติก</li><li>บันทึกข้อจำกัดของ Calibration และภาพนิ่ง</li></ol></article>
      </section>
      <section className="research-contact"><div><span>SCHOLARLY INQUIRIES & CITATION</span><h2>ต้องการอ้างอิงงานวิจัยหรือชุดข้อมูลนี้สำหรับการศึกษาวิจัยต่อยอด?</h2><p>ตรวจรายการอ้างอิงและข้อจำกัดฉบับเต็มในเอกสารระเบียบวิธีของโครงการ</p></div><a href="https://github.com/nawkkwan/tactivision-mvp/tree/main/docs" target="_blank" rel="noreferrer">เปิดเอกสารโครงการ ↗</a></section>
    </main>
  );
}
