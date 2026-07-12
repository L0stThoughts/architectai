"use client";

import { Package, Download, AlertTriangle } from "lucide-react";
import clsx from "clsx";

interface DownloadBundleProps {
  jobId: number;
  status: string;
  bundleSize?: number;
}

export default function DownloadBundle({ jobId, status, bundleSize }: DownloadBundleProps) {
  const enabled = status === "COMPLETE" || status === "COMPLETE_WITH_WARNINGS";
  const hasWarnings = status === "COMPLETE_WITH_WARNINGS";

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-800)] p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={clsx(
            "flex h-10 w-10 items-center justify-center rounded-lg",
            enabled ? "bg-emerald-500/10" : "bg-[var(--color-surface-600)]"
          )}>
            <Package className={clsx("h-5 w-5", enabled ? "text-emerald-400" : "text-[var(--color-text-dim)]")} />
          </div>
          <div>
            <p className="text-sm font-medium text-white">Project Bundle</p>
            <p className="text-xs text-[var(--color-text-dim)]">
              {enabled
                ? `Ready to download${bundleSize ? ` (${(bundleSize / 1024).toFixed(1)} KB)` : ""}`
                : "Available when generation completes"
              }
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {hasWarnings && (
            <span className="flex items-center gap-1.5 text-xs text-yellow-400">
              <AlertTriangle className="h-3.5 w-3.5" />
              Has warnings
            </span>
          )}
          <a
            href={enabled ? `/api/v1/jobs/${jobId}/bundle` : "#"}
            download
            className={clsx(
              "inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-medium transition-all",
              enabled
                ? "bg-emerald-600 text-white hover:bg-emerald-500 active:scale-[0.98]"
                : "bg-[var(--color-surface-600)] text-[var(--color-text-dim)] cursor-not-allowed"
            )}
            onClick={(e) => !enabled && e.preventDefault()}
            aria-disabled={!enabled}
          >
            <Download className="h-4 w-4" />
            Download ZIP
          </a>
        </div>
      </div>
    </div>
  );
}
