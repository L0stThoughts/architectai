"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, ArrowRight, Zap } from "lucide-react";

const EXAMPLES = [
  "Build a task manager with user authentication, CRUD tasks, and due dates",
  "Build a blog platform with markdown support and comments",
  "Build a URL shortener with click analytics and custom aliases",
  "Build an invoice generator with PDF export and client management",
  "Build a recipe sharing app with search and rating system",
];

export default function HomePage() {
  const [goal, setGoal] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleSubmit = async () => {
    if (!goal.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/v1/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: goal.slice(0, 60),
          description: goal,
          product_goal: goal,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Server returned ${res.status}`);
      }
      const project = await res.json();
      router.push(`/projects/${project.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center pt-12 sm:pt-20">
      {/* Hero */}
      <div className="text-center space-y-4 max-w-2xl">
        <div className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border-bright)] bg-[var(--color-surface-800)] px-4 py-1.5 text-xs font-medium text-[var(--color-accent-hover)]">
          <Zap className="h-3 w-3" />
          Autonomous Code Generation Pipeline
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-white leading-tight">
          Describe your app.
          <br />
          <span className="text-[var(--color-accent)]">Watch it build itself.</span>
        </h1>
        <p className="text-lg text-[var(--color-text-muted)] max-w-xl mx-auto">
          ArchitectAI turns plain-language product goals into tested, security-reviewed,
          downloadable project bundles — powered by an agentic LangGraph pipeline.
        </p>
      </div>

      {/* Input Card */}
      <div className="mt-10 w-full max-w-2xl">
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-800)] p-6 space-y-4 shadow-2xl shadow-black/20">
          <label htmlFor="goal-input" className="block text-sm font-medium text-[var(--color-text-muted)]">
            What do you want to build?
          </label>
          <textarea
            id="goal-input"
            className="w-full h-32 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-900)] p-4 text-white placeholder-[var(--color-text-dim)] focus:border-[var(--color-accent)] focus:ring-1 focus:ring-[var(--color-accent)] resize-none transition text-sm leading-relaxed"
            placeholder="Describe the application you want to build in plain language..."
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            disabled={loading}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit();
            }}
          />

          <button
            onClick={handleSubmit}
            disabled={loading || !goal.trim()}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-[var(--color-accent)] px-6 py-3 text-sm font-semibold text-white hover:bg-[var(--color-accent-hover)] disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Creating project...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Generate Application
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>

          {error && (
            <div role="alert" className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <p className="text-xs text-[var(--color-text-dim)] text-center">
            Press <kbd className="px-1.5 py-0.5 rounded bg-[var(--color-surface-700)] text-[var(--color-text-muted)] font-mono text-[11px]">⌘</kbd> + <kbd className="px-1.5 py-0.5 rounded bg-[var(--color-surface-700)] text-[var(--color-text-muted)] font-mono text-[11px]">Enter</kbd> to submit
          </p>
        </div>

        {/* Example Goals */}
        <div className="mt-6 space-y-2">
          <p className="text-xs font-medium text-[var(--color-text-dim)] uppercase tracking-wider">Try an example</p>
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((eg, i) => (
              <button
                key={i}
                onClick={() => setGoal(eg)}
                className="rounded-full border border-[var(--color-border)] bg-[var(--color-surface-800)] px-3 py-1.5 text-xs text-[var(--color-text-muted)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent-hover)] transition-colors"
              >
                {eg.length > 45 ? eg.slice(0, 45) + "…" : eg}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
