"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Cpu, FolderKanban, Activity } from "lucide-react";
import clsx from "clsx";

export function Navbar() {
  const pathname = usePathname();

  const links = [
    { href: "/", label: "New Project", icon: Cpu },
    { href: "/projects", label: "Projects", icon: FolderKanban },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--color-border)] bg-[var(--color-surface-900)]/80 backdrop-blur-xl">
      <nav className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-accent)] text-white">
            <Activity className="h-4 w-4" />
          </div>
          <span className="text-lg font-bold tracking-tight text-white">
            Architect<span className="text-[var(--color-accent)]">AI</span>
          </span>
        </Link>

        <div className="flex items-center gap-1">
          {links.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-[var(--color-accent-muted)] text-[var(--color-accent-hover)]"
                    : "text-[var(--color-text-muted)] hover:text-white hover:bg-[var(--color-surface-700)]"
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
