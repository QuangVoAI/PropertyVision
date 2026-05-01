import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const currencyMillions = (value) =>
  `${(value / 1_000_000).toFixed(1)}M`;

function SectionHeader({ title, subtitle, action }) {
  return (
    <div className="section-header">
      <div>
        <h2>{title}</h2>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}

function StatCard({ label, value, tone }) {
  return (
    <div className={`stat-card tone-${tone || "neutral"}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function DashboardMap({ points }) {
  const center = useMemo(() => {
    if (!points?.length) return [10.78, 106.69];
    const avgLat = points.reduce((sum, item) => sum + item.latitude, 0) / points.length;
    const avgLng = points.reduce((sum, item) => sum + item.longitude, 0) / points.length;
    return [avgLat, avgLng];
  }, [points]);

  return (
    <MapContainer center={center} zoom={11} scrollWheelZoom={false} className="map-panel">
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {(points || []).map((point) => (
        <CircleMarker
          key={point.district_name}
          center={[point.latitude, point.longitude]}
          radius={Math.max(12, Math.min(26, point.avg_price_per_sqm / 12_000_000))}
          pathOptions={{ color: "#102542", fillColor: "#d4a017", fillOpacity: 0.72 }}
        >
          <Popup>
            <strong>{point.district_name}</strong>
            <br />
            {currencyMillions(point.avg_price_per_sqm)}/m²
            <br />
            {point.listing_count} listings
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}

function ChatVisualization({ visual }) {
  if (!visual) return null;

  if (visual.kind === "forecast") {
    return (
      <div className="chat-visual">
        <h4>{visual.title}</h4>
        <p>{visual.subtitle}</p>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={visual.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5ded4" />
            <XAxis dataKey="month" />
            <YAxis tickFormatter={currencyMillions} />
            <Tooltip formatter={(value) => currencyMillions(value)} />
            <Line type="monotone" dataKey="avg_price_per_sqm" stroke="#102542" strokeWidth={2.5} dot />
            <Line type="monotone" dataKey="prediction" stroke="#d4a017" strokeWidth={2.5} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (visual.kind === "scenario_projection") {
    return (
      <div className="chat-visual">
        <h4>{visual.title}</h4>
        <p>{visual.subtitle}</p>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={visual.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5ded4" />
            <XAxis dataKey="year" />
            <YAxis tickFormatter={currencyMillions} />
            <Tooltip formatter={(value) => currencyMillions(value)} />
            <Line type="monotone" dataKey="simulated_price" stroke="#8c1c13" strokeWidth={2.8} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (visual.kind === "district_compare") {
    return (
      <div className="chat-visual">
        <h4>{visual.title}</h4>
        <p>{visual.subtitle}</p>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={visual.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5ded4" />
            <XAxis dataKey="district_name" angle={-18} textAnchor="end" height={70} interval={0} />
            <YAxis tickFormatter={currencyMillions} />
            <Tooltip formatter={(value) => currencyMillions(value)} />
            <Bar dataKey="avg_price_per_sqm" fill="#102542" radius={[10, 10, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (visual.kind === "zscore_compare") {
    return (
      <div className="chat-visual">
        <h4>{visual.title}</h4>
        <p>{visual.subtitle}</p>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={visual.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5ded4" />
            <XAxis dataKey="district_name" angle={-18} textAnchor="end" height={70} interval={0} />
            <YAxis />
            <Tooltip />
            <Bar dataKey="z_score" fill="#d4a017" radius={[10, 10, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return null;
}

function App() {
  const [meta, setMeta] = useState(null);
  const [filters, setFilters] = useState({
    city: "TP.HCM",
    districts: [],
    propertyTypes: []
  });
  const [dashboard, setDashboard] = useState(null);
  const [scenarioPreset, setScenarioPreset] = useState("Ổn định");
  const [scenarioControls, setScenarioControls] = useState({
    district: "",
    interest_rate: 8,
    growth_rate: 7,
    supply_shock: 1,
    years: 5
  });
  const [scenarioData, setScenarioData] = useState(null);
  const [chatQuestion, setChatQuestion] = useState("");
  const [chatTone, setChatTone] = useState("advisor");
  const [chatState, setChatState] = useState({
    loading: false,
    answer: "",
    citations: [],
    evidence: [],
    visualizations: [],
    trace: null
  });
  const [opsMessage, setOpsMessage] = useState("");

  useEffect(() => {
    async function bootstrap() {
      const [{ data: metaPayload }, { data: healthPayload }] = await Promise.all([
        axios.get(`${API_BASE}/api/meta`),
        axios.get(`${API_BASE}/api/health`)
      ]);
      setMeta({ ...metaPayload, health: healthPayload });
      const defaultCity = metaPayload.cities?.[0] || "TP.HCM";
      const defaultDistricts = metaPayload.districts_by_city?.[defaultCity] || [];
      setFilters({
        city: defaultCity,
        districts: defaultDistricts.slice(0, 4),
        propertyTypes: metaPayload.property_types || []
      });
      setScenarioControls((prev) => ({
        ...prev,
        district: defaultDistricts[0] || ""
      }));
    }
    bootstrap().catch(console.error);
  }, []);

  useEffect(() => {
    if (!filters.city || !filters.districts.length) return;
    const params = new URLSearchParams();
    params.set("city", filters.city);
    filters.districts.forEach((district) => params.append("districts", district));
    filters.propertyTypes.forEach((type) => params.append("property_types", type));
    axios
      .get(`${API_BASE}/api/dashboard?${params.toString()}`)
      .then(({ data }) => {
        setDashboard(data);
        setScenarioControls((prev) => ({
          ...prev,
          district: data.forecast?.district || prev.district
        }));
      })
      .catch(console.error);
  }, [filters]);

  useEffect(() => {
    if (!meta?.scenario_presets?.[scenarioPreset]) return;
    const preset = meta.scenario_presets[scenarioPreset];
    setScenarioControls((prev) => ({
      ...prev,
      interest_rate: preset.interest_rate,
      growth_rate: preset.growth_rate,
      supply_shock: preset.supply_shock
    }));
  }, [scenarioPreset, meta]);

  useEffect(() => {
    if (!scenarioControls.district || !filters.city) return;
    axios
      .post(`${API_BASE}/api/forecast/scenario`, {
        city: filters.city,
        district: scenarioControls.district,
        interest_rate: scenarioControls.interest_rate,
        growth_rate: scenarioControls.growth_rate,
        supply_shock: scenarioControls.supply_shock,
        years: scenarioControls.years
      })
      .then(({ data }) => setScenarioData(data))
      .catch(console.error);
  }, [filters.city, scenarioControls]);

  const districtOptions = meta?.districts_by_city?.[filters.city] || [];
  const propertyOptions = meta?.property_types || [];

  const handleSeed = async (kind) => {
    const endpoint = kind === "sample" ? "load-sample" : "load-kaggle";
    try {
      const { data } = await axios.post(`${API_BASE}/api/data/${endpoint}`);
      setOpsMessage(data.message);
      const { data: metaPayload } = await axios.get(`${API_BASE}/api/meta`);
      setMeta((prev) => ({ ...metaPayload, health: prev?.health }));
      const nextCity = metaPayload.cities?.[0] || filters.city;
      const nextDistricts = metaPayload.districts_by_city?.[nextCity] || [];
      setFilters({
        city: nextCity,
        districts: nextDistricts.slice(0, 4),
        propertyTypes: metaPayload.property_types || []
      });
    } catch (error) {
      setOpsMessage(error.response?.data?.detail || "Failed to load data.");
    }
  };

  const handleReindex = async () => {
    try {
      const { data } = await axios.post(`${API_BASE}/api/rag/reindex`);
      setOpsMessage(data.enabled ? `Indexed ${data.chunks} chunks.` : data.reason);
    } catch (error) {
      setOpsMessage("Failed to build vector index.");
    }
  };

  const submitChat = async (event) => {
    event.preventDefault();
    if (!chatQuestion.trim()) return;
    setChatState((prev) => ({ ...prev, loading: true }));
    try {
      const { data } = await axios.post(`${API_BASE}/api/chat`, {
        question: chatQuestion,
        city: filters.city,
        districts: filters.districts,
        property_types: filters.propertyTypes,
        tone: chatTone
      });
      setChatState({ loading: false, ...data });
    } catch (error) {
      setChatState({
        loading: false,
        answer: error.response?.data?.detail || "Chat request failed.",
        citations: [],
        evidence: [],
        visualizations: [],
        trace: null
      });
    }
  };

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="eyebrow">PropertyVision</span>
          <h1>Urban Intelligence Console</h1>
          <p>RAG + pricing analytics + investor storytelling for Vietnam housing data.</p>
        </div>

        <div className="panel">
          <h3>Filters</h3>
          <label>
            City
            <select
              value={filters.city}
              onChange={(event) =>
                setFilters((prev) => ({
                  ...prev,
                  city: event.target.value,
                  districts: (meta?.districts_by_city?.[event.target.value] || []).slice(0, 4)
                }))
              }
            >
              {(meta?.cities || []).map((city) => (
                <option key={city}>{city}</option>
              ))}
            </select>
          </label>
          <label>
            Districts
            <select
              multiple
              value={filters.districts}
              onChange={(event) =>
                setFilters((prev) => ({
                  ...prev,
                  districts: Array.from(event.target.selectedOptions, (option) => option.value)
                }))
              }
            >
              {districtOptions.map((district) => (
                <option key={district}>{district}</option>
              ))}
            </select>
          </label>
          <label>
            Property Types
            <select
              multiple
              value={filters.propertyTypes}
              onChange={(event) =>
                setFilters((prev) => ({
                  ...prev,
                  propertyTypes: Array.from(event.target.selectedOptions, (option) => option.value)
                }))
              }
            >
              {propertyOptions.map((propertyType) => (
                <option key={propertyType}>{propertyType}</option>
              ))}
            </select>
          </label>
        </div>

        <div className="panel">
          <h3>Ops</h3>
          <button onClick={() => handleSeed("sample")}>Load Synthetic Data</button>
          <button onClick={() => handleSeed("kaggle")}>Import Kaggle CSV</button>
          <button onClick={handleReindex}>Build RAG Index</button>
          <p className="ops-note">{opsMessage || `RAG mode: ${meta?.health?.rag_mode || "loading..."}`}</p>
        </div>
      </aside>

      <main className="content">
        <section className="hero">
          <div className="hero-copy">
            <span className="eyebrow">Decision-grade visualization</span>
            <h2>Market pulse, forecast tension, and RAG-grounded investment narrative in one web experience.</h2>
          </div>
          <div className="stats-grid">
            <StatCard
              label="Listings"
              value={dashboard?.overview?.summary?.listing_count?.toLocaleString() || "-"}
              tone="gold"
            />
            <StatCard
              label="Districts"
              value={dashboard?.overview?.summary?.district_count || "-"}
              tone="navy"
            />
            <StatCard
              label="Avg price / m²"
              value={
                dashboard?.overview?.summary?.avg_price_per_sqm
                  ? currencyMillions(dashboard.overview.summary.avg_price_per_sqm)
                  : "-"
              }
              tone="slate"
            />
            <StatCard
              label="Market delta"
              value={`${dashboard?.overview?.summary?.market_delta_pct?.toFixed?.(1) || "0.0"}%`}
              tone="rose"
            />
          </div>
        </section>

        <section className="grid-two">
          <div className="card large-card">
            <SectionHeader
              title="Spatial Heat"
              subtitle="Bubble intensity reflects average price per sqm by district."
            />
            <DashboardMap points={dashboard?.overview?.district_heat || []} />
          </div>

          <div className="card">
            <SectionHeader
              title="Market Pulse"
              subtitle="Monthly average price signal across selected districts."
            />
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={dashboard?.overview?.trend || []}>
                <defs>
                  <linearGradient id="pulse" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#d4a017" stopOpacity={0.75} />
                    <stop offset="100%" stopColor="#102542" stopOpacity={0.08} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#d9d6d1" />
                <XAxis dataKey="month" stroke="#425466" />
                <YAxis stroke="#425466" tickFormatter={currencyMillions} />
                <Tooltip formatter={(value) => currencyMillions(value)} />
                <Area dataKey="avg_price_per_sqm" stroke="#102542" fill="url(#pulse)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="grid-two">
          <div className="card">
            <SectionHeader title="Segment Pricing" subtitle="Type-level price stratification for storytelling." />
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={dashboard?.overview?.top_segments || []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e7e0d5" />
                <XAxis type="number" tickFormatter={currencyMillions} />
                <YAxis dataKey="property_type_name" type="category" width={100} />
                <Tooltip formatter={(value) => currencyMillions(value)} />
                <Bar dataKey="avg_price_per_sqm" fill="#102542" radius={[0, 10, 10, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <SectionHeader title="District Signals" subtitle="Undervalued districts float upward in the scorecard." />
            <div className="score-list">
              {(dashboard?.scorecard || []).slice(0, 8).map((row) => (
                <div key={row.district_name} className="score-row">
                  <div>
                    <strong>{row.district_name}</strong>
                    <span>{row.signal}</span>
                  </div>
                  <div>
                    <b>{currencyMillions(row.avg_price_per_sqm)}</b>
                    <span>z {row.z_score.toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="grid-two">
          <div className="card">
            <SectionHeader
              title="Forecast Canvas"
              subtitle="Historical line, projected band, and scenario controls for demo narratives."
              action={
                <select value={scenarioPreset} onChange={(event) => setScenarioPreset(event.target.value)}>
                  {Object.keys(meta?.scenario_presets || {}).map((preset) => (
                    <option key={preset}>{preset}</option>
                  ))}
                </select>
              }
            />
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dashboard?.forecast?.series || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ddd5c7" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={currencyMillions} />
                <Tooltip formatter={(value) => currencyMillions(value)} />
                <Area type="monotone" dataKey="y_upper" stroke="transparent" fill="#d4a017" fillOpacity={0.12} />
                <Area type="monotone" dataKey="y_lower" stroke="transparent" fill="#ffffff" fillOpacity={1} />
                <Line type="monotone" dataKey="avg_price_per_sqm" stroke="#102542" strokeWidth={2.5} dot />
                <Line type="monotone" dataKey="prediction" stroke="#d4a017" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
            <div className="scenario-grid">
              <label>
                District
                <select
                  value={scenarioControls.district}
                  onChange={(event) => setScenarioControls((prev) => ({ ...prev, district: event.target.value }))}
                >
                  {districtOptions.map((district) => (
                    <option key={district}>{district}</option>
                  ))}
                </select>
              </label>
              <label>
                Interest rate
                <input
                  type="range"
                  min="5"
                  max="15"
                  step="0.5"
                  value={scenarioControls.interest_rate}
                  onChange={(event) =>
                    setScenarioControls((prev) => ({ ...prev, interest_rate: Number(event.target.value) }))
                  }
                />
                <span>{scenarioControls.interest_rate}%</span>
              </label>
              <label>
                Growth
                <input
                  type="range"
                  min="-5"
                  max="20"
                  step="0.5"
                  value={scenarioControls.growth_rate}
                  onChange={(event) =>
                    setScenarioControls((prev) => ({ ...prev, growth_rate: Number(event.target.value) }))
                  }
                />
                <span>{scenarioControls.growth_rate}%</span>
              </label>
              <label>
                Supply shock
                <input
                  type="range"
                  min="0.8"
                  max="1.2"
                  step="0.01"
                  value={scenarioControls.supply_shock}
                  onChange={(event) =>
                    setScenarioControls((prev) => ({ ...prev, supply_shock: Number(event.target.value) }))
                  }
                />
                <span>{scenarioControls.supply_shock.toFixed(2)}</span>
              </label>
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={scenarioData?.series || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5ded4" />
                <XAxis dataKey="year" />
                <YAxis tickFormatter={currencyMillions} />
                <Tooltip formatter={(value) => currencyMillions(value)} />
                <Line type="monotone" dataKey="simulated_price" stroke="#8c1c13" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="card chat-card">
            <SectionHeader
              title="RAG Analyst"
              subtitle="SQL-grounded chat plus planning context retrieval for district-level investor Q&A."
              action={
                <select value={chatTone} onChange={(event) => setChatTone(event.target.value)}>
                  <option value="advisor">Advisor</option>
                  <option value="analyst">Analyst</option>
                  <option value="pitch">Pitch</option>
                </select>
              }
            />
            <form onSubmit={submitChat} className="chat-form">
              <textarea
                value={chatQuestion}
                onChange={(event) => setChatQuestion(event.target.value)}
                placeholder="Ví dụ: Quận 7 có đáng đầu tư không và vì sao?"
              />
              <button type="submit" disabled={chatState.loading}>
                {chatState.loading ? "Thinking..." : "Ask RAG"}
              </button>
            </form>
            <div className="chat-answer">
              <p>{chatState.answer || "Ask a district-specific investment question to activate the RAG pipeline."}</p>
            </div>
            {chatState.citations?.length ? (
              <div className="citations">
                {chatState.citations.map((citation) => (
                  <span key={citation}>{citation}</span>
                ))}
              </div>
            ) : null}
            {chatState.evidence?.length ? (
              <div className="evidence-list">
                {chatState.evidence.map((item) => (
                  <div key={`${item.source}-${item.score}`} className="evidence-card">
                    <strong>{item.source}</strong>
                    <span>score {item.score}</span>
                    <p>{item.excerpt}</p>
                  </div>
                ))}
              </div>
            ) : null}
            {chatState.visualizations?.length ? (
              <div className="chat-visuals">
                {chatState.visualizations.map((visual, index) => (
                  <ChatVisualization key={`${visual.kind}-${index}`} visual={visual} />
                ))}
              </div>
            ) : null}
            {chatState.trace ? (
              <div className="trace-box">
                <strong>Trace</strong>
                <p>Intent: {chatState.trace.intent}</p>
                <p>Rewritten query: {chatState.trace.rewritten_query}</p>
                <p>Retrieved: {(chatState.trace.retrieved_docs || []).join(", ") || "None"}</p>
              </div>
            ) : null}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
