const papers = [
  { number: "PAPER 02 / AVAILABILITY", date: "JUNE 2022", status: "PUBLISHED", title: "แบบจำลองความพร้อมของผู้เล่นต่อการรับบอล (Player Availability)", detail: "เปรียบเทียบเวลาที่ผู้รับบอลและฝ่ายรับเข้าถึงตำแหน่งต่าง ๆ บนแนวทางการจ่าย เพื่ออธิบายว่าทางเลือกใดยังเปิดอยู่ในจังหวะนั้น", source: "Brefeld et al. · Data Mining and Knowledge Discovery", action: "เปิดงานต้นฉบับ ↗", url: "https://doi.org/10.1007/s10618-022-00827-2" },
  { number: "PAPER 03 / PASS SEQUENCE", date: "NOV 2021", status: "PEER REVIEWED", title: "การประเมินผลของลำดับการจ่ายต่อโครงสร้างแนวรับ", detail: "ใช้แบบจำลอง defensive disruptiveness เพื่อตรวจสอบว่าลำดับการจ่ายบอลเปลี่ยนความพร้อมและโครงสร้างของฝ่ายรับอย่างไร", source: "Forcher et al. · Entropy 23(12)", action: "อ่านงานต้นฉบับ ↗", url: "https://doi.org/10.3390/e23121607" },
  { number: "PAPER 04 / FIELD POSITION", date: "JULY 2017", status: "OPEN ACCESS", title: "การหาตำแหน่งสนามจากภาพถ่ายทอดด้วยแบบจำลองเชิงโครงสร้าง", detail: "ใช้เส้นสนาม พื้นสนาม และวงกลมกลางสนามเพื่อระบุตำแหน่งพิกัดจากกล้องถ่ายทอด ซึ่งเป็นพื้นฐานของการวางตำแหน่งผู้เล่นลงบนสนามมาตรฐาน", source: "Homayounfar et al. · CVPR 2017", action: "เปิด CVF Paper ↗", url: "https://openaccess.thecvf.com/content_cvpr_2017/html/Homayounfar_Sports_Field_Localization_CVPR_2017_paper.html" },
  { number: "PAPER 05 / BALL FLIGHT", date: "JUNE 2020", status: "OPEN ACCESS", title: "การวัดวิถีการเคลื่อนที่ของลูกฟุตบอลที่มีการหมุน", detail: "อธิบายผลของความเร็วต้น สปิน และแรงต้านต่อวิถีบอล รวมถึงข้อจำกัดของการประมาณลูกโค้งจากภาพนิ่งเพียงภาพเดียว", source: "Hong et al. · Proceedings 49(1)", action: "เปิด MDPI ↗", url: "https://www.mdpi.com/2504-3900/49/1/88" },
];

const repositories = [
  ["SoccerNet Camera Calibration", "ชุดข้อมูลเส้นสนามและการเทียบพิกัดจากภาพฟุตบอล", "SOCCERNET ↗", "https://www.soccer-net.org/tasks/camera-calibration"],
  ["TactiVision Project Documentation", "สูตรคำนวณ สมมติฐาน และรายละเอียดการทำงานของระบบ", "GITHUB REPO ↗", "https://github.com/nawkkwan/tactivision-mvp/tree/main/docs"],
  ["FIFA Research & Standards Hub", "มาตรฐานสนามและข้อมูลเทคนิคที่ใช้อ้างอิง", "FIFA.COM ↗", "https://www.fifa.com/technical/football-technology/standards"],
];

