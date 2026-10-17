import { BrandMark, type SiteRoute } from "./SiteHeader";

interface SiteFooterProps {
  onNavigate: (route: SiteRoute) => void;
}

export function SiteFooter({ onNavigate }: SiteFooterProps) {
  return (
    <footer className="site-footer">
      <div className="footer-brand"><BrandMark /><strong>TACTIVISION</strong></div>
      <p>A tactical football journal and analytical workspace for comparing pass routes, field coordinates, and interception assumptions.</p>
      <div>
        <span>METHODOLOGY TRANSPARENCY</span>
        <p>Results are deterministic kinematic scores based on visible inputs and adjustable assumptions.</p>
      </div>
      <nav aria-label="Footer navigation">
        <button type="button" onClick={() => onNavigate("/")}>Home</button>
        <button type="button" onClick={() => onNavigate("/analyze")}>Analysis</button>
        <button type="button" onClick={() => onNavigate("/news")}>News / Breakdown</button>
        <button type="button" onClick={() => onNavigate("/research")}>Research</button>
      </nav>
      <small>© 2026 TactiVision Analytical Press.</small>
    </footer>
  );
}
