"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FolderKanban, Clock, ChevronRight, Inbox, Loader2 } from "lucide-react";
import clsx from "clsx";

interface ProjectSummary {
  id: number;
  name: string;
  product_goal: string | null;
  created_at: string | null;
  jobs: { id: number; status: string; current_phase: string }[];
}

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  COMPLETE: { bg: "bg-emerald-500/10", text: "text-emerald-400", label: "Complete" },
  COMPLETE_WITH_WARNINGS: { bg: "bg-yellow-500/10", text: "text-yellow-400", label: "Warnings" },
  FAILED: { bg: "bg-red-500/10", text: "text-red-400", label: "Failed" },
  RUNNING: { bg: "bg-blue-500/10", text: "text-blue-400", label: "Running" },
  PENDING: { bg: "bg-gray-500/10", text: "text-gray-400", label: "Pending" },
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/v1/projects?limit=50")
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setProjects)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--color-accent)]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-32 space-y-3">
        <p className="text-red-400 text-sm">Failed to load projects: {error}</p>
        <button
          onClick={() => window.location.reload()}
          className="text-sm text-[var(--color-accent)] hover:underline"
        >
          Retry
        </button>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-32 space-y-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--color-surface-700)]">
          <Inbox className="h-8 w-8 text-[var(--color-text-dim)]" />
        </div>
        <h2 className="text-lg font-semibold text-white">No projects yet</h2>
        <p className="text-sm text-[var(--color-text-muted)]">Create your first project to get started.</p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-lg bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-accent-hover)] transition"
        >
          <FolderKanban className="h-4 w-4" />
          New Project
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Projects</h1>
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-lg bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-accent-hover)] transition"
        >
          New Project
        </Link>
      </div>

      <div className="grid gap-3">
        {projects.map((p) => {
          const latestJob = p.jobs?.[p.jobs.length - 1];
          const statusInfo = latestJob
            ? STATUS_STYLES[latestJob.status] || STATUS_STYLES.PENDING
            : null;

          return (
            <Link
              key={p.id}
              href={`/projects/${p.id}`}
              className="group flex items-center justify-between rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-800)] p-4 hover:border-[var(--color-border-bright)] hover:bg-[var(--color-surface-700)] transition-all"
            >
              <div className="flex items-center gap-4 min-w-0">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--color-surface-600)]">
                  <FolderKanban className="h-5 w-5 text-[var(--color-accent)]" />
                </div>
                <div className="min-w-0">
                  <h3 className="font-medium text-white truncate">{p.name}</h3>
                  <div className="flex items-center gap-3 mt-0.5">
                    {p.created_at && (
                      <span className="flex items-center gap-1 text-xs text-[var(--color-text-dim)]">
                        <Clock className="h-3 w-3" />
                        {new Date(p.created_at).toLocaleDateString()}
                      </span>
                    )}
                    <span className="text-xs text-[var(--color-text-dim)]">
                      {p.jobs.length} job{p.jobs.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {statusInfo && (
                  <span className={clsx("rounded-full px-2.5 py-0.5 text-xs font-medium", statusInfo.bg, statusInfo.text)}>
                    {statusInfo.label}
                  </span>
                )}
                <ChevronRight className="h-4 w-4 text-[var(--color-text-dim)] group-hover:text-white transition" />
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
