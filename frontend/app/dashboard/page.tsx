"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Assignment, Message } from "@/lib/api";
import StatsRow from "@/components/StatsRow";
import DeadlineTimeline from "@/components/DeadlineTimeline";
import AssignmentCard from "@/components/AssignmentCard";
import ChatPanel from "@/components/ChatPanel";

const COURSE_ID = "6.1220";
const COURSE_NAME = "Design and Analysis of Algorithms";

function daysUntil(due: string) {
  return Math.ceil((new Date(due).getTime() - Date.now()) / 86_400_000);
}

function UrgentBanner({
  assignment,
  onAsk,
}: {
  assignment: Assignment;
  onAsk: () => void;
}) {
  if (!assignment.due_at) return null;
  const d = daysUntil(assignment.due_at);
  if (d > 3 || assignment.submitted) return null;

  const isToday = d === 0;
  const isOverdue = d < 0;

  return (
    <div
      className={`rounded-xl border px-5 py-4 flex items-center gap-4 ${
        isOverdue
          ? "bg-rose-50 border-rose-300"
          : isToday
          ? "bg-orange-50 border-orange-300"
          : "bg-amber-50 border-amber-200"
      }`}
    >
      <span className="text-2xl shrink-0">{isOverdue ? "🔴" : isToday ? "⚠️" : "⏰"}</span>
      <div className="flex-1 min-w-0">
        <p
          className={`text-sm font-semibold ${
            isOverdue ? "text-rose-800" : isToday ? "text-orange-800" : "text-amber-800"
          }`}
        >
          {isOverdue
            ? `Overdue by ${Math.abs(d)} day${Math.abs(d) !== 1 ? "s" : ""}`
            : isToday
            ? "Due today!"
            : `Due in ${d} day${d !== 1 ? "s" : ""}`}
          {" · "}
          {assignment.name}
        </p>
        {assignment.topics.length > 0 && (
          <p className="text-xs text-slate-500 mt-0.5 truncate">
            Topics: {assignment.topics.join(", ")}
          </p>
        )}
      </div>
      <button
        onClick={onAsk}
        className={`shrink-0 text-xs font-semibold px-3 py-1.5 rounded-lg border transition-colors ${
          isOverdue
            ? "border-rose-300 text-rose-700 hover:bg-rose-100"
            : "border-amber-300 text-amber-700 hover:bg-amber-100"
        }`}
      >
        Ask assistant →
      </button>
    </div>
  );
}

type FilterTab = "all" | "pending" | "submitted";

