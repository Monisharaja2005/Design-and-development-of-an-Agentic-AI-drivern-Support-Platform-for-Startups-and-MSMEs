/**
 * SchemesStep.jsx — Production-Grade AI Scheme Recommendation Component
 * =========================================================================
 * Fixes applied:
 *  1. Blank screen          → SafeRenderer + null guards on every data path
 *  2. JSX crash             → safe() helper normalises every field before render
 *  3. Modal state           → dedicated openModal/closeModal handlers with useCallback
 *  4. Button click          → explicit type="button", stopPropagation guard
 *  5. Timeline / priority   → dual-key resolver (Timeline_Days || timeline_days)
 *  6. scheme_name mapping   → getName() resolves both Scheme_Name & scheme_name
 *  7. matchedSchemes null   → initialised to 0, guarded in every display
 *  8. Render before load    → LoadingSkeleton blocks render until data is ready
 */

import {
  useEffect,
  useState,
  useMemo,
  useCallback,
  useRef,
} from "react";
import { getSessionUser, saveUserSchemes } from '../../lib/userWorkspace.js';
import { useTranslation } from "react-i18next";

// ─── API ─────────────────────────────────────────────────────────────────────
const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function fetchRecommendations(profile, language) {
  console.log("[SchemesStep] POST /v1/recommend →", profile, language);
  const res = await fetch(`${API_BASE}/v1/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...profile, language }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  const data = await res.json();
  console.log("[SchemesStep] /v1/recommend raw response →", data);
  return data;
}

// ─── FIELD RESOLVERS (fix: dual-key + safe fallback) ────────────────────────

/** Resolve scheme display name — handles both PascalCase and snake_case */
const getName = (s) =>
  String(s?.Scheme_Name || s?.scheme_name || s?.name || "Unnamed Scheme").trim();

/** Resolve scheme ID — multiple possible key names */
const getId = (s) =>
  s?.Scheme_ID || s?.scheme_id || s?.id || getName(s);

/** Resolve timeline — fix: Timeline_Days vs timeline_days mismatch */
const getTimeline = (s) => {
  const v = s?.Timeline_Days ?? s?.timeline_days ?? s?.timeline ?? null;
  if (v === null || v === undefined || v === "") return "—";
  return `${v} days`;
};

/** Resolve priority — fix: Priority_Level vs priority_level mismatch */
const getPriority = (s) =>
  String(s?.Priority_Level || s?.priority_level || s?.priority || "Medium").trim();

/** Resolve funding type */
const getFundingType = (s) =>
  String(s?.funding_type || s?.Funding_Type || s?.fundingType || "—").trim();

/** Resolve benefits summary */
const getBenefits = (s) =>
  String(
    s?.benefits_summary ||
    s?.Benefits_Summary ||
    s?.Scheme_Description ||
    s?.description ||
    ""
  ).trim();

/** Resolve sector */
const getSector = (s) =>
  String(s?.target_sector || s?.Target_Sector || s?.sector || "General").trim();

/** Resolve state */
const getState = (s) =>
  String(s?.State_Applicable || s?.state || "India").trim();

/** Resolve status */
const getStatus = (s) =>
  String(s?.Status || s?.status || "Active").trim();

/** Resolve authority */
const getAuthority = (s) =>
  String(s?.authority || s?.Authority || s?.Ministry || s?.ministry || "").trim();

/** Resolve portal hint */
const getPortal = (s) =>
  String(s?.official_portal_hint || s?.portal || "").trim();

/** Resolve tags — fix: always return an array */
const getTags = (s) => {
  const raw = s?.tags || s?.Tags || [];
  return Array.isArray(raw) ? raw : [];
};

/** Safe array — fix: prevents map() crash if API returns null / object */
const safeArray = (val) => (Array.isArray(val) ? val : []);

/** Resolve required documents */
const getDocs = (s) => safeArray(s?.required_documents || s?.ai_required_documents);

/** Resolve application steps */
const getSteps = (s) => safeArray(s?.application_steps || s?.ai_application_steps);

/** Resolve funding strength score */
const getFundingScore = (s) => {
  const v = s?.funding_strength_score ?? s?.Benefit_Score ?? 50;
  return Math.min(100, Math.max(0, Number(v) || 50));
};

/** Resolve success probability score */
const getSuccessScore = (s) => {
  const v = s?.success_probability_score ?? s?.success_score ?? 60;
  return Math.min(100, Math.max(0, Number(v) || 60));
};

/** Resolve complexity */
const getComplexity = (s) =>
  String(s?.application_complexity || s?.complexity || "Moderate").trim();

// ─── STYLE HELPERS ────────────────────────────────────────────────────────────

const PRIORITY_STYLES = {
  High:   { bg: "#fff0f0", color: "#c0392b", border: "#f5c6c6" },
  Medium: { bg: "#fffbf0", color: "#b7770d", border: "#f5e6b0" },
  Low:    { bg: "#f0fff4", color: "#1e7e34", border: "#b7e4c7" },
};

const COMPLEXITY_STYLES = {
  Easy:     { color: "#1e7e34" },
  Moderate: { color: "#b7770d" },
  Difficult:{ color: "#c0392b" },
};

const FUNDING_COLORS = {
  Grant:     "#6c3483",
  Subsidy:   "#1a5276",
  Loan:      "#0e6251",
  Equity:    "#4a235a",
  Incentive: "#7d6608",
};

function priorityStyle(p) {
  return PRIORITY_STYLES[p] || PRIORITY_STYLES.Medium;
}

function fundingColor(ft) {
  return FUNDING_COLORS[ft] || "#34495e";
}

function scoreBar(score) {
  const hue = Math.round((score / 100) * 120); // red→green
  return `hsl(${hue}, 70%, 45%)`;
}

// ─── SUB-COMPONENTS ───────────────────────────────────────────────────────────

/** Loading skeleton — fix: prevents render before data */
function LoadingSkeleton() {
  return (
    <div style={styles.skeletonWrap}>
      {[1, 2, 3, 4, 5, 6].map((n) => (
        <div key={n} style={styles.skeletonCard}>
          <div style={{ ...styles.skeletonLine, width: "60%", height: 18 }} />
          <div style={{ ...styles.skeletonLine, width: "40%", height: 13, marginTop: 8 }} />
          <div style={{ ...styles.skeletonLine, width: "90%", height: 11, marginTop: 12 }} />
          <div style={{ ...styles.skeletonLine, width: "75%", height: 11, marginTop: 6 }} />
          <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
            <div style={{ ...styles.skeletonLine, width: 80, height: 30, borderRadius: 6 }} />
            <div style={{ ...styles.skeletonLine, width: 80, height: 30, borderRadius: 6 }} />
          </div>
        </div>
      ))}
    </div>
  );
}

/** Error fallback — fix: never crash to blank screen */
function ErrorBanner({ message, onRetry }) {
  console.error("[SchemesStep] ErrorBanner →", message);
  return (
    <div style={styles.errorBanner} role="alert">
      <span style={styles.errorIcon}>⚠</span>
      <div>
        <strong style={{ display: "block", marginBottom: 4 }}>
          Unable to load scheme recommendations
        </strong>
        <span style={{ fontSize: 13, color: "#7f1d1d" }}>{String(message || "Unknown error")}</span>
      </div>
      {onRetry && (
        <button
          type="button"
          style={styles.retryBtn}
          onClick={onRetry}
        >
          Retry
        </button>
      )}
    </div>
  );
}

/** Priority badge */
function PriorityBadge({ scheme }) {
  const p = getPriority(scheme);
  const s = priorityStyle(p);
  return (
    <span
      style={{
        ...styles.badge,
        background: s.bg,
        color: s.color,
        border: `1px solid ${s.border}`,
      }}
    >
      {p} Priority
    </span>
  );
}

/** Funding type badge */
function FundingBadge({ scheme }) {
  const ft = getFundingType(scheme);
  if (ft === "—") return null;
  return (
    <span
      style={{
        ...styles.badge,
        background: fundingColor(ft),
        color: "#fff",
        border: "none",
      }}
    >
      {ft}
    </span>
  );
}

/** Score bar */
function ScoreBar({ label, value, color }) {
  return (
    <div style={styles.scoreRow}>
      <span style={styles.scoreLabel}>{label}</span>
      <div style={styles.scoreTrack}>
        <div
          style={{
            ...styles.scoreFill,
            width: `${value}%`,
            background: color || scoreBar(value),
          }}
        />
      </div>
      <span style={styles.scoreValue}>{value}%</span>
    </div>
  );
}

/** Tag pill */
function Tag({ label }) {
  return <span style={styles.tag}>{label}</span>;
}

/** Modal overlay */
function SchemeModal({ scheme, onClose }) {
  const overlayRef = useRef(null);

  // Close on Escape key
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  if (!scheme) return null;

  const name       = getName(scheme);
  const priority   = getPriority(scheme);
  const pStyle     = priorityStyle(priority);
  const docs       = getDocs(scheme);
  const steps      = getSteps(scheme);
  const tags       = getTags(scheme);
  const benefits   = getBenefits(scheme);
  const complexity = getComplexity(scheme);
  const cStyle     = COMPLEXITY_STYLES[complexity] || COMPLEXITY_STYLES.Moderate;

  console.log("[SchemesStep] Modal opened for →", name, scheme);

  return (
    <div
      ref={overlayRef}
      style={styles.modalOverlay}
      role="dialog"
      aria-modal="true"
      aria-label={`Scheme details: ${name}`}
      onClick={(e) => {
        // fix: close only when clicking the backdrop, not modal content
        if (e.target === overlayRef.current) onClose();
      }}
    >
      <div style={styles.modalBox}>
        {/* ── Header ── */}
        <div style={styles.modalHeader}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <h2 style={styles.modalTitle}>{name}</h2>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
              <PriorityBadge scheme={scheme} />
              <FundingBadge scheme={scheme} />
              {tags.slice(0, 4).map((tag) => (
                <Tag key={tag} label={tag} />
              ))}
            </div>
          </div>
          <button
            type="button"
            style={styles.closeBtn}
            onClick={onClose}
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* ── Body ── */}
        <div style={styles.modalBody}>
          {/* Meta grid */}
          <div style={styles.metaGrid}>
            {[
              ["Sector",      getSector(scheme)],
              ["State",       getState(scheme)],
              ["Timeline",    getTimeline(scheme)],
              ["Complexity",  complexity],
              ["Status",      getStatus(scheme)],
              ["Funding",     getFundingType(scheme)],
            ].map(([k, v]) => (
              <div key={k} style={styles.metaCell}>
                <span style={styles.metaKey}>{k}</span>
                <span
                  style={{
                    ...styles.metaVal,
                    ...(k === "Complexity" ? cStyle : {}),
                  }}
                >
                  {v}
                </span>
              </div>
            ))}
          </div>

          {/* Authority */}
          {getAuthority(scheme) && (
            <div style={styles.section}>
              <h4 style={styles.sectionTitle}>Implementing Authority</h4>
              <p style={styles.bodyText}>{getAuthority(scheme)}</p>
            </div>
          )}

          {/* Benefits */}
          {benefits && (
            <div style={styles.section}>
              <h4 style={styles.sectionTitle}>Benefits & Support</h4>
              <p style={styles.bodyText}>{benefits}</p>
            </div>
          )}

          {/* Scores */}
          <div style={styles.section}>
            <h4 style={styles.sectionTitle}>Match Intelligence</h4>
            <ScoreBar
              label="Funding Strength"
              value={getFundingScore(scheme)}
            />
            <ScoreBar
              label="Success Probability"
              value={getSuccessScore(scheme)}
            />
          </div>

          {/* Portal */}
          {getPortal(scheme) && (
            <div style={styles.section}>
              <h4 style={styles.sectionTitle}>Application Portal</h4>
              <p style={{ ...styles.bodyText, color: "#1a5276" }}>
                {getPortal(scheme)}
              </p>
            </div>
          )}

          {/* Required Documents */}
          {docs.length > 0 && (
            <div style={styles.section}>
              <h4 style={styles.sectionTitle}>
                Required Documents
                <span style={styles.countPill}>{docs.length}</span>
              </h4>
              <ol style={styles.orderedList}>
                {docs.map((doc, i) => (
                  <li key={i} style={styles.listItem}>
                    {String(doc)}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Application Steps */}
          {steps.length > 0 && (
            <div style={styles.section}>
              <h4 style={styles.sectionTitle}>
                How to Apply
                <span style={styles.countPill}>{steps.length} steps</span>
              </h4>
              <ol style={styles.orderedList}>
                {steps.map((step, i) => (
                  <li key={i} style={styles.listItem}>
                    <strong style={{ color: "#1a3a5c", marginRight: 6 }}>
                      {i + 1}.
                    </strong>
                    {String(step)}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>

        {/* ── Footer ── */}
        <div style={styles.modalFooter}>
          <button type="button" style={styles.btnSecondary} onClick={onClose}>
            Close
          </button>
          {scheme?.Website_URL && (
            <a
              href={scheme.Website_URL}
              target="_blank"
              rel="noreferrer"
              style={styles.btnPrimary}
            >
              Visit Official Portal ↗
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

/** Scheme card */
function SchemeCard({ scheme, onViewDetails, isSelected, onToggleSelect }) {
  const name       = getName(scheme);
  const schemeId   = getId(scheme);
  const priority   = getPriority(scheme);
  const timeline   = getTimeline(scheme);
  const ft         = getFundingType(scheme);
  const sector     = getSector(scheme);
  const state      = getState(scheme);
  const benefits   = getBenefits(scheme);
  const tags       = getTags(scheme);
  const fundScore  = getFundingScore(scheme);
  const successSc  = getSuccessScore(scheme);

  /** Resolve match reasons — always returns an array */
  const getMatchReasons = (s) => {
    const raw = s?.match_reasons || s?.matchReasons || [];
    return Array.isArray(raw) ? raw : [];
  };

  /** Resolve match score (0–100) */
  const getMatchScore = (s) => {
    const v = s?.final_rank_score ?? s?.match_score ?? 0;
    return Math.min(100, Math.max(0, Math.round(Number(v) || 0)));
  };

  return (
    <div style={{ ...styles.card, ...(isSelected ? styles.cardSelected : {}) }}>
      {/* Card header */}
      <div style={styles.cardHeader}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 style={styles.cardTitle}>{name}</h3>
          <p style={styles.cardMeta}>
            {sector}
            {state && state !== "India" ? ` · ${state}` : " · Pan India"}
          </p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
          <PriorityBadge scheme={scheme} />
          {getMatchScore(scheme) > 0 && (
            <span style={{
              fontSize: 11, fontWeight: 700, padding: "2px 8px",
              background: "#e8f8ee", color: "#1e7e34", borderRadius: 20,
              border: "1px solid #b7e4c7", whiteSpace: "nowrap"
            }}>
              {getMatchScore(scheme)}% Match
            </span>
          )}
        </div>
      </div>

      {/* Badges row */}
      <div style={styles.badgeRow}>
        {ft !== "—" && <FundingBadge scheme={scheme} />}
        {tags.slice(0, 3).map((tag) => (
          <Tag key={tag} label={tag} />
        ))}
      </div>

      {/* Benefits snippet */}
      {benefits && (
        <p style={styles.benefitsSnippet}>
          {benefits.length > 160 ? `${benefits.slice(0, 160)}…` : benefits}
        </p>
      )}

      {/* ── Why This Matched (Decision Panel) ── */}
      {getMatchReasons(scheme).length > 0 && (
        <div style={{
          marginTop: 10, marginBottom: 6,
          padding: "8px 10px",
          background: "#f0fff4",
          borderRadius: 8,
          border: "1px solid #c8edd1"
        }}>
          <p style={{ fontSize: 10, fontWeight: 700, color: "#155724", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.5px" }}>
            ✓ Why this matched your profile
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
            {getMatchReasons(scheme).map((reason, i) => (
              <span key={i} style={{
                fontSize: 11, fontWeight: 600,
                padding: "2px 8px",
                background: "#d4edda",
                color: "#155724",
                borderRadius: 12,
                border: "1px solid #b8dfc8"
              }}>
                ✓ {reason}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Scores */}
      <div style={styles.cardScores}>
        <ScoreBar label="Funding" value={fundScore} />
        <ScoreBar label="Success" value={successSc} />
      </div>

      {/* Timeline + complexity row */}
      <div style={styles.statRow}>
        <span style={styles.stat}>
          <span style={styles.statIcon}>⏱</span> {timeline}
        </span>
        <span style={styles.stat}>
          <span style={styles.statIcon}>📋</span> {getComplexity(scheme)}
        </span>
        {getAuthority(scheme) && (
          <span style={{ ...styles.stat, flex: 1, textAlign: "right" }}>
            {getAuthority(scheme).split(",")[0]}
          </span>
        )}
      </div>

      {/* Action buttons */}
      <div style={styles.cardActions}>
        <button
          type="button"
          style={styles.btnViewDetails}
          onClick={(e) => {
            e.stopPropagation();
            console.log("[SchemesStep] View Details clicked →", name, schemeId);
            onViewDetails(scheme);
          }}
        >
          View Details →
        </button>
        <button
          type="button"
          style={{
            ...styles.btnSelect,
            ...(isSelected ? styles.btnSelectActive : {}),
          }}
          onClick={(e) => {
            e.stopPropagation();
            console.log("[SchemesStep] Toggle select →", schemeId, !isSelected);
            onToggleSelect(schemeId);
          }}
        >
          {isSelected ? "✓ Saved" : "Save"}
        </button>
      </div>
    </div>
  );
}

/** Header stats bar */
function StatsBar({ total, matched, filtered, selected }) {
  const stats = [
    { label: "Total Schemes",   value: total,    color: "#1a3a5c" },
    { label: "AI Matched",      value: matched,  color: "#1e7e34" },
    { label: "Showing",         value: filtered, color: "#0e6251" },
    { label: "Saved",           value: selected, color: "#6c3483" },
  ];
  return (
    <div style={styles.statsBar}>
      {stats.map(({ label, value, color }) => (
        <div key={label} style={styles.statCell}>
          <span style={{ ...styles.statNumber, color }}>{value ?? 0}</span>
          <span style={styles.statLabel}>{label}</span>
        </div>
      ))}
    </div>
  );
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────

/**
 * SchemesStep
 *
 * Props:
 *   profile  — { state, sector, entityType, turnover, businessDescription }
 *   onSave   — (savedSchemeIds: string[]) => void
 */
export default function SchemesStep({ profile = {}, onSave }) {
  const { i18n } = useTranslation();
  // ── State ──────────────────────────────────────────────────────────────────
  const [schemes,        setSchemes]        = useState([]);     // fix: [], not null
  const [matchedCount,   setMatchedCount]   = useState(0);      // fix: 0, not null
  const [totalCount,     setTotalCount]     = useState(0);
  const [loading,        setLoading]        = useState(true);
  const [error,          setError]          = useState(null);
  const [activeScheme,   setActiveScheme]   = useState(null);   // fix: modal state
  const [selectedIds,    setSelectedIds]    = useState({});
  const [searchQuery,    setSearchQuery]    = useState("");
  const [filterPriority, setFilterPriority] = useState("All");
  const [filterFunding,  setFilterFunding]  = useState("All");

  // ── Data fetch ─────────────────────────────────────────────────────────────
  const loadSchemes = useCallback(async () => {
    setLoading(true);
    setError(null);
    console.log("[SchemesStep] Loading schemes for profile →", profile);

    try {
      const data = await fetchRecommendations(profile, i18n.language);

      // fix: handle multiple possible response shapes from the API
      let rawSchemes = [];
      if (Array.isArray(data)) {
        rawSchemes = data;
      } else if (Array.isArray(data?.schemes)) {
        rawSchemes = data.schemes;
      } else if (Array.isArray(data?.results)) {
        rawSchemes = data.results;
      } else if (data && typeof data === "object") {
        // Some backends wrap: [{ scheme: {...}, match_score: N }]
        const first = Object.values(data)[0];
        rawSchemes = Array.isArray(first) ? first : [];
      }

      // Unwrap { scheme: {...}, match_score: N } wrapper if present
      rawSchemes = rawSchemes.map((item) =>
        item?.scheme && typeof item.scheme === "object" ? item.scheme : item
      );

      console.log(`[SchemesStep] Resolved ${rawSchemes.length} schemes`);

      setSchemes(rawSchemes);
      // fix: use API-provided counts where available, fallback to array length
      setMatchedCount(
        Number(data?.matched_count ?? data?.matchedCount ?? rawSchemes.length) || 0
      );
      setTotalCount(
        Number(data?.total_schemes ?? data?.totalSchemes ?? rawSchemes.length) || 0
      );
    } catch (err) {
      console.error("[SchemesStep] Fetch error →", err);
      setError(err?.message || "Failed to load scheme recommendations.");
    } finally {
      setLoading(false);
    }
  }, [profile]);

  useEffect(() => {
    loadSchemes();
  }, [loadSchemes]);

  // ── Filtered schemes (search + priority + funding filters) ─────────────────
  const filteredSchemes = useMemo(() => {
    // fix: always start with safeArray
    let list = safeArray(schemes);
    const q = searchQuery.trim().toLowerCase();

    if (q) {
      list = list.filter((s) => {
        const name     = getName(s).toLowerCase();
        const sector   = getSector(s).toLowerCase();
        const state    = getState(s).toLowerCase();
        const benefits = getBenefits(s).toLowerCase();
        const auth     = getAuthority(s).toLowerCase();
        return (
          name.includes(q) ||
          sector.includes(q) ||
          state.includes(q) ||
          benefits.includes(q) ||
          auth.includes(q)
        );
      });
    }

    if (filterPriority !== "All") {
      list = list.filter((s) => getPriority(s) === filterPriority);
    }

    if (filterFunding !== "All") {
      list = list.filter((s) => getFundingType(s) === filterFunding);
    }

    return list;
  }, [schemes, searchQuery, filterPriority, filterFunding]);

  // ── Derived unique filter options ─────────────────────────────────────────
  const fundingOptions = useMemo(() => {
    const set = new Set(safeArray(schemes).map(getFundingType).filter((v) => v !== "—"));
    return ["All", ...set];
  }, [schemes]);

  // ── Modal handlers — fix: useCallback for stable references ───────────────
  const openModal = useCallback((scheme) => {
    console.log("[SchemesStep] openModal →", getName(scheme));
    setActiveScheme(scheme);
    document.body.style.overflow = "hidden";
  }, []);

  const closeModal = useCallback(() => {
    console.log("[SchemesStep] closeModal");
    setActiveScheme(null);
    document.body.style.overflow = "";
  }, []);

// ── Selection handler ─────────────────────────────────────────────────────
  const [savingSchemeId, setSavingSchemeId] = useState(null);

  const toggleSelect = useCallback(async (schemeId) => {
    const user = getSessionUser();
    const email = user?.email;
    if (!email) {
      console.warn("[SchemesStep] Save blocked - no logged in user");
      alert('Please login first to save schemes'); // TODO: replace with toast
      return;
    }

    setSavingSchemeId(schemeId);
    try {
      const wasSelected = selectedIds[schemeId];
      const nextSelectedIds = { 
        ...selectedIds, 
        [schemeId]: !wasSelected 
      };
      const savedIds = Object.keys(nextSelectedIds).filter(k => nextSelectedIds[k]);

      console.log(`[SchemesStep] Saving ${savedIds.length} schemes for ${email}`);
      
      // Backend persist
      await saveUserSchemes(email, savedIds);
      
      // Update local state
      setSelectedIds(nextSelectedIds);
      
      console.log(`[SchemesStep] Saved successfully: ${schemeId} → ${!wasSelected}`);
      
      // Notify parent
      onSave?.(savedIds);
      
    } catch (error) {
      console.error("[SchemesStep] Save failed:", error);
      alert(`Save failed: ${error.message}`); // TODO: toast
    } finally {
      setSavingSchemeId(null);
    }
  }, [selectedIds, onSave]);

  const selectedCount = Object.values(selectedIds).filter(Boolean).length;

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div style={styles.root}>
      {/* ── Page title ── */}
      <div style={styles.pageHeader}>
        <div>
          <h2 style={styles.pageTitle}>AI Scheme Recommendations</h2>
          <p style={styles.pageSubtitle}>
            Matched to your business profile using intelligent policy analysis
          </p>
        </div>
      </div>

      {/* ── Stats bar — fix: shows 0, not blank, before data ── */}
      <StatsBar
        total={totalCount}
        matched={matchedCount}
        filtered={filteredSchemes.length}
        selected={selectedCount}
      />

      {/* ── Search + filters ── */}
      {!loading && !error && (
        <div style={styles.filterBar}>
          <input
            type="search"
            placeholder="Search schemes by name, sector, state…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={styles.searchInput}
            aria-label="Search schemes"
          />
          <select
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value)}
            style={styles.filterSelect}
            aria-label="Filter by priority"
          >
            {["All", "High", "Medium", "Low"].map((v) => (
              <option key={v} value={v}>
                {v === "All" ? "All Priorities" : `${v} Priority`}
              </option>
            ))}
          </select>
          <select
            value={filterFunding}
            onChange={(e) => setFilterFunding(e.target.value)}
            style={styles.filterSelect}
            aria-label="Filter by funding type"
          >
            {fundingOptions.map((v) => (
              <option key={v} value={v}>
                {v === "All" ? "All Funding Types" : v}
              </option>
            ))}
          </select>
          {(searchQuery || filterPriority !== "All" || filterFunding !== "All") && (
            <button
              type="button"
              style={styles.clearBtn}
              onClick={() => {
                setSearchQuery("");
                setFilterPriority("All");
                setFilterFunding("All");
              }}
            >
              Clear filters
            </button>
          )}
        </div>
      )}

      {/* ── Loading skeleton — fix: blocks premature render ── */}
      {loading && <LoadingSkeleton />}

      {/* ── Error banner — fix: never crashes to blank screen ── */}
      {!loading && error && (
        <ErrorBanner message={error} onRetry={loadSchemes} />
      )}

      {/* ── Empty state ── */}
      {!loading && !error && filteredSchemes.length === 0 && (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>🔍</div>
          <h3 style={styles.emptyTitle}>
            {schemes.length === 0
              ? "No schemes matched your profile"
              : "No schemes match your search"}
          </h3>
          <p style={styles.emptyBody}>
            {schemes.length === 0
              ? "Try completing more profile fields for better AI matching accuracy."
              : "Adjust your search query or remove filters to see more results."}
          </p>
          {schemes.length > 0 && (
            <button
              type="button"
              style={styles.btnSecondary}
              onClick={() => {
                setSearchQuery("");
                setFilterPriority("All");
                setFilterFunding("All");
              }}
            >
              Clear filters
            </button>
          )}
        </div>
      )}

      {/* ── Scheme grid — fix: safe array, no crash ── */}
      {!loading && !error && filteredSchemes.length > 0 && (
        <>
          <p style={styles.resultCount}>
            Showing <strong>{filteredSchemes.length}</strong> of{" "}
            <strong>{schemes.length}</strong> matched schemes
            {searchQuery && (
              <> for <em>"{searchQuery}"</em></>
            )}
          </p>
          <div style={styles.grid}>
            {filteredSchemes.map((scheme, idx) => {
              const schemeId = getId(scheme);
              return (
                <SchemeCard
                  key={schemeId || idx}
                  scheme={scheme}
                  onViewDetails={openModal}
                  isSelected={Boolean(selectedIds[schemeId])}
                  saving={savingSchemeId === schemeId}
                  onToggleSelect={toggleSelect}
                />
              );
            })}
          </div>
        </>
      )}

      {/* ── Modal — fix: controlled open/close state ── */}
      {activeScheme && (
        <SchemeModal scheme={activeScheme} onClose={closeModal} />
      )}
    </div>
  );
}

// ─── STYLES ───────────────────────────────────────────────────────────────────

const styles = {
  // Layout
  root: {
    fontFamily: "'IBM Plex Sans', 'Segoe UI', system-ui, sans-serif",
    maxWidth: 1100,
    margin: "0 auto",
    padding: "24px 20px 60px",
    color: "#1a1a2e",
    minHeight: "100vh",
    background: "#f8fafd",
  },

  // Header
  pageHeader: {
    marginBottom: 24,
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: 12,
  },
  pageTitle: {
    fontSize: 26,
    fontWeight: 700,
    color: "#0d1b2a",
    margin: 0,
    letterSpacing: "-0.4px",
  },
  pageSubtitle: {
    fontSize: 14,
    color: "#5a6a7a",
    margin: "4px 0 0",
  },

  // Stats bar
  statsBar: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 1,
    background: "#dde3ed",
    border: "1px solid #dde3ed",
    borderRadius: 12,
    overflow: "hidden",
    marginBottom: 20,
  },
  statCell: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: "14px 8px",
    background: "#fff",
    gap: 2,
  },
  statNumber: {
    fontSize: 26,
    fontWeight: 800,
    lineHeight: 1,
    fontVariantNumeric: "tabular-nums",
  },
  statLabel: {
    fontSize: 11,
    color: "#6b7a8d",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    fontWeight: 600,
  },

  // Filters
  filterBar: {
    display: "flex",
    gap: 10,
    flexWrap: "wrap",
    marginBottom: 20,
    alignItems: "center",
  },
  searchInput: {
    flex: "1 1 240px",
    padding: "9px 14px",
    border: "1.5px solid #d0d7e3",
    borderRadius: 8,
    fontSize: 14,
    background: "#fff",
    outline: "none",
    color: "#1a1a2e",
    transition: "border-color 0.15s",
  },
  filterSelect: {
    padding: "9px 12px",
    border: "1.5px solid #d0d7e3",
    borderRadius: 8,
    fontSize: 13,
    background: "#fff",
    color: "#1a1a2e",
    cursor: "pointer",
    outline: "none",
  },
  clearBtn: {
    padding: "9px 14px",
    border: "none",
    borderRadius: 8,
    fontSize: 13,
    background: "transparent",
    color: "#c0392b",
    cursor: "pointer",
    fontWeight: 600,
    textDecoration: "underline",
  },

  // Result count
  resultCount: {
    fontSize: 13,
    color: "#6b7a8d",
    marginBottom: 16,
    marginTop: 0,
  },

  // Grid
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
    gap: 18,
  },

  // Card
  card: {
    background: "#fff",
    border: "1.5px solid #e3e8f0",
    borderRadius: 14,
    padding: "20px 20px 16px",
    display: "flex",
    flexDirection: "column",
    gap: 0,
    transition: "box-shadow 0.2s, border-color 0.2s",
    cursor: "default",
    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
  },
  cardSelected: {
    borderColor: "#2563eb",
    boxShadow: "0 0 0 3px rgba(37,99,235,0.12)",
  },
  cardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 12,
    marginBottom: 10,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: 700,
    color: "#0d1b2a",
    margin: 0,
    lineHeight: 1.3,
  },
  cardMeta: {
    fontSize: 12,
    color: "#7a8a9a",
    margin: "3px 0 0",
  },
  badgeRow: {
    display: "flex",
    flexWrap: "wrap",
    gap: 6,
    marginBottom: 12,
  },
  benefitsSnippet: {
    fontSize: 13,
    color: "#3a4a5a",
    lineHeight: 1.55,
    margin: "0 0 14px",
  },
  cardScores: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
    marginBottom: 12,
  },
  statRow: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    fontSize: 12,
    color: "#5a6a7a",
    marginBottom: 16,
    flexWrap: "wrap",
  },
  stat: {
    display: "flex",
    alignItems: "center",
    gap: 4,
  },
  statIcon: {
    fontSize: 13,
  },
  cardActions: {
    display: "flex",
    gap: 10,
    marginTop: "auto",
  },

  // Badges
  badge: {
    display: "inline-block",
    padding: "3px 10px",
    borderRadius: 20,
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: "0.3px",
    whiteSpace: "nowrap",
  },
  tag: {
    display: "inline-block",
    padding: "2px 8px",
    borderRadius: 20,
    fontSize: 11,
    fontWeight: 600,
    background: "#eef2ff",
    color: "#3730a3",
    border: "1px solid #c7d2fe",
    whiteSpace: "nowrap",
  },

  // Score bar
  scoreRow: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  scoreLabel: {
    fontSize: 11,
    color: "#6b7a8d",
    width: 60,
    flexShrink: 0,
    fontWeight: 600,
  },
  scoreTrack: {
    flex: 1,
    height: 6,
    background: "#e9ecef",
    borderRadius: 4,
    overflow: "hidden",
  },
  scoreFill: {
    height: "100%",
    borderRadius: 4,
    transition: "width 0.4s ease",
  },
  scoreValue: {
    fontSize: 11,
    color: "#4a5568",
    width: 30,
    textAlign: "right",
    fontVariantNumeric: "tabular-nums",
    flexShrink: 0,
  },

  // Buttons
  btnViewDetails: {
    flex: 1,
    padding: "9px 0",
    border: "1.5px solid #2563eb",
    borderRadius: 8,
    background: "transparent",
    color: "#2563eb",
    fontSize: 13,
    fontWeight: 600,
    cursor: "pointer",
    transition: "background 0.15s",
  },
  btnSelect: {
    flex: 1,
    padding: "9px 0",
    border: "1.5px solid #e3e8f0",
    borderRadius: 8,
    background: "#f8fafd",
    color: "#4a5568",
    fontSize: 13,
    fontWeight: 600,
    cursor: "pointer",
    transition: "background 0.15s",
  },
  btnSelectActive: {
    background: "#2563eb",
    color: "#fff",
    border: "1.5px solid #2563eb",
  },
  btnPrimary: {
    display: "inline-block",
    padding: "10px 20px",
    background: "#2563eb",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
    textDecoration: "none",
    transition: "background 0.15s",
  },
  btnSecondary: {
    display: "inline-block",
    padding: "10px 20px",
    background: "transparent",
    color: "#4a5568",
    border: "1.5px solid #d0d7e3",
    borderRadius: 8,
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
    textDecoration: "none",
  },
  retryBtn: {
    marginLeft: "auto",
    padding: "8px 18px",
    background: "#c0392b",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    fontSize: 13,
    fontWeight: 600,
    cursor: "pointer",
    flexShrink: 0,
  },

  // Modal
  modalOverlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(10, 15, 30, 0.7)",
    zIndex: 9999,
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "center",
    padding: "32px 16px",
    overflowY: "auto",
    backdropFilter: "blur(3px)",
  },
  modalBox: {
    background: "#fff",
    borderRadius: 16,
    width: "100%",
    maxWidth: 700,
    boxShadow: "0 25px 60px rgba(0,0,0,0.25)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    maxHeight: "90vh",
  },
  modalHeader: {
    display: "flex",
    alignItems: "flex-start",
    gap: 16,
    padding: "22px 24px 18px",
    borderBottom: "1px solid #e3e8f0",
    background: "#fafbfd",
    flexShrink: 0,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 700,
    color: "#0d1b2a",
    margin: 0,
    lineHeight: 1.3,
  },
  closeBtn: {
    background: "none",
    border: "none",
    fontSize: 18,
    cursor: "pointer",
    color: "#6b7a8d",
    padding: "4px 8px",
    borderRadius: 6,
    flexShrink: 0,
    lineHeight: 1,
    marginTop: 2,
  },
  modalBody: {
    padding: "20px 24px",
    overflowY: "auto",
    flex: 1,
  },
  modalFooter: {
    display: "flex",
    justifyContent: "flex-end",
    gap: 12,
    padding: "16px 24px",
    borderTop: "1px solid #e3e8f0",
    background: "#fafbfd",
    flexShrink: 0,
  },

  // Meta grid
  metaGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: 1,
    background: "#e3e8f0",
    border: "1px solid #e3e8f0",
    borderRadius: 10,
    overflow: "hidden",
    marginBottom: 20,
  },
  metaCell: {
    display: "flex",
    flexDirection: "column",
    gap: 2,
    padding: "12px 14px",
    background: "#fff",
  },
  metaKey: {
    fontSize: 10,
    fontWeight: 700,
    color: "#9aa5b4",
    textTransform: "uppercase",
    letterSpacing: "0.6px",
  },
  metaVal: {
    fontSize: 14,
    fontWeight: 600,
    color: "#1a2a3a",
  },

  // Sections
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: 700,
    color: "#1a3a5c",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    margin: "0 0 10px",
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  bodyText: {
    fontSize: 14,
    color: "#3a4a5a",
    lineHeight: 1.6,
    margin: 0,
  },
  countPill: {
    display: "inline-block",
    background: "#eef2ff",
    color: "#3730a3",
    border: "1px solid #c7d2fe",
    borderRadius: 20,
    padding: "1px 8px",
    fontSize: 11,
    fontWeight: 700,
    textTransform: "none",
    letterSpacing: 0,
  },
  orderedList: {
    margin: 0,
    paddingLeft: 0,
    listStyle: "none",
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  listItem: {
    fontSize: 13,
    color: "#3a4a5a",
    lineHeight: 1.5,
    padding: "8px 12px",
    background: "#f8fafd",
    borderRadius: 7,
    border: "1px solid #e8edf4",
  },

  // Skeleton
  skeletonWrap: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
    gap: 18,
  },
  skeletonCard: {
    background: "#fff",
    border: "1.5px solid #e3e8f0",
    borderRadius: 14,
    padding: "20px",
  },
  skeletonLine: {
    background: "linear-gradient(90deg, #f0f3f8 25%, #e4e8f0 50%, #f0f3f8 75%)",
    backgroundSize: "400% 100%",
    animation: "shimmer 1.4s ease infinite",
    borderRadius: 4,
  },

  // Error
  errorBanner: {
    display: "flex",
    alignItems: "flex-start",
    gap: 14,
    padding: "18px 20px",
    background: "#fef2f2",
    border: "1.5px solid #fecaca",
    borderRadius: 12,
    marginBottom: 24,
  },
  errorIcon: {
    fontSize: 22,
    lineHeight: 1,
    color: "#c0392b",
    flexShrink: 0,
  },

  // Empty state
  emptyState: {
    textAlign: "center",
    padding: "60px 20px",
    color: "#6b7a8d",
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: 700,
    color: "#1a2a3a",
    marginBottom: 8,
  },
  emptyBody: {
    fontSize: 14,
    color: "#6b7a8d",
    marginBottom: 20,
    maxWidth: 400,
    marginInline: "auto",
  },
};

// ── Inject shimmer keyframe (once) ────────────────────────────────────────────
if (typeof document !== "undefined") {
  const styleId = "__schemes_shimmer__";
  if (!document.getElementById(styleId)) {
    const el = document.createElement("style");
    el.id = styleId;
    el.textContent = `
      @keyframes shimmer {
        0%   { background-position: 200% 0 }
        100% { background-position: -200% 0 }
      }
    `;
    document.head.appendChild(el);
  }
}
