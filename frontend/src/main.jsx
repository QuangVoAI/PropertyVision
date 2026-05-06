import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "";
const PALETTE = ["#2563eb", "#0f766e", "#7c3aed", "#d97706", "#c2410c", "#0891b2", "#4f46e5"];

const emptyFilters = {
  districts: [],
  property_types: [],
  price_min: null,
  price_max: null,
  area_min: null,
  area_max: null,
  roi_min: null,
  roi_max: null
};

const pages = [
  { id: "overview", path: "/overview", label: "Tổng quan điều hành", short: "Tổng quan", icon: "dashboard" },
  { id: "market", path: "/market", label: "Thông tin thị trường", short: "Thị trường", icon: "query_stats" },
  { id: "slice", path: "/slice-dice", label: "Phân tích đa chiều", short: "Slice & Dice", icon: "analytics" },
  { id: "decision", path: "/decision-lab", label: "Phòng thí nghiệm", short: "Decision Lab", icon: "science" },
  { id: "gis", path: "/gis-planning", label: "GIS & Quy hoạch", short: "GIS", icon: "map" },
  { id: "ai", path: "/ai-analyst", label: "Phân tích AI", short: "AI Analyst", icon: "psychology" },
  { id: "ops", path: "/data-ops", label: "Vận hành dữ liệu", short: "Data Ops", icon: "settings_input_component" },
  { id: "explorer", path: "/explorer", label: "Khai thác dữ liệu", short: "Explorer", icon: "explore" },
  { id: "method", path: "/methodology", label: "Phương pháp", short: "Methodology", icon: "schema" },
  { id: "report", path: "/executive-report", label: "Báo cáo lãnh đạo", short: "Report", icon: "summarize" }
];

function currentPageId() {
  const path = window.location.pathname === "/" ? "/overview" : window.location.pathname;
  return pages.find((page) => page.path === path)?.id || "overview";
}

function money(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "N/A";
  const number = Number(value);
  if (Math.abs(number) >= 1_000_000_000) return `${(number / 1_000_000_000).toFixed(2)} tỷ`;
  return `${(number / 1_000_000).toFixed(0)} triệu`;
}

function compact(value) {
  return new Intl.NumberFormat("vi-VN", { notation: "compact", maximumFractionDigits: 1 }).format(value || 0);
}

function pct(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "N/A";
  return `${Number(value).toFixed(2)}%`;
}

function renderMarkdown(text = "") {
  const escaped = String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return escaped
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/^\s*[-*]\s+(.*)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
    .replace(/\n{2,}/g, "</p><p>")
    .replace(/\n/g, "<br />");
}

function MarkdownBlock({ text }) {
  return <div className="markdown-body" dangerouslySetInnerHTML={{ __html: `<p>${renderMarkdown(text)}</p>` }} />;
}

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  if (!response.ok) throw new Error(`API ${path} failed`);
  return response.json();
}

function Icon({ name, fill = false }) {
  return (
    <span className="material-symbols-outlined" style={{ fontVariationSettings: fill ? "'FILL' 1" : undefined }}>
      {name}
    </span>
  );
}

function KpiCard({ label, value, delta, icon, tone = "default" }) {
  return (
    <article className={`kpi-card tone-${tone}`}>
      <div className="kpi-head">
        <span>{label}</span>
        {icon ? <Icon name={icon} /> : null}
      </div>
      <strong>{value}</strong>
      {delta ? <small>{delta}</small> : null}
    </article>
  );
}

function Panel({ title, children, action, className = "" }) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-head">
        <h3>{title}</h3>
        {action}
      </div>
      {children}
    </section>
  );
}

function PageHeader({ eyebrow, title, description }) {
  return (
    <div className="page-header">
      <p>{eyebrow}</p>
      <h2>{title}</h2>
      <span>{description}</span>
    </div>
  );
}

