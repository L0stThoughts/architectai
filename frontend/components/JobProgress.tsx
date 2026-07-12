"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";

interface JobEvent {
  event_type: string;
  data: Record<string, unknown>;
  timestamp: number;
}

const PHASE_CONFIG: Record<string, { icon: string; label: string }> = {
  PLAN: { icon: "📋", label: "Planning Architecture" },
  GENERATE: { icon: "⚡", label: "Generating Code" },
  TEST: { icon: "🧪", label: "Running Tests" },
  PATCH: { icon: "🔧", label: "Patching Bugs" },
  SECURITY: { icon: "🛡️", label: "Security Audit" },
  PACKAGE: { icon: "📦", label: "Packaging Bundle" },
  COMPLETE: { icon: "✅", label: "Complete" },
  FAILED: { icon: "❌", label: "Failed" },
};

const PHASE_ORDER = ["PLAN", "GENERATE", "TEST", "PATCH", "SECURITY", "PACKAGE", "COMPLETE"];

const EVENT_STYLES: Record<string, string> = {
  phase_change: "text-[var(--color-accent-hover)]",
  file_generated: "text-emerald-400",
  test_result: "text-yellow-400",
  bug_found: "text-red-400",
  security_finding: "text-orange-400",
  complete: "text-emerald-400",
  error: "text-red-500",
};

export default function JobProgress({ jobId }: { jobId: number }) {
  const [events, setEvents] = useState<JobEvent[]>([]);
  const [currentPhase, setCurrentPhase] = useState("PLAN");

  useEffect(() => {
    const evtSource = new EventSource(`/api/v1/jobs/${jobId}/events/stream`);
    evtSource.onmessage = (e) => {
      try {
        const event: JobEvent = JSON.parse(e.data);
        setEvents((prev) => [...prev, event]);
        if (event.event_type === "phase_change" && event.data.phase) {
          setCurrentPhase(event.data.phase as string);
        }
        if (event.event_type === "complete" || event.event_type === "error") {
          evtSource.close();
        }
      } catch { /* skip malformed events */ }
    };
    evtSource.onerror = () => evtSource.close();
    return () => evtSource.close();
  }, [jobId]);

  const phaseIndex = PHASE_ORDER.indexOf(currentPhase);
  const progress = phaseIndex >= 0 ? ((phaseIndex + 1) / PHASE_ORDER.length) * 100 : 0;
  const config = PHASE_CONFIG[currentPhase] || { icon: "⏳", label: currentPhase };

  return (
    <div className="space-y-5">
      {/* Current phase display */}
      <div className="flex items-center gap-3">
        <span className="text-2xl" role="img" aria-label={config.label}>{config.icon}</span>
        <div>
          <p className="text-sm font-semibold text-white">{config.label}</p>
          <p className="text-xs text-[var(--color-text-dim)]">Phase {phaseIndex + 1} of {PHASE_ORDER.length}</p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 w-full rounded-full bg-[var(--color-surface-600)] overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-[var(--color-accent)] to-[var(--color-accent-hover)] transition-all duration-700 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Pipeline steps */}
      <div className="flex items-center justify-between gap-1">
        {PHASE_ORDER.map((phase, i) => {
          const p = PHASE_CONFIG[phase];
          const reached = i <= phaseIndex;
          return (
            <div key={phase} className="flex items-center gap-1">
              <div
                className={clsx(
                  "flex h-7 w-7 items-center justify-center rounded-full text-xs transition-all",
                  reached
                    ? "bg-[var(--color-accent)] text-white"
                    : "bg-[var(--color-surface-600)] text-[var(--color-text-dim)]"
                )}
                title={p?.label || phase}
              >
                {p?.icon}
              </div>
              {i < PHASE_ORDER.length - 1 && (
                <div
                  className={clsx(
                    "hidden sm:block h-0.5 w-4 rounded transition-colors",
                    i < phaseIndex ? "bg-[var(--color-accent)]" : "bg-[var(--color-surface-600)]"
                  )}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Event log */}
      <div className="max-h-48 overflow-y-auto rounded-lg bg-[var(--color-surface-900)] p-3 space-y-0.5">
        {events.length === 0 && (
          <p className="text-[var(--color-text-dim)] text-xs py-2 text-center">Waiting for pipeline events...</p>
        )}
        {events.map((event, i) => (
          <div
            key={i}
            className={clsx("text-xs font-mono leading-relaxed", EVENT_STYLES[event.event_type] || "text-[var(--color-text-dim)]")}
          >
            <span className="text-[var(--color-text-dim)] mr-2">
              {new Date(event.timestamp * 1000).toLocaleTimeString()}
            </span>
            <span className="font-medium">{event.event_type}</span>
            {event.data.phase ? <span className="ml-1">→ {String(event.data.phase)}</span> : null}
            {event.data.path ? <span className="ml-1 text-[var(--color-text-muted)]">{String(event.data.path)}</span> : null}
            {event.data.message ? <span className="ml-1 text-[var(--color-text-muted)]">{String(event.data.message)}</span> : null}
          </div>
        ))}
      </div>
    </div>
  );
}
