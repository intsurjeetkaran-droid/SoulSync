/**
 * SoulSync AI - Message Renderer
 * Converts AI response text into clean, structured JSX.
 *
 * Handles:
 *   **bold**          → <strong>
 *   *italic*          → <em>
 *   # Heading         → section header
 *   ## Sub-heading    → smaller header
 *   • / - / * bullet  → styled list item
 *   numbered list     → 1. 2. 3.
 *   `code`            → inline code
 *   [date] prefix     → date badge
 *   emoji lines       → preserved
 *   blank lines       → paragraph breaks
 *   ─── dividers      → visual separator
 */

import React from "react";

// ── Inline formatter: bold, italic, code, links ───────────
function InlineText({ text }) {
  // Split on **bold**, *italic*, `code`
  const parts = [];
  const regex = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;
  let last = 0;
  let m;

  while ((m = regex.exec(text)) !== null) {
    if (m.index > last) {
      parts.push(<span key={last}>{text.slice(last, m.index)}</span>);
    }
    if (m[2]) {
      parts.push(<strong key={m.index} className="font-semibold text-white">{m[2]}</strong>);
    } else if (m[3]) {
      parts.push(<em key={m.index} className="italic text-surface-300">{m[3]}</em>);
    } else if (m[4]) {
      parts.push(
        <code key={m.index}
          className="bg-surface-700 text-soul-300 px-1.5 py-0.5 rounded text-[11px] font-mono">
          {m[4]}
        </code>
      );
    }
    last = m.index + m[0].length;
  }
  if (last < text.length) {
    parts.push(<span key={last}>{text.slice(last)}</span>);
  }
  return <>{parts}</>;
}

// ── Date badge: [2026-03-23] ──────────────────────────────
function DateBadge({ date }) {
  return (
    <span className="inline-flex items-center gap-1 bg-soul-900/40 border border-soul-700/40
                     text-soul-400 text-[10px] font-mono px-1.5 py-0.5 rounded-md mr-1.5">
      📅 {date}
    </span>
  );
}

// ── Parse a single line ───────────────────────────────────
function parseLine(line, idx) {
  const trimmed = line.trim();

  // Empty line — spacer
  if (!trimmed) return <div key={idx} className="h-1" />;

  // Divider: ─── or --- or ===
  if (/^[─\-=]{3,}$/.test(trimmed)) {
    return <hr key={idx} className="border-surface-700/50 my-2" />;
  }

  // H1: # Title
  if (trimmed.startsWith("# ")) {
    return (
      <h3 key={idx} className="text-sm font-bold text-white mt-3 mb-1 tracking-tight">
        <InlineText text={trimmed.slice(2)} />
      </h3>
    );
  }

  // H2: ## Sub-title
  if (trimmed.startsWith("## ")) {
    return (
      <h4 key={idx} className="text-xs font-semibold text-soul-300 uppercase tracking-wider mt-2 mb-1">
        <InlineText text={trimmed.slice(3)} />
      </h4>
    );
  }

  // Bullet: • or - or * (not bold/italic)
  if (/^[•\-\*]\s/.test(trimmed) && !trimmed.startsWith("**")) {
    const content = trimmed.replace(/^[•\-\*]\s+/, "");

    // Check for [date] prefix inside bullet
    const dateMatch = content.match(/^\[(\d{4}-\d{2}-\d{2})\]\s*(.*)/);
    if (dateMatch) {
      return (
        <div key={idx} className="flex items-start gap-2 py-0.5">
          <span className="text-soul-500 mt-0.5 shrink-0">•</span>
          <span className="text-surface-200 text-sm leading-relaxed">
            <DateBadge date={dateMatch[1]} />
            <InlineText text={dateMatch[2]} />
          </span>
        </div>
      );
    }

    return (
      <div key={idx} className="flex items-start gap-2 py-0.5">
        <span className="text-soul-500 mt-1 shrink-0 text-xs">●</span>
        <span className="text-surface-200 text-sm leading-relaxed">
          <InlineText text={content} />
        </span>
      </div>
    );
  }

  // Numbered list: 1. 2. 3.
  const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
  if (numMatch) {
    return (
      <div key={idx} className="flex items-start gap-2.5 py-0.5">
        <span className="text-soul-400 font-semibold text-xs shrink-0 mt-0.5 min-w-[16px]">
          {numMatch[1]}.
        </span>
        <span className="text-surface-200 text-sm leading-relaxed">
          <InlineText text={numMatch[2]} />
        </span>
      </div>
    );
  }

  // Key: Value pattern (e.g. "Name: Rohit" or "• Name: Rohit")
  const kvMatch = trimmed.match(/^[•\-]?\s*([A-Za-z /]+):\s+(.+)$/);
  if (kvMatch && !trimmed.startsWith("http") && kvMatch[1].length < 30) {
    return (
      <div key={idx} className="flex items-baseline gap-2 py-0.5">
        <span className="text-surface-400 text-xs font-medium shrink-0 min-w-[80px]">
          {kvMatch[1]}
        </span>
        <span className="text-surface-100 text-sm">
          <InlineText text={kvMatch[2]} />
        </span>
      </div>
    );
  }

  // [date] standalone prefix
  const dateLineMatch = trimmed.match(/^\[(\d{4}-\d{2}-\d{2})\]\s*(.*)/);
  if (dateLineMatch) {
    return (
      <div key={idx} className="flex items-start gap-2 py-0.5">
        <DateBadge date={dateLineMatch[1]} />
        <span className="text-surface-200 text-sm leading-relaxed">
          <InlineText text={dateLineMatch[2]} />
        </span>
      </div>
    );
  }

  // Bold-only line (section label)
  if (trimmed.startsWith("**") && trimmed.endsWith("**") && trimmed.length > 4) {
    return (
      <p key={idx} className="text-sm font-semibold text-white mt-2 mb-0.5">
        {trimmed.slice(2, -2)}
      </p>
    );
  }

  // Regular paragraph
  return (
    <p key={idx} className="text-sm text-surface-100 leading-relaxed">
      <InlineText text={trimmed} />
    </p>
  );
}

// ── Main renderer ─────────────────────────────────────────
export default function MessageRenderer({ text }) {
  if (!text) return null;

  // Split into lines, preserving structure
  const lines = text.split("\n");

  // Group consecutive bullet/numbered lines into visual blocks
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line    = lines[i];
    const trimmed = line.trim();

    // Detect start of a list block
    const isBullet  = /^[•\-\*]\s/.test(trimmed) && !trimmed.startsWith("**");
    const isNumeric = /^\d+\.\s/.test(trimmed);

    if (isBullet || isNumeric) {
      // Collect all consecutive list items
      const listItems = [];
      while (i < lines.length) {
        const t = lines[i].trim();
        const stillList = /^[•\-\*]\s/.test(t) || /^\d+\.\s/.test(t) ||
                          (t.startsWith("[") && /^\[\d{4}/.test(t));
        if (!stillList && t !== "") break;
        if (t !== "") listItems.push(lines[i]);
        i++;
      }
      elements.push(
        <div key={`list-${i}`} className="space-y-0.5 my-1">
          {listItems.map((l, j) => parseLine(l, `${i}-${j}`))}
        </div>
      );
    } else {
      elements.push(parseLine(line, i));
      i++;
    }
  }

  return <div className="space-y-0.5">{elements}</div>;
}
