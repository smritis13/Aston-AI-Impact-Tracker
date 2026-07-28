import React, { useEffect, useState } from "react";
import { ContentHttpService } from "../services";

interface UseCase {
  id: number;
  use_case_name: string;
  use_case_description: string;
  source: string;
  source_reference: string;
  credibility_score: number | null;
  relevance_score: number | null;
}

interface Props {
  themeId: number;
}

const credibilityLabel = (score: number | null): { label: string; color: string } => {
  if (score === null || score === undefined) return { label: "Unknown", color: "#6b7280" };
  if (score >= 7) return { label: "Credible", color: "#15803d" };
  if (score >= 4) return { label: "Moderate", color: "#b45309" };
  return { label: "Weak", color: "#b91c1c" };
};

const shortenUrl = (url: string): string => {
  if (!url) return "-";
  try {
    const u = new URL(url.startsWith("http") ? url : "https://" + url);
    const path = u.pathname.length > 30 ? u.pathname.slice(0, 30) + "…" : u.pathname;
    return u.hostname.replace(/^www\./, "") + path;
  } catch {
    return url.length > 50 ? url.slice(0, 50) + "…" : url;
  }
};

const firstSentence = (text: string): string => {
  if (!text) return "-";
  const m = text.match(/^(.{10,200}?[.!?])\s/);
  return m ? m[1] : text.slice(0, 160) + (text.length > 160 ? "…" : "");
};

const ReportReferencesTable: React.FC<Props> = ({ themeId }) => {
  const [useCases, setUseCases] = useState<UseCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState<string | null>(null);

  useEffect(() => {
    if (!themeId) { setLoading(false); return; }
    setLoading(true);
    setApiError(null);
    ContentHttpService.loadUseCases(themeId, undefined, 1, 200, "relevance_score", "desc")
      .then((data: any) => {
        const results: UseCase[] = Array.isArray(data?.results)
          ? data.results
          : Array.isArray(data) ? data : [];
        const sorted = [...results].sort((a, b) => {
          const relDiff = (b.relevance_score ?? 0) - (a.relevance_score ?? 0);
          if (relDiff !== 0) return relDiff;
          return (b.credibility_score ?? 0) - (a.credibility_score ?? 0);
        });
        setUseCases(sorted);
      })
      .catch((err: any) => {
        setApiError(err?.message || "Failed to load references");
      })
      .finally(() => setLoading(false));
  }, [themeId]);

  if (loading) return (
    <p style={{ color: "#9ca3af", fontSize: "0.9rem", marginTop: "32px" }}>
      Loading references for theme {themeId}…
    </p>
  );
  if (apiError) return (
    <p style={{ color: "#ef4444", fontSize: "0.9rem", marginTop: "32px" }}>
      References error: {apiError}
    </p>
  );
  if (!useCases.length) return (
    <p style={{ color: "#9ca3af", fontSize: "0.9rem", marginTop: "32px" }}>
      No use cases found for theme {themeId}.
    </p>
  );

  return (
    <div style={{ marginTop: "40px" }}>
      <h2 style={{ fontSize: "1.35rem", fontWeight: 700, marginBottom: "12px", borderBottom: "2px solid #1e3a5f", paddingBottom: "6px" }}>
        References
      </h2>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
          <thead>
            <tr>
              {["#", "Link", "Title", "Claim corroborated", "Where to check", "Evidence Quality"].map((h) => (
                <th key={h} style={{
                  background: "#1e3a5f", color: "#fff", padding: "8px 10px",
                  textAlign: "left", fontWeight: 600, border: "1px solid #1e3a5f",
                  whiteSpace: "nowrap",
                }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {useCases.map((uc, idx) => {
              const { label, color } = credibilityLabel(uc.credibility_score);
              const fullUrl = uc.source || uc.source_reference || "";
              const isUrl = fullUrl.startsWith("http");
              const rowBg = idx % 2 === 0 ? "transparent" : "rgba(30,58,95,0.06)";
              return (
                <tr key={uc.id} style={{ background: rowBg }}>
                  <td style={tdStyle}>{idx + 1}</td>
                  <td style={{ ...tdStyle, maxWidth: "140px", wordBreak: "break-all", color: "#1d4ed8" }}>
                    {isUrl ? (
                      <a href={fullUrl} target="_blank" rel="noopener noreferrer" style={{ color: "#1d4ed8" }}>
                        {shortenUrl(fullUrl)}
                      </a>
                    ) : (
                      shortenUrl(fullUrl)
                    )}
                  </td>
                  <td style={{ ...tdStyle, maxWidth: "180px" }}>
                    {uc.use_case_name ? (uc.use_case_name.length > 90 ? uc.use_case_name.slice(0, 90) + "…" : uc.use_case_name) : "-"}
                  </td>
                  <td style={{ ...tdStyle, maxWidth: "220px" }}>
                    {firstSentence(uc.use_case_description)}
                  </td>
                  <td style={{ ...tdStyle, maxWidth: "200px", wordBreak: "break-all" }}>
                    {isUrl ? (
                      <a href={fullUrl} target="_blank" rel="noopener noreferrer" style={{ color: "#1d4ed8", fontSize: "0.78rem" }}>
                        {fullUrl}
                      </a>
                    ) : (
                      <span style={{ color: "#6b7280", fontStyle: "italic" }}>{fullUrl || "—"}</span>
                    )}
                  </td>
                  <td style={{ ...tdStyle, whiteSpace: "nowrap" }}>
                    <span style={{ color, fontWeight: 600 }}>{label}</span>
                    {uc.credibility_score !== null && (
                      <span style={{ color: "#9ca3af", fontWeight: 400, marginLeft: "4px" }}>
                        ({uc.credibility_score}/10)
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const tdStyle: React.CSSProperties = {
  padding: "7px 10px",
  border: "1px solid #d1d5db",
  verticalAlign: "top",
  lineHeight: 1.45,
};

export default ReportReferencesTable;
