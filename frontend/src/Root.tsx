import { useEffect, useState } from "react";
import AnalysisApp from "./App";
import { SiteFooter } from "./components/SiteFooter";
import { SiteHeader, type SiteRoute } from "./components/SiteHeader";
import { HomePage } from "./pages/HomePage";
import { NewsPage } from "./pages/NewsPage";
import { ResearchPage } from "./pages/ResearchPage";

function routeFromPath(pathname: string): SiteRoute {
  if (pathname.startsWith("/analyze")) return "/analyze";
  if (pathname.startsWith("/news")) return "/news";
  if (pathname.startsWith("/research")) return "/research";
  return "/";
}

export default function Root() {
  const [route, setRoute] = useState<SiteRoute>(() => routeFromPath(window.location.pathname));

  useEffect(() => {
    const handlePopState = () => setRoute(routeFromPath(window.location.pathname));
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    const titles: Record<SiteRoute, string> = {
      "/": "TactiVision — Tactical Pass Analysis",
      "/analyze": "Analyze — TactiVision",
      "/news": "News & Breakdown — TactiVision",
      "/research": "Research — TactiVision",
    };
    document.title = titles[route];
  }, [route]);

  function navigate(nextRoute: SiteRoute) {
    if (nextRoute !== route) window.history.pushState({}, "", nextRoute);
    setRoute(nextRoute);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className={`site-shell route-${route === "/" ? "home" : route.slice(1)}`}>
      <SiteHeader route={route} onNavigate={navigate} />
      {route === "/" ? <HomePage onAnalyze={() => navigate("/analyze")} onResearch={() => navigate("/research")} /> : null}
      {route === "/analyze" ? <AnalysisApp /> : null}
      {route === "/news" ? <NewsPage onAnalyze={() => navigate("/analyze")} /> : null}
      {route === "/research" ? <ResearchPage /> : null}
      {route !== "/analyze" ? <SiteFooter onNavigate={navigate} /> : null}
    </div>
  );
}