export function ResearchPage() {
  return (
    <main className="editorial-page research-page">
      <section className="research-heading">
        <div className="research-intro">
          <div className="research-kicker"><span>ARCHIVE · ISSN</span><b>TACTIVISION RESEARCH ARCHIVE &amp; WORKING PAPERS</b></div>
          <h1>คลังงานวิจัยและระเบียบวิธีทางฟุตบอล</h1>
          <h2>RESEARCH &amp; TECHNICAL WORKING PAPERS</h2>
          <p>รวมงานวิจัยเรื่องการเคลื่อนที่ของผู้เล่น แบบจำลองการจ่ายบอล การเทียบภาพกับพิกัดสนาม และข้อจำกัดของการคำนวณที่นำมาใช้ใน TactiVision</p>
        </div>
        <aside className="research-audit"><span>REPOSITORY AUDIT STATUS</span><div><p><strong>05</strong><small>SELECTED PAPERS</small></p><p><strong>100%</strong><small>SOURCE LINKS</small></p></div><footer>METHOD &amp; LIMITS DISCLOSED</footer></aside>
      </section>

      <section className="lead-paper section-rule">
        <div className="research-section-bar"><span>FEATURED LEAD PAPER</span><b>PAPER 01 · FIELD REGISTRATION</b><small>OPEN ACCESS</small></div>
        <div className="lead-paper-grid">
          <figure className="research-figure"><div className="research-figure-meta"><span>SOURCE FRAME: MATCH BROADCAST</span><span>PITCH: 105 × 68 M.</span></div><img src="/research-featured-match.jpg" alt="ภาพการแข่งขันฟุตบอลสำหรับงานเทียบพิกัดสนาม" /><figcaption><span>ภาพการแข่งขันก่อนเทียบพิกัดสนาม</span><b>CALIBRATION INPUT</b></figcaption></figure>
          <article className="lead-paper-copy">
            <span>WORKING PAPER 01</span><h2>การปรับระนาบกล้อง 2D Homography จากภาพถ่ายทอด เพื่อคำนวณพิกัดบนสนามจริง</h2><small>SINGLE-CAMERA 2D HOMOGRAPHY &amp; SPORTS FIELD REGISTRATION</small>
            <dl><div><dt>Authors</dt><dd>Theiner &amp; Ewerth</dd></div><div><dt>Published</dt><dd>WACV 2023</dd></div><div><dt>Access</dt><dd>Open access</dd></div></dl>
            <h3>บทคัดย่อสำหรับการใช้งาน</h3><p>ระบบอาศัยเส้นสนามเพื่อแปลงจุดจากภาพถ่ายทอดไปยังสนามมาตรฐาน 105 × 68 เมตร แล้วจึงคำนวณระยะทาง เวลาบอลเดินทาง และเวลาที่ฝ่ายรับเข้าถึงแนวบอล</p><p>หากภาพไม่มีเส้นสนามเพียงพอ ผู้ใช้กำหนดจุดเทียบพิกัดเองได้ และตรวจสอบค่าความคลาดเคลื่อนก่อนเริ่มวิเคราะห์</p>
            <a className="research-primary-link" href="https://openaccess.thecvf.com/content/WACV2023/html/Theiner_TVCalib_Camera_Calibration_for_Sports_Field_Registration_in_Soccer_WACV_2023_paper.html" target="_blank" rel="noreferrer">อ่านงาน TVCalib ฉบับเต็ม ↗</a>
          </article>
        </div>
      </section>

      <section className="paper-index section-rule">
        <header><div><span>INDEXED LITERATURE</span><h2>คลังเอกสารจำแนกตามหมวดหมู่</h2><strong>CLASSIFIED PAPERS INDEX</strong></div><div className="paper-filters"><b>ALL PAPERS (5)</b><span>FIELD (2)</span><span>TACTICS (2)</span><span>BALL FLIGHT (1)</span></div></header>
        <div className="paper-list">{papers.map((paper) => <article key={paper.number}><div className="paper-meta"><b>{paper.number}</b><span>{paper.date}</span><em>{paper.status}</em></div><div><h3>{paper.title}</h3><p>{paper.detail}</p><small>{paper.source}</small></div><a href={paper.url} target="_blank" rel="noreferrer">{paper.action}</a></article>)}</div>
      </section>

      <section className="research-boundaries section-rule">
        <article><span>OPEN DATA INFRASTRUCTURE</span><h2>แหล่งข้อมูลและมาตรฐานที่เชื่อมต่อ</h2><strong>DATA REPOSITORIES &amp; EXTERNAL MIRRORS</strong><p>แหล่งข้อมูลและเอกสารด้านล่างใช้ตรวจสอบที่มาของวิธีคำนวณ รวมถึงมาตรฐานสนามและข้อจำกัดของภาพถ่ายทอด</p><div className="repository-list">{repositories.map(([name, description, action, url]) => <a key={name} href={url} target="_blank" rel="noreferrer"><i>▣</i><span><b>{name}</b><small>{description}</small></span><em>{action}</em></a>)}</div></article>
        <article><span>TRANSPARENCY STANDARD</span><h2>นโยบายตรวจสอบความถูกต้อง</h2><strong>VERIFICATION &amp; PEER REVIEW POLICY</strong><ol><li><b>สมการต้องตรวจสอบย้อนกลับได้</b><p>ระบุตัวแปร หน่วย และสมมติฐานที่ใช้คำนวณทุกครั้ง</p></li><li><b>แยกผลคำนวณจากคำอธิบาย</b><p>คะแนนความเสี่ยงไม่ใช่ความน่าจะเป็นจากข้อมูลการแข่งขันจริง</p></li><li><b>เปิดเผยข้อจำกัดของภาพ</b><p>แจ้งเมื่อภาพหรือการเทียบพิกัดไม่เพียงพอสำหรับข้อสรุป</p></li></ol></article>
      </section>

      <section className="research-contact"><div><span>SCHOLARLY INQUIRIES &amp; CITATION</span><h2>ต้องการอ้างอิงงานวิจัยหรือดูสูตรคำนวณเพิ่มเติม?</h2><p>เปิดเอกสารโครงการเพื่อดูสมการ ตัวแปร และข้อจำกัดของแบบจำลอง</p></div><a href="https://github.com/nawkkwan/tactivision-mvp/tree/main/docs" target="_blank" rel="noreferrer">เปิดเอกสารโครงการ ↗</a></section>
    </main>
  );
}
