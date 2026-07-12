"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles } from "lucide-react";

const EXAMPLE_GOALS = [
  "Build a task manager with user authentication, CRUD tasks, and due dates",
  "Build a blog platform with markdown support and comments",
  "Build a URL shortener with click analytics and custom aliases",
];

interface GoalInputProps {
  readOnly?: boolean;
  initialGoal?: string;
}

export default function GoalInput({ readOnly = false, initialGoal = "" }: GoalInputProps) {
  const [goal, setGoal] = useState(initialGoal);
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
      if (!res.ok) throw new Error("Failed to create project");
      const project = await res.json();
      router.push(`/projects/${project.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  if (readOnly) {
    return null; // Goal is shown in the page header now
  }

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      <label htmlFor="goal" className="block text-sm font-medium text-[var(--color-text-muted)]">
        Product Goal
      </label>
      <textarea
        id="goal"
        className="w-full h-32 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-900)] p-4 text-white placeholder-[var(--color-text-dim)] focus:border-[var(--color-accent)] focus:ring-1 focus:ring-[var(--color-accent)] resize-none transition"
        placeholder="Describe the application you want to build..."
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
        disabled={loading}
      />
      <div className="flex flex-wrap gap-2">
        {EXAMPLE_GOALS.map((eg, i) => (
          <button
            key={i}
            onClick={() => setGoal(eg)}
            className="rounded-full border border-[var(--color-border)] bg-[var(--color-surface-800)] px-3 py-1 text-xs text-[var(--color-text-muted)] hover:border-[var(--color-accent)] transition"
          >
            {eg.slice(0, 40)}…
          </button>
        ))}
      </div>
      <button
        onClick={handleSubmit}
        disabled={loading || !goal.trim()}
        className="w-full flex items-center justify-center gap-2 rounded-xl bg-[var(--color-accent)] px-6 py-3 font-semibold text-white hover:bg-[var(--color-accent-hover)] disabled:opacity-40 transition"
      >
        <Sparkles className="h-4 w-4" />
        {loading ? "Creating..." : "Generate Application"}
      </button>
      {error && (
        <p role="alert" className="text-red-400 text-sm">{error}</p>
      )}
    </div>
  );
}
