export type SiteRoute = "/" | "/analyze" | "/news" | "/research";

interface SiteHeaderProps {
  route: SiteRoute;
  onNavigate: (route: SiteRoute) => void;
}

const links: Array<{ route: SiteRoute; label: string }> = [
  { route: "/", label: "HOME" },
  { route: "/analyze", label: "ANALYZE" },
  { route: "/news", label: "NEWS / BREAKDOWN" },
  { route: "/research", label: "RESEARCH" },
];

export function BrandMark() {
  return (
    <span className="site-brand-mark" aria-hidden="true">
      <svg viewBox="0 0 40 22">
        <path d="M2 3h14M9 3v16M20 3l7 16L34 3" />
        <path className="brand-route" d="M4 19Q20 8 36 18" />
        <circle cx="36" cy="18" r="1.8" />
      </svg>
    </span>
  );
}

export function SiteHeader({ route, onNavigate }: SiteHeaderProps) {
  return (
    <header className="site-header">
      <button className="site-brand" type="button" onClick={() => onNavigate("/")} aria-label="TactiVision home">
        <BrandMark />
        <strong>TACTIVISION</strong>
      </button>
      <nav className="site-nav" aria-label="Main navigation">
        {links.map((link) => (
          <button
            type="button"
            key={link.route}
            className={route === link.route ? "active" : ""}
            onClick={() => onNavigate(link.route)}
          >
            {link.label}
          </button>
        ))}
      </nav>
      <button className="site-cta" type="button" onClick={() => onNavigate("/analyze")}>START ANALYSIS</button>
    </header>
  );
}
