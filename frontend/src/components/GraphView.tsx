import { useEffect, useRef, useState } from "react";
import cytoscape from "cytoscape";
import type { GraphData } from "../api";

const LABEL_COLORS: Record<string, string> = {
  Contract: "#1d4ed8",
  Function: "#0284c7",
  Vulnerability: "#dc2626",
  Exploit: "#b45309",
  Library: "#475569",
  Auditor: "#0d9488",
  Protocol: "#4f46e5",
};
const SEVERITY_COLORS: Record<string, string> = {
  critical: "#dc2626", high: "#ea580c", medium: "#d97706", low: "#65a30d",
};

export default function GraphView({ data, onSelect, focus }: {
  data: GraphData;
  onSelect: (node: any) => void;
  focus?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    cyRef.current?.destroy();
    const cy = cytoscape({
      container: ref.current,
      elements: [
        ...data.nodes.map((n) => ({
          data: n.data,
          style: {
            "background-color": n.data.label === "Vulnerability"
              ? (SEVERITY_COLORS[n.data.severity as string] || "#dc2626")
              : (LABEL_COLORS[n.data.label as string] || "#64748b"),
            width: n.data.label === "Contract" ? 34 : n.data.label === "Exploit" ? 30 : n.data.label === "Vulnerability" ? 22 : 14,
            height: n.data.label === "Contract" ? 34 : n.data.label === "Exploit" ? 30 : n.data.label === "Vulnerability" ? 22 : 14,
            shape: n.data.label === "Contract" ? "round-rectangle"
              : n.data.label === "Exploit" ? "diamond"
              : n.data.label === "Vulnerability" ? "hexagon" : "ellipse",
            label: String(n.data.name || n.data.swc || ""),
            "font-size": n.data.label === "Contract" ? 11 : 9,
            "text-valign": "bottom" as const, "text-margin-y": 4,
            "text-wrap": "wrap" as const, "text-max-width": "90px" as string,
            color: "#334155",
            "text-background-color": "#f8fafc", "text-background-opacity": 0.75,
          },
        })),
        ...data.edges.map((e) => ({
          data: e.data,
          style: {
            "line-color": "#cbd5e1", "target-arrow-color": "#94a3b8",
            "target-arrow-shape": "triangle" as const, "curve-style": "bezier" as const,
            width: 1.2,
            "arrow-scale": 0.8,
            label: e.data.type === "CALLS" || e.data.type === "EXPLOITED" || e.data.type === "USES_LIBRARY" ? e.data.type : "",
            "font-size": 7, "edge-text-rotation": "autorotate" as const,
            color: "#94a3b8",
          },
        })),
      ],
      layout: data.nodes.length <= 60
        ? {
            name: "concentric", animate: false, randomize: false,
            minNodeSpacing: 60, spacing: 24,
            centerBy: (node: any) =>
              (focus && node.data("name") === focus ? 0
               : (node.data("label") === "Contract" ? 1 : 2)),
          } as any
        : { name: "cose", animate: false, nodeRepulsion: 4500, idealEdgeLength: 90 } as any,
      wheelSensitivity: 0.2,
    });
    cyRef.current = cy;
    cy.on("tap", "node", (e) => onSelect(e.target.data()));
    if (focus) {
      const n = cy.getElementById(focus);
      if (n.length) { cy.animate({ fit: { eles: n, padding: 60 }, duration: 0 }); }
    }
    return () => { cy.destroy(); cyRef.current = null; };
  }, [data, focus]);

  return <div ref={ref} className="h-full w-full rounded-lg border border-slate-200 bg-white" />;
}

export function GraphLegend() {
  const items: [string, string][] = [
    ["Contract", LABEL_COLORS.Contract], ["Function", LABEL_COLORS.Function],
    ["Vulnerability (severity)", LABEL_COLORS.Vulnerability], ["Exploit", LABEL_COLORS.Exploit],
    ["Library", LABEL_COLORS.Library], ["Auditor", LABEL_COLORS.Auditor],
  ];
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600">
      {items.map(([l, c]) => (
        <span key={l} className="inline-flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-full" style={{ background: c }} />{l}
        </span>
      ))}
    </div>
  );
}
