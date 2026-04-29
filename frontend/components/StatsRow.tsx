import type { Assignment } from "@/lib/api";

function daysUntil(due: string): number {
  return Math.ceil((new Date(due).getTime() - Date.now()) / 86_400_000);
}

interface Stat {
  label: string;
  value: string | number;
  color: string;
  bg: string;
  border: string;
  icon: string;
}

export default function StatsRow({ assignments }: { assignments: Assignment[] }) {
  const total = assignments.length;
  const submitted = assignments.filter((a) => a.submitted).length;
  const overdue = assignments.filter(
    (a) => !a.submitted && a.due_at && daysUntil(a.due_at) < 0
  ).length;
  const dueSoon = assignments.filter(
    (a) => !a.submitted && a.due_at && daysUntil(a.due_at) >= 0 && daysUntil(a.due_at) <= 7
  ).length;

  const graded = assignments.filter((a) => a.score !== null && a.max_score);
  const avgScore =
    graded.length > 0
      ? Math.round(
          graded.reduce((s, a) => s + (a.score! / a.max_score!) * 100, 0) / graded.length
        )
      : null;

  const stats: Stat[] = [
    {
      label: "Total",
      value: total,
      icon: "📋",
      color: "text-slate-700",
      bg: "bg-white",
      border: "border-slate-200",
    },
    {
      label: "Submitted",
      value: submitted,
      icon: "✅",
      color: "text-emerald-700",
      bg: "bg-emerald-50",
      border: "border-emerald-200",
    },
    {
      label: "Due This Week",
      value: dueSoon,
      icon: "⏰",
      color: "text-amber-700",
      bg: "bg-amber-50",
      border: "border-amber-200",
    },
    {
      label: "Overdue",
      value: overdue,
      icon: "🔴",
      color: "text-rose-700",
      bg: "bg-rose-50",
      border: "border-rose-200",
    },
    ...(avgScore !== null
      ? [
          {
            label: "Avg Score",
            value: `${avgScore}%`,
            icon: "📊",
            color: "text-indigo-700",
            bg: "bg-indigo-50",
            border: "border-indigo-200",
          } as Stat,
        ]
      : []),
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3">
      {stats.map((s) => (
        <div
          key={s.label}
          className={`${s.bg} ${s.border} border rounded-xl p-4 flex flex-col gap-1`}
        >
          <span className="text-lg">{s.icon}</span>
          <p className={`text-2xl font-bold tracking-tight ${s.color}`}>{s.value}</p>
          <p className="text-xs text-slate-500 font-medium">{s.label}</p>
        </div>
      ))}
    </div>
  );
}
