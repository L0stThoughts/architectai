"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, ShieldCheck, AlertTriangle, ShieldAlert, Info } from "lucide-react";
import clsx from "clsx";

interface Finding {
  file_path: string;
  line_number: number | null;
  owasp_category: string;
  severity: string;
  description: string;
  code_snippet: string | null;
  suggested_fix: string;
}

const SEVERITY_CONFIG: Record<string, { icon: typeof ShieldAlert; color: string; bg: string }> = {
  critical: { icon: ShieldAlert, color: "text-red-400", bg: "bg-red-500/10 border-red-500/20" },
  high: { icon: AlertTriangle, color: "text-red-400", bg: "bg-red-500/10 border-red-500/20" },
  medium: { icon: AlertTriangle, color: "text-yellow-400", bg: "bg-yellow-500/10 border-yellow-500/20" },
  low: { icon: Info, color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  info: { icon: Info, color: "text-gray-400", bg: "bg-gray-500/10 border-gray-500/20" },
};

export default function SecurityReport({ findings }: { findings: Finding[] }) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const bySeverity = findings.reduce<Record<string, number>>((acc, f) => {
    acc[f.severity] = (acc[f.severity] || 0) + 1;
    return acc;
  }, {});

  const toggle = (i: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  };

  if (findings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-3">
        <ShieldCheck className="h-10 w-10 text-emerald-400" />
        <p className="text-sm font-medium text-emerald-400">No security issues found</p>
        <p className="text-xs text-[var(--color-text-dim)]">All checks passed successfully</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Severity summary */}
      <div className="flex gap-2 flex-wrap">
        {Object.entries(bySeverity)
          .sort(([a], [b]) => {
            const order = ["critical", "high", "medium", "low", "info"];
            return order.indexOf(a) - order.indexOf(b);
          })
          .map(([sev, count]) => {
            const config = SEVERITY_CONFIG[sev] || SEVERITY_CONFIG.info;
            return (
              <span
                key={sev}
                className={clsx("rounded-lg px-3 py-1 text-xs font-medium border", config.bg, config.color)}
              >
                {sev}: {count}
              </span>
            );
          })}
      </div>

      {/* Findings list */}
      <div className="space-y-2">
        {findings.map((f, i) => {
          const isOpen = expanded.has(i);
          const config = SEVERITY_CONFIG[f.severity] || SEVERITY_CONFIG.info;
          const Icon = config.icon;

          return (
            <div key={i} className={clsx("rounded-lg border overflow-hidden", config.bg)}>
              <button
                onClick={() => toggle(i)}
                className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-left hover:bg-white/[0.02] transition"
              >
                <Icon className={clsx("h-4 w-4 shrink-0", config.color)} />
                <span className={clsx("font-medium text-xs px-2 py-0.5 rounded capitalize", config.color)}>
                  {f.severity}
                </span>
                <span className="text-[var(--color-text-dim)] text-xs shrink-0">{f.owasp_category}</span>
                <span className="text-[var(--color-text)] truncate">{f.description}</span>
                <span className="ml-auto shrink-0">
                  {isOpen ? (
                    <ChevronDown className="h-3.5 w-3.5 text-[var(--color-text-dim)]" />
                  ) : (
                    <ChevronRight className="h-3.5 w-3.5 text-[var(--color-text-dim)]" />
                  )}
                </span>
              </button>
              {isOpen && (
                <div className="px-4 pb-3 space-y-2 border-t border-white/5">
                  <p className="text-xs text-[var(--color-text-muted)] font-mono mt-2">
                    {f.file_path}{f.line_number ? `:${f.line_number}` : ""}
                  </p>
                  {f.code_snippet && (
                    <pre className="text-xs text-[var(--color-text)] bg-[var(--color-surface-900)] rounded-lg p-2.5 overflow-x-auto font-mono">
                      {f.code_snippet}
                    </pre>
                  )}
                  <div className="flex items-start gap-2 rounded-lg bg-emerald-500/5 border border-emerald-500/10 p-2.5">
                    <span className="text-emerald-400 text-xs mt-0.5">💡</span>
                    <span className="text-xs text-emerald-300">{f.suggested_fix}</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
