import { MatchStories } from "../components/MatchStories";

export function NewsPage({ onAnalyze }: { onAnalyze: () => void }) {
  return <main className="editorial-page dossier-page">
    <section className="news-intro"><span>NEWS & BREAKDOWNS</span><h1>สองจังหวะ สองคำถามเรื่องการจ่ายบอล</h1><p>เปรียบเทียบภาพการแข่งขันกับผลวิเคราะห์ และดูคลิปต้นทางประกอบการตัดสินใจ</p></section>
    <section className="case-section news-stories"><MatchStories onAnalyze={onAnalyze} /></section>
    <section className="submit-case"><div><h2>ลองวิเคราะห์จังหวะของคุณ</h2><p>อัปโหลดภาพ แล้วเลือกทางจ่ายที่ต้องการเปรียบเทียบ</p></div><button type="button" onClick={onAnalyze}>เริ่มวิเคราะห์</button></section>
  </main>;
}