function AppShell({ activePage, setActivePage, children, loading, metadata, filters, setFilters }) {
  function navigate(page) {
    window.history.pushState({}, "", page.path);
    setActivePage(page.id);
  }

  useEffect(() => {
    const handler = () => setActivePage(currentPageId());
    window.addEventListener("popstate", handler);
    return () => window.removeEventListener("popstate", handler);
  }, [setActivePage]);

  return (
    <div className="enterprise-shell">
      <aside className="side-nav">
        <div className="brand-block">
          <div className="brand-mark">PV</div>
          <div>
            <h1>PropertyVision</h1>
            <p>Decision Intelligence</p>
          </div>
        </div>
        <nav className="main-nav">
          {pages.map((page) => (
            <button key={page.id} className={activePage === page.id ? "active" : ""} onClick={() => navigate(page)}>
              <Icon name={page.icon} fill={activePage === page.id} />
              <span>{page.label}</span>
            </button>
          ))}
        </nav>
        <GlobalFilters metadata={metadata} filters={filters} setFilters={setFilters} />
      </aside>

      <header className="top-appbar">
        <div className="crumb">
          <Icon name="search" />
          <span>PROPERTYVISION / {pages.find((page) => page.id === activePage)?.short?.toUpperCase()}</span>
        </div>
        <strong>Hệ thống Hỗ trợ Quyết định</strong>
        <div className="top-actions">
          {loading ? <span className="live-pill">Đang cập nhật</span> : <span className="live-pill online">Live API</span>}
          <Icon name="notifications_active" />
          <Icon name="help_outline" />
          <Icon name="account_circle" />
        </div>
      </header>

      <main className="page-canvas">{children}</main>
    </div>
  );
}

function GlobalFilters({ metadata, filters, setFilters }) {
  if (!metadata) return null;
  return (
    <div className="global-filters">
      <div className="filter-caption">
        <span>Global Filters</span>
        <button onClick={() => setFilters(emptyFilters)}>Reset</button>
      </div>
      <label>
        Giá tối đa: {filters.price_max ? `${filters.price_max.toFixed(1)} tỷ` : "toàn bộ"}
        <input
          type="range"
          min={metadata.price_range[0]}
          max={metadata.price_range[1]}
          step="0.1"
          value={filters.price_max || metadata.price_range[1]}
          onChange={(event) => setFilters((current) => ({ ...current, price_max: Number(event.target.value) }))}
        />
      </label>
      <label>
        ROI tối thiểu: {filters.roi_min ? `${filters.roi_min.toFixed(1)}%` : "toàn bộ"}
        <input
          type="range"
          min={metadata.roi_range[0]}
          max={metadata.roi_range[1]}
          step="0.5"
          value={filters.roi_min || metadata.roi_range[0]}
          onChange={(event) => setFilters((current) => ({ ...current, roi_min: Number(event.target.value) }))}
        />
      </label>
    </div>
  );
}

