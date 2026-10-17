import { BrandMark, type SiteRoute } from "./SiteHeader";

interface SiteFooterProps {
  onNavigate: (route: SiteRoute) => void;
}

export function SiteFooter({ onNavigate }: SiteFooterProps) {
  return (
    <footer className="site-footer">
      <div className="footer-main">
        <button type="button" className="footer-brand" onClick={() => onNavigate("/")} aria-label="กลับหน้าแรก">
          <BrandMark /><strong>TACTIVISION</strong>
        </button>
        <p className="footer-summary">วิเคราะห์เส้นทางการจ่ายบอลจากภาพการแข่งขัน ด้วยพิกัด ระยะทาง และเวลา</p>
        <nav aria-label="Footer navigation">
          <button type="button" onClick={() => onNavigate("/")}>Home</button>
          <button type="button" onClick={() => onNavigate("/analyze")}>Analyze</button>
          <button type="button" onClick={() => onNavigate("/news")}>News</button>
          <button type="button" onClick={() => onNavigate("/research")}>Research</button>
        </nav>
      </div>
      <div className="footer-lower">
        <span>คะแนนความเสี่ยงอ้างอิงแบบจำลองคิเนมาติกส์และค่าที่ผู้ใช้กำหนด</span>
        <small>© 2026 TactiVision</small>
      </div>
    </footer>
  );
}
