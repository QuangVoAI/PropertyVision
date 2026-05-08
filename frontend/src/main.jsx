import React, { useEffect, useMemo, useRef, useState } from "react";
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
  ReferenceLine,
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
const DEFAULT_MODEL_LABEL = "AI provider";
const APP_VERSION = "2.0.0";
const DECISION_BASE_YEAR = 2025;
const DECISION_MAX_YEAR = 2050;

const emptyFilters = {
  city: "TP Hồ Chí Minh",
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
  { id: "overview", path: "/overview", label: "Tổng quan điều hành", short: "Tổng quan", icon: "dashboard", description: "KPI trọng yếu và xu hướng danh mục." },
  { id: "market", path: "/market", label: "Thông tin thị trường", short: "Thị trường", icon: "query_stats", description: "So sánh thị trường và mặt bằng giá." },
  { id: "slice", path: "/slice-dice", label: "Phân tích đa chiều", short: "Đa chiều", icon: "analytics", description: "Phân tích theo nhiều chiều dữ liệu." },
  { id: "decision", path: "/decision-lab", label: "Mô phỏng đầu tư", short: "Mô phỏng", icon: "science", description: "Mô phỏng ROI và hoàn vốn." },
  { id: "gis", path: "/gis-planning", label: "Bản đồ quy hoạch", short: "Bản đồ", icon: "map", description: "Rủi ro quy hoạch và cơ hội." },
  { id: "ai", path: "/ai-analyst", label: "Trợ lý phân tích", short: "Trợ lý", icon: "psychology", description: "Hỏi nhanh, ra quyết định nhanh." },
  { id: "ops", path: "/data-ops", label: "Theo dõi dữ liệu", short: "Dữ liệu", icon: "settings_input_component", description: "Giám sát ETL và chất lượng dữ liệu." },
  { id: "explorer", path: "/explorer", label: "Chi tiết tài sản", short: "Tài sản", icon: "explore", description: "Xem sâu từng tài sản." },
  { id: "report", path: "/periodic-report", label: "Báo cáo định kỳ", short: "Báo cáo", icon: "summarize", description: "Tóm tắt điều hành theo kỳ." }
];

const PANEL_HINTS = {
  "Xu hướng điều hành 2025–2050": "Theo dõi xu hướng KPI và kịch bản điều hành dài hạn.",
  "Kiểm tra giả định tăng trưởng": "Điều chỉnh tăng trưởng để kiểm tra độ nhạy chiến lược.",
  "Khuyến nghị điều hành": "Tóm tắt hành động ưu tiên cho ban điều hành.",
  "ROI theo khu vực nổi bật": "So sánh hiệu quả đầu tư giữa các khu vực.",
  "Thanh khoản và Giá/m²": "Đọc sức mua và mặt bằng giá trên cùng biểu đồ.",
  "So sánh phân khúc": "Đối chiếu hiệu quả giữa các nhóm tài sản.",
  "Insight phân biệt khu vực": "Rút ra điểm khác biệt nhanh giữa các khu vực.",
  "Thiết lập phân tích": "Chọn chiều phân tích và chỉ tiêu đo lường.",
  "Thông tin so sánh": "Hiển thị phạm vi và bối cảnh đang so sánh.",
  "Ma trận hiệu quả (": "Heatmap hiệu quả để nhìn nhanh khu vực/phân khúc.",
  "Phân đoạn tiềm năng cao": "Lọc ra nhóm phân khúc đáng ưu tiên.",
  "Thông số tài sản": "Thông tin đầu vào của tài sản đang mô phỏng.",
  "Giả định đầu tư": "Thiết lập ngân sách, tăng trưởng và thời gian nắm giữ.",
  "Kết quả tài chính dự kiến": "Kết quả mô phỏng tài chính đầu ra.",
  "Triển vọng giá trị theo kịch bản": "So sánh ba kịch bản xấu, cơ sở và lạc quan.",
  "Mốc thời gian & tình huống thua lỗ": "Xem mốc hoàn vốn và điểm rủi ro.",
  "Khuyến nghị đầu tư tương lai": "Đọc khuyến nghị AI cho quyết định đầu tư.",
  "Bản đồ quy hoạch": "Xem rủi ro quy hoạch và opportunity score.",
  "Chú giải và khu vực cần theo dõi": "Giải thích màu sắc và khu vực cảnh báo.",
  "Câu hỏi phân tích": "Nhập câu hỏi để truy vấn RAG/LLM.",
  "Thanh tra nguồn": "Kiểm tra nguồn trích dẫn và độ tin cậy.",
  "Tình trạng dữ liệu": "Theo dõi trạng thái nạp và cập nhật dữ liệu.",
  "Nhật ký cập nhật dữ liệu": "Xem lịch sử các lần nạp dữ liệu.",
  "Trung tâm dữ liệu công cộng": "Nguồn dữ liệu và trạng thái khai thác.",
  "Bảng tài sản": "Danh sách tài sản trong bộ lọc hiện tại.",
  "Phát hiện chính": "Tóm tắt các phát hiện cần nhấn mạnh.",
  "Ghi chú điều hành": "Ghi chú ngắn cho báo cáo định kỳ của lãnh đạo.",
  "Tóm tắt mô phỏng đầu tư": "Tóm tắt ba chỉ số chính của mô phỏng.",
  "Báo cáo định kỳ": "Tổng hợp kết quả để trình bày theo chu kỳ."
};

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

function riskPriority(riskLevel) {
  if (riskLevel === "high") return 3;
  if (riskLevel === "medium") return 2;
  return 1;
}

function groupMapMarkers(rows = []) {
  const groups = new Map();
  rows.forEach((row) => {
    const latitude = Number(row.latitude);
    const longitude = Number(row.longitude);
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return;
    const key = `${latitude.toFixed(4)}:${longitude.toFixed(4)}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(row);
  });

  return [...groups.values()]
    .map((items) => {
      const sortedByScore = [...items].sort((a, b) => Number(b.opportunity_score || 0) - Number(a.opportunity_score || 0));
      const primary = sortedByScore[0];
      const riskOrder = [...items].sort((a, b) => riskPriority(b.risk_level) - riskPriority(a.risk_level));
      const dominantRisk = riskOrder[0]?.risk_level || primary?.risk_level || "medium";
      return {
        ...primary,
        district: items.length === 1 ? primary.district : `${primary.district} +${items.length - 1}`,
        districts: items.map((item) => item.district),
        district_count: items.length,
        aggregate_opportunity_score: Number(primary.opportunity_score || 0),
        aggregate_roi_pct: Number(primary.roi_pct || 0),
        risk_level: dominantRisk,
        planning_note: items.length > 1 ? `Có ${items.length} khu cùng tọa độ. Khu nổi bật: ${primary.district}.` : primary.planning_note
      };
    })
    .sort((a, b) => Number(b.aggregate_opportunity_score || 0) - Number(a.aggregate_opportunity_score || 0));
}

function markerScore(row) {
  return Number(row?.aggregate_opportunity_score ?? row?.opportunity_score ?? 0);
}

function markerRoi(row) {
  return Number(row?.aggregate_roi_pct ?? row?.roi_pct ?? 0);
}

function formatDateTime(value) {
  if (!value) return "Chưa cập nhật";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Chưa cập nhật";
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

function aiStageInfo(status, loading = false) {
  const normalized = String(status || "").toLowerCase();
  if (normalized === "error") return { label: "Error", tone: "high" };
  if (normalized === "stopped") return { label: "Paused", tone: "medium" };
  if (normalized === "done") return { label: "Ready", tone: "good" };
  if (normalized === "streaming") return { label: "Model warm", tone: "good" };
  if (normalized === "waiting_huggingface" || normalized === "waiting_featherless" || normalized === "waiting_provider") return { label: "Model loading", tone: "loading" };
  if (loading) return { label: "Model loading", tone: "loading" };
  return { label: "Ready", tone: "good" };
}

function normalizeMarkdownText(text = "") {
  return String(text)
    .replace(/\r\n/g, "\n")
    .replace(/^Chào\s+CEO,?\s*/i, "")
    .replace(/^Chào\s+bạn,?\s*/i, "")
    .replace(/^\s*---+\s*$/gm, "")
    .replace(/^\s*(\d+)\.\s*$/gm, "$1.")
    .replace(/^\s*(\d+)\.\s*\n\s*([^\n]+)/gm, "$1. $2")
    .replace(/^\s*(\d+)\.\s*(Kết luận điều hành|Cơ sở nhận định|Rủi ro cần lưu ý|Hành động tiếp theo|Phát hiện chính|Lợi thế|Rủi ro|Hành động|Tổng quan|Cơ sở|Rủi ro cần lưu ý|Hành động tiếp theo)\s*$/gim, "## $2")
    .replace(/^\s*[-*]\s*\n\s*([^\n]+)/gm, "- $1")
    .replace(/^\*\*(Kết luận điều hành|Cơ sở nhận định|Rủi ro cần lưu ý|Hành động tiếp theo|Phát hiện chính|Lợi thế|Rủi ro|Hành động|Rủi ro quy hoạch|Rủi ro pháp lý|Ảnh hưởng thanh khoản|Gợi ý kiểm tra tiếp theo)\*\*:\s*/gm, "## $1\n")
    .replace(/^(1|2|3|4)\.\s*(Kết luận điều hành|Cơ sở nhận định|Rủi ro cần lưu ý|Hành động tiếp theo|Phát hiện chính|Lợi thế|Rủi ro|Hành động)\s*:\s*/gim, "## $2\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function sanitizeRecommendationText(text = "") {
  return String(text)
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .split("\n")
    .map((rawLine) => {
      let line = rawLine.trim();
      if (!line) return "";
      line = line.replace(/^\s*#{1,6}\s*/, "").trim();
      if (!line || /^[-*_ ]+$/.test(line)) return "";
      if (/\*/.test(line) && /^\*+\s*[A-Za-zÀ-ỹ_ ]{1,4}\s*$/u.test(line)) return "";
      if (/^(?:[-*]\s*)?(?:\*\*)?\s*(CHART_SPEC|CHART SPEC|CHARTSPEC|chart_type|title|caption|insight|x_key|series|reference_line)(?:\*\*)?\s*:/i.test(line)) return "";
      if (/^(?:\*\*)?\s*(ACTION|WHY|RISKS|SUGGESTION|BASIS|KET_LUAN|LY_DO|RUI_RO|GOI_Y|CO_SO|CHART_SPEC|CHART SPEC|CHARTSPEC)(?:\*\*)?\s*:?\s*$/i.test(line)) return "";
      line = line.replace(/\*\*/g, "").trim();
      line = line.replace(/^(ACTION|WHY|RISKS|SUGGESTION|BASIS|KET_LUAN|LY_DO|RUI_RO|GOI_Y|CO_SO)\s*:?\s*/i, "").trim();
      line = line.replace(/^(KẾT LUẬN|LÝ DO|RỦI RO CẦN NÊU|HÀNH ĐỘNG|CƠ SỞ ĐƯA RA KHUYẾN NGHỊ)\s*:?\s*/i, "").trim();
      return line;
    })
    .filter(Boolean)
    .join("\n")
    .trim();
}

function sanitizeRecommendationList(items = []) {
  return items.map((item) => sanitizeRecommendationText(item)).filter(Boolean);
}

function providerWaitingCopy(status, llmMode) {
  const normalizedStatus = String(status || "").toLowerCase();
  const normalizedMode = String(llmMode || "").toLowerCase();
  if (normalizedStatus === "waiting_featherless" || normalizedMode === "featherless-direct") {
    return {
      title: "Đang chờ Featherless...",
      body: "Hệ thống đang chờ Featherless trả phản hồi để sinh câu ngữ nghĩa."
    };
  }
  if (normalizedStatus === "waiting_huggingface" || normalizedMode === "hf-hosted") {
    return {
      title: "Đang chờ Hugging Face...",
      body: "Hệ thống đang chờ phản hồi từ hosted model để sinh câu ngữ nghĩa."
    };
  }
  return {
    title: "Đang chờ AI provider...",
    body: "Hệ thống đang chờ phản hồi từ model để sinh câu ngữ nghĩa."
  };
}

function renderMarkdown(text = "") {
  const normalized = normalizeMarkdownText(text);
  if (!normalized) return "";

  const escapeInline = (value) => String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  const lines = normalized.split("\n");
  const segments = [];
  let paragraph = [];
  let currentListType = null;
  let currentList = [];

  const flushParagraph = () => {
    if (!paragraph.length) return;
    segments.push(`<p>${paragraph.map((line) => escapeInline(line)).join("<br />")}</p>`);
    paragraph = [];
  };

  const flushList = () => {
    if (!currentList.length) return;
    const tag = currentListType === "ol" ? "ol" : "ul";
    segments.push(`<${tag}>${currentList.map((item) => `<li>${escapeInline(item)}</li>`).join("")}</${tag}>`);
    currentList = [];
    currentListType = null;
  };

  lines.forEach((rawLine) => {
    const line = rawLine.trim();
    if (!line) {
      flushList();
      flushParagraph();
      return;
    }

    const headingMatch = line.match(/^(#{1,3})\s+(.*)$/);
    if (headingMatch) {
      flushList();
      flushParagraph();
      const level = Math.min(3, headingMatch[1].length);
      segments.push(`<h${level}>${escapeInline(headingMatch[2])}</h${level}>`);
      return;
    }

    const orderedMatch = line.match(/^(\d+)\.\s+(.*)$/);
    if (orderedMatch) {
      flushParagraph();
      if (currentListType && currentListType !== "ol") flushList();
      currentListType = "ol";
      currentList.push(orderedMatch[2]);
      return;
    }

    const bulletMatch = line.match(/^[-*]\s+(.*)$/);
    if (bulletMatch) {
      flushParagraph();
      if (currentListType && currentListType !== "ul") flushList();
      currentListType = "ul";
      currentList.push(bulletMatch[1]);
      return;
    }

    if (currentList.length) flushList();
    paragraph.push(line);
  });

  flushList();
  flushParagraph();
  return segments.join("");
}

function parseStructuredSections(text = "", sectionTitles = []) {
  const normalized = normalizeMarkdownText(text);
  if (!normalized) return [];

  const canonical = sectionTitles.map((title) => ({
    title,
    pattern: new RegExp(`^(?:#{1,3}\\s*)?(?:\\d+\\.\\s*)?(?:\\*\\*)?${title}(?:\\*\\*)?\\s*(?::|$)`, "i")
  }));

  const lines = normalized.split("\n");
  const sections = [];
  let current = null;

  const startSection = (title) => {
    if (current) sections.push(current);
    current = { title, lines: [] };
  };

  lines.forEach((rawLine) => {
    const line = rawLine.trim();
    if (!line || /^---+$/.test(line)) return;
    const matched = canonical.find((item) => item.pattern.test(line));
    if (matched) {
      startSection(matched.title);
      return;
    }
    if (/^\d+\.\s+/.test(line)) {
      return;
    }
    if (!current) {
      startSection(sectionTitles[0] || "Nội dung");
    }
    current.lines.push(line);
  });

  if (current) sections.push(current);
  return sections
    .map((section) => ({
      title: section.title,
      body: section.lines.join("\n").trim()
    }))
    .filter((section) => section.body);
}