function OverviewPage({ analytics, typeShare }) {
  const kpis = analytics?.kpis || {};
  return (
    <>
      <PageHeader
        eyebrow="Executive Overview"
        title="Tổng quan Quyết định Chiến lược"
        description="Thông tin thị trường thời gian thực, hiệu quả danh mục và khuyến nghị cho lãnh đạo."
      />
      <div className="kpi-grid">
        <KpiCard label="Total Value" value={money(kpis.total_value)} delta="Filtered market" icon="account_balance" />
        <KpiCard label="Median Price" value={money(kpis.median_price)} delta="Representative price" icon="sell" />
        <KpiCard label="Avg ROI" value={pct(kpis.avg_roi)} delta="Portfolio yield" icon="monitoring" tone="good" />
        <KpiCard label="Best District" value={kpis.best_district || "N/A"} delta={`${(kpis.best_score || 0).toFixed(1)}/100`} icon="location_city" />
        <KpiCard label="Txn Proxy" value={(kpis.transaction_count || 0).toLocaleString("vi-VN")} delta={`Confidence ${((kpis.avg_confidence || 0) * 100).toFixed(0)}%`} icon="swap_horiz" />
      </div>
      <div className="grid-12">
        <Panel title="Xu hướng Thị trường & ROI" className="span-8">
          <ResponsiveContainer width="100%" height={340}>
            <ComposedChart data={analytics?.timeline || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={(v) => String(v).slice(0, 7)} />
              <YAxis yAxisId="left" tickFormatter={(v) => `${v.toFixed(0)} tỷ`} />
              <YAxis yAxisId="right" orientation="right" tickFormatter={(v) => `${v.toFixed(0)}%`} />
              <Tooltip formatter={(v) => Number(v).toFixed(2)} />
              <Legend />
              <Area yAxisId="left" type="monotone" dataKey="price_billion" name="Giá TB (tỷ)" fill="#dbeafe" stroke="#2563eb" />
              <Line yAxisId="right" type="monotone" dataKey="roi_pct" name="ROI (%)" stroke="#0f766e" strokeWidth={2} />
            </ComposedChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Phân bổ Vốn theo Phân khúc" className="span-4">
          <ResponsiveContainer width="100%" height={340}>
            <PieChart>
              <Pie data={typeShare} dataKey="value" nameKey="name" innerRadius={70} outerRadius={110}>
                {typeShare.map((_, index) => <Cell key={index} fill={PALETTE[index % PALETTE.length]} />)}
              </Pie>
              <Tooltip formatter={(v) => `${Number(v).toFixed(2)}%`} />
            </PieChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Khuyến nghị Chiến lược AI" className="span-12 recommendation-panel">
          <Icon name="auto_awesome" />
          <div>
            <strong>Ưu tiên {kpis.best_district || "khu vực có điểm cơ hội cao nhất"}</strong>
            <p>
              Dữ liệu hiện tại cho thấy khu vực ưu tiên có opportunity score {(kpis.best_score || 0).toFixed(1)}/100.
              Doanh nghiệp nên dùng kết quả này làm lớp sàng lọc trước khi kiểm tra pháp lý, quy hoạch và dòng tiền.
            </p>
          </div>
        </Panel>
      </div>
    </>
  );
}

function MarketPage({ analytics }) {
  const districtRows = analytics?.districts || [];
  const topScore = [...districtRows].sort((a, b) => b.opportunity_score - a.opportunity_score).slice(0, 3);
  const underpriced = [...districtRows].sort((a, b) => a.price_m2_million - b.price_m2_million).slice(0, 3);
  return (
    <>
      <PageHeader eyebrow="Market Intelligence" title="Phân tích thị trường" description="So sánh ROI, giá/m² và thanh khoản proxy giữa các khu vực và phân khúc." />
      <div className="grid-12">
        <Panel title="ROI theo Quận (Top 12)" className="span-6">
          <ResponsiveContainer width="100%" height={360}>
            <BarChart data={[...districtRows].sort((a, b) => b.roi_pct - a.roi_pct).slice(0, 12)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="district" interval={0} angle={-25} textAnchor="end" height={90} />
              <YAxis tickFormatter={(v) => `${v}%`} />
              <Tooltip formatter={(v) => pct(v)} />
              <Bar dataKey="roi_pct" fill="#0f766e" name="ROI" />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Giá vs Thanh khoản" className="span-6">
          <ResponsiveContainer width="100%" height={360}>
            <ScatterChart>
              <CartesianGrid />
              <XAxis type="number" dataKey="price_m2_million" name="Triệu/m²" label={{ value: "Giá/m² (triệu VND)", position: "insideBottom", offset: -4 }} />
              <YAxis type="number" dataKey="listings" name="Số tin" tickFormatter={compact} label={{ value: "Thanh khoản proxy", angle: -90, position: "insideLeft" }} />
              <Tooltip cursor={{ strokeDasharray: "3 3" }} formatter={(v) => Number(v).toFixed(1)} />
              <Scatter data={districtRows} fill="#2563eb" />
            </ScatterChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="So sánh phân khúc" className="span-12">
          <DataTable rows={districtRows.slice(0, 12)} />
        </Panel>
        <Panel title="Insight phân biệt khu vực" className="span-12">
          <div className="insight-grid">
            <div><strong>Top opportunity</strong><p>{topScore.map((row) => `${row.district} (${row.opportunity_score.toFixed(1)})`).join(" · ")}</p></div>
            <div><strong>Giá/m² thấp nhất</strong><p>{underpriced.map((row) => `${row.district} (${row.price_m2_million.toFixed(1)}tr/m²)`).join(" · ")}</p></div>
            <div><strong>Benchmark</strong><p>ROI nên đọc cùng opportunity score, giá/m² và thanh khoản proxy để tránh kết luận sai khi ROI gần nhau.</p></div>
          </div>
        </Panel>
      </div>
    </>
  );
}

function DataTable({ rows }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Khu vực</th>
            <th>Hành động</th>
            <th>Số tin</th>
            <th>Giá trung vị</th>
            <th>ROI</th>
            <th>Triệu/m²</th>
            <th>Điểm</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.district}>
              <td>{row.district}</td>
              <td><span className="badge good">{row.opportunity_score >= 65 ? "Mở rộng" : row.roi_pct < 10 ? "Kiểm soát" : "Gom chọn lọc"}</span></td>
              <td>{row.listings?.toLocaleString("vi-VN")}</td>
              <td>{money(row.median_price)}</td>
              <td>{pct(row.roi_pct)}</td>
              <td>{Number(row.price_m2_million || 0).toFixed(1)}</td>
              <td><Score value={row.opportunity_score} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Score({ value }) {
  const score = Number(value || 0);
  return (
    <div className="score-cell">
      <span><i style={{ width: `${Math.min(100, score)}%` }} /></span>
      <b>{score.toFixed(1)}</b>
    </div>
  );
}

function SlicePage({ sliceDice, sliceConfig, setSliceConfig }) {
  return (
    <>
      <PageHeader eyebrow="Slice & Dice Analysis" title="Phân tích đa chiều" description="Cắt dữ liệu theo nhiều chiều để tìm phân khúc hiệu quả nhất cho doanh nghiệp." />
      <div className="grid-12">
        <Panel title="Điều khiển kích thước" className="span-4">
          <div className="control-stack">
            <label>Row dimension<select value={sliceConfig.row_dimension} onChange={(e) => setSliceConfig({ ...sliceConfig, row_dimension: e.target.value })}>{Object.entries(sliceDice?.dimensions || {}).map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select></label>
            <label>Column dimension<select value={sliceConfig.column_dimension} onChange={(e) => setSliceConfig({ ...sliceConfig, column_dimension: e.target.value })}>{Object.entries(sliceDice?.dimensions || {}).map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select></label>
            <label>Metric<select value={sliceConfig.metric} onChange={(e) => setSliceConfig({ ...sliceConfig, metric: e.target.value })}>{Object.entries(sliceDice?.metrics || {}).map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select></label>
          </div>
        </Panel>
        <Panel title="Thông tin so sánh" className="span-8">
          <div className="kpi-grid compact">
            <KpiCard label="Filtered records" value={(sliceDice?.filter_context?.filtered_records || 0).toLocaleString("vi-VN")} delta={`${(sliceDice?.filter_context?.coverage_pct || 0).toFixed(1)}% coverage`} />
            <KpiCard label="Filtered ROI" value={pct(sliceDice?.benchmark?.filtered_avg_roi)} delta={`Market ${pct(sliceDice?.benchmark?.market_avg_roi)}`} />
            <KpiCard label="Filtered giá/m²" value={money(sliceDice?.benchmark?.filtered_avg_price_m2)} delta={`Market ${money(sliceDice?.benchmark?.market_avg_price_m2)}`} />
          </div>
        </Panel>
        <Panel title={`Ma trận hiệu suất (${sliceDice?.metric_label || "Metric"})`} className="span-12">
          <div className="table-wrap">
            <table>
              <thead><tr><th>Segment</th>{(sliceDice?.columns || []).map((column) => <th key={column}>{column}</th>)}</tr></thead>
              <tbody>{(sliceDice?.matrix || []).slice(0, 18).map((row) => <tr key={row.segment}><td>{row.segment}</td>{(sliceDice?.columns || []).map((column) => <td key={column}>{formatMetric(row[column], sliceConfig.metric)}</td>)}</tr>)}</tbody>
            </table>
          </div>
        </Panel>
        <Panel title="Phân đoạn tiềm năng cao" className="span-12">
          <div className="table-wrap">
            <table>
              <thead><tr><th>Segment</th><th>Sub segment</th><th>Records</th><th>ROI</th><th>Giá/m²</th><th>Score</th></tr></thead>
              <tbody>{(sliceDice?.top_segments || []).map((row, index) => <tr key={index}><td>{row[sliceDice.row_dimension]}</td><td>{row[sliceDice.column_dimension]}</td><td>{row.listings?.toLocaleString("vi-VN")}</td><td>{pct(row.avg_roi)}</td><td>{money(row.avg_price_m2)}</td><td>{Number(row.opportunity_score || 0).toFixed(1)}</td></tr>)}</tbody>
            </table>
          </div>
        </Panel>
      </div>
    </>
  );
}

function formatMetric(value, metric) {
  if (metric?.includes("price") || metric === "total_value") return money(value);
  if (metric?.includes("roi")) return pct(value);
  return Number(value || 0).toFixed(2);
}

function DecisionPage({ metadata, predictForm, setPredictForm, simulationForm, setSimulationForm, prediction, whatIf, runWhatIf }) {
  return (
    <>
      <PageHeader eyebrow="Decision Lab" title="Phòng thí nghiệm Quyết định" description="Mô phỏng kết quả đầu tư đa kịch bản và kiểm tra các giả định áp lực." />
      <form className="grid-12" onSubmit={runWhatIf}>
        <Panel title="Thông số Tài sản" className="span-3">
          <div className="control-stack">
            <select value={predictForm.district} onChange={(e) => setPredictForm({ ...predictForm, district: e.target.value })}>{metadata?.districts?.map((item) => <option key={item}>{item}</option>)}</select>
            <select value={predictForm.property_type} onChange={(e) => setPredictForm({ ...predictForm, property_type: e.target.value })}>{metadata?.property_types?.map((item) => <option key={item}>{item}</option>)}</select>
            <select value={predictForm.legal_documents} onChange={(e) => setPredictForm({ ...predictForm, legal_documents: e.target.value })}>{metadata?.legal_documents?.map((item) => <option key={item}>{item}</option>)}</select>
            {["area", "bedrooms", "toilets", "floors"].map((key) => <label key={key}>{key}<input type="number" value={predictForm[key]} onChange={(e) => setPredictForm({ ...predictForm, [key]: e.target.value })} /></label>)}
            <label>ROI kỳ vọng<input type="number" step="0.01" value={predictForm.roi_expected} onChange={(e) => setPredictForm({ ...predictForm, roi_expected: e.target.value })} /></label>
          </div>
        </Panel>
        <Panel title="Mô phỏng Kịch bản" className="span-4">
          <div className="control-stack">
            <label>Ngân sách: {Number(simulationForm.budget_billion).toFixed(1)} tỷ<input type="range" min="1" max="100" step="0.5" value={simulationForm.budget_billion} onChange={(e) => setSimulationForm({ ...simulationForm, budget_billion: e.target.value })} /></label>
            <label>Tăng trưởng/năm: {Number(simulationForm.annual_growth_pct).toFixed(1)}%<input type="range" min="-5" max="25" step="0.5" value={simulationForm.annual_growth_pct} onChange={(e) => setSimulationForm({ ...simulationForm, annual_growth_pct: e.target.value })} /></label>
            <label>Số năm: {simulationForm.years}<input type="range" min="1" max="10" step="1" value={simulationForm.years} onChange={(e) => setSimulationForm({ ...simulationForm, years: e.target.value })} /></label>
            <button className="primary-btn" type="submit">Chạy What-If DSS</button>
          </div>
        </Panel>
        <Panel title="Dự báo Giá trị Tương lai" className="span-5">
          {whatIf ? <div className="result-grid"><KpiCard label="Future Value" value={money(whatIf.summary.future_value)} /><KpiCard label="Capital Gain" value={money(whatIf.summary.capital_gain)} /><KpiCard label="Cumulative ROI" value={pct(whatIf.summary.cumulative_roi_pct)} /><KpiCard label="Payback" value={`${whatIf.summary.payback_years?.toFixed(1)} năm`} /></div> : <p className="muted">Chạy mô phỏng để xem FV, ROI và payback period.</p>}
          {prediction ? <p className="model-note">Giá dự đoán: <b>{money(prediction.predicted_price)}</b> | R² {prediction.model.r2.toFixed(3)} | MAE {money(prediction.model.mae)}</p> : null}
        </Panel>
        <Panel title="Dự báo tăng trưởng (10 năm)" className="span-12">
          {whatIf ? <ResponsiveContainer width="100%" height={380}><ComposedChart data={whatIf.projection}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="year" /><YAxis tickFormatter={(v) => `${(v / 1_000_000_000).toFixed(0)} tỷ`} /><Tooltip formatter={(v) => money(v)} /><Legend /><Area dataKey="confidence_high" name="Confidence high" fill="#dbeafe" stroke="none" fillOpacity={0.45} /><Area dataKey="confidence_low" name="Confidence low" fill="#ffffff" stroke="none" fillOpacity={1} /><Line dataKey="pessimistic" name="Xấu" stroke="#c2410c" strokeWidth={2} dot={false} /><Line dataKey="base" name="Cơ sở" stroke="#2563eb" strokeWidth={3} dot={false} /><Line dataKey="optimistic" name="Lạc quan" stroke="#0f766e" strokeWidth={2} dot={false} /></ComposedChart></ResponsiveContainer> : <p className="muted">Biểu đồ sẽ hiển thị 3 kịch bản và confidence band.</p>}
        </Panel>
      </form>
    </>
  );
}

function GisPage({ mapData }) {
  return (
    <>
      <PageHeader eyebrow="GIS & Planning" title="Bản đồ & Quy hoạch GIS" description="Phân tích điểm cơ hội và risk screening theo không gian." />
      <div className="grid-12">
        <Panel title="Bản đồ quy hoạch" className="span-8 map-panel-host">
          <MapContainer center={[10.78, 106.7]} zoom={10} scrollWheelZoom={false} className="leaflet-panel">
            <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            {(mapData?.districts || []).map((row) => <CircleMarker key={row.district} center={[row.latitude, row.longitude]} radius={Math.max(8, Math.min(30, row.opportunity_score / 3))} pathOptions={{ color: row.risk_level === "low" ? "#0f766e" : row.risk_level === "high" ? "#c2410c" : "#d97706", fillOpacity: 0.62 }}><Popup><strong>{row.district}</strong><p>Score {row.opportunity_score.toFixed(1)}</p><p>ROI {row.roi_pct.toFixed(2)}%</p><p>{row.planning_note}</p></Popup></CircleMarker>)}
          </MapContainer>
        </Panel>
        <Panel title="Chú giải & Risk Watchlist" className="span-4">
          <div className="map-legend">
            <span><i className="dot low" /> Low risk</span>
            <span><i className="dot medium" /> Medium risk</span>
            <span><i className="dot high" /> High risk</span>
            <small>Bubble size = opportunity score</small>
          </div>
          <div className="map-list">{(mapData?.districts || []).slice(0, 10).map((row) => <article className="risk-card" key={row.district}><div><strong>{row.district}</strong><span className={`badge ${row.risk_level}`}>{row.risk_level}</span></div><p>{row.planning_note}</p><small>ROI {row.roi_pct.toFixed(2)}% | Score {row.opportunity_score.toFixed(1)}</small></article>)}</div>
        </Panel>
      </div>
    </>
  );
}

function AiPage({ question, setQuestion, assistant, askAssistant }) {
  return (
    <>
      <PageHeader eyebrow="AI Analyst" title="Trợ lý AI" description="RAG/LLM khai thác tri thức pháp lý, quy hoạch và dữ liệu BI có citation." />
      <div className="grid-12">
        <Panel title="Câu hỏi phân tích" className="span-7">
          <div className="chat-box">
            <textarea value={question} onChange={(e) => setQuestion(e.target.value)} />
            <div className="prompt-row">{["Quận Tân Bình có rủi ro quy hoạch gì?", "Nên ưu tiên khu nào nếu ROI tốt?", "So sánh Bình Chánh và Thủ Đức"].map((prompt) => <button key={prompt} onClick={() => setQuestion(prompt)}>{prompt}</button>)}</div>
            <button className="primary-btn" onClick={askAssistant}>Phân tích</button>
          </div>
          {assistant ? <div className="answer-panel"><div className="meta-row"><span>{assistant.mode}</span><span>{assistant.model}</span><span>{assistant.llm_available ? "LLM online" : "fallback"}</span><span>{assistant.retrieval_time_ms} ms</span></div><MarkdownBlock text={assistant.answer} /></div> : null}
        </Panel>
        <Panel title="Thanh tra nguồn" className="span-5">
          <div className="source-list">{(assistant?.sources || []).map((source) => <a key={source.title} href={source.source_url} target="_blank" rel="noreferrer" className="source-card"><strong>{source.title}</strong><span>{source.content}</span><small>{source.source_name} · score {source.score?.toFixed(2)}</small></a>)}</div>
        </Panel>
      </div>
    </>
  );
}

function DataOpsPage({ etl, refreshEtl, loading, ragStatus }) {
  return (
    <>
      <PageHeader eyebrow="Data Operations" title="Giám sát vận hành dữ liệu" description="Theo dõi ETL gần real-time, nguồn công khai, transaction proxy và RAG index." />
      <div className="grid-12">
        <Panel title="Pipeline Status" className="span-12" action={<button className="primary-btn small" onClick={refreshEtl}>{loading ? "Đang refresh" : "Refresh ETL"}</button>}>
          <div className="kpi-grid compact"><KpiCard label="Transaction Proxy" value={(etl?.transaction_records || 0).toLocaleString("vi-VN")} /><KpiCard label="Planning Zones" value={(etl?.planning_zones || 0).toLocaleString("vi-VN")} /><KpiCard label="Legal Docs" value={(etl?.legal_documents || 0).toLocaleString("vi-VN")} /><KpiCard label="RAG Index" value={ragStatus ? `${ragStatus.documents} docs` : "Ready"} /></div>
        </Panel>
        <Panel title="Nhật ký chạy ETL" className="span-7"><SimpleRuns runs={etl?.runs || []} /></Panel>
        <Panel title="Trung tâm dữ liệu công cộng" className="span-5"><div className="source-list">{(etl?.sources || []).map((source) => <a className="source-card" href={source.url} target="_blank" rel="noreferrer" key={source.url}><strong>{source.name}</strong><span>{source.type}</span><small>{source.status}</small></a>)}</div></Panel>
      </div>
    </>
  );
}

function SimpleRuns({ runs }) {
  return <div className="table-wrap"><table><thead><tr><th>Run</th><th>Mode</th><th>Status</th><th>Seen</th><th>Inserted</th></tr></thead><tbody>{runs.map((run) => <tr key={run.run_id}><td>{run.finished_at?.slice(0, 19)}</td><td>{run.mode}</td><td><span className="badge good">{run.status}</span></td><td>{run.records_seen?.toLocaleString("vi-VN")}</td><td>{run.records_inserted?.toLocaleString("vi-VN")}</td></tr>)}</tbody></table></div>;
}

function ExplorerPage({ analytics }) {
  return (
    <>
      <PageHeader eyebrow="Data Explorer" title="Khai thác dữ liệu" description="Xem chi tiết tài sản ROI cao trong bộ lọc hiện tại." />
      <Panel title="Listings Table">
        <div className="table-wrap"><table><thead><tr><th>Địa chỉ</th><th>Khu vực</th><th>Loại</th><th>Giá</th><th>Diện tích</th><th>ROI</th></tr></thead><tbody>{(analytics?.samples || []).map((row) => <tr key={`${row.Location}-${row.date}`}><td>{row.Location}</td><td>{row.district}</td><td>{row["Type of House"]}</td><td>{money(row.price_vnd)}</td><td>{row.area} m²</td><td>{pct(row.ROI * 100)}</td></tr>)}</tbody></table></div>
      </Panel>
    </>
  );
}

function MethodPage({ methodology }) {
  return (
    <>
      <PageHeader eyebrow="Methodology & Baseline" title="Phương pháp, dữ liệu và hệ thống thông tin" description="Giải thích bài toán, phương pháp BI/DSS/EIS, baseline model và RAG architecture." />
      <div className="grid-12">
        <Panel title="Problem & Method" className="span-7"><p>{methodology?.problem}</p><div className="method-list">{(methodology?.methods || []).map((item) => <p key={item}>• {item}</p>)}</div></Panel>
        <Panel title="MIS/DSS/EIS Mapping" className="span-5"><div className="system-grid">{(methodology?.information_systems || []).map((item) => <article key={item.type}><strong>{item.type}</strong><p>{item.mapping}</p></article>)}</div></Panel>
        <Panel title="RAG Architecture Note" className="span-12"><p>Prototype dùng sentence-transformers + sklearn NearestNeighbors cho cosine similarity search. Khi production, retrieval layer có thể migrate sang ChromaDB, FAISS, Milvus hoặc pgvector để hỗ trợ persistence, metadata filtering và scale lớn hơn.</p></Panel>
      </div>
    </>
  );
}

function ReportPage({ analytics, whatIf, assistant }) {
  const kpis = analytics?.kpis || {};
  return (
    <>
      <PageHeader eyebrow="Executive Report" title="Báo cáo lãnh đạo" description="Tóm tắt phát hiện chính, khuyến nghị và nguồn giải thích để trình bày." />
      <div className="grid-12">
        <Panel title="Key Findings" className="span-6"><ul className="memo-list"><li>Khu ưu tiên: <b>{kpis.best_district}</b> ({(kpis.best_score || 0).toFixed(1)}/100)</li><li>ROI trung bình: <b>{pct(kpis.avg_roi)}</b></li><li>Transaction proxy: <b>{(kpis.transaction_count || 0).toLocaleString("vi-VN")}</b></li></ul></Panel>
        <Panel title="Decision Memo" className="span-6">{assistant?.answer ? <MarkdownBlock text={assistant.answer} /> : <p>Chạy AI Analyst để tạo memo có citation cho báo cáo lãnh đạo.</p>}</Panel>
        <Panel title="What-If Summary" className="span-12">{whatIf ? <div className="kpi-grid compact"><KpiCard label="Future Value" value={money(whatIf.summary.future_value)} /><KpiCard label="Cumulative ROI" value={pct(whatIf.summary.cumulative_roi_pct)} /><KpiCard label="Payback" value={`${whatIf.summary.payback_years?.toFixed(1)} năm`} /></div> : <p className="muted">Chạy Decision Lab để đưa What-If vào báo cáo.</p>}</Panel>
      </div>
    </>
  );
}

function App() {
  const [activePage, setActivePage] = useState(currentPageId());
  const [metadata, setMetadata] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [filters, setFilters] = useState(emptyFilters);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [prediction, setPrediction] = useState(null);
  const [whatIf, setWhatIf] = useState(null);
  const [assistant, setAssistant] = useState(null);
  const [mapData, setMapData] = useState(null);
  const [etl, setEtl] = useState(null);
  const [methodology, setMethodology] = useState(null);
  const [ragStatus, setRagStatus] = useState(null);
  const [sliceDice, setSliceDice] = useState(null);
  const [sliceConfig, setSliceConfig] = useState({ row_dimension: "district", column_dimension: "Type of House", metric: "avg_roi" });
  const [question, setQuestion] = useState("Nên ưu tiên khu vực nào để đầu tư với ROI tốt và rủi ro vừa phải?");
  const [predictForm, setPredictForm] = useState({ district: "", property_type: "", legal_documents: "", area: 70, bedrooms: 3, toilets: 3, floors: 3, roi_expected: 0.14 });
  const [simulationForm, setSimulationForm] = useState({ budget_billion: 10, annual_growth_pct: 8, years: 7 });

  useEffect(() => {
    request("/api/metadata")
      .then((data) => {
        setMetadata(data);
        setPredictForm((current) => ({ ...current, district: data.districts[0], property_type: data.property_types[0], legal_documents: data.legal_documents[0] }));
      })
      .catch(() => setError("Không kết nối được backend FastAPI. Hãy chạy uvicorn backend.main:app --reload."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    Promise.all([request("/api/map/districts"), request("/api/etl/status"), request("/api/methodology")])
      .then(([mapPayload, etlPayload, methodologyPayload]) => { setMapData(mapPayload); setEtl(etlPayload); setMethodology(methodologyPayload); })
      .catch(() => setError("Không tải được dữ liệu GIS/ETL/methodology từ backend."));
  }, []);

  useEffect(() => {
    if (!metadata) return;
    setLoading(true);
    Promise.all([
      request("/api/analytics", { method: "POST", body: JSON.stringify(filters) }),
      request("/api/slice-dice", { method: "POST", body: JSON.stringify({ filters, ...sliceConfig }) })
    ])
      .then(([analyticsPayload, slicePayload]) => { setAnalytics(analyticsPayload); setSliceDice(slicePayload); })
      .catch(() => setError("Không tải được dữ liệu phân tích."))
      .finally(() => setLoading(false));
  }, [filters, metadata, sliceConfig]);

  const typeRows = analytics?.types || [];
  const typeShare = useMemo(() => {
    const total = typeRows.reduce((sum, row) => sum + row.avg_price * row.listings, 0);
    return typeRows.map((row) => ({ name: row["Type of House"], value: total ? (row.avg_price * row.listings) / total * 100 : 0 }));
  }, [typeRows]);

  async function runWhatIf(event) {
    event.preventDefault();
    const payload = {
      ...predictForm,
      area: Number(predictForm.area),
      bedrooms: Number(predictForm.bedrooms),
      toilets: Number(predictForm.toilets),
      floors: Number(predictForm.floors),
      roi_expected: Number(predictForm.roi_expected),
      budget_vnd: Number(simulationForm.budget_billion) * 1_000_000_000,
      annual_growth_pct: Number(simulationForm.annual_growth_pct),
      years: Number(simulationForm.years)
    };
    const [predictionPayload, whatIfPayload] = await Promise.all([
      request("/api/predict", { method: "POST", body: JSON.stringify(payload) }),
      request("/api/what-if", { method: "POST", body: JSON.stringify(payload) })
    ]);
    setPrediction(predictionPayload);
    setWhatIf(whatIfPayload);
  }

  async function askAssistant() {
    setAssistant(await request("/api/assistant", { method: "POST", body: JSON.stringify({ question, filters }) }));
  }

  async function refreshEtl() {
    setLoading(true);
    const payload = await request("/api/etl/run", { method: "POST", body: JSON.stringify({}) });
    setEtl(payload.status);
    setMapData(await request("/api/map/districts"));
    setRagStatus(await request("/api/rag/reindex", { method: "POST", body: JSON.stringify({}) }));
    setAnalytics(await request("/api/analytics", { method: "POST", body: JSON.stringify(filters) }));
    setLoading(false);
  }

  if (error) return <div className="boot-error">{error}</div>;
  if (!metadata || !analytics) return <div className="boot">Đang khởi tạo PropertyVision...</div>;

  const pageProps = { analytics, typeShare, sliceDice, sliceConfig, setSliceConfig, metadata, predictForm, setPredictForm, simulationForm, setSimulationForm, prediction, whatIf, runWhatIf, mapData, etl, refreshEtl, loading, ragStatus, question, setQuestion, assistant, askAssistant, methodology };

  return (
    <AppShell activePage={activePage} setActivePage={setActivePage} loading={loading} metadata={metadata} filters={filters} setFilters={setFilters}>
      {activePage === "overview" && <OverviewPage {...pageProps} />}
      {activePage === "market" && <MarketPage {...pageProps} />}
      {activePage === "slice" && <SlicePage {...pageProps} />}
      {activePage === "decision" && <DecisionPage {...pageProps} />}
      {activePage === "gis" && <GisPage {...pageProps} />}
      {activePage === "ai" && <AiPage {...pageProps} />}
      {activePage === "ops" && <DataOpsPage {...pageProps} />}
      {activePage === "explorer" && <ExplorerPage {...pageProps} />}
      {activePage === "method" && <MethodPage {...pageProps} />}
      {activePage === "report" && <ReportPage {...pageProps} />}
    </AppShell>
  );
}

createRoot(document.getElementById("root")).render(<App />);
