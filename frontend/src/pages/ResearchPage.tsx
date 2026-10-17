import { TelemetryFrame } from "../components/TelemetryFrame";

const papers = [
  { code: "การรับบอล", title: "Who can receive the pass? A computational model for quantifying availability in soccer", detail: "เปรียบเทียบเวลาที่ผู้รับและฝ่ายรับเข้าถึงตำแหน่งบนแนวบอล", source: "Brefeld et al. (2022)", url: "https://doi.org/10.1007/s10618-022-00827-2" },
  { code: "ลำดับการจ่าย", title: "Validation of a defensive disruptiveness model to evaluate passing sequences", detail: "ใช้ประกอบการวัดผลของลำดับการจ่ายบอลและการรบกวนแนวรับ", source: "Forcher et al. (2021)", url: "https://doi.org/10.3390/e23121607" },
  { code: "การเทียบพิกัด", title: "TVCalib: Camera Calibration for Sports Field Registration in Soccer", detail: "ประมาณตำแหน่งกล้องและพิกัดสนามจากเส้นในภาพถ่ายทอด", source: "Theiner & Ewerth (2023)", url: "https://openaccess.thecvf.com/content/WACV2023/html/Theiner_TVCalib_Camera_Calibration_for_Sports_Field_Registration_in_Soccer_WACV_2023_paper.html" },
  { code: "ตำแหน่งสนาม", title: "Sports Field Localization via Deep Structured Models", detail: "ใช้พื้นสนาม เส้น และวงกลม เพื่อระบุตำแหน่งในสนามจากภาพ", source: "Homayounfar et al. (2017)", url: "https://openaccess.thecvf.com/content_cvpr_2017/html/Homayounfar_Sports_Field_Localization_CVPR_2017_paper.html" },
  { code: "วิถีบอล", title: "Measurements of the flight trajectory of a spinning soccer ball", detail: "อธิบายข้อจำกัดของการประมาณลูกโค้งเมื่อไม่มีข้อมูลความเร็วต้น สปิน และแรงต้าน", source: "Hong et al. (2020)", url: "https://www.mdpi.com/2504-3900/49/1/88" },
];

export function ResearchPage() {
  return (
    <main className="editorial-page research-page">
      <section className="research-heading">
        <div><span>หลักฐานและวิธีการ</span><h1>งานวิจัยที่ TactiVision ใช้อ้างอิง</h1><p>แหล่งข้อมูลสำหรับการจำลองการจ่ายบอล การเคลื่อนที่ของผู้เล่น และการเทียบภาพกับสนามจริง พร้อมข้อจำกัดของวิธีคำนวณ</p></div>
        <aside><span>แหล่งอ้างอิงหลัก</span><strong>7</strong><small>รายการในเอกสารโครงการ</small></aside>
      </section>

      <section className="lead-paper section-rule">
        <TelemetryFrame label="การเทียบภาพกับพิกัดสนาม" />
        <article><h2>เปลี่ยนตำแหน่งในภาพถ่ายทอดให้เป็นพิกัดบนสนาม</h2><p>ระบบแปลงจุดจากภาพไปยังสนามมาตรฐาน 105 × 68 เมตร แล้วคำนวณเวลาเดินทางของบอลและเวลาที่ผู้เล่นเข้าถึงแนวบอล</p><p>ระบบจะลองเทียบพิกัดให้อัตโนมัติก่อน หากภาพไม่เหมาะ ผู้ใช้สามารถกำหนดจุดสนามเองได้ ความเร็วและเวลาตอบสนองยังปรับได้ทุกค่า</p><a href="https://openaccess.thecvf.com/content/WACV2023/html/Theiner_TVCalib_Camera_Calibration_for_Sports_Field_Registration_in_Soccer_WACV_2023_paper.html" target="_blank" rel="noreferrer">อ่านงาน TVCalib ต้นทาง ↗</a></article>
      </section>

      <section className="paper-index section-rule">
        <div className="section-heading-editorial"><div><span>อ่านเพิ่มเติม</span><h2>งานวิจัยที่เกี่ยวข้อง</h2></div><small>เปิดอ่านได้จากเว็บไซต์ต้นทาง</small></div>
        <div>{papers.map((paper) => <article key={paper.code}><span>{paper.code}</span><div><h3>{paper.title}</h3><p>{paper.detail}</p><small>{paper.source}</small></div><a href={paper.url} target="_blank" rel="noreferrer">เปิดแหล่งอ้างอิง ↗</a></article>)}</div>
      </section>

      <section className="research-boundaries section-rule">
        <article><h2>แหล่งข้อมูลที่ใช้</h2><ul><li>SoccerNet Camera Calibration</li><li>FIFA Research & Standards Hub</li><li>งานวิจัยการติดตามผู้เล่นและทางเลือกการจ่ายบอล</li></ul></article>
        <article><h2>สิ่งที่ระบบยืนยันได้</h2><ol><li>แสดงตัวแปรที่ใช้คำนวณทุกครั้ง</li><li>แยกผลคำนวณออกจากความเห็นทางแท็กติก</li><li>บอกข้อจำกัดของภาพและการเทียบพิกัดสนาม</li></ol></article>
      </section>
      <section className="research-contact"><div><h2>ต้องการดูรายการอ้างอิงทั้งหมด?</h2><p>อ่านที่มา วิธีคำนวณ และข้อจำกัดฉบับเต็มได้ในเอกสารโครงการ</p></div><a href="https://github.com/nawkkwan/tactivision-mvp/tree/main/docs" target="_blank" rel="noreferrer">เปิดเอกสารโครงการ ↗</a></section>
    </main>
  );
}
