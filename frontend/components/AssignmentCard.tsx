"use client";

import { useEffect, useState } from "react";
import type { Assignment, MaterialResult } from "@/lib/api";

function daysUntil(due: string) {
  return Math.ceil((new Date(due).getTime() - Date.now()) / 86_400_000);
}

function DeadlineBadge({ due_at, submitted }: { due_at: string | null; submitted: boolean }) {
  if (submitted)
    return (
      <span className="shrink-0 text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-medium">
        ✓ Submitted
      </span>
    );
  if (!due_at) return null;
  const d = daysUntil(due_at);
  if (d < 0)
    return (
      <span className="shrink-0 text-xs px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 font-semibold">
        Overdue
      </span>
    );
  if (d === 0)
    return (
      <span className="shrink-0 text-xs px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 font-semibold animate-pulse">
        Due today!
      </span>
    );
  if (d <= 3)
    return (
      <span className="shrink-0 text-xs px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 font-medium">
        {d}d left
      </span>
    );
  if (d <= 7)
    return (
      <span className="shrink-0 text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 font-medium">
        {d}d left
      </span>
    );
  return (
    <span className="shrink-0 text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 font-medium">
      {d}d left
    </span>
  );
}

const SOURCE_LABELS: Record<string, string> = {
  canvas: "Canvas",
  panopto: "Lecture",
  piazza: "Piazza",
  gradescope: "Gradescope",
  manual: "Notes",
};

const TYPE_COLORS: Record<string, string> = {
  transcript: "bg-purple-100 text-purple-700 border-purple-200",
  slide: "bg-indigo-100 text-indigo-700 border-indigo-200",
  post: "bg-teal-100 text-teal-700 border-teal-200",
  assignment: "bg-orange-100 text-orange-700 border-orange-200",
  announcement: "bg-slate-100 text-slate-600 border-slate-200",
};

function MaterialBadge({ m }: { m: MaterialResult }) {
  const color = TYPE_COLORS[m.doc_type] ?? "bg-slate-100 text-slate-600 border-slate-200";
  const label = SOURCE_LABELS[m.source] ?? m.source;
  const name = (m.metadata?.title as string) || (m.metadata?.name as string) || "";
  return (
    <span
      className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full border ${color} max-w-[160px] truncate`}
      title={name || label}
    >
      {label}
      {name ? ` · ${name}` : ""}
    </span>
  );
}

interface Props {
  assignment: Assignment;
  onAskAbout: (name: string) => void;
}

export default function AssignmentCard({ assignment: a, onAskAbout }: Props) {
  const [materials, setMaterials] = useState<MaterialResult[]>([]);
  const [loadingMats, setLoadingMats] = useState(false);

  useEffect(() => {
    if (a.topics.length === 0) return;
    setLoadingMats(true);
    const q = a.topics.slice(0, 3).join(" ");
    fetch(`/api/materials/search?q=${encodeURIComponent(q)}&course_id=6.1220`)
      .then((r) => r.json())
      .then((d) => {
        setMaterials((d.results ?? []).slice(0, 4));
        setLoadingMats(false);
      })
      .catch(() => setLoadingMats(false));
  }, [a.topics]);

  const scorePercent =
    a.score !== null && a.max_score ? Math.round((a.score / a.max_score) * 100) : null;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col gap-3 hover:shadow-md hover:border-slate-300 transition-all">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-slate-800 text-sm leading-snug">{a.name}</h3>
        <DeadlineBadge due_at={a.due_at} submitted={a.submitted} />
      </div>

      {/* Due date */}
      {a.due_at && (
        <p className="text-xs text-slate-400 -mt-1">
          {new Date(a.due_at).toLocaleDateString("en-US", {
            weekday: "short",
            month: "short",
            day: "numeric",
            hour: "numeric",
            minute: "2-digit",
          })}
        </p>
      )}

      {/* Score bar */}
      {scorePercent !== null && (
        <div>
          <div className="flex justify-between text-xs text-slate-500 mb-1.5">
            <span>Score</span>
            <span className="font-medium text-slate-700">
              {a.score} / {a.max_score}{" "}
              <span className="text-slate-400">({scorePercent}%)</span>
            </span>
          </div>
          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                scorePercent >= 90
                  ? "bg-emerald-500"
                  : scorePercent >= 70
                  ? "bg-amber-500"
                  : "bg-rose-500"
              }`}
              style={{ width: `${scorePercent}%` }}
            />
          </div>
        </div>
      )}

      {/* Topics */}
      {a.topics.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {a.topics.map((t) => (
            <span
              key={t}
              className="text-[11px] bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full border border-indigo-100"
            >
              {t}
            </span>
          ))}
        </div>
      )}

      {/* Related materials */}
      {(loadingMats || materials.length > 0) && (
        <div>
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-1.5">
            Related Materials
          </p>
          {loadingMats ? (
            <div className="flex gap-1.5">
              {[1, 2].map((i) => (
                <div key={i} className="h-5 w-20 bg-slate-100 rounded-full animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {materials.map((m) => (
                <MaterialBadge key={m.id} m={m} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Footer actions */}
      <div className="mt-auto flex items-center gap-2">
        <button
          onClick={() => onAskAbout(a.name)}
          className="flex-1 text-xs font-medium text-indigo-600 hover:text-indigo-800 border border-indigo-200 hover:border-indigo-400 hover:bg-indigo-50 rounded-lg px-3 py-2 transition-colors text-left flex items-center gap-1.5"
        >
          <span>💬</span>
          <span>Ask assistant</span>
        </button>
        {a.html_url && (
          <a
            href={a.html_url}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 text-xs font-medium text-slate-500 hover:text-slate-700 border border-slate-200 hover:border-slate-300 hover:bg-slate-50 rounded-lg px-3 py-2 transition-colors"
          >
            Canvas ↗
          </a>
        )}
      </div>
    </div>
  );
}
