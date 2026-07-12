"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, CheckCircle2, XCircle } from "lucide-react";
import clsx from "clsx";

interface TestResultData {
  test_file: string;
  passed: boolean;
  output: string;
  errors: string[];
  duration_ms: number;
}

export default function TestResults({ results }: { results: TestResultData[] }) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const passed = results.filter((r) => r.passed).length;
  const failed = results.length - passed;

  const toggle = (i: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  };

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm font-medium">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          <span className="text-emerald-400">{passed} passed</span>
        </div>
        {failed > 0 && (
          <div className="flex items-center gap-2 text-sm font-medium">
            <XCircle className="h-4 w-4 text-red-400" />
            <span className="text-red-400">{failed} failed</span>
          </div>
        )}
        <span className="text-xs text-[var(--color-text-dim)]">{results.length} total</span>
      </div>

      {/* Results list */}
      <div className="space-y-2">
        {results.map((r, i) => {
          const isOpen = expanded.has(i);
          return (
            <div
              key={i}
              className={clsx(
                "rounded-lg border overflow-hidden transition-colors",
                r.passed
                  ? "border-emerald-500/20 bg-emerald-500/5"
                  : "border-red-500/20 bg-red-500/5"
              )}
            >
              <button
                onClick={() => toggle(i)}
                className="flex items-center justify-between w-full px-4 py-2.5 text-sm text-left hover:bg-white/[0.02] transition"
              >
                <span className="flex items-center gap-2">
                  {r.passed ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-400 shrink-0" />
                  )}
                  <span className={r.passed ? "text-emerald-300" : "text-red-300"}>{r.test_file}</span>
                </span>
                <span className="flex items-center gap-2">
                  <span className="text-xs text-[var(--color-text-dim)]">{r.duration_ms}ms</span>
                  {isOpen ? (
                    <ChevronDown className="h-3.5 w-3.5 text-[var(--color-text-dim)]" />
                  ) : (
                    <ChevronRight className="h-3.5 w-3.5 text-[var(--color-text-dim)]" />
                  )}
                </span>
              </button>
              {isOpen && (
                <div className="px-4 pb-3 space-y-2 border-t border-white/5">
                  {r.errors.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {r.errors.map((err, j) => (
                        <code key={j} className="block text-xs text-red-300 bg-red-900/20 rounded-lg p-2.5 font-mono">
                          {err}
                        </code>
                      ))}
                    </div>
                  )}
                  {r.output && (
                    <pre className="mt-2 text-xs text-[var(--color-text-muted)] bg-[var(--color-surface-900)] rounded-lg p-2.5 max-h-40 overflow-y-auto whitespace-pre-wrap font-mono">
                      {r.output}
                    </pre>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
