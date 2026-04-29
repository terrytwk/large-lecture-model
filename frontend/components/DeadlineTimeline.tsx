"use client";

import type { Assignment } from "@/lib/api";

function daysUntil(due: string) {
  return Math.ceil((new Date(due).getTime() - Date.now()) / 86_400_000);
}

function assignmentType(name: string): "ps" | "quiz" | "warmup" | "other" {
  const n = name.toLowerCase();
  if (n.includes("problem set") || /\bps\s*\d/.test(n) || n.includes("pset")) return "ps";
  if (n.includes("quiz")) return "quiz";
  if (n.includes("warm")) return "warmup";
  return "other";
}

const TYPE_CFG = {
  ps: {
    label: "Problem Sets",
    dot: "bg-indigo-500",
    badge: "bg-indigo-100 text-indigo-700",
    row: "text-indigo-600",
  },
  quiz: {
    label: "Quizzes",
    dot: "bg-amber-500",
    badge: "bg-amber-100 text-amber-700",
    row: "text-amber-600",
  },
  warmup: {
    label: "Warm-ups",
    dot: "bg-emerald-500",
    badge: "bg-emerald-100 text-emerald-700",
    row: "text-emerald-600",
  },
  other: {
    label: "Other",
    dot: "bg-slate-400",
    badge: "bg-slate-100 text-slate-600",
    row: "text-slate-500",
  },
};

export default function DeadlineTimeline({ assignments }: { assignments: Assignment[] }) {
  const withDates = assignments.filter((a) => a.due_at);
  if (withDates.length === 0) return null;

  const timestamps = withDates.map((a) => new Date(a.due_at!).getTime());
  const minTs = Math.min(...timestamps);
  const maxTs = Math.max(...timestamps);
  // Pad 5% on each side so dots aren't clipped at edges
  const padding = (maxTs - minTs) * 0.05 || 86_400_000;
  const start = minTs - padding;
  const end = maxTs + padding;
  const span = end - start;

  const pct = (ts: number) => Math.max(0, Math.min(100, ((ts - start) / span) * 100));
  const todayPct = pct(Date.now());

  // Deduplicate week boundaries
  const weekMs = 7 * 86_400_000;
  const weeks: Date[] = [];
  let cur = new Date(start);
  cur.setHours(0, 0, 0, 0);
  cur.setDate(cur.getDate() - cur.getDay());
  while (cur.getTime() <= end) {
    weeks.push(new Date(cur));
    cur = new Date(cur.getTime() + weekMs);
  }

  const groups = (["ps", "quiz", "warmup", "other"] as const)
    .map((t) => ({ type: t, items: withDates.filter((a) => assignmentType(a.name) === t) }))
    .filter((g) => g.items.length > 0);

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5">
      <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-5">
        Semester Timeline
      </h2>

      <div className="space-y-4">
        {/* Week labels row */}
        <div className="flex">
          <div className="w-28 shrink-0" />
          <div className="relative flex-1 h-5">
            {weeks.map((w, i) => {
              const p = pct(w.getTime());
              if (p < 0 || p > 100) return null;
              return (
                <span
                  key={i}
                  className="absolute -translate-x-1/2 text-[10px] text-slate-400 whitespace-nowrap"
                  style={{ left: `${p}%` }}
                >
                  {w.toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                </span>
              );
            })}
          </div>
        </div>

        {/* Assignment rows */}
        {groups.map(({ type, items }) => {
          const cfg = TYPE_CFG[type];
          return (
            <div key={type} className="flex items-center">
              <span
                className={`w-28 shrink-0 text-right text-xs font-semibold pr-4 ${cfg.row}`}
              >
                {cfg.label}
              </span>
              <div className="relative flex-1 h-8">
                {/* Track line */}
                <div className="absolute top-1/2 inset-x-0 h-px bg-slate-100" />

                {/* Today line */}
                <div
                  className="absolute top-0 bottom-0 w-px bg-rose-300 z-10"
                  style={{ left: `${todayPct}%` }}
                />

                {/* Assignment dots */}
                {items.map((a) => {
                  const p = pct(new Date(a.due_at!).getTime());
                  const days = daysUntil(a.due_at!);
                  let dotCls = cfg.dot;
                  if (a.submitted) dotCls = "bg-slate-300";
                  else if (days < 0) dotCls = "bg-rose-600";
                  else if (days <= 3) dotCls = "bg-orange-500";

                  return (
                    <div
                      key={a.id}
                      className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 group z-20"
                      style={{ left: `${p}%` }}
                    >
                      <div
                        className={`w-3.5 h-3.5 rounded-full ${dotCls} ring-2 ring-white shadow-sm cursor-default hover:scale-125 transition-transform`}
                      />
                      {/* Hover tooltip */}
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:flex flex-col items-center z-30 pointer-events-none">
                        <div
                          className={`${cfg.badge} text-[11px] font-medium px-2.5 py-1.5 rounded-lg shadow-md whitespace-nowrap text-center`}
                        >
                          <p className="font-semibold">{a.name}</p>
                          <p className="font-normal opacity-80 mt-0.5">
                            {a.submitted
                              ? "Submitted"
                              : days < 0
                              ? `${Math.abs(days)}d overdue`
                              : days === 0
                              ? "Due today!"
                              : `Due in ${days}d`}
                          </p>
                        </div>
                        <div className="w-2 h-2 rotate-45 -mt-1 bg-current opacity-20" />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}

        {/* Today label */}
        <div className="flex">
          <div className="w-28 shrink-0" />
          <div className="relative flex-1">
            <span
              className="absolute -translate-x-1/2 text-[10px] font-semibold text-rose-500"
              style={{ left: `${todayPct}%` }}
            >
              Today
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
