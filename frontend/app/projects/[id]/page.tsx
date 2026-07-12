"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { Play, RotateCcw, Loader2, FileCode, TestTube2, Shield, ArrowLeft } from "lucide-react";
import Link from "next/link";
import clsx from "clsx";
import JobProgress from "@/components/JobProgress";
import FileTree from "@/components/FileTree";
import TestResults from "@/components/TestResults";
import SecurityReport from "@/components/SecurityReport";
import DownloadBundle from "@/components/DownloadBundle";

interface ProjectData {
  id: number;
  name: string;
  product_goal: string | null;
  created_at: string | null;
  jobs: { id: number; status: string; current_phase: string }[];
}

type TabId = "files" | "tests" | "security";

const TAB_CONFIG: { id: TabId; label: string; icon: typeof FileCode }[] = [
  { id: "files", label: "Generated Files", icon: FileCode },
  { id: "tests", label: "Test Results", icon: TestTube2 },
  { id: "security", label: "Security Audit", icon: Shield },
];

export default function ProjectPage() {
  const params = useParams();
  const projectId = params.id as string;

  const [project, setProject] = useState<ProjectData | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("files");
  const [artifacts, setArtifacts] = useState<Record<string, string>>({});
  const [testResults, setTestResults] = useState<any[]>([]);
  const [securityFindings, setSecurityFindings] = useState<any[]>([]);
  const [launching, setLaunching] = useState(false);
  const [loadingProject, setLoadingProject] = useState(true);
  const [error, setError] = useState("");

  const latestJob = project?.jobs?.[project.jobs.length - 1];
  const terminalStatuses = ["COMPLETE", "COMPLETE_WITH_WARNINGS", "FAILED"];
  const jobRunning = latestJob && !terminalStatuses.includes(latestJob.status);
  const jobComplete = latestJob && terminalStatuses.includes(latestJob.status);

  // Load project
  useEffect(() => {
    setLoadingProject(true);
    fetch(`/api/v1/projects/${projectId}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setProject)
      .catch((e) => setError(e.message))
      .finally(() => setLoadingProject(false));
  }, [projectId]);

  // Load job data when job changes
  const loadJobData = useCallback((jobId: number) => {
    fetch(`/api/v1/jobs/${jobId}/artifacts`)
      .then((r) => r.json())
      .then((arts: any[]) => {
        const map: Record<string, string> = {};
        arts.forEach((a: any) => { map[a.file_path] = a.content || ""; });
        setArtifacts(map);
      })
      .catch(() => {});

    fetch(`/api/v1/jobs/${jobId}/tests`)
      .then((r) => r.json())
      .then((runs: any[]) => {
        const results = runs.flatMap((r: any) => r.results || []);
        setTestResults(results);
      })
      .catch(() => {});

    fetch(`/api/v1/jobs/${jobId}/security`)
      .then((r) => r.json())
      .then(setSecurityFindings)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (latestJob) loadJobData(latestJob.id);
  }, [latestJob?.id, latestJob?.status, loadJobData]);

  // Poll for status updates when job is running
  useEffect(() => {
    if (!jobRunning || !latestJob) return;
    const interval = setInterval(() => {
      fetch(`/api/v1/projects/${projectId}`)
        .then((r) => r.json())
        .then(setProject)
        .catch(() => {});
    }, 3000);
    return () => clearInterval(interval);
  }, [jobRunning, latestJob?.id, projectId]);

  const launchJob = async () => {
    if (!project) return;
    setLaunching(true);
    setError("");
    try {
      const res = await fetch(`/api/v1/projects/${project.id}/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error(`Failed to launch: HTTP ${res.status}`);
      const job = await res.json();
      setProject((p) => p ? { ...p, jobs: [...p.jobs, job] } : p);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to launch job");
    } finally {
      setLaunching(false);
    }
  };

  if (loadingProject) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--color-accent)]" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-32 space-y-3">
        <p className="text-red-400">Project not found</p>
        <Link href="/projects" className="text-sm text-[var(--color-accent)] hover:underline">
          ← Back to projects
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb + Header */}
      <div>
        <Link
          href="/projects"
          className="inline-flex items-center gap-1 text-sm text-[var(--color-text-dim)] hover:text-[var(--color-accent)] transition mb-3"
        >
          <ArrowLeft className="h-3 w-3" />
          All Projects
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white">{project.name}</h1>
            {project.product_goal && (
              <p className="mt-1 text-sm text-[var(--color-text-muted)] max-w-2xl line-clamp-2">
                {project.product_goal}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {(!latestJob || latestJob.status === "FAILED") && (
              <button
                onClick={launchJob}
                disabled={launching}
                className="inline-flex items-center gap-2 rounded-lg bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-accent-hover)] disabled:opacity-40 transition"
              >
                {launching ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : latestJob?.status === "FAILED" ? (
                  <RotateCcw className="h-4 w-4" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                {latestJob?.status === "FAILED" ? "Retry" : "Generate"}
              </button>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div role="alert" className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Job Progress */}
      {latestJob && jobRunning && (
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-800)] p-6">
          <JobProgress jobId={latestJob.id} />
        </div>
      )}

      {/* Tabs + Content */}
      {latestJob && (
        <>
          <div className="flex items-center gap-1 border-b border-[var(--color-border)]">
            {TAB_CONFIG.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={clsx(
                  "flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px",
                  activeTab === id
                    ? "text-[var(--color-accent-hover)] border-[var(--color-accent)]"
                    : "text-[var(--color-text-dim)] border-transparent hover:text-white"
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
                {id === "tests" && testResults.length > 0 && (
                  <span className="rounded-full bg-[var(--color-surface-600)] px-1.5 py-0.5 text-[11px]">
                    {testResults.length}
                  </span>
                )}
                {id === "security" && securityFindings.length > 0 && (
                  <span className="rounded-full bg-[var(--color-surface-600)] px-1.5 py-0.5 text-[11px]">
                    {securityFindings.length}
                  </span>
                )}
              </button>
            ))}
          </div>

          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-800)] p-6">
            {activeTab === "files" && (
              Object.keys(artifacts).length > 0 ? (
                <FileTree files={artifacts} />
              ) : (
                <p className="text-sm text-[var(--color-text-dim)] text-center py-12">
                  {jobRunning ? "Files will appear as they are generated..." : "No files generated yet"}
                </p>
              )
            )}
            {activeTab === "tests" && (
              testResults.length > 0 ? (
                <TestResults results={testResults} />
              ) : (
                <p className="text-sm text-[var(--color-text-dim)] text-center py-12">
                  {jobRunning ? "Waiting for test results..." : "No test results"}
                </p>
              )
            )}
            {activeTab === "security" && (
              <SecurityReport findings={securityFindings} />
            )}
          </div>

          {/* Download */}
          {jobComplete && latestJob.status !== "FAILED" && (
            <DownloadBundle jobId={latestJob.id} status={latestJob.status} />
          )}
        </>
      )}

      {/* No jobs yet state */}
      {!latestJob && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface-800)]/50 py-16 space-y-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--color-surface-700)]">
            <Play className="h-7 w-7 text-[var(--color-accent)]" />
          </div>
          <h3 className="text-lg font-semibold text-white">Ready to generate</h3>
          <p className="text-sm text-[var(--color-text-muted)] max-w-sm text-center">
            Click the Generate button to start the autonomous build pipeline for this project.
          </p>
        </div>
      )}
    </div>
  );
}
