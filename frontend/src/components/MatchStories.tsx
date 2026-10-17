import { useState } from "react";

export const matchStories = [
  { id: "arsenal-leeds", label: "ARSENAL 1–1 LEEDS · 69:26", title: "จังหวะขึ้นนำ 2–1: P14 จ่ายให้ P3", description: "เปรียบเทียบภาพก่อนจ่ายกับผลวิเคราะห์เมื่อกำหนด P14 เป็นผู้ครองบอล และเลือก P3 เป็นเป้าหมายการจ่าย", source: "/arsenal-leeds-source.png", analysis: "/arsenal-leeds-analysis.png", url: "https://www.youtube.com/watch?v=eePZPgO4F0g&t=266s", note: "ผลวิเคราะห์ของเส้นทาง P14 → P3 แสดงร่วมกับทางเลือก A / B / C โดยคะแนนใช้เปรียบเทียบความเสี่ยงภายใต้ค่าที่กำหนด" },
  { id: "spain-japan", label: "SPAIN / JAPAN · 08:14", title: "จังหวะแทงช่องด้านซ้าย: ฝ่ายรับเข้าถึงแนวบอลทันไหม?", description: "ดูช่องจ่ายจากภาพจริง แล้วเปรียบเทียบกับเส้นทางและผลคำนวณเมื่อเลือกพื้นที่ด้านซ้าย", source: "/spain-japan-through-ball-source.png", analysis: "/spain-japan-through-ball-analysis.png", url: "https://www.youtube.com/watch?v=DtzIyXc56f4", note: "ภาพผลคำนวณแสดงคะแนนความเสี่ยง 48/100 สำหรับทางเลือกที่เลือก คะแนนขึ้นกับสมมติฐานของการจำลอง" },
];

export function MatchStories({ onAnalyze }: { onAnalyze: () => void }) {
  return <div className="match-stories">{matchStories.map((story, index) => <article className="story-dossier" id={story.id} key={story.id}>
    <header><span>CASE {String(index + 1).padStart(2, "0")} · {story.label}</span><a href={story.url} target="_blank" rel="noreferrer">ดูคลิปต้นทาง ↗</a></header>
    <h3>{story.title}</h3><p>{story.description}</p>
    <div className="story-images">
      <figure><figcaption>ภาพการแข่งขัน <span>BEFORE</span></figcaption><a href={story.source} target="_blank" rel="noreferrer" aria-label={`เปิดภาพก่อนวิเคราะห์ ${story.label}`}><img loading="lazy" src={story.source} alt={`ภาพก่อนวิเคราะห์ ${story.label}`} /></a></figure>
      <figure><figcaption>ภาพหลังวิเคราะห์ <span>AFTER</span></figcaption><a href={story.analysis} target="_blank" rel="noreferrer" aria-label={`เปิดผลวิเคราะห์ ${story.label}`}><img loading="lazy" src={story.analysis} alt={`ภาพผลวิเคราะห์ ${story.label}`} /></a></figure>
    </div>
    <footer><p>{story.note}</p><button type="button" onClick={onAnalyze}>ลองวิเคราะห์ภาพของคุณ →</button></footer>
  </article>)}</div>;
}

export function MatchComparison() {
  const [split, setSplit] = useState(50);
  return <figure className="match-wipe">
    <div className="match-wipe-stage">
      <img src="/arsenal-leeds-analysis.png" alt="ภาพวิเคราะห์เส้นทาง P14 จ่ายให้ P3 ในเกม Arsenal พบ Leeds" />
      <img className="match-wipe-before" src="/arsenal-leeds-source.png" alt="ภาพการแข่งขันก่อน P14 จ่ายให้ P3" style={{ clipPath: `inset(0 ${100 - split}% 0 0)` }} />
      <span className="wipe-label before">ภาพการแข่งขัน · BEFORE</span><span className="wipe-label after">หลังวิเคราะห์ · AFTER</span>
      <div className="wipe-divider" style={{ left: `${split}%` }} aria-hidden="true"><span>↔</span></div>
      <input type="range" min="0" max="100" value={split} onChange={(event) => setSplit(Number(event.target.value))} aria-label="เลื่อนเปรียบเทียบภาพก่อนและหลังวิเคราะห์" aria-valuetext={`ภาพก่อนวิเคราะห์ ${split} เปอร์เซ็นต์`} />
    </div><figcaption><span>เลื่อนเส้นกลางเพื่อเปรียบเทียบภาพ</span><span>ภาพผลจำลองจากค่าที่กำหนด</span></figcaption>
  </figure>;
}
