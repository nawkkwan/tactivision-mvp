import { BrandMark, type SiteRoute } from "./SiteHeader";

interface SiteFooterProps {
  onNavigate: (route: SiteRoute) => void;
}

export function SiteFooter({ onNavigate }: SiteFooterProps) {
  return (
    <footer className="site-footer">
      <div className="footer-brand"><BrandMark /><strong>TACTIVISION</strong></div>
      <p>พื้นที่วิเคราะห์เส้นทางการจ่ายบอล พิกัดสนาม และจุดเสี่ยงถูกสกัด</p>
      <div>
        <span>วิธีการคำนวณ</span>
        <p>คะแนนมาจากแบบจำลองคิเนมาติกส์และสมมติฐานที่ผู้ใช้ตรวจสอบหรือปรับได้</p>
      </div>
      <nav aria-label="Footer navigation">
        <button type="button" onClick={() => onNavigate("/")}>Home</button>
        <button type="button" onClick={() => onNavigate("/analyze")}>Analysis</button>
        <button type="button" onClick={() => onNavigate("/news")}>News / Breakdown</button>
        <button type="button" onClick={() => onNavigate("/research")}>Research</button>
      </nav>
      <small>© 2026 TactiVision</small>
    </footer>
  );
}
