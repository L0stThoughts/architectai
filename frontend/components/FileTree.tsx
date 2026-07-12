"use client";

import { useState, useMemo } from "react";
import clsx from "clsx";

interface FileTreeProps {
  files: Record<string, string>;
}

interface TreeNode {
  name: string;
  path: string;
  isFile: boolean;
  children: TreeNode[];
  content?: string;
}

function buildTree(files: Record<string, string>): TreeNode[] {
  const root: TreeNode[] = [];
  for (const [path, content] of Object.entries(files)) {
    const parts = path.split("/");
    let current = root;
    for (let i = 0; i < parts.length; i++) {
      const name = parts[i];
      const isFile = i === parts.length - 1;
      let node = current.find((n) => n.name === name);
      if (!node) {
        node = { name, path: parts.slice(0, i + 1).join("/"), isFile, children: [], content: isFile ? content : undefined };
        current.push(node);
      }
      current = node.children;
    }
  }
  return root;
}

const EXT_BADGE: Record<string, string> = {
  py: "bg-yellow-500/20 text-yellow-400",
  ts: "bg-blue-500/20 text-blue-400",
  tsx: "bg-blue-400/20 text-blue-300",
  js: "bg-yellow-400/20 text-yellow-300",
  json: "bg-gray-500/20 text-gray-400",
  css: "bg-purple-500/20 text-purple-400",
  html: "bg-orange-500/20 text-orange-400",
  md: "bg-gray-400/20 text-gray-300",
};

function FileNode({ node, onSelect, selectedPath }: {
  node: TreeNode;
  onSelect: (n: TreeNode) => void;
  selectedPath: string | null;
}) {
  const [open, setOpen] = useState(false);
  const ext = node.name.split(".").pop() || "";
  const badge = EXT_BADGE[ext];

  if (node.isFile) {
    return (
      <button
        onClick={() => onSelect(node)}
        className={clsx(
          "flex items-center gap-2 w-full text-left px-2 py-1.5 text-sm rounded-lg transition-colors",
          selectedPath === node.path
            ? "bg-[var(--color-accent-muted)] text-[var(--color-accent-hover)]"
            : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-700)] hover:text-white"
        )}
      >
        <span className="text-xs">📄</span>
        <span className="truncate">{node.name}</span>
        {badge && (
          <span className={clsx("text-[10px] px-1.5 py-0.5 rounded font-medium", badge)}>{ext}</span>
        )}
        {node.content && (
          <span className="text-[var(--color-text-dim)] text-[10px] ml-auto shrink-0">
            {node.content.split("\n").length}L
          </span>
        )}
      </button>
    );
  }

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 w-full text-left px-2 py-1.5 text-sm text-white hover:bg-[var(--color-surface-700)] rounded-lg font-medium transition-colors"
      >
        <span className="text-xs">{open ? "📂" : "📁"}</span>
        <span>{node.name}</span>
        <span className="text-[var(--color-text-dim)] text-[10px]">({node.children.length})</span>
      </button>
      {open && (
        <div className="ml-3 border-l border-[var(--color-border)] pl-2">
          {node.children.map((child) => (
            <FileNode key={child.path} node={child} onSelect={onSelect} selectedPath={selectedPath} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function FileTree({ files }: FileTreeProps) {
  const tree = useMemo(() => buildTree(files), [files]);
  const [selected, setSelected] = useState<TreeNode | null>(null);

  return (
    <div className="flex gap-4 h-[480px]">
      {/* Sidebar */}
      <div className="w-72 shrink-0 overflow-y-auto rounded-lg bg-[var(--color-surface-900)] p-2">
        <div className="px-2 py-1.5 text-xs font-medium text-[var(--color-text-dim)] uppercase tracking-wider">
          Files ({Object.keys(files).length})
        </div>
        {tree.map((node) => (
          <FileNode key={node.path} node={node} onSelect={setSelected} selectedPath={selected?.path || null} />
        ))}
      </div>

      {/* Code viewer */}
      <div className="flex-1 overflow-auto rounded-lg bg-[var(--color-surface-900)]">
        {selected ? (
          <div>
            <div className="sticky top-0 z-10 flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface-900)] px-4 py-2">
              <span className="text-xs text-[var(--color-text-muted)] font-mono">{selected.path}</span>
              <span className="text-[10px] text-[var(--color-text-dim)]">
                {selected.content ? `${(selected.content.length / 1024).toFixed(1)} KB` : ""}
              </span>
            </div>
            <pre className="p-4 text-sm text-[var(--color-text)] whitespace-pre-wrap font-mono leading-relaxed">
              {selected.content}
            </pre>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-[var(--color-text-dim)] text-sm">
            Select a file to view its content
          </div>
        )}
      </div>
    </div>
  );
}