export default function DashboardPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [filter, setFilter] = useState<FilterTab>("all");

  // Chat state
  const [chatOpen, setChatOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [autoQuery, setAutoQuery] = useState<string | null>(null);

  // Keep messages fresh for streaming closure
  const messagesRef = useRef<Message[]>([]);
  messagesRef.current = messages;

  useEffect(() => {
    fetch(`/api/assignments?course_id=${COURSE_ID}`)
      .then((r) => r.json())
      .then((d) => {
        setAssignments(d.assignments ?? []);
        setLoadingData(false);
      })
      .catch(() => setLoadingData(false));
  }, []);

  const handleChatSubmit = useCallback(async (query: string) => {
    const userMsg: Message = { role: "user", content: query };
    setMessages((prev) => [...prev, userMsg]);
    setChatLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          course_id: COURSE_ID,
          history: messagesRef.current,
        }),
      });

      if (!res.body) {
        setChatLoading(false);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let text = "";
      let sources: Message["sources"] = [];

      setMessages((prev) => [...prev, { role: "assistant", content: "", sources: [] }]);

      outer: while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        for (const line of decoder.decode(value).split("\n")) {
          if (!line.startsWith("data: ")) continue;
          if (line === "data: [DONE]") break outer;
          try {
            const ev = JSON.parse(line.slice(6));
            if (ev.type === "sources") sources = ev.sources;
            if (ev.type === "delta") {
              text += ev.text;
              setMessages((prev) => {
                const next = [...prev];
                next[next.length - 1] = { role: "assistant", content: text, sources };
                return next;
              });
            }
          } catch {
            // skip malformed line
          }
        }
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "⚠️ Could not connect to the backend. Make sure `uvicorn backend.main:app` is running on port 8000.",
          sources: [],
        },
      ]);
    }

    setChatLoading(false);
  }, []);

  const handleAskAbout = useCallback(
    (assignmentName: string) => {
      const q = `I'm working on "${assignmentName}". What topics should I study and where can I find related lectures or materials?`;
      setAutoQuery(q);
      setChatOpen(true);
    },
    []
  );

  const openChat = useCallback(() => {
    setAutoQuery(null);
    setChatOpen(true);
  }, []);

  // Sorted assignments: pending first, then by due date ascending
  const sorted = [...assignments]
    .filter((a) => {
      if (filter === "pending") return !a.submitted;
      if (filter === "submitted") return a.submitted;
      return true;
    })
    .sort((a, b) => {
      if (a.submitted !== b.submitted) return a.submitted ? 1 : -1;
      if (!a.due_at && !b.due_at) return 0;
      if (!a.due_at) return 1;
      if (!b.due_at) return -1;
      return new Date(a.due_at).getTime() - new Date(b.due_at).getTime();
    });

  // Next urgent assignment (pending, with soonest due date ≤ 3 days)
  const urgentNext = assignments
    .filter((a) => !a.submitted && a.due_at && daysUntil(a.due_at) <= 3)
    .sort((a, b) => new Date(a.due_at!).getTime() - new Date(b.due_at!).getTime())[0] ?? null;

  const FILTERS: { key: FilterTab; label: string }[] = [
    { key: "all", label: "All" },
    { key: "pending", label: "Pending" },
    { key: "submitted", label: "Submitted" },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* ── Top navigation ── */}
      <header className="sticky top-0 z-30 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white text-sm font-bold shrink-0">
              L
            </div>
            <div className="min-w-0">
              <h1 className="text-sm font-semibold text-slate-800 truncate leading-tight">
                6.1220 · {COURSE_NAME}
              </h1>
              <p className="text-[11px] text-slate-400 leading-tight">Spring 2026 · MIT</p>
            </div>
          </div>

          <button
            onClick={openChat}
            className="shrink-0 flex items-center gap-2 bg-indigo-600 text-white text-sm font-medium px-4 py-2 rounded-xl hover:bg-indigo-700 transition-colors"
          >
            <span>💬</span>
            <span className="hidden sm:inline">Study Assistant</span>
          </button>
        </div>
      </header>

      {/* ── Main content ── */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-6 space-y-5">
        {/* Stats */}
        {!loadingData && <StatsRow assignments={assignments} />}

        {/* Urgent banner */}
        {!loadingData && urgentNext && (
          <UrgentBanner
            assignment={urgentNext}
            onAsk={() => handleAskAbout(urgentNext.name)}
          />
        )}

        {/* Timeline */}
        {!loadingData && assignments.length > 0 && (
          <DeadlineTimeline assignments={assignments} />
        )}

        {/* Assignments section */}
        <section>
          <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
            <h2 className="text-sm font-semibold text-slate-700">Assignments</h2>
            <div className="flex bg-slate-100 rounded-lg p-0.5 gap-0.5">
              {FILTERS.map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setFilter(key)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    filter === key
                      ? "bg-white text-slate-700 shadow-sm"
                      : "text-slate-500 hover:text-slate-700"
                  }`}
                >
                  {label}
                  {key !== "all" && (
                    <span className="ml-1 text-slate-400">
                      (
                      {key === "pending"
                        ? assignments.filter((a) => !a.submitted).length
                        : assignments.filter((a) => a.submitted).length}
                      )
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Loading skeleton */}
          {loadingData ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div
                  key={i}
                  className="bg-white border border-slate-200 rounded-xl p-4 space-y-3 animate-pulse"
                >
                  <div className="flex justify-between gap-2">
                    <div className="h-4 bg-slate-100 rounded w-3/4" />
                    <div className="h-5 bg-slate-100 rounded-full w-16" />
                  </div>
                  <div className="h-3 bg-slate-100 rounded w-1/2" />
                  <div className="flex gap-1.5 pt-1">
                    <div className="h-4 bg-slate-100 rounded-full w-14" />
                    <div className="h-4 bg-slate-100 rounded-full w-20" />
                  </div>
                  <div className="h-8 bg-slate-100 rounded-lg mt-2" />
                </div>
              ))}
            </div>
          ) : sorted.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-xl py-16 text-center">
              <p className="text-4xl mb-3">
                {assignments.length === 0 ? "📚" : "✅"}
              </p>
              <p className="text-sm font-semibold text-slate-600 mb-1">
                {assignments.length === 0
                  ? "No assignments loaded yet"
                  : `No ${filter} assignments`}
              </p>
              {assignments.length === 0 && (
                <p className="text-xs text-slate-400 max-w-xs mx-auto">
                  Run{" "}
                  <code className="font-mono bg-slate-100 px-1 rounded">
                    python scripts/run_ingest.py
                  </code>{" "}
                  to pull course data from Canvas.
                </p>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {sorted.map((a) => (
                <AssignmentCard key={a.id} assignment={a} onAskAbout={handleAskAbout} />
              ))}
            </div>
          )}
        </section>
      </main>

      {/* ── Chat panel ── */}
      <ChatPanel
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        messages={messages}
        loading={chatLoading}
        onSubmit={handleChatSubmit}
        autoQuery={autoQuery}
        onAutoQueryConsumed={() => setAutoQuery(null)}
      />

      {/* Floating action button (when chat is closed) */}
      {!chatOpen && (
        <button
          onClick={openChat}
          className="fixed bottom-6 right-6 w-14 h-14 bg-indigo-600 text-white rounded-full shadow-lg hover:bg-indigo-700 hover:scale-105 transition-all flex items-center justify-center text-2xl z-40"
          aria-label="Open study assistant"
        >
          💬
        </button>
      )}
    </div>
  );
}