function StructuredResponse({ text, sectionTitles }) {
  const sections = parseStructuredSections(text, sectionTitles);
  if (!sections.length) return <MarkdownBlock text={text} />;
  return (
    <div className="structured-response">
      {sections.map((section) => (
        <article key={section.title} className="structured-response-card">
          <strong>{section.title}</strong>
          <MarkdownBlock text={section.body} />
        </article>
      ))}
    </div>
  );
}

function MarkdownBlock({ text }) {
  return <div className="markdown-body" dangerouslySetInnerHTML={{ __html: renderMarkdown(text) }} />;
}

function SectionTabs({ tabs, active, onChange }) {
  return (
    <div className="section-tabs" role="tablist" aria-label="Section tabs">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={active === tab.id ? "active" : ""}
          onClick={() => onChange(tab.id)}
          type="button"
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

function InsightHero({ title, body, tone = "default", meta }) {
  return (
    <section className={`insight-hero tone-${tone}`}>
      <div>
        <strong>{title}</strong>
        <p>{body}</p>
      </div>
      {meta ? <small>{meta}</small> : null}
    </section>
  );
}

function Disclosure({ title, children, defaultOpen = false, open: controlledOpen, onToggle, compact = false }) {
  const [open, setOpen] = useState(defaultOpen);
  useEffect(() => {
    setOpen(defaultOpen);
  }, [defaultOpen]);
  useEffect(() => {
    if (controlledOpen !== undefined) {
      setOpen(Boolean(controlledOpen));
    }
  }, [controlledOpen]);
  return (
    <details
      className={`disclosure ${compact ? "compact" : ""}`}
      open={open}
      onToggle={(event) => {
        const nextOpen = event.currentTarget.open;
        setOpen(nextOpen);
        if (onToggle) onToggle(nextOpen);
      }}
    >
      <summary>{title}</summary>
      <div className="disclosure-body">{children}</div>
    </details>
  );
}

function buildExecutiveTrend(timeline = [], overrideGrowthPct = null) {
  if (!timeline.length) return [];
  const sorted = [...timeline].sort((a, b) => String(a.date).localeCompare(String(b.date)));
  const yearlyActual = new Map();
  sorted.forEach((row) => {
    const year = Number(String(row.date).slice(0, 4));
    if (!yearlyActual.has(year)) yearlyActual.set(year, []);
    yearlyActual.get(year).push(row);
  });

  const actualRows = [...yearlyActual.entries()].map(([year, rows]) => ({
    year,
    price_billion: rows.reduce((sum, row) => sum + Number(row.price_billion || 0), 0) / rows.length,
    roi_pct: rows.reduce((sum, row) => sum + Number(row.roi_pct || 0), 0) / rows.length,
    stage: year < 2025 ? "actual" : "projection"
  }));
  const base2025 = actualRows.find((row) => row.year === 2025) || actualRows[actualRows.length - 1];
  const recent = actualRows.slice(-3);
  const firstRecent = recent[0] || base2025;
  const lastRecent = recent[recent.length - 1] || base2025;
  const spanYears = Math.max(1, (lastRecent.year || 2025) - (firstRecent.year || 2024));
  const inferredGrowth = Math.pow((lastRecent.price_billion || 1) / Math.max(firstRecent.price_billion || 1, 0.1), 1 / spanYears) - 1;
  const annualGrowth = overrideGrowthPct === null
    ? Math.max(0.02, Math.min(0.09, Number.isFinite(inferredGrowth) ? inferredGrowth : 0.055))
    : Number(overrideGrowthPct) / 100;
  const roiSlope = ((lastRecent.roi_pct || 0) - (firstRecent.roi_pct || 0)) / spanYears;
  const startPrice = base2025.price_billion || lastRecent.price_billion || 0;
  const startRoi = base2025.roi_pct || lastRecent.roi_pct || 0;

  const projection = [];
  for (let year = 2025; year <= 2050; year += 1) {
    const offset = year - 2025;
    projection.push({
      year,
      price_billion: Number((startPrice * ((1 + annualGrowth) ** offset)).toFixed(2)),
      roi_pct: Number(Math.max(6, Math.min(24, startRoi + roiSlope * offset * 0.35)).toFixed(2)),
      stage: year === 2025 ? "actual" : "projection"
    });
  }
  return projection;
}

function buildTrendSnapshots(trend = []) {
  if (!trend.length) return [];
  const desiredYears = [2025, 2030, 2035, 2040, 2045, 2050];
  const byYear = new Map(trend.map((row) => [Number(row.year), row]));
  const latest = trend[trend.length - 1];
  return desiredYears
    .map((year) => byYear.get(year) || latest)
    .filter(Boolean)
    .map((row, index) => ({
      year: row.year,
      price_billion: Number(row.price_billion || 0),
      roi_pct: Number(row.roi_pct || 0),
      stage: row.stage || "projection",
      emphasis: index === 0 ? "current" : index === desiredYears.length - 1 ? "target" : "forecast"
    }));
}

function normalizeText(value = "") {
  return String(value).trim().toLowerCase();
}

function propertyNeedsRoomFields(propertyType = "") {
  const text = normalizeText(propertyType);
  return !["đất", "kho", "xưởng", "bãi", "nông nghiệp", "mặt bằng"].some((keyword) => text.includes(keyword));
}

function propertyNeedsFloorField(propertyType = "") {
  const text = normalizeText(propertyType);
  return !["đất", "nông nghiệp", "bãi", "mặt bằng"].some((keyword) => text.includes(keyword));
}

function toNullableNumber(value) {
  if (value === "" || value === null || value === undefined) return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function useTypewriterText(text, enabled = true, speed = 14) {
  const [displayed, setDisplayed] = useState("");

  useEffect(() => {
    const source = String(text || "");
    if (!enabled || !source) {
      setDisplayed(source);
      return undefined;
    }

    setDisplayed("");
    let index = 0;
    const step = Math.max(1, Math.ceil(source.length / 120));
    const timer = window.setInterval(() => {
      index = Math.min(source.length, index + step);
      setDisplayed(source.slice(0, index));
      if (index >= source.length) {
        window.clearInterval(timer);
      }
    }, speed);

    return () => window.clearInterval(timer);
  }, [text, enabled, speed]);

  return displayed;
}

function buildOverviewRecommendation(kpis, riskyRows = [], growthPct = 8) {
  const weakest = riskyRows[0];
  if (growthPct <= 0 && weakest) {
    return {
      title: "Khuyến nghị phòng thủ",
      body: `Giả định tăng trưởng ${growthPct.toFixed(1)}% cho thấy nên hạn chế mua mới và xem xét bán bớt hoặc cơ cấu lại tại ${weakest.district}. Đây là nhóm dễ chịu áp lực giảm giá và hiệu quả đầu tư thấp hơn mặt bằng chung.`
    };
  }
  if (growthPct < 5 && weakest) {
    return {
      title: "Khuyến nghị giữ tiền mặt cao hơn",
      body: `Tăng trưởng chậm làm biên an toàn thu hẹp. Nên giải ngân chọn lọc tại ${kpis.best_district || "khu dẫn đầu"} và tránh mở rộng quá nhanh ở ${weakest.district}.`
    };
  }
  return {
    title: `Ưu tiên mở rộng tại ${kpis.best_district || "khu vực dẫn đầu"}`,
    body: `Với giả định tăng trưởng ${growthPct.toFixed(1)}%, danh mục vẫn phù hợp để tích lũy thêm ở khu dẫn đầu và chỉ kiểm soát rủi ro ở các khu có hiệu quả thấp hoặc biến động cao.`
  };
}

function buildScenarioMilestones(whatIf) {
  if (!whatIf?.projection?.length) return [];
  const budget = Number(whatIf.input?.budget_vnd || 0);
  const rows = whatIf.projection.map((row) => ({
    ...row,
    status: Number(row.pessimistic || 0) < budget ? "Rủi ro lỗ" : Number(row.base || 0) < budget ? "Hoà vốn yếu" : "An toàn hơn"
  }));
  return rows.filter((row, index) => index === 0 || index === rows.length - 1 || index % 2 === 0).slice(0, 6);
}

function defaultDecisionChartSpec() {
  return {
    chart_type: "line",
    title: "",
    caption: "So sánh ba kịch bản xấu, cơ sở và tích cực theo từng năm.",
    insight: "Đường cơ sở là trọng tâm, hai đường còn lại giúp nhìn nhanh biên an toàn.",
    x_key: "calendar_year",
    series: ["pessimistic", "base", "optimistic"],
    reference_line: "budget_vnd"
  };
}

function chartTitleForDecisionTab(tab = "whatif") {
  if (tab === "scenario") return "Dải kịch bản theo từng năm";
  if (tab === "asset") return "Mức hấp dẫn tài sản so với danh mục";
  return "Mô phỏng tài chính theo vốn và tăng trưởng";
}

function chartTypeForDecisionTab(tab = "whatif") {
  if (tab === "scenario") return "area";
  if (tab === "asset") return "bar";
  return "line";
}

function normalizeChartSpec(spec) {
  const base = defaultDecisionChartSpec();
  if (!spec || typeof spec !== "object") return base;
  const series = Array.isArray(spec.series)
    ? spec.series.filter(Boolean)
    : String(spec.series || "").split(",").map((item) => item.trim()).filter(Boolean);
  return {
    ...base,
    ...spec,
    chart_type: ["line", "area", "bar"].includes(String(spec.chart_type || "").toLowerCase()) ? String(spec.chart_type).toLowerCase() : base.chart_type,
    x_key: spec.x_key || base.x_key,
    series: series.length ? series : base.series,
    reference_line: spec.reference_line || base.reference_line
  };
}

function buildExecutiveBriefs(districtRows = []) {
  const rows = [...(districtRows || [])].filter((row) => row && row.district);
  if (!rows.length) return [];

  const byScore = [...rows].sort((a, b) => Number(b.opportunity_score || 0) - Number(a.opportunity_score || 0));
  const byValue = [...rows].sort((a, b) => Number(a.price_m2_million || 0) - Number(b.price_m2_million || 0) || Number(b.roi_pct || 0) - Number(a.roi_pct || 0));
  const byRisk = [...rows].sort((a, b) => Number(b.volatility || 0) - Number(a.volatility || 0) || Number(a.opportunity_score || 0) - Number(b.opportunity_score || 0));

  const picks = [byScore[0], byValue[0], byRisk[0]].filter(Boolean);
  const unique = [];
  const seen = new Set();
  picks.forEach((row, index) => {
    if (!seen.has(row.district)) {
      unique.push({ ...row, kind: index === 0 ? "priority" : index === 1 ? "value" : "risk" });
      seen.add(row.district);
    }
  });

  if (!unique.length && byScore[0]) unique.push({ ...byScore[0], kind: "priority" });
  if (unique.length < 3) {
    for (const row of rows) {
      if (unique.some((item) => item.district === row.district)) continue;
      unique.push({ ...row, kind: unique.length === 0 ? "priority" : unique.length === 1 ? "value" : "risk" });
      if (unique.length === 3) break;
    }
  }

  return unique.slice(0, 3).map((row, index) => {
    const score = Number(row.opportunity_score || 0);
    const roi = Number(row.roi_pct || 0);
    const price = Number(row.price_m2_million || 0);
    const volatility = Number(row.volatility || 0);
    const kind = row.kind || (index === 0 ? "priority" : index === 1 ? "value" : "risk");
    const title = kind === "priority"
      ? "Ưu tiên mở rộng"
      : kind === "value"
        ? "Tích lũy chọn lọc"
        : "Theo dõi rủi ro";
    const edge = kind === "priority"
      ? `Điểm cơ hội ${score.toFixed(1)}/100, ROI ${roi.toFixed(2)}% và thanh khoản ${Number(row.listings || 0).toLocaleString("vi-VN")} tin.`
      : kind === "value"
        ? `Giá/m² ${price.toFixed(1)} triệu tạo biên vào lệnh tốt hơn, vẫn giữ ROI ${roi.toFixed(2)}%.`
        : `Biến động ROI ${volatility.toFixed(2)} cho thấy nên giữ tỷ trọng nhỏ và theo dõi sát.`;
    const strength = kind === "risk"
      ? `Mặc dù rủi ro cao hơn, khu vực này vẫn giúp đa dạng hóa danh mục nếu kiểm soát tỷ trọng.`
      : kind === "value"
        ? `Phù hợp cho chiến lược gom dần vì mặt bằng giá thấp hơn mặt bằng chung.`
        : `Phù hợp để dẫn danh mục vì đang nổi bật cả về hiệu quả lẫn độ quan tâm thị trường.`;
    const risk = kind === "priority"
      ? `Cần kiểm soát pháp lý và quy hoạch vì khu dẫn đầu thường đi kèm mặt bằng giá cao hơn.`
      : kind === "value"
        ? `Rủi ro là thanh khoản có thể thấp hơn nếu khu vực chưa đủ đông người mua.`
        : `Rủi ro là biến động lợi suất lớn nên không nên giải ngân quá nhanh.`;
    return {
      ...row,
      title,
      edge,
      strength,
      risk,
      tag: kind === "priority" ? "Dẫn đầu" : kind === "value" ? "Giá tốt" : "Cảnh báo"
    };
  });
}

function DecisionChart({ whatIf, chartSpec }) {
  const spec = normalizeChartSpec(chartSpec);
  const data = (whatIf?.projection || []).map((row) => ({ ...row, calendar_year: 2025 + Number(row.year || 0) }));
  if (!data.length) return <p className="muted">Biểu đồ sẽ hiển thị triển vọng theo ba kịch bản đầu tư.</p>;

  const commonProps = {
    data,
    margin: { top: 8, right: 16, left: 0, bottom: 0 }
  };
  const colors = {
    pessimistic: "#c2410c",
    base: "#2563eb",
    optimistic: "#0f766e"
  };
  const seriesMap = {
    pessimistic: "Kịch bản xấu",
    base: "Kịch bản cơ sở",
    optimistic: "Kịch bản tích cực"
  };
  const yFormatter = (v) => `${(v / 1_000_000_000).toFixed(0)} tỷ`;
  const tooltipFormatter = (v) => money(v);
  const series = spec.series.filter((key) => key in seriesMap);
  const referenceValue = spec.reference_line === "budget_vnd" ? whatIf?.input?.budget_vnd : null;

  const axes = (
    <>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey={spec.x_key || "calendar_year"} />
      <YAxis tickFormatter={yFormatter} />
      <Tooltip formatter={tooltipFormatter} labelFormatter={(value) => `Năm ${value}`} />
      <Legend />
      {referenceValue ? <ReferenceLine y={referenceValue} stroke="#64748b" strokeDasharray="4 4" label="Vốn ban đầu" /> : null}
    </>
  );

  if (spec.chart_type === "area") {
    return (
      <ResponsiveContainer width="100%" height={380}>
        <AreaChart {...commonProps}>
          {axes}
          {series.map((key, index) => (
            <Area
              key={key}
              dataKey={key}
              name={seriesMap[key]}
              fill={colors[key]}
              stroke={colors[key]}
              fillOpacity={index === 0 ? 0.18 : index === 1 ? 0.28 : 0.2}
              dot={false}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    );
  }

  if (spec.chart_type === "bar") {
    return (
      <ResponsiveContainer width="100%" height={380}>
        <BarChart {...commonProps}>
          {axes}
          {series.map((key) => (
            <Bar key={key} dataKey={key} name={seriesMap[key]} fill={colors[key]} radius={[6, 6, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={380}>
      <ComposedChart {...commonProps}>
        {axes}
        {series.map((key) => (
          <Line key={key} dataKey={key} name={seriesMap[key]} stroke={colors[key]} strokeWidth={key === "base" ? 3 : 2} dot={false} />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  );
}

function ResultSkeleton() {
  return (
    <div className="result-skeleton" aria-hidden="true">
      <div className="skeleton-line skeleton-lg" />
      <div className="skeleton-grid">
        <div className="skeleton-card" />
        <div className="skeleton-card" />
        <div className="skeleton-card" />
        <div className="skeleton-card" />
      </div>
      <div className="skeleton-line" />
      <div className="skeleton-line" />
    </div>
  );
}

function buildGrowthWhatIfPayload(predictForm, simulationForm, filters, growthPct) {
  return {
    district: predictForm.district,
    property_type: predictForm.property_type,
    legal_documents: predictForm.legal_documents,
    area: Number(predictForm.area),
    bedrooms: propertyNeedsRoomFields(predictForm.property_type) ? toNullableNumber(predictForm.bedrooms) : null,
    toilets: propertyNeedsRoomFields(predictForm.property_type) ? toNullableNumber(predictForm.toilets) : null,
    floors: propertyNeedsFloorField(predictForm.property_type) ? toNullableNumber(predictForm.floors) : null,
    roi_expected: Number(predictForm.roi_expected),
    budget_vnd: Number(simulationForm.budget_billion) * 1_000_000_000,
    annual_growth_pct: Number(growthPct),
    years: Number(simulationForm.years),
    filters
  };
}

function buildOverviewGrowthPayload(analytics, filters, growthPct) {
  const kpis = analytics?.kpis || {};
  const districts = analytics?.districts || [];
  const types = analytics?.types || [];
  const samples = analytics?.samples || [];
  const topDistrict = kpis.best_district || districts[0]?.district || (filters?.city || "TP Hồ Chí Minh");
  const bestType = types[0]?.["Type of House"] || types[0]?.type || samples[0]?.["Type of House"] || "Nhà mặt tiền";
  const bestLegal = samples[0]?.["Legal Documents"] || "Sổ hồng";
  const avgArea = Number(districts[0]?.avg_area || samples[0]?.area || 80);
  const budgetSource = Number(kpis.avg_transaction_price || kpis.median_price || kpis.total_value / Math.max(1, kpis.listings || 1) || 0);
  const budgetVnd = Math.max(1, budgetSource || 1);
  const roiExpected = Number.isFinite(Number(kpis.avg_roi)) ? Number(kpis.avg_roi) / 100 : 0.14;

  return {
    district: topDistrict,
    property_type: bestType,
    legal_documents: bestLegal,
    area: Math.max(1, avgArea),
    bedrooms: null,
    toilets: null,
    floors: null,
    roi_expected: roiExpected,
    budget_vnd: budgetVnd,
    annual_growth_pct: Number(growthPct),
    years: 25,
    filters: {
      city: filters?.city || "TP Hồ Chí Minh",
      districts: kpis.best_district ? [kpis.best_district] : [],
      property_types: bestType ? [bestType] : [],
      price_min: null,
      price_max: null,
      area_min: null,
      area_max: null,
      roi_min: null,
      roi_max: null
    }
  };
}

function buildReportQuestion(analytics, filters) {
  const best = analytics?.kpis?.best_district || "khu vực dẫn đầu";
  const risky = (analytics?.risky || []).slice(0, 3).map((row) => row.district).filter(Boolean);
  const city = filters?.city || "thị trường";
  return `Viết ghi chú điều hành ngắn gọn cho báo cáo định kỳ của ${city}. Nhấn mạnh ${best}, ROI trung bình ${pct(analytics?.kpis?.avg_roi)}, các khu vực cần theo dõi gồm ${risky.join(", ") || "chưa có cảnh báo rõ"}. Nêu rõ lợi thế, rủi ro và hành động ưu tiên theo giọng điệu chuyên viên phân tích đầu tư.`;
}

function buildReportCoverSummary(analytics, whatIf) {
  const kpis = analytics?.kpis || {};
  const executiveTrend = buildExecutiveTrend(analytics?.timeline || [], 8);
  const baseline = executiveTrend[0] || null;
  const latest = executiveTrend[executiveTrend.length - 1] || null;
  const bestDistrict = kpis.best_district || analytics?.districts?.[0]?.district || "Khu vực dẫn đầu";

  const projectedFutureValue = whatIf?.summary?.future_value ?? (latest?.price_billion ? latest.price_billion * 1_000_000_000 : null);
  const projectedCumulativeRoi = whatIf?.summary?.cumulative_roi_pct ?? (
    baseline && latest && Number(baseline.price_billion) > 0
      ? ((Number(latest.price_billion) / Number(baseline.price_billion)) - 1) * 100
      : null
  );

  const projectedPaybackYears = whatIf?.summary?.payback_years ?? (() => {
    const roiFromKpis = Number(kpis.avg_roi);
    if (Number.isFinite(roiFromKpis) && roiFromKpis > 0) return 100 / roiFromKpis;
    const roiFromTrend = Number(latest?.roi_pct);
    if (Number.isFinite(roiFromTrend) && roiFromTrend > 0) return 100 / roiFromTrend;
    return null;
  })();

  const sourceLabel = whatIf ? "Từ mô phỏng đầu tư" : "Ước tính theo xu hướng điều hành";

  return {
    bestDistrict,
    projectedFutureValue,
    projectedCumulativeRoi,
    projectedPaybackYears,
    sourceLabel
  };
}

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  if (!response.ok) {
    let detail = `API ${path} failed`;
    try {
      const payload = await response.json();
      detail = payload?.detail || detail;
    } catch {
      detail = (await response.text()) || detail;
    }
    throw new Error(detail);
  }
  return response.json();
}

async function requestNdjsonStream(path, options = {}, handlers = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  if (!response.ok) {
    let detail = `API ${path} failed`;
    try {
      const payload = await response.json();
      detail = payload?.detail || detail;
    } catch {
      detail = (await response.text()) || detail;
    }
    throw new Error(detail);
  }
  if (!response.body) throw new Error("Streaming is not supported by this browser.");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let newlineIndex = buffer.indexOf("\n");
    while (newlineIndex >= 0) {
      const rawLine = buffer.slice(0, newlineIndex).trim();
      buffer = buffer.slice(newlineIndex + 1);
      newlineIndex = buffer.indexOf("\n");
      if (!rawLine) continue;
      let event;
      try {
        event = JSON.parse(rawLine);
      } catch {
        continue;
      }
      if (event.type === "meta" && handlers.onMeta) handlers.onMeta(event);
      if (event.type === "stage" && handlers.onStage) handlers.onStage(event);
      if (event.type === "what_if" && handlers.onWhatIf) handlers.onWhatIf(event);
      if (event.type === "line" && handlers.onLine) handlers.onLine(event);
      if (event.type === "token" && handlers.onToken) handlers.onToken(event);
      if (event.type === "done" && handlers.onDone) handlers.onDone(event);
      if (event.type === "error") {
        if (handlers.onError) handlers.onError(event);
        throw new Error(event.detail || "Streaming error");
      }
    }
  }
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
  const hint = Object.entries(PANEL_HINTS).find(([key]) => title.startsWith(key))?.[1];
  return (
    <section className={`panel ${className}`}>
      <div className="panel-head">
        <div className="panel-title-wrap">
          <h3 tabIndex={0} aria-label={hint ? `${title}. ${hint}` : title}>{title}</h3>
          {hint ? <span className="panel-hint-tooltip">{hint}</span> : null}
        </div>
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

function AppFooter({ activePage, loading, aiRuntime, analytics, etl }) {
  const dataTimestamp = analytics?.kpis?.last_data_refresh || etl?.status?.finished_at || aiRuntime?.updated_at;
  const systemStatus = loading ? "Data syncing" : "System ready";
  return (
    <footer className="app-footer">
      <div className="app-footer-brand">
        <strong>PropertyVision BI</strong>
        <span>Decision Intelligence for real estate analysis and executive reporting.</span>
      </div>
      <div className="app-footer-meta">
        <span>Version {APP_VERSION}</span>
        <span>© {new Date().getFullYear()} PropertyVision</span>
        <span>Updated {dataTimestamp ? formatDateTime(dataTimestamp) : "Chưa cập nhật"}</span>
        <span>{systemStatus}</span>
      </div>
    </footer>
  );
}

function buildFilterSummary(filters) {
  const parts = [];
  if (filters.city) parts.push(filters.city);
  parts.push(filters.districts?.length ? `${filters.districts.length} khu vực` : "Toàn bộ khu vực");
  if (filters.property_types?.length) parts.push(`${filters.property_types.length} loại tài sản`);
  if (filters.roi_min !== null && filters.roi_min !== undefined) parts.push(`ROI >= ${Number(filters.roi_min).toFixed(1)}%`);
  if (filters.price_max !== null && filters.price_max !== undefined) parts.push(`Giá <= ${Number(filters.price_max).toFixed(1)} tỷ`);
  return parts.join(" · ");
}

function isDefaultFilters(filters) {
  return (
    (filters.city || emptyFilters.city) === emptyFilters.city
    && JSON.stringify(filters.districts || []) === JSON.stringify(emptyFilters.districts)
    && JSON.stringify(filters.property_types || []) === JSON.stringify(emptyFilters.property_types)
    && filters.price_min === emptyFilters.price_min
    && filters.price_max === emptyFilters.price_max
    && filters.area_min === emptyFilters.area_min
    && filters.area_max === emptyFilters.area_max
    && filters.roi_min === emptyFilters.roi_min
    && filters.roi_max === emptyFilters.roi_max
  );
}

function AppShell({ activePage, setActivePage, children, loading, metadata, filters, setFilters, aiRuntime, analytics, etl }) {
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [navTip, setNavTip] = useState(null);

  function navigate(page) {
    window.history.pushState({}, "", page.path);
    setActivePage(page.id);
  }

  function showNavTip(page, event) {
    const rect = event.currentTarget.getBoundingClientRect();
    setNavTip({
      title: page.label,
      description: page.description,
      top: rect.top + rect.height / 2,
    });
  }

  const filterSummary = buildFilterSummary(filters);
  const resetFilters = () => setFilters(emptyFilters);
  const hasActiveFilters = !isDefaultFilters(filters);
  const runtimeStage = aiStageInfo(aiRuntime?.status, !aiRuntime);

  useEffect(() => {
    const handler = () => setActivePage(currentPageId());
    window.addEventListener("popstate", handler);
    return () => window.removeEventListener("popstate", handler);
  }, [setActivePage]);

  useEffect(() => {
    function handleEscape(event) {
      if (event.key === "Escape") setFiltersOpen(false);
    }
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, []);

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
            <button
              key={page.id}
              className={activePage === page.id ? "active" : "" }
              onClick={() => navigate(page)}
              onMouseEnter={(event) => showNavTip(page, event)}
              onMouseLeave={() => setNavTip(null)}
              onFocus={(event) => showNavTip(page, event)}
              onBlur={() => setNavTip(null)}
              title={page.description}
              aria-label={`${page.label}. ${page.description}`}
            >
              <Icon name={page.icon} fill={activePage === page.id} />
              <span className="nav-label">{page.label}</span>
            </button>
          ))}
        </nav>
        <GlobalFilters metadata={metadata} filters={filters} setFilters={setFilters} />
      </aside>
      {navTip ? (
        <div className="nav-tooltip" style={{ top: `${Math.round(navTip.top)}px` }}>
          <strong>{navTip.title}</strong>
          <span>{navTip.description}</span>
        </div>
      ) : null}

      <header className="top-appbar">
        <div className="top-appbar-left">
          <div className="crumb">
            <Icon name="search" />
            <span>PROPERTYVISION / {pages.find((page) => page.id === activePage)?.short?.toUpperCase()}</span>
          </div>
          <div className="filter-status-row">
            <small className="filter-status-line">{filterSummary}</small>
            {hasActiveFilters ? <button type="button" className="clear-filters-btn" onClick={resetFilters}>Xóa bộ lọc</button> : null}
          </div>
        </div>
        <strong></strong>
        <div className="top-actions">
          <button type="button" className="filter-drawer-trigger" onClick={() => setFiltersOpen(true)}>
            <Icon name="tune" />
            <span>Bộ lọc</span>
          </button>
          {loading ? <span className="live-pill">Đang cập nhật</span> : <span className="live-pill online">Đang hoạt động</span>}
          <span className={`badge ${runtimeStage.tone}`}>{runtimeStage.label}</span>
          <Icon name="notifications_active" />
          <Icon name="help_outline" />
          <Icon name="account_circle" />
        </div>
      </header>

      {filtersOpen ? <button type="button" className="drawer-backdrop" aria-label="Đóng bộ lọc" onClick={() => setFiltersOpen(false)} /> : null}
      <GlobalFilters
        metadata={metadata}
        filters={filters}
        setFilters={setFilters}
        open={filtersOpen}
        onClose={() => setFiltersOpen(false)}
      />

      <main className="page-canvas">
        <div className="page-content">{children}</div>
        <AppFooter activePage={activePage} loading={loading} aiRuntime={aiRuntime} analytics={analytics} etl={etl} />
      </main>
    </div>
  );
}

function GlobalFilters({ metadata, filters, setFilters, open, onClose }) {
  const [districtQuery, setDistrictQuery] = useState("");
  if (!metadata) return null;
  const cities = metadata.cities || [];
  const districtOptions = metadata.districts_by_city?.[filters.city] || [];
  const normalizedQuery = districtQuery.trim().toLowerCase();
  const visibleDistricts = normalizedQuery
    ? districtOptions.filter((district) => district.toLowerCase().includes(normalizedQuery))
    : districtOptions;

  function updateDistricts(nextDistricts) {
    setFilters((current) => ({ ...current, districts: nextDistricts }));
  }

  function toggleDistrict(district) {
    const selected = filters.districts.includes(district)
      ? filters.districts.filter((item) => item !== district)
      : [...filters.districts, district];
    updateDistricts(selected);
  }

  const previewDistricts = filters.districts.slice(0, 3);
  const remainingDistricts = Math.max(0, filters.districts.length - previewDistricts.length);

  useEffect(() => {
    setDistrictQuery("");
  }, [filters.city]);

  return (
    <aside className={`global-filters drawer-panel ${open ? "open" : ""}`} aria-hidden={!open}>
      <div className="filter-caption">
        <span>Bộ lọc điều hành</span>
        <div className="filter-caption-actions">
          <button type="button" onClick={onClose}>Đóng</button>
          <button type="button" onClick={() => setFilters(emptyFilters)}>Đặt lại</button>
        </div>
      </div>
      <div className="filter-summary">
        <strong>{filters.city || "Toàn bộ thị trường"}</strong>
        <div className="filter-chip-row">
          {filters.districts.length ? (
            <>
              {previewDistricts.map((district) => (
                <button key={district} type="button" className="filter-chip" onClick={() => toggleDistrict(district)}>
                  {district}
                </button>
              ))}
              {remainingDistricts ? <span className="filter-chip more">+{remainingDistricts}</span> : null}
            </>
          ) : (
            <span className="filter-chip muted">Toàn bộ quận/huyện</span>
          )}
        </div>
      </div>
      <div className="filter-controls">
        <Disclosure title="Phạm vi thị trường" defaultOpen>
          <label>
            Thành phố
            <select
              value={filters.city || cities[0] || ""}
              onChange={(event) => setFilters((current) => ({ ...current, city: event.target.value, districts: [] }))}
            >
              {cities.map((city) => <option key={city}>{city}</option>)}
            </select>
          </label>
        </Disclosure>

        <Disclosure title="Khu vực theo quận / huyện" defaultOpen>
          <label>
            Quận / huyện
            <input
              type="text"
              placeholder="Tìm quận/huyện..."
              value={districtQuery}
              onChange={(event) => setDistrictQuery(event.target.value)}
            />
            <div className="district-picker-actions">
              <button type="button" onClick={() => updateDistricts(districtOptions)}>Chọn tất cả</button>
              <button type="button" onClick={() => updateDistricts([])}>Bỏ chọn</button>
            </div>
            <div className="district-checklist">
              {visibleDistricts.map((district) => (
                <label key={district} className="district-option">
                  <input
                    type="checkbox"
                    checked={filters.districts.includes(district)}
                    onChange={() => toggleDistrict(district)}
                  />
                  <span>{district}</span>
                </label>
              ))}
              {!visibleDistricts.length ? <p className="district-empty">Không tìm thấy khu vực phù hợp.</p> : null}
            </div>
            <small>{filters.districts.length ? `Đã chọn ${filters.districts.length} khu vực` : "Giữ trống để xem toàn bộ thành phố"}</small>
          </label>
        </Disclosure>

        <Disclosure title="Ngưỡng đầu tư" defaultOpen>
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
        </Disclosure>
      </div>
    </aside>
  );
}

function OverviewPage({ activePage, analytics, typeShare, filters }) {
  const kpis = analytics?.kpis || {};
  const [growthStressPct, setGrowthStressPct] = useState(8);
  const [liveGrowthRecommendation, setLiveGrowthRecommendation] = useState(null);
  const [growthStatus, setGrowthStatus] = useState("idle");
  const executiveTrend = useMemo(() => buildExecutiveTrend(analytics?.timeline || [], growthStressPct), [analytics?.timeline, growthStressPct]);
  const trendSnapshots = useMemo(() => buildTrendSnapshots(executiveTrend), [executiveTrend]);
  const executiveBriefs = useMemo(() => buildExecutiveBriefs(analytics?.districts || []), [analytics?.districts]);
  const projected2050 = executiveTrend[executiveTrend.length - 1];
  const overviewRecommendation = useMemo(
    () => buildOverviewRecommendation(kpis, analytics?.risky || [], growthStressPct),
    [kpis, analytics?.risky, growthStressPct]
  );
  const growthPayload = useMemo(
    () => buildOverviewGrowthPayload(analytics || {}, filters || emptyFilters, growthStressPct),
    [analytics, filters, growthStressPct]
  );

  useEffect(() => {
    if (activePage !== "overview" || !growthPayload?.district) return;
    let cancelled = false;
    setGrowthStatus("loading");
    const timer = window.setTimeout(async () => {
      try {
        const recommendation = await request("/api/recommendation/future", { method: "POST", body: JSON.stringify(growthPayload) });
        if (!cancelled) {
          setLiveGrowthRecommendation(recommendation);
          setGrowthStatus("ready");
        }
      } catch {
        if (!cancelled) {
          setGrowthStatus("error");
        }
      }
    }, 450);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [activePage, growthPayload]);

  return (
    <>
      <PageHeader
        eyebrow="Điều hành"
        title="Tổng quan Quyết định Chiến lược"
        description="Tóm tắt diễn biến thị trường, hiệu quả danh mục và khuyến nghị hành động dành cho lãnh đạo."
      />
      <InsightHero
        title={overviewRecommendation.title}
        body={overviewRecommendation.body}
        meta={projected2050 ? `Theo giả định hiện tại, quy mô giá trị có thể đạt khoảng ${projected2050.price_billion.toFixed(1)} tỷ vào năm 2050 ở kịch bản cơ sở.` : ""}
      />
      <div className="kpi-grid">
        <KpiCard label="Tổng giá trị thị trường" value={money(kpis.total_value)} delta="Theo bộ lọc hiện tại" icon="account_balance" />
        <KpiCard label="Giá trung vị" value={money(kpis.median_price)} delta="Mức giá đại diện" icon="sell" />
        <KpiCard label="ROI bình quân" value={pct(kpis.avg_roi)} delta="Hiệu quả danh mục" icon="monitoring" tone="good" />
        <KpiCard label="Khu vực ưu tiên" value={kpis.best_district || "N/A"} delta={`${(kpis.best_score || 0).toFixed(1)}/100`} icon="location_city" />
        <KpiCard label="Số bản ghi thị trường" value={(kpis.transaction_count || 0).toLocaleString("vi-VN")} delta={`Độ tin cậy ${((kpis.avg_confidence || 0) * 100).toFixed(0)}%`} icon="swap_horiz" />
      </div>
      <div className="grid-12">
        <Panel title="Xu hướng điều hành 2025–2050" className="span-8">
          <ResponsiveContainer width="100%" height={340}>
            <ComposedChart data={executiveTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" ticks={[2025, 2030, 2035, 2040, 2045, 2050]} />
              <YAxis yAxisId="left" tickFormatter={(v) => `${v.toFixed(0)} tỷ`} />
              <YAxis yAxisId="right" orientation="right" tickFormatter={(v) => `${v.toFixed(0)}%`} />
              <Tooltip formatter={(v) => Number(v).toFixed(2)} />
              <Legend />
              <Area yAxisId="left" type="monotone" dataKey="price_billion" name="Giá trị cơ sở (tỷ)" fill="#dbeafe" stroke="#2563eb" />
              <Line yAxisId="right" type="monotone" dataKey="roi_pct" name="ROI điều hành (%)" stroke="#0f766e" strokeWidth={2} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
          <p className="panel-note prominent">Biểu đồ này được trình bày theo góc nhìn điều hành: tập trung vào xu hướng dài hạn và mức sinh lời chung thay vì chi tiết biến động ngắn hạn.</p>
          <div className="trend-snapshot-grid">
            {trendSnapshots.map((row) => (
              <article className={`trend-snapshot ${row.emphasis}`} key={row.year}>
                <span>Năm {row.year}</span>
                <strong>{row.price_billion.toFixed(1)} tỷ</strong>
                <small>ROI {row.roi_pct.toFixed(1)}%</small>
              </article>
            ))}
          </div>
        </Panel>
        <Panel title="Kiểm tra giả định tăng trưởng" className="span-4">
          <div className="control-stack">
            <label>
              Tăng trưởng giả định: {growthStressPct.toFixed(1)}%
              <input type="range" min="-5" max="18" step="0.5" value={growthStressPct} onChange={(e) => setGrowthStressPct(Number(e.target.value))} />
            </label>
            <small className="panel-note">Dữ liệu kiểm tra được lấy từ KPI và khu vực dẫn đầu đang hiển thị trên trang này.</small>
          </div>
          <div className={`scenario-recommendation tone-${growthStatus === "error" ? "warn" : growthStatus === "ready" ? "good" : "neutral"}`}>
            <div className="scenario-recommendation-head">
              <strong>{growthStatus === "ready" ? "RAG đã trả kết quả" : growthStatus === "loading" ? "RAG đang truy xuất và phân tích" : "Khuyến nghị chờ làm mới"}</strong>
              {growthStatus === "loading" ? (
                <span className="generation-badge scenario-badge">
                  <span className="streaming-dots" aria-hidden="true"><i /><i /><i /></span>
                  Đang xử lý giả định tăng trưởng
                </span>
              ) : null}
            </div>
            {growthStatus === "loading" ? (
              <div className="scenario-processing">
                <p>Hệ thống đang nối dữ liệu RAG, so sánh kịch bản tăng trưởng và sinh khuyến nghị điều hành.</p>
                <div className="simulation-progress"><i /></div>
              </div>
            ) : null}
            <p>{liveGrowthRecommendation?.answer || overviewRecommendation.body}</p>
            {liveGrowthRecommendation?.why ? <p><b>Lý do:</b> {liveGrowthRecommendation.why}</p> : null}
            {liveGrowthRecommendation?.suggestion ? <p><b>Hành động:</b> {liveGrowthRecommendation.suggestion}</p> : null}
            {(liveGrowthRecommendation?.risks || []).length ? <div className="scenario-risk-list"><b>Rủi ro cần theo dõi</b><ul>{liveGrowthRecommendation.risks.map((risk, index) => <li key={index}>{risk}</li>)}</ul></div> : null}
            <small>{liveGrowthRecommendation ? `${liveGrowthRecommendation.model} · ${liveGrowthRecommendation.retrieval_time_ms} ms` : "Cập nhật theo từng lần kéo thanh"}</small>
          </div>
        </Panel>
        <Panel
          title="Khuyến nghị điều hành"
          className="span-12"
          action={<span className="panel-hint">Sinh từ ROI, giá/m², thanh khoản, biến động và RAG</span>}
        >
          <div className="brief-grid">
            {executiveBriefs.map((brief) => (
              <article className="brief-card" key={brief.district}>
                <div className="brief-head">
                  <span className="brief-tag">{brief.tag}</span>
                  <strong>{brief.district}</strong>
                </div>
                <p>{brief.edge}</p>
                <small><b>Lợi thế:</b> {brief.strength}</small>
                <small><b>Rủi ro:</b> {brief.risk}</small>
              </article>
            ))}
          </div>
        </Panel>
      </div>
    </>
  );
}

function MarketPage({ analytics, etl }) {
  const districtRows = analytics?.districts || [];
  const topScore = [...districtRows].sort((a, b) => b.opportunity_score - a.opportunity_score).slice(0, 3);
  const underpriced = [...districtRows].sort((a, b) => a.price_m2_million - b.price_m2_million).slice(0, 3);
  const liquidityReadable = [...districtRows].sort((a, b) => b.listings - a.listings).slice(0, 10);
  const lastRefresh = analytics?.kpis?.last_data_refresh || etl?.status?.finished_at;
  const [marketView, setMarketView] = useState("chart");
  return (
    <>
      <PageHeader
        eyebrow="Thị trường"
        title="Phân tích thị trường"
        description="So sánh ROI, giá/m² và mức độ quan tâm thị trường giữa các khu vực và phân khúc."
      />
      <InsightHero
        title={topScore[0] ? `${topScore[0].district} đang dẫn đầu về opportunity score` : "Thị trường đang có phân hóa theo khu vực"}
        body={topScore[0] ? `Điểm ${topScore[0].opportunity_score.toFixed(1)}/100, phù hợp để đưa vào danh sách xem xét đầu tư. Nên đọc cùng giá/m² và mức độ quan tâm thị trường để tránh kết luận chỉ dựa trên ROI.` : "Dùng trang này để đọc nhanh khu nào đáng chú ý trước khi đi sâu vào phân tích đa chiều."}
        meta={`Dữ liệu cập nhật: ${formatDateTime(lastRefresh)}`}
      />
      <div className="status-strip">
        <span className="status-strip-label">Cập nhật gần nhất</span>
        <strong>{formatDateTime(lastRefresh)}</strong>
        <small>Trang thị trường tự đổi theo bộ lọc và nạp lại khi dữ liệu mới được cập nhật.</small>
      </div>
      <SectionTabs
        tabs={[
          { id: "chart", label: "Tóm tắt thị trường" },
          { id: "detail", label: "Chi tiết thêm" }
        ]}
        active={marketView}
        onChange={setMarketView}
      />
      <div className="grid-12">
        {marketView !== "table" ? <>
          <Panel title="ROI theo khu vực nổi bật" className="span-6">
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
          <Panel title="Thanh khoản và Giá/m²" className="span-6">
            <ResponsiveContainer width="100%" height={360}>
              <ComposedChart data={liquidityReadable}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="district" interval={0} angle={-25} textAnchor="end" height={90} />
                <YAxis yAxisId="left" tickFormatter={compact} />
                <YAxis yAxisId="right" orientation="right" tickFormatter={(v) => `${Number(v).toFixed(0)}tr`} />
                <Tooltip formatter={(value, name) => name === "Giá/m²" ? `${Number(value).toFixed(1)} triệu/m²` : Number(value).toLocaleString("vi-VN")} />
                <Legend />
                <Bar yAxisId="left" dataKey="listings" name="Số tin" fill="#2563eb" />
                <Line yAxisId="right" type="monotone" dataKey="price_m2_million" name="Giá/m²" stroke="#d97706" strokeWidth={3} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
            <p className="panel-note">Cách đọc nhanh: cột càng cao là khu vực được thị trường quan tâm nhiều hơn, đường càng cao là mặt bằng giá/m² càng lớn.</p>
          </Panel>
        </> : null}
        {marketView !== "chart" ? <Panel title="So sánh phân khúc" className="span-12">
          <DataTable rows={districtRows.slice(0, 12)} />
        </Panel> : null}
        <Panel title="Insight phân biệt khu vực" className="span-12">
          <div className="insight-grid">
            <div><strong>Khu vực nổi bật</strong><p>{topScore.map((row) => `${row.district} (${row.opportunity_score.toFixed(1)})`).join(" · ")}</p></div>
            <div><strong>Giá/m² thấp nhất</strong><p>{underpriced.map((row) => `${row.district} (${row.price_m2_million.toFixed(1)}tr/m²)`).join(" · ")}</p></div>
            <div><strong>Mốc so sánh</strong><p>Hiệu quả đầu tư nên đọc cùng điểm cơ hội, giá/m² và mức độ quan tâm thị trường để tránh kết luận sai khi các khu vực có ROI gần nhau.</p></div>
          </div>
          {marketView === "detail" ? <Disclosure title="Mở bảng chi tiết 12 khu vực" defaultOpen={false}><DataTable rows={districtRows.slice(0, 12)} /></Disclosure> : null}
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
  const [addressDetail, setAddressDetail] = useState(null);
  const [copyState, setCopyState] = useState("idle");
  const [searchQuery, setSearchQuery] = useState("");

  function openAddressDetail(row) {
    setAddressDetail({
      segment: row?.[sliceDice?.row_dimension] ?? "N/A",
      subSegment: row?.[sliceDice?.column_dimension] ?? "N/A",
      records: Number(row?.listings || 0),
      addressCount: Number(row?.address_count || 0),
      addresses: Array.isArray(row?.addresses) ? row.addresses : []
    });
    setSearchQuery("");
    setCopyState("idle");
  }

  function closeAddressDetail() {
    setAddressDetail(null);
  }

  function normalizeAddress(address) {
    if (typeof address === "string") {
      return {
        house_number: "",
        street_name: "",
        ward_name: "",
        district_display: "",
        property_type_name: "",
        address_display: address
      };
    }
    return {
      house_number: address?.house_number || "",
      street_name: address?.street_name || "",
      ward_name: address?.ward_name || "",
      district_display: address?.district_display || "",
      property_type_name: address?.property_type_name || "",
      address_display: address?.address_display || "N/A"
    };
  }

  const visibleAddresses = useMemo(() => {
    const source = Array.isArray(addressDetail?.addresses) ? addressDetail.addresses : [];
    const query = searchQuery.trim().toLowerCase();
    if (!query) return source;
    return source.filter((address) => {
      const item = normalizeAddress(address);
      const haystack = [
        item.house_number,
        item.street_name,
        item.ward_name,
        item.district_display,
        item.property_type_name,
        item.address_display
      ].join(" ").toLowerCase();
      return haystack.includes(query);
    });
  }, [addressDetail, searchQuery]);

  const hasAnyHouseNumber = useMemo(
    () => visibleAddresses.some((address) => Boolean(normalizeAddress(address).house_number)),
    [visibleAddresses]
  );

  function buildAddressTextRows(addresses) {
    return addresses.map((address, index) => {
      const item = normalizeAddress(address);
      const numbered = `${index + 1}. ${item.address_display}`;
      return numbered;
    });
  }

  function buildAddressTableRows(addresses) {
    return addresses.map((address, index) => {
      const item = normalizeAddress(address);
      const columns = [
        index + 1,
        item.house_number || "",
        item.street_name || "",
        item.ward_name || "",
        item.district_display || "",
        item.address_display || ""
      ];
      return columns.join(" | ");
    });
  }

  function escapeCsv(value) {
    const text = String(value ?? "");
    return `"${text.replaceAll('"', '""')}"`;
  }

  function buildCsvRows(addresses) {
    const header = ["STT", "Số nhà", "Đường", "Phường/Xã", "Quận/Huyện", "Địa chỉ"];
    const rows = addresses.map((address, index) => {
      const item = normalizeAddress(address);
      return [
        index + 1,
        item.house_number || "",
        item.street_name || "",
        item.ward_name || "",
        item.district_display || "",
        item.address_display || ""
      ].map(escapeCsv).join(",");
    });
    return [header.map(escapeCsv).join(","), ...rows];
  }

  function safeFilename(value) {
    return String(value || "addresses")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-zA-Z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "")
      .toLowerCase() || "addresses";
  }

  async function copyText(kind) {
    if (!visibleAddresses.length) return;
    const lines = kind === "table"
      ? [
          "STT | Số nhà | Đường | Phường/Xã | Quận/Huyện | Địa chỉ",
          ...buildAddressTableRows(visibleAddresses)
        ]
      : buildAddressTextRows(visibleAddresses);
    try {
      await navigator.clipboard.writeText(lines.join("\n"));
      setCopyState(kind === "table" ? "copied_table" : "copied_list");
      window.setTimeout(() => setCopyState("idle"), 1800);
    } catch {
      setCopyState("error");
      window.setTimeout(() => setCopyState("idle"), 1800);
    }
  }

  async function downloadCsv() {
    if (!visibleAddresses.length) return;
    const csv = `\ufeff${buildCsvRows(visibleAddresses).join("\n")}`;
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    const base = `${safeFilename(addressDetail?.segment)}_${safeFilename(addressDetail?.subSegment)}`;
    anchor.download = `${base || "propertyvision_addresses"}.csv`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(url);
    setCopyState("downloaded_csv");
    window.setTimeout(() => setCopyState("idle"), 1800);
  }

  return (
    <>
      <PageHeader eyebrow="Đa chiều" title="Phân tích đa chiều" description="So sánh dữ liệu theo nhiều góc nhìn để tìm phân khúc đáng ưu tiên cho doanh nghiệp." />
      <div className="grid-12">
        <Panel title="Thiết lập phân tích" className="span-4">
          <div className="control-stack">
            <label>Chiều phân tích chính<select value={sliceConfig.row_dimension} onChange={(e) => setSliceConfig({ ...sliceConfig, row_dimension: e.target.value })}>{Object.entries(sliceDice?.dimensions || {}).map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select></label>
            <label>Chiều phân tích phụ<select value={sliceConfig.column_dimension} onChange={(e) => setSliceConfig({ ...sliceConfig, column_dimension: e.target.value })}>{Object.entries(sliceDice?.dimensions || {}).map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select></label>
            <label>Chỉ tiêu xem xét<select value={sliceConfig.metric} onChange={(e) => setSliceConfig({ ...sliceConfig, metric: e.target.value })}>{Object.entries(sliceDice?.metrics || {}).map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select></label>
          </div>
        </Panel>
        <Panel title="Thông tin so sánh" className="span-8">
          <div className="kpi-grid compact">
            <KpiCard label="Số bản ghi đang xét" value={(sliceDice?.filter_context?.filtered_records || 0).toLocaleString("vi-VN")} delta={`${(sliceDice?.filter_context?.coverage_pct || 0).toFixed(1)}% độ bao phủ`} />
            <KpiCard label="ROI trong bộ lọc" value={pct(sliceDice?.benchmark?.filtered_avg_roi)} delta={`Toàn thị trường ${pct(sliceDice?.benchmark?.market_avg_roi)}`} />
            <KpiCard label="Giá/m² trong bộ lọc" value={money(sliceDice?.benchmark?.filtered_avg_price_m2)} delta={`Toàn thị trường ${money(sliceDice?.benchmark?.market_avg_price_m2)}`} />
          </div>
        </Panel>
        <Panel title={`Ma trận hiệu quả (${sliceDice?.metric_label || "Chỉ tiêu"})`} className="span-12">
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
              <tbody>{(sliceDice?.top_segments || []).map((row, index) => <tr key={index}><td>{row[sliceDice.row_dimension]}</td><td>{row[sliceDice.column_dimension]}</td><td><button type="button" className="record-link" onClick={() => openAddressDetail(row)}>{row.listings?.toLocaleString("vi-VN")}</button></td><td>{pct(row.avg_roi)}</td><td>{money(row.avg_price_m2)}</td><td>{Number(row.opportunity_score || 0).toFixed(1)}</td></tr>)}</tbody>
            </table>
          </div>
        </Panel>
      </div>
      {addressDetail ? (
        <>
          <button type="button" className="detail-backdrop" aria-label="Đóng danh sách địa chỉ" onClick={closeAddressDetail} />
          <section className="record-detail-modal" role="dialog" aria-modal="true" aria-labelledby="record-detail-title">
            <div className="record-detail-head">
              <div>
                <p>Danh sách địa chỉ</p>
                <h4 id="record-detail-title">{addressDetail.segment} / {addressDetail.subSegment}</h4>
              </div>
              <div className="record-detail-actions">
                <button type="button" className="detail-copy-button" onClick={() => copyText("list")} disabled={!visibleAddresses.length}>
                  {copyState === "copied_list" ? "Đã copy danh sách" : "Copy đánh số"}
                </button>
                <button type="button" className="detail-copy-secondary" onClick={() => copyText("table")} disabled={!visibleAddresses.length}>
                  {copyState === "copied_table" ? "Đã copy bảng" : "Copy bảng"}
                </button>
                <button type="button" className="detail-download-button" onClick={downloadCsv} disabled={!visibleAddresses.length}>
                  {copyState === "downloaded_csv" ? "Đã tải CSV" : "Tải CSV"}
                </button>
                <button type="button" className="detail-close-button" onClick={closeAddressDetail}>Đóng</button>
              </div>
            </div>
            <div className="record-detail-searchbar">
              <div className="record-detail-search-row">
                <input
                  type="search"
                  className="record-detail-search"
                  placeholder="Tìm số nhà, đường, phường hoặc quận..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <button type="button" className="detail-clear-button" onClick={() => setSearchQuery("")} disabled={!searchQuery}>
                  Xóa lọc
                </button>
              </div>
              <small>{visibleAddresses.length.toLocaleString("vi-VN")} / {addressDetail.addresses.length.toLocaleString("vi-VN")} địa chỉ đang hiển thị</small>
              {!hasAnyHouseNumber ? (
                <div className="record-detail-note">Không có số nhà, chỉ có địa chỉ cấp xã/huyện.</div>
              ) : null}
            </div>
            <div className="record-detail-meta">
              <span>{addressDetail.records.toLocaleString("vi-VN")} bản ghi</span>
              <span>{addressDetail.addressCount.toLocaleString("vi-VN")} địa chỉ</span>
              <span>{visibleAddresses.length.toLocaleString("vi-VN")} địa chỉ xem nhanh</span>
            </div>
            <div className="record-detail-body">
              {visibleAddresses.length ? (
                <ul className="record-detail-list">
                  {visibleAddresses.map((address, idx) => {
                    const item = normalizeAddress(address);
                    const houseNumber = item.house_number;
                    const streetName = item.street_name;
                    const wardName = item.ward_name;
                    const districtDisplay = item.district_display;
                    const propertyType = item.property_type_name;
                    return (
                      <li key={`${item.address_display}-${idx}`}>
                        <div className="record-address-head">
                          <strong><span className="record-address-index">{idx + 1}</span>{item.address_display}</strong>
                          {houseNumber ? <span className="record-address-pill">Số nhà {houseNumber}</span> : null}
                        </div>
                        <div className="record-address-foot">
                          {propertyType ? <span>{propertyType}</span> : null}
                          {(streetName || wardName || districtDisplay) ? <small>{[streetName, wardName, districtDisplay].filter(Boolean).join(" · ")}</small> : null}
                        </div>
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <p className="record-detail-empty">Chưa có địa chỉ chi tiết cho phân đoạn này.</p>
              )}
            </div>
          </section>
        </>
      ) : null}
    </>
  );
}

function formatMetric(value, metric) {
  if (metric?.includes("price") || metric === "total_value") return money(value);
  if (metric?.includes("roi")) return pct(value);
  return Number(value || 0).toFixed(2);
}

function RecommendationSection({ label, children }) {
  if (!children) return null;
  return (
    <section className="recommendation-section">
      <span>{label}</span>
      <div>{children}</div>
    </section>
  );
}

function DecisionPage({ analytics, metadata, filters, decisionView, setDecisionView, predictForm, setPredictForm, simulationForm, setSimulationForm, prediction, whatIf, aiRecommendation, runWhatIf, simulationLoading, simulationStage }) {
  const availableDistricts = metadata?.districts_by_city?.[filters.city] || metadata?.districts || [];
  const showRoomFields = propertyNeedsRoomFields(predictForm.property_type);
  const showFloorField = propertyNeedsFloorField(predictForm.property_type);
  const scenarioProjection = (whatIf?.projection || []).map((row) => ({ ...row, calendar_year: 2025 + Number(row.year || 0) }));
  const scenarioMilestones = buildScenarioMilestones(whatIf ? { ...whatIf, projection: scenarioProjection } : null);
  const chartSpec = normalizeChartSpec(aiRecommendation?.chart_spec);
  const chartTitle = chartSpec.title || chartTitleForDecisionTab(decisionView);
  const chartType = chartSpec.chart_type || chartTypeForDecisionTab(decisionView);
  const cleanRecommendationAnswer = sanitizeRecommendationText(aiRecommendation?.answer || "");
  const cleanRecommendationWhy = sanitizeRecommendationText(aiRecommendation?.why || "");
  const cleanRecommendationSuggestion = sanitizeRecommendationText(aiRecommendation?.suggestion || "");
  const cleanRecommendationRisks = sanitizeRecommendationList(aiRecommendation?.risks || []);
  const cleanRecommendationBasis = sanitizeRecommendationList(aiRecommendation?.basis || []);
  const recommendationTone = cleanRecommendationRisks.some((item) => /l[oỗ]|g[ii]am|rủi ro|rui ro/i.test(item)) ? "warn" : aiRecommendation?.llm_available ? "good" : "neutral";
  const recommendationStage = aiStageInfo(aiRecommendation?.status || aiRecommendation?.mode, Boolean(cleanRecommendationAnswer) && !aiRecommendation?.mode?.includes("error"));
  const typedRecommendation = useTypewriterText(cleanRecommendationAnswer, Boolean(cleanRecommendationAnswer), 12);
  const typedWhy = useTypewriterText(cleanRecommendationWhy, Boolean(cleanRecommendationWhy), 12);
  const typedSuggestion = useTypewriterText(cleanRecommendationSuggestion, Boolean(cleanRecommendationSuggestion), 12);
  const recommendationIsStreaming = aiRecommendation?.status === "streaming" || simulationLoading;
  const recommendationText = recommendationIsStreaming ? cleanRecommendationAnswer : typedRecommendation || cleanRecommendationAnswer;
  const endYear = DECISION_BASE_YEAR + Number(simulationForm.years || 0);
  return (
    <>
      <PageHeader eyebrow="Mô phỏng đầu tư" title="Mô phỏng quyết định đầu tư" description="Mô phỏng kết quả đầu tư theo nhiều kịch bản để hỗ trợ ra quyết định." />
      <SectionTabs
        tabs={[
          { id: "asset", label: "Thông số tài sản" }
        ]}
        active={decisionView}
        onChange={setDecisionView}
      />
      <form className="grid-12" onSubmit={runWhatIf}>
        {decisionView !== "scenario" ? <Panel title="Thông số tài sản" className="span-3">
          <div className="control-stack">
            <select value={predictForm.district} onChange={(e) => setPredictForm({ ...predictForm, district: e.target.value })}>{availableDistricts.map((item) => <option key={item}>{item}</option>)}</select>
            <select value={predictForm.property_type} onChange={(e) => setPredictForm({ ...predictForm, property_type: e.target.value })}>{metadata?.property_types?.map((item) => <option key={item}>{item}</option>)}</select>
            <select value={predictForm.legal_documents} onChange={(e) => setPredictForm({ ...predictForm, legal_documents: e.target.value })}>{metadata?.legal_documents?.map((item) => <option key={item}>{item}</option>)}</select>
            <label>Diện tích<input type="number" value={predictForm.area} onChange={(e) => setPredictForm({ ...predictForm, area: e.target.value })} /></label>
            {showRoomFields ? <label>Số phòng ngủ<input type="number" value={predictForm.bedrooms} onChange={(e) => setPredictForm({ ...predictForm, bedrooms: e.target.value })} /></label> : <p className="panel-note">Loại tài sản này không cần nhập số phòng ngủ và số nhà vệ sinh.</p>}
            {showRoomFields ? <label>Số nhà vệ sinh<input type="number" value={predictForm.toilets} onChange={(e) => setPredictForm({ ...predictForm, toilets: e.target.value })} /></label> : null}
            {showFloorField ? <label>Số tầng<input type="number" value={predictForm.floors} onChange={(e) => setPredictForm({ ...predictForm, floors: e.target.value })} /></label> : null}
            <label>ROI kỳ vọng<input type="number" step="0.01" value={predictForm.roi_expected} onChange={(e) => setPredictForm({ ...predictForm, roi_expected: e.target.value })} /></label>
          </div>
        </Panel> : null}
        <Panel title="Giả định đầu tư" className={decisionView === "scenario" ? "span-4" : "span-4"}>
          <div className="control-stack">
            <label>Ngân sách: {Number(simulationForm.budget_billion).toFixed(1)} tỷ<input type="range" min="1" max="100" step="0.5" value={simulationForm.budget_billion} onChange={(e) => setSimulationForm({ ...simulationForm, budget_billion: e.target.value })} /></label>
            <label>Tăng trưởng/năm: {Number(simulationForm.annual_growth_pct).toFixed(1)}%<input type="range" min="-5" max="25" step="0.5" value={simulationForm.annual_growth_pct} onChange={(e) => setSimulationForm({ ...simulationForm, annual_growth_pct: e.target.value })} /></label>
            <label>Nắm giữ đến năm: {endYear} ({simulationForm.years} năm)<input type="range" min="1" max={DECISION_MAX_YEAR - DECISION_BASE_YEAR} step="1" value={simulationForm.years} onChange={(e) => setSimulationForm({ ...simulationForm, years: e.target.value })} /></label>
            <button className="primary-btn" type="submit" disabled={simulationLoading}>{simulationLoading ? "Đang mô phỏng..." : "Chạy mô phỏng đầu tư"}</button>
            <div className={`simulation-status ${simulationLoading ? "loading" : "ready"}`}>
              <span className={`badge ${simulationLoading ? "loading" : "good"}`}>{simulationLoading ? "Simulation loading" : "Ready"}</span>
              <div className="simulation-progress" aria-hidden="true">
                <i />
              </div>
            </div>
          </div>
        </Panel>
        <Panel title="Kết quả tài chính dự kiến" className={decisionView === "scenario" ? "span-8" : "span-5"}>
          {simulationLoading ? (
            <div className="assistant-streaming simulation-streaming">
              <span className="streaming-dots"><i /><i /><i /></span>
              <div>
                <strong>{simulationStage || "Đang tính toán mô phỏng tài chính..."}</strong>
                <p>Hệ thống đang cập nhật số liệu, chạy kịch bản và sinh khuyến nghị theo dữ liệu hiện tại.</p>
              </div>
            </div>
          ) : null}
          {simulationLoading && !whatIf ? <><ResultSkeleton /></> : whatIf ? <div className="result-grid"><KpiCard label="Giá trị tương lai" value={money(whatIf.summary.future_value)} /><KpiCard label="Lợi nhuận vốn" value={money(whatIf.summary.capital_gain)} /><KpiCard label="ROI tích lũy" value={pct(whatIf.summary.cumulative_roi_pct)} /><KpiCard label="Thời gian hoàn vốn" value={`${whatIf.summary.payback_years?.toFixed(1)} năm`} /></div> : <p className="muted">Chạy mô phỏng để xem giá trị tương lai, ROI và thời gian hoàn vốn.</p>}
          {simulationLoading ? <span className="generation-badge">Mô hình đang xử lý kịch bản và khuyến nghị</span> : null}
          {prediction ? <p className="model-note">Mức giá tham chiếu: <b>{money(prediction.predicted_price)}</b> | Sai số bình quân {money(prediction.model.mae)}</p> : null}
        </Panel>
        <Panel title="Triển vọng giá trị theo kịch bản" className="span-12">
          {whatIf ? <DecisionChart whatIf={whatIf} chartSpec={{ ...chartSpec, chart_type: chartType }} /> : <p className="muted">Biểu đồ sẽ hiển thị triển vọng theo ba kịch bản đầu tư.</p>}
          <p className="panel-note">Biểu đồ dùng mốc năm lịch để người xem thấy rõ từ năm nào danh mục có thể chịu áp lực, hoà vốn hay tăng trưởng tốt.</p>
        </Panel>
        <Panel title="Mốc thời gian & tình huống thua lỗ" className="span-7">
          {scenarioMilestones.length ? <div className="table-wrap"><table><thead><tr><th>Năm</th><th>Xấu</th><th>Cơ sở</th><th>Trạng thái</th></tr></thead><tbody>{scenarioMilestones.map((row) => <tr key={row.calendar_year}><td>{row.calendar_year}</td><td>{money(row.pessimistic)}</td><td>{money(row.base)}</td><td><span className={`badge ${row.status === "Rủi ro lỗ" ? "high" : row.status === "Hoà vốn yếu" ? "medium" : "good"}`}>{row.status}</span></td></tr>)}</tbody></table></div> : <p className="muted">Chạy mô phỏng để xem mốc năm cụ thể.</p>}
        </Panel>
        <Panel title="Khuyến nghị đầu tư tương lai" className="span-5">
          {aiRecommendation ? (
            <div className={`scenario-recommendation tone-${recommendationTone}`}>
              <div className="meta-row compact">
                <strong>{aiRecommendation.mode === "error" ? "AI gián đoạn" : "Khuyến nghị từ trợ lý phân tích"}</strong>
                <span className={`badge ${recommendationStage.tone}`}>{recommendationStage.label}</span>
              </div>
              <p className="panel-note">Khuyến nghị này chỉ bám đúng Thông tin tài sản và Giả định đầu tư đang chọn trong cùng trang mô phỏng.</p>
              {recommendationIsStreaming ? <span className="generation-badge">Đang stream khuyến nghị từ Qwen...</span> : cleanRecommendationAnswer && typedRecommendation !== cleanRecommendationAnswer ? <span className="generation-badge">Đang sinh câu trả lời...</span> : null}
              {recommendationText?.trim() ? <RecommendationSection label="Kết luận"><MarkdownBlock text={recommendationText} /></RecommendationSection> : null}
              {cleanRecommendationWhy ? <RecommendationSection label="Lý do"><MarkdownBlock text={typedWhy} /></RecommendationSection> : null}
              {cleanRecommendationSuggestion ? <RecommendationSection label="Hành động"><MarkdownBlock text={typedSuggestion} /></RecommendationSection> : null}
              {cleanRecommendationRisks.length ? <RecommendationSection label="Rủi ro cần nêu"><ul className="scenario-bullet-list">{cleanRecommendationRisks.map((risk, index) => <li key={index}>{risk}</li>)}</ul></RecommendationSection> : null}
              {cleanRecommendationBasis.length ? <RecommendationSection label="Cơ sở đưa ra khuyến nghị"><ul className="scenario-bullet-list">{cleanRecommendationBasis.map((item, index) => <li key={index}>{item}</li>)}</ul></RecommendationSection> : null}
              <small>{aiRecommendation.model} · {aiRecommendation.retrieval_time_ms} ms</small>
            </div>
          ) : <p className="muted">Chạy mô phỏng để nhận khuyến nghị mua thêm, giữ hay bán bớt theo kịch bản tương lai.</p>}
        </Panel>
      </form>
    </>
  );
}

function GisPage({ mapData, analytics }) {
  const [riskFilter, setRiskFilter] = useState("all");
  const [minRoi, setMinRoi] = useState(0);
  const [minScore, setMinScore] = useState(0);
  const center = mapData?.center || { latitude: 10.78, longitude: 106.7, zoom: 10 };
  const lastRefresh = analytics?.kpis?.last_data_refresh;
  const districts = mapData?.districts || [];
  const markers = useMemo(() => groupMapMarkers(districts), [districts]);
  const maxRoi = markers.length ? Math.max(...markers.map((row) => markerRoi(row))) : 0;
  const maxScore = markers.length ? Math.max(...markers.map((row) => markerScore(row))) : 0;
  const filteredDistricts = useMemo(
    () => markers.filter((row) => {
      const roi = markerRoi(row);
      const score = markerScore(row);
      const riskMatch = riskFilter === "all" || row.risk_level === riskFilter;
      return riskMatch && roi >= Number(minRoi || 0) && score >= Number(minScore || 0);
    }),
    [markers, riskFilter, minRoi, minScore]
  );
  const leading = [...filteredDistricts].sort((a, b) => markerScore(b) - markerScore(a)).slice(0, 3);
  const watchlist = [...filteredDistricts].filter((row) => row.risk_level === "high").sort((a, b) => markerScore(a) - markerScore(b)).slice(0, 4);
  const avgRoi = markers.length ? markers.reduce((sum, row) => sum + markerRoi(row), 0) / markers.length : 0;
  const avgScore = markers.length ? markers.reduce((sum, row) => sum + markerScore(row), 0) / markers.length : 0;
  const chartRows = [...filteredDistricts].sort((a, b) => markerRoi(b) - markerRoi(a)).slice(0, 5);
  return (
    <>
      <PageHeader eyebrow="Bản đồ quy hoạch" title="Bản đồ và quy hoạch" description="Phân tích điểm cơ hội và mức độ rủi ro theo không gian." />
      <div className="grid-12">
        <Panel title="Bản đồ quy hoạch" className="span-8 map-panel-host">
          <div className="map-filter-bar">
            <label>
              <span>Rủi ro</span>
              <select value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}>
                <option value="all">Tất cả</option>
                <option value="low">Thấp</option>
                <option value="medium">Trung bình</option>
                <option value="high">Cao</option>
              </select>
            </label>
            <label>
              <span>ROI tối thiểu: {Number(minRoi).toFixed(1)}%</span>
              <input type="range" min="0" max={Math.max(20, Math.ceil(maxRoi))} step="0.5" value={minRoi} onChange={(e) => setMinRoi(Number(e.target.value))} />
            </label>
            <label>
              <span>Score tối thiểu: {Number(minScore).toFixed(0)}</span>
              <input type="range" min="0" max={Math.max(100, Math.ceil(maxScore))} step="1" value={minScore} onChange={(e) => setMinScore(Number(e.target.value))} />
            </label>
            <button
              type="button"
              className="secondary-btn map-filter-reset"
              onClick={() => {
                setRiskFilter("all");
                setMinRoi(0);
                setMinScore(0);
              }}
            >
              Bỏ lọc
            </button>
          </div>
          <p className="map-interaction-hint">Có thể kéo để di chuyển, lăn chuột hoặc chụm hai ngón để zoom.</p>
          <MapContainer
            key={mapData?.city || "default-city"}
            center={[center.latitude, center.longitude]}
            zoom={center.zoom || 10}
            scrollWheelZoom
            dragging
            touchZoom
            doubleClickZoom
            boxZoom
            zoomControl
            className="leaflet-panel main-map"
          >
            <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            {(filteredDistricts.length ? filteredDistricts : markers).map((row) => {
              const scoreValue = markerScore(row);
              const roiValue = markerRoi(row);
              const markerLabel = row.district_count > 1 ? `${row.district} · ${row.district_count} khu` : row.district;
              return (
                <CircleMarker
                  key={`${row.latitude}-${row.longitude}-${row.district}`}
                  center={[row.latitude, row.longitude]}
                  radius={Math.max(8, Math.min(30, scoreValue / 3))}
                  pathOptions={{ color: row.risk_level === "low" ? "#0f766e" : row.risk_level === "high" ? "#c2410c" : "#d97706", fillOpacity: 0.62 }}
                >
                  <Popup>
                    <strong>{markerLabel}</strong>
                    {row.district_count > 1 ? <p>{row.districts.join(" · ")}</p> : null}
                    <p>Score {scoreValue.toFixed(1)}</p>
                    <p>ROI {roiValue.toFixed(2)}%</p>
                    <p>{row.planning_note}</p>
                  </Popup>
                </CircleMarker>
              );
            })}
          </MapContainer>
          <div className="map-footer-grid">
            <article className="map-fact-card">
              <span>Cập nhật</span>
              <strong>{formatDateTime(lastRefresh)}</strong>
            </article>
            <article className="map-fact-card">
              <span>Số khu vực</span>
              <strong>{markers.length.toLocaleString("vi-VN")}</strong>
              <small>Các điểm trên bản đồ đang khớp với thành phố và bộ lọc hiện tại.</small>
            </article>
            {leading.map((row) => (
              <article className="map-fact-card" key={row.district}>
                <span>{row.district}</span>
                <strong>{row.opportunity_score.toFixed(1)}/100</strong>
                <small>{row.risk_level === "high" ? "Cần theo dõi quy hoạch" : row.risk_level === "medium" ? "Rủi ro trung bình" : "Mức rủi ro thấp hơn"}</small>
              </article>
            ))}
          </div>
        </Panel>
        <Panel title="Chú giải và khu vực cần theo dõi" className="span-4">
          <div className="map-side-stack">
            <div className="map-executive-card">
              <span>Tóm tắt điều hành</span>
              <strong>{leading[0]?.district || "Chưa có khu dẫn đầu"}</strong>
              <small>{filteredDistricts.length ? `${filteredDistricts.length} khu đang khớp bộ lọc` : "Không có khu vực nào khớp bộ lọc hiện tại"}</small>
            </div>
            <div className="map-legend">
              <span><i className="dot low" /> Rủi ro thấp</span>
              <span><i className="dot medium" /> Rủi ro trung bình</span>
              <span><i className="dot high" /> Rủi ro cao</span>
              <small>Kích thước điểm tròn thể hiện điểm cơ hội</small>
            </div>
            <div className="map-metrics-grid">
              <article className="map-metric-card">
                <span>ROI TB</span>
                <strong>{pct(avgRoi)}</strong>
              </article>
              <article className="map-metric-card">
                <span>Score TB</span>
                <strong>{avgScore.toFixed(1)}</strong>
              </article>
              <article className="map-metric-card">
              <span>Top nổi bật</span>
              <strong>{leading[0]?.district || "N/A"}</strong>
            </article>
              <article className="map-metric-card">
                <span>Cần theo dõi</span>
                <strong>{watchlist[0]?.district || "N/A"}</strong>
              </article>
            </div>
            <div className="map-subsection">
              <span className="map-subsection-title">ROI top khu vực</span>
              {chartRows.length ? (
                <ResponsiveContainer width="100%" height={190}>
                  <BarChart data={chartRows}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="district" interval={0} angle={-20} textAnchor="end" height={58} tick={{ fontSize: 11 }} />
                    <YAxis tickFormatter={(v) => `${Number(v).toFixed(0)}%`} />
                    <Tooltip formatter={(value) => pct(value)} />
                    <Bar dataKey="roi_pct" fill="#0f766e" radius={[6, 6, 0, 0]} name="ROI" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="map-empty-state">Không có khu vực nào thỏa điều kiện lọc để vẽ chart.</p>
              )}
            </div>
            <div className="map-subsection">
              <span className="map-subsection-title">Điểm nóng</span>
              <div className="map-list compact">
                {leading.length ? leading.map((row) => <article className="risk-card compact" key={`lead-${row.district}`}><div><strong>{row.district}</strong><span className={`badge ${row.risk_level}`}>{row.risk_level}</span></div><p>{row.planning_note}</p><small>ROI {row.roi_pct.toFixed(2)}% | Score {row.opportunity_score.toFixed(1)}</small></article>) : <p className="map-empty-state">Không có khu nóng nào sau khi lọc.</p>}
              </div>
            </div>
            <div className="map-subsection">
              <span className="map-subsection-title">Khu cần theo dõi</span>
              <div className="map-list compact">
                {(watchlist.length ? watchlist : filteredDistricts.slice(0, 4)).map((row) => <article className="risk-card compact" key={`watch-${row.district}`}><div><strong>{row.district}</strong><span className={`badge ${row.risk_level}`}>{row.risk_level}</span></div><p>{row.planning_note}</p><small>ROI {row.roi_pct.toFixed(2)}% | Score {row.opportunity_score.toFixed(1)}</small></article>)}
                {!watchlist.length && !filteredDistricts.length ? <p className="map-empty-state">Không có khu vực rủi ro cao thỏa điều kiện lọc.</p> : null}
              </div>
            </div>
          </div>
        </Panel>
      </div>
    </>
  );
}

function AiPage({ question, setQuestion, assistant, assistantLoading, askAssistant }) {
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const assistantStage = aiStageInfo(assistant?.status || assistant?.mode, assistantLoading);
  const assistantWaitingCopy = providerWaitingCopy(assistant?.status, assistant?.llm_mode);

  useEffect(() => {
    if (assistant?.sources?.length) {
      setSourcesOpen(true);
    }
  }, [assistant]);

  return (
    <>
      <PageHeader eyebrow="Trợ lý phân tích" title="Trợ lý phân tích" description="Tổng hợp dữ liệu thị trường, pháp lý và quy hoạch để hỗ trợ quyết định đầu tư." />
      <div className="grid-12">
        <Panel title="Câu hỏi phân tích" className="span-7">
          <div className="chat-box">
            <textarea value={question} onChange={(e) => setQuestion(e.target.value)} />
            <div className="prompt-row">{["Quận Tân Bình có rủi ro quy hoạch gì?", "Nên ưu tiên khu nào nếu ROI tốt?", "So sánh Bình Chánh và Thủ Đức"].map((prompt) => <button key={prompt} onClick={() => setQuestion(prompt)}>{prompt}</button>)}</div>
            <div className="assistant-action-row">
              <button className="primary-btn" onClick={askAssistant} disabled={assistantLoading}>{assistantLoading ? "Đang phân tích..." : "Phân tích"}</button>
              <button className="secondary-btn" onClick={() => askAssistant("stop")} disabled={!assistantLoading}>Dừng sinh</button>
            </div>
            {assistantLoading ? (
              <div className="assistant-streaming">
                <span className="streaming-dots"><i /><i /><i /></span>
                <div>
                  <strong>{assistant?.status?.startsWith("waiting_") ? assistantWaitingCopy.title : "RAG đang truy xuất nguồn và Qwen đang sinh câu trả lời..."}</strong>
                  <p>{assistant?.status?.startsWith("waiting_") ? assistantWaitingCopy.body : "Kết quả sẽ hiện ra ngay khi mô hình trả lời xong."}</p>
                </div>
              </div>
            ) : null}
          </div>
          {assistant ? <div className="answer-panel"><div className="meta-row"><span>{assistant.mode}</span><span>{assistant.model}</span><span className={`badge ${assistantStage.tone}`}>{assistantStage.label}</span><span>{assistant.retrieval_time_ms} ms</span></div>{assistantLoading ? <span className="generation-badge">{assistantStage.label}</span> : null}<StructuredResponse text={assistant.answer || ""} sectionTitles={["Kết luận điều hành", "Cơ sở nhận định", "Rủi ro cần lưu ý", "Hành động tiếp theo"]} /></div> : null}
        </Panel>
        <Panel title="Thanh tra nguồn" className="span-5">
          <Disclosure title="Nguồn trích dẫn" open={sourcesOpen} defaultOpen={false} compact onToggle={setSourcesOpen}>
            <div className="source-list">{(assistant?.sources || []).map((source) => <a key={source.title} href={source.source_url} target="_blank" rel="noreferrer" className="source-card"><strong>{source.title}</strong><span>{source.content}</span><small>{source.source_name} · score {source.score?.toFixed(2)}</small></a>)}</div>
          </Disclosure>
        </Panel>
      </div>
    </>
  );
}

function DataOpsPage({ etl, refreshEtl, loading, ragStatus }) {
  return (
    <>
      <PageHeader eyebrow="Theo dõi dữ liệu" title="Giám sát vận hành dữ liệu" description="Theo dõi trạng thái nạp dữ liệu, quy hoạch và kho tri thức AI." />
      <div className="grid-12">
        <Panel title="Tình trạng dữ liệu" className="span-12" action={<button className="primary-btn small" onClick={refreshEtl}>{loading ? "Đang cập nhật" : "Cập nhật dữ liệu"}</button>}>
          <div className="kpi-grid compact"><KpiCard label="Bản ghi thị trường" value={(etl?.transaction_records || 0).toLocaleString("vi-VN")} /><KpiCard label="Lớp quy hoạch" value={(etl?.planning_zones || 0).toLocaleString("vi-VN")} /><KpiCard label="Tài liệu pháp lý" value={(etl?.legal_documents || 0).toLocaleString("vi-VN")} /><KpiCard label="Metro impact" value={(etl?.metro_impacts || 0).toLocaleString("vi-VN")} /><KpiCard label="Kho tri thức AI" value={ragStatus ? `${ragStatus.documents} tài liệu` : "Sẵn sàng"} /></div>
        </Panel>
        <Panel title="Nhật ký cập nhật dữ liệu" className="span-7"><SimpleRuns runs={etl?.runs || []} /></Panel>
        <Panel title="Trung tâm dữ liệu công cộng" className="span-5"><div className="source-list">{(etl?.sources || []).map((source) => <a className="source-card" href={source.url} target="_blank" rel="noreferrer" key={source.url}><strong>{source.name}</strong><span>{source.type}</span><small>{source.status}</small></a>)}</div></Panel>
      </div>
    </>
  );
}

function SimpleRuns({ runs }) {
  return <div className="table-wrap"><table><thead><tr><th>Thời điểm</th><th>Hình thức</th><th>Trạng thái</th><th>Đã đọc</th><th>Đã nạp</th></tr></thead><tbody>{runs.map((run) => <tr key={run.run_id}><td>{run.finished_at?.slice(0, 19)}</td><td>{run.mode}</td><td><span className="badge good">{run.status}</span></td><td>{run.records_seen?.toLocaleString("vi-VN")}</td><td>{run.records_inserted?.toLocaleString("vi-VN")}</td></tr>)}</tbody></table></div>;
}

function ExplorerPage({ analytics }) {
  return (
    <>
      <PageHeader eyebrow="Chi tiết tài sản" title="Danh sách tài sản" description="Xem chi tiết các tài sản có ROI cao trong bộ lọc hiện tại." />
      <Panel title="Bảng tài sản">
        <div className="table-wrap"><table><thead><tr><th>Địa chỉ</th><th>Khu vực</th><th>Loại</th><th>Giá</th><th>Diện tích</th><th>ROI</th></tr></thead><tbody>{(analytics?.samples || []).map((row) => <tr key={`${row.Location}-${row.date}`}><td>{row.Location}</td><td>{row.district}</td><td>{row["Type of House"]}</td><td>{money(row.price_vnd)}</td><td>{row.area} m²</td><td>{pct(row.ROI * 100)}</td></tr>)}</tbody></table></div>
      </Panel>
    </>
  );
}

function ReportPage({ analytics, whatIf, reportNote, reportNoteLoading }) {
  const kpis = analytics?.kpis || {};
  const reportBriefs = useMemo(() => buildExecutiveBriefs(analytics?.districts || []), [analytics?.districts]);
  const coverSummary = useMemo(() => buildReportCoverSummary(analytics || {}, whatIf), [analytics, whatIf]);
  const reportStage = aiStageInfo(reportNote?.status || reportNote?.mode, reportNoteLoading);
  const exportTimestamp = analytics?.kpis?.last_data_refresh ? formatDateTime(analytics.kpis.last_data_refresh) : formatDateTime(new Date().toISOString());

  function exportPdf() {
    window.print();
  }

  return (
    <>
      <PageHeader eyebrow="Báo cáo định kỳ" title="Báo cáo định kỳ" description="Tóm tắt phát hiện chính, khuyến nghị và căn cứ tham chiếu để trình bày theo chu kỳ." />
      <div className="report-toolbar no-print">
        <div>
          <strong>Bản in điều hành</strong>
          <span>Định dạng sẵn sàng xuất PDF cho báo cáo công ty.</span>
        </div>
        <button type="button" className="primary-btn" onClick={exportPdf}>Xuất PDF</button>
      </div>
      <section className="report-cover">
        <div className="report-cover-main">
          <span>Executive Report</span>
          <h3>PropertyVision BI</h3>
          <p>Báo cáo định kỳ tập trung vào phát hiện chính, khuyến nghị hành động và cơ sở dữ liệu làm căn cứ trình bày cho ban điều hành.</p>
          <div className="report-cover-meta">
            <span>Cập nhật {exportTimestamp}</span>
            <span>ROI TB {pct(kpis.avg_roi)}</span>
            <span>{(kpis.transaction_count || 0).toLocaleString("vi-VN")} giao dịch / bản ghi</span>
          </div>
        </div>
        <div className="report-cover-stats">
          <article>
            <span>Khu dẫn đầu</span>
            <strong>{coverSummary.bestDistrict}</strong>
          </article>
          <article>
            <span>Giá trị tương lai</span>
            <strong>{coverSummary.projectedFutureValue ? money(coverSummary.projectedFutureValue) : "Chưa mô phỏng"}</strong>
          </article>
          <article>
            <span>ROI tích lũy</span>
            <strong>{coverSummary.projectedCumulativeRoi !== null ? pct(coverSummary.projectedCumulativeRoi) : "Chưa mô phỏng"}</strong>
          </article>
          <article>
            <span>Hoàn vốn</span>
            <strong>{coverSummary.projectedPaybackYears ? `${coverSummary.projectedPaybackYears.toFixed(1)} năm` : "Chưa mô phỏng"}</strong>
          </article>
        </div>
      </section>
      <div className="grid-12 report-grid">
        <Panel title="Phát hiện chính" className="span-6">
          <div className="brief-grid compact">
            {reportBriefs.map((brief) => (
              <article className="brief-card" key={brief.district}>
                <div className="brief-head">
                  <span className="brief-tag">{brief.tag}</span>
                  <strong>{brief.district}</strong>
                </div>
                <p>{brief.edge}</p>
                <small><b>Lợi thế:</b> {brief.strength}</small>
                <small><b>Rủi ro:</b> {brief.risk}</small>
              </article>
            ))}
          </div>
          <div className="report-meta-row">
            <span>ROI trung bình: <b>{pct(kpis.avg_roi)}</b></span>
            <span>Bản ghi thị trường: <b>{(kpis.transaction_count || 0).toLocaleString("vi-VN")}</b></span>
          </div>
        </Panel>
        <Panel title="Ghi chú điều hành" className="span-6">
          {reportNote?.answer ? (
            <div className="answer-panel">
              <div className="meta-row">
                <span>{reportNote.mode}</span>
                <span>{reportNote.model}</span>
                <span className={`badge ${reportStage.tone}`}>{reportStage.label}</span>
                <span>{reportNote.retrieval_time_ms} ms</span>
              </div>
              {reportNoteLoading ? <span className="generation-badge">{reportStage.label}</span> : null}
              <StructuredResponse text={reportNote.answer || ""} sectionTitles={["Kết luận điều hành", "Cơ sở nhận định", "Rủi ro cần lưu ý", "Hành động tiếp theo"]} />
            </div>
          ) : (
            <p>{reportNoteLoading ? "Đang làm mới ghi chú điều hành..." : "Ghi chú điều hành sẽ tự làm mới theo dữ liệu hiện tại để không phải chờ thao tác thủ công."}</p>
          )}
        </Panel>
        <Panel title="Tóm tắt mô phỏng đầu tư" className="span-12">{whatIf ? <div className="kpi-grid compact"><KpiCard label="Giá trị tương lai" value={money(whatIf.summary.future_value)} /><KpiCard label="ROI tích lũy" value={pct(whatIf.summary.cumulative_roi_pct)} /><KpiCard label="Thời gian hoàn vốn" value={`${whatIf.summary.payback_years?.toFixed(1)} năm`} /></div> : <p className="muted">Chạy mô phỏng đầu tư để đưa kết quả vào báo cáo.</p>}</Panel>
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
  const [aiRuntime, setAiRuntime] = useState(null);
  const [error, setError] = useState("");
  const [prediction, setPrediction] = useState(null);
  const [whatIf, setWhatIf] = useState(null);
  const [aiRecommendation, setAiRecommendation] = useState(null);
  const [simulationLoading, setSimulationLoading] = useState(false);
  const [simulationStage, setSimulationStage] = useState("Ready");
  const [decisionView, setDecisionView] = useState("whatif");
  const [assistant, setAssistant] = useState(null);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [reportNote, setReportNote] = useState(null);
  const [reportNoteLoading, setReportNoteLoading] = useState(false);
  const [mapData, setMapData] = useState(null);
  const [etl, setEtl] = useState(null);
  const [ragStatus, setRagStatus] = useState(null);
  const [sliceDice, setSliceDice] = useState(null);
  const [sliceConfig, setSliceConfig] = useState({ row_dimension: "district", column_dimension: "Type of House", metric: "avg_roi" });
  const [question, setQuestion] = useState("Nên ưu tiên khu vực nào để đầu tư với ROI tốt và rủi ro vừa phải?");
  const [predictForm, setPredictForm] = useState({ district: "", property_type: "", legal_documents: "", area: 70, bedrooms: 3, toilets: 3, floors: 3, roi_expected: 0.14 });
  const [simulationForm, setSimulationForm] = useState({ budget_billion: 10, annual_growth_pct: 8, years: 25 });
  const assistantAbortRef = useRef(null);
  const reportNoteAbortRef = useRef(null);
  const runtimeModelLabel = aiRuntime?.model || DEFAULT_MODEL_LABEL;

  useEffect(() => {
    request("/api/metadata")
      .then((data) => {
        setMetadata(data);
        const initialCity = data.cities?.[0] || emptyFilters.city;
        const initialDistrict = data.districts_by_city?.[initialCity]?.[0] || data.districts?.[0] || "";
        setFilters((current) => ({ ...current, city: initialCity }));
        setPredictForm((current) => ({ ...current, district: initialDistrict, property_type: data.property_types[0], legal_documents: data.legal_documents[0] }));
      })
      .catch(() => setError("Không kết nối được backend FastAPI. Hãy chạy uvicorn backend.main:app --reload."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    request("/api/etl/status")
      .then((etlPayload) => { setEtl(etlPayload); })
      .catch(() => setError("Không tải được dữ liệu vận hành từ backend."));
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function refreshAiRuntime() {
      try {
        const payload = await request("/api/ai/status");
        if (!cancelled) setAiRuntime(payload);
      } catch {
        if (!cancelled) setAiRuntime({ status: "error", label: "Error", message: "Không đọc được trạng thái AI." });
      }
    }
    refreshAiRuntime();
    const timer = window.setInterval(refreshAiRuntime, 3000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    if (!filters.city) return;
    request(`/api/map/districts?city=${encodeURIComponent(filters.city)}`)
      .then((payload) => setMapData(payload))
      .catch(() => setError("Không tải được dữ liệu bản đồ theo thành phố đã chọn."));
  }, [filters.city]);

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

  useEffect(() => {
    if (!metadata || !analytics || activePage !== "report") return;
    let cancelled = false;
    setReportNoteLoading(true);
    if (reportNoteAbortRef.current) reportNoteAbortRef.current.abort();
    const controller = new AbortController();
    reportNoteAbortRef.current = controller;
    const timer = window.setTimeout(async () => {
      try {
        let streamedNote = "";
        await requestNdjsonStream("/api/assistant/stream", {
          method: "POST",
          body: JSON.stringify({
            question: buildReportQuestion(analytics, filters),
            filters,
            task: "executive_brief"
          }),
          signal: controller.signal
        }, {
          onMeta: (event) => {
            if (cancelled) return;
            setReportNote((current) => ({
              ...current,
              answer: streamedNote,
              sources: event.sources || [],
              model: event.model || current?.model || runtimeModelLabel,
              mode: event.mode || current?.mode || "hf-qwen",
              llm_available: Boolean(event.llm_available),
              llm_mode: event.llm_mode || current?.llm_mode,
              status: event.status || current?.status
            }));
          },
          onLine: (event) => {
            if (cancelled) return;
            streamedNote += `${event.text || ""}\n`;
            setReportNote((current) => ({
              ...current,
              answer: streamedNote,
              llm_available: true,
              mode: "hf-qwen",
              status: "streaming"
            }));
          },
          onDone: (event) => {
            if (cancelled) return;
            streamedNote = event.answer || streamedNote;
            setReportNote((current) => ({
              ...current,
              answer: streamedNote,
              model: event.model || current?.model || runtimeModelLabel,
              mode: event.mode || current?.mode || "hf-qwen",
              llm_available: true,
              llm_mode: event.llm_mode || current?.llm_mode,
              status: "done"
            }));
          }
        });
        if (!cancelled) {
          setReportNoteLoading(false);
        }
      } catch (error) {
        if (error?.name === "AbortError") {
          if (!cancelled) setReportNoteLoading(false);
          return;
        }
        if (!cancelled) {
          setReportNote({
            answer: `AI gián đoạn: ${error instanceof Error ? error.message : "AI provider chưa phản hồi trong thời gian quy định."}`,
            sources: [],
            model: runtimeModelLabel,
            mode: "error",
            llm_available: false,
            retrieval_time_ms: 0,
            llm_mode: "featherless-direct",
            status: "error"
          });
          setReportNoteLoading(false);
        }
      }
    }, 500);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
      controller.abort();
      setReportNoteLoading(false);
    };
  }, [activePage, analytics, filters, metadata]);

  useEffect(() => {
    if (!metadata) return;
    const availableDistricts = metadata.districts_by_city?.[filters.city] || metadata.districts || [];
    if (!availableDistricts.length) return;
    if (!availableDistricts.includes(predictForm.district)) {
      setPredictForm((current) => ({ ...current, district: availableDistricts[0] }));
    }
  }, [metadata, filters.city, predictForm.district]);

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
      bedrooms: propertyNeedsRoomFields(predictForm.property_type) ? toNullableNumber(predictForm.bedrooms) : null,
      toilets: propertyNeedsRoomFields(predictForm.property_type) ? toNullableNumber(predictForm.toilets) : null,
      floors: propertyNeedsFloorField(predictForm.property_type) ? toNullableNumber(predictForm.floors) : null,
      roi_expected: Number(predictForm.roi_expected),
      budget_vnd: Number(simulationForm.budget_billion) * 1_000_000_000,
      annual_growth_pct: Number(simulationForm.annual_growth_pct),
      years: Number(simulationForm.years)
    };
    const recommendationPayloadBody = {
      ...payload,
      filters,
      task: "decision_memo",
      decision_tab: decisionView
    };
    try {
      setSimulationLoading(true);
      setPrediction(null);
      setWhatIf(null);
      setSimulationStage("Đang gửi yêu cầu mô phỏng...");
      setAiRecommendation({
        answer: "",
        why: "",
        suggestion: "",
        risks: [],
        basis: [],
        sources: [],
        model: runtimeModelLabel,
        mode: "loading",
        status: "loading",
        llm_available: false,
        retrieval_time_ms: 0,
        llm_mode: "featherless-direct"
      });
      let streamedRecommendation = "";
      await requestNdjsonStream("/api/recommendation/future/stream", {
        method: "POST",
        body: JSON.stringify(recommendationPayloadBody)
      }, {
        onMeta: (eventPayload) => {
          setAiRecommendation((current) => ({
            ...current,
            model: eventPayload.model || current?.model || runtimeModelLabel,
            mode: eventPayload.mode || current?.mode || "loading",
            status: eventPayload.status || current?.status || "loading",
            llm_available: Boolean(eventPayload.llm_available),
            llm_mode: eventPayload.llm_mode || current?.llm_mode || "featherless-direct"
          }));
          if (eventPayload.status === "waiting_featherless") {
            setSimulationStage("Đang chờ Featherless...");
          } else if (eventPayload.status === "waiting_huggingface") {
            setSimulationStage("Đang chờ Hugging Face...");
          }
        },
        onStage: (eventPayload) => {
          setSimulationStage(eventPayload.text || "Đang xử lý mô phỏng...");
          setAiRecommendation((current) => ({
            ...current,
            status: "streaming",
            mode: current?.mode || "hf-qwen-future-recommendation",
            llm_available: true,
            llm_mode: current?.llm_mode || "featherless-direct"
          }));
        },
        onWhatIf: (eventPayload) => {
          setPrediction(eventPayload.prediction || eventPayload.what_if?.asset_prediction || null);
          setWhatIf(eventPayload.what_if || null);
          setSimulationStage("Đang sinh khuyến nghị AI...");
        },
        onLine: (eventPayload) => {
          const text = sanitizeRecommendationText(eventPayload.text || "");
          if (!text) return;
          const section = eventPayload.section || "answer";
          if (section === "answer") {
            streamedRecommendation = `${streamedRecommendation}${text}\n`;
          }
          setAiRecommendation((current) => ({
            ...current,
            answer: section === "answer" ? streamedRecommendation : current?.answer || "",
            why: section === "why" ? `${current?.why || ""}${text}\n` : current?.why || "",
            suggestion: section === "suggestion" ? `${current?.suggestion || ""}${text}\n` : current?.suggestion || "",
            risks: section === "risks" ? [...(current?.risks || []), text] : current?.risks || [],
            basis: section === "basis" ? [...(current?.basis || []), text] : current?.basis || [],
            mode: "hf-qwen-future-recommendation",
            status: "streaming",
            llm_available: true,
            llm_mode: current?.llm_mode || "featherless-direct"
          }));
        },
        onDone: (eventPayload) => {
          setPrediction(eventPayload.what_if?.asset_prediction || null);
          setWhatIf(eventPayload.what_if || null);
          const doneAnswer = sanitizeRecommendationText(eventPayload.answer || "");
          const doneWhy = sanitizeRecommendationText(eventPayload.why || "");
          const doneSuggestion = sanitizeRecommendationText(eventPayload.suggestion || "");
          const doneRisks = sanitizeRecommendationList(eventPayload.risks || []);
          const doneBasis = sanitizeRecommendationList(eventPayload.basis || []);
          setAiRecommendation((current) => ({
            ...current,
            ...eventPayload,
            answer: doneAnswer,
            why: doneWhy,
            suggestion: doneSuggestion,
            risks: doneRisks,
            basis: doneBasis,
            chart_caption: sanitizeRecommendationText(eventPayload.chart_caption || current?.chart_caption || ""),
            mode: eventPayload.mode || "hf-qwen-future-recommendation",
            status: "done",
            llm_available: true,
            llm_mode: eventPayload.llm_mode || current?.llm_mode || "featherless-direct"
          }));
          setSimulationStage("Hoàn tất mô phỏng.");
        }
      });
    } catch (error) {
      setAiRecommendation({
        answer: `AI gián đoạn: ${error instanceof Error ? error.message : "AI provider chưa phản hồi trong thời gian quy định."}`,
        why: "",
        suggestion: "",
        risks: ["Khuyến nghị không thể sinh đúng thời gian vì mô hình hosted chưa phản hồi."],
        basis: [],
        sources: [],
        model: runtimeModelLabel,
        mode: "error",
        status: "error",
        llm_available: false,
        retrieval_time_ms: 0,
        llm_mode: "featherless-direct"
      });
      setSimulationStage("Mô phỏng bị gián đoạn.");
    } finally {
      setSimulationLoading(false);
    }
  }

  async function askAssistant(action = "run") {
    if (action === "stop") {
      assistantAbortRef.current?.abort();
      setAssistantLoading(false);
      return;
    }
    setAssistantLoading(true);
    setAssistant({
      answer: "",
      sources: [],
      model: runtimeModelLabel,
      mode: "streaming",
      llm_available: true,
      retrieval_time_ms: 0,
      llm_mode: "featherless-direct",
      status: "waiting_featherless"
    });
    if (assistantAbortRef.current) assistantAbortRef.current.abort();
    const controller = new AbortController();
    assistantAbortRef.current = controller;
    try {
      let streamedAnswer = "";
      let streamBuffer = "";
      await requestNdjsonStream("/api/assistant/stream", {
        method: "POST",
        body: JSON.stringify({ question, filters, task: "assistant_question" }),
        signal: controller.signal
      }, {
        onMeta: (event) => {
          setAssistant((current) => ({
            ...current,
            answer: streamedAnswer,
            sources: event.sources || [],
            model: event.model || current.model || runtimeModelLabel,
          mode: event.mode || current.mode,
          llm_available: Boolean(event.llm_available),
          llm_mode: event.llm_mode || current.llm_mode,
            status: event.status || current.status
          }));
        },
        onLine: (event) => {
          streamBuffer = `${streamBuffer}${event.text || ""}\n`;
          streamedAnswer += event.text || "";
          setAssistant((current) => ({
            ...current,
            answer: streamBuffer,
            llm_available: true,
            mode: "hf-qwen",
            status: "streaming"
          }));
        },
        onDone: (event) => {
          streamedAnswer = event.answer || streamedAnswer;
          setAssistant((current) => ({
            ...current,
            answer: streamedAnswer.split("\n").filter(Boolean).join("\n"),
            model: event.model || current.model || runtimeModelLabel,
            mode: event.mode || "hf-qwen",
            llm_available: true,
            llm_mode: event.llm_mode || current.llm_mode,
            status: "done"
          }));
        }
      });
    } catch (error) {
      if (error?.name === "AbortError") {
        setAssistant((current) => ({
          ...current,
          mode: "stopped",
          llm_available: false,
          status: "stopped"
        }));
      } else {
        setAssistant({
          answer: `AI gián đoạn: ${error instanceof Error ? error.message : "AI provider chưa phản hồi trong thời gian quy định."}`,
          sources: [],
          model: runtimeModelLabel,
          mode: "error",
          llm_available: false,
          retrieval_time_ms: 0,
          llm_mode: "featherless-direct",
          status: "error"
        });
      }
    } finally {
      if (assistantAbortRef.current === controller) assistantAbortRef.current = null;
      setAssistantLoading(false);
    }
  }

  async function refreshEtl() {
    setLoading(true);
    const payload = await request("/api/etl/run", { method: "POST", body: JSON.stringify({}) });
    setEtl(payload.status);
    setMapData(await request(`/api/map/districts?city=${encodeURIComponent(filters.city || emptyFilters.city)}`));
    setRagStatus(await request("/api/rag/reindex", { method: "POST", body: JSON.stringify({}) }));
    setAnalytics(await request("/api/analytics", { method: "POST", body: JSON.stringify(filters) }));
    setLoading(false);
  }

  if (error) return <div className="boot-error">{error}</div>;
  if (!metadata || !analytics) return <div className="boot">Đang khởi tạo PropertyVision...</div>;

  const sharedPageProps = { activePage, analytics, typeShare, sliceDice, sliceConfig, setSliceConfig, metadata, filters, mapData, etl, refreshEtl, loading, ragStatus, question, setQuestion, assistant, assistantLoading, askAssistant, reportNote, reportNoteLoading };
  const decisionPageProps = { ...sharedPageProps, decisionView, setDecisionView, predictForm, setPredictForm, simulationForm, setSimulationForm, prediction, whatIf, aiRecommendation, runWhatIf, simulationLoading, simulationStage };

  return (
    <AppShell activePage={activePage} setActivePage={setActivePage} loading={loading} metadata={metadata} filters={filters} setFilters={setFilters} aiRuntime={aiRuntime} analytics={analytics} etl={etl}>
      {activePage === "overview" && <OverviewPage {...sharedPageProps} />}
      {activePage === "market" && <MarketPage {...sharedPageProps} />}
      {activePage === "slice" && <SlicePage {...sharedPageProps} />}
      {activePage === "decision" && <DecisionPage {...decisionPageProps} />}
      {activePage === "gis" && <GisPage {...sharedPageProps} />}
      {activePage === "ai" && <AiPage {...sharedPageProps} />}
      {activePage === "ops" && <DataOpsPage {...sharedPageProps} />}
      {activePage === "explorer" && <ExplorerPage {...sharedPageProps} />}
      {activePage === "report" && <ReportPage {...sharedPageProps} />}
    </AppShell>
  );
}

createRoot(document.getElementById("root")).render(<App />);
