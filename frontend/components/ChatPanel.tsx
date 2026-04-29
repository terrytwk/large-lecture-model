"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Message } from "@/lib/api";

const SOURCE_LABELS: Record<string, string> = {
  canvas: "Canvas",
  panopto: "Lecture",
  piazza: "Piazza",
  gradescope: "Gradescope",
  manual: "Notes",
};

const TYPE_COLORS: Record<string, string> = {
  transcript: "bg-purple-100 text-purple-700",
  slide: "bg-indigo-100 text-indigo-700",
  post: "bg-teal-100 text-teal-700",
  assignment: "bg-orange-100 text-orange-700",
  announcement: "bg-slate-100 text-slate-600",
};

interface Props {
  open: boolean;
  onClose: () => void;
  messages: Message[];
  loading: boolean;
  onSubmit: (query: string) => void;
  /** When set, the panel will pre-fill and auto-submit this query. */
  autoQuery?: string | null;
  onAutoQueryConsumed?: () => void;
}

export default function ChatPanel({
  open,
  onClose,
  messages,
  loading,
  onSubmit,
  autoQuery,
  onAutoQueryConsumed,
}: Props) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const autoFired = useRef(false);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input when opened
  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  // Auto-submit the contextual query once
  useEffect(() => {
    if (open && autoQuery && !autoFired.current) {
      autoFired.current = true;
      onSubmit(autoQuery);
      onAutoQueryConsumed?.();
    }
    if (!autoQuery) autoFired.current = false;
  }, [open, autoQuery, onSubmit, onAutoQueryConsumed]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSubmit(input.trim());
    setInput("");
  }

  const SUGGESTED = [
    "What topics are covered this week?",
    "When is the next deadline?",
    "Explain dynamic programming",
  ];

  return (
    <>
      {/* Backdrop (mobile) */}
      {open && (
        <div
          className="fixed inset-0 bg-black/30 z-40 lg:hidden"
          onClick={onClose}
          aria-hidden
        />
      )}

      {/* Slide-in panel */}
      <div
        className={`fixed top-0 right-0 h-full w-full sm:w-[420px] bg-white shadow-2xl z-50 flex flex-col transition-transform duration-300 ease-in-out ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
        role="dialog"
        aria-label="Study Assistant"
      >
        {/* Panel header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 bg-gradient-to-r from-indigo-600 to-indigo-500 text-white">
          <div>
            <h2 className="text-sm font-semibold">Study Assistant</h2>
            <p className="text-xs text-indigo-200 mt-0.5">6.1220 · Design and Analysis of Algorithms</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 transition-colors text-white text-lg leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center mt-8 space-y-4">
              <div className="text-5xl">🎓</div>
              <div>
                <p className="text-sm font-semibold text-slate-700">How can I help you?</p>
                <p className="text-xs text-slate-400 mt-1">
                  Ask about lectures, concepts, deadlines, or materials.
                </p>
              </div>
              {/* Suggested prompts */}
              <div className="flex flex-col gap-2 mt-4">
                {SUGGESTED.map((s) => (
                  <button
                    key={s}
                    onClick={() => onSubmit(s)}
                    className="text-xs text-left text-slate-600 hover:text-indigo-700 bg-slate-50 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-200 rounded-xl px-3 py-2.5 transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div className="max-w-[88%]">
                  {/* Avatar label */}
                  <p
                    className={`text-[10px] font-semibold mb-1 ${
                      msg.role === "user" ? "text-right text-slate-400" : "text-left text-indigo-500"
                    }`}
                  >
                    {msg.role === "user" ? "You" : "Assistant"}
                  </p>

                  <div
                    className={`px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed ${
                      msg.role === "user"
                        ? "bg-indigo-600 text-white rounded-br-sm whitespace-pre-wrap"
                        : "bg-slate-100 text-slate-800 rounded-bl-sm"
                    }`}
                  >
                    {msg.role === "user" ? (
                      msg.content
                    ) : msg.content ? (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                          ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-0.5">{children}</ul>,
                          ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-0.5">{children}</ol>,
                          li: ({ children }) => <li className="text-sm">{children}</li>,
                          code: ({ inline, children }: { inline?: boolean; children?: React.ReactNode }) =>
                            inline ? (
                              <code className="bg-slate-200 text-slate-800 rounded px-1 py-0.5 text-xs font-mono">{children}</code>
                            ) : (
                              <pre className="bg-slate-800 text-slate-100 rounded-lg px-3 py-2 my-2 overflow-x-auto text-xs font-mono"><code>{children}</code></pre>
                            ),
                          strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                          h1: ({ children }) => <h1 className="font-bold text-base mb-1">{children}</h1>,
                          h2: ({ children }) => <h2 className="font-semibold text-sm mb-1">{children}</h2>,
                          h3: ({ children }) => <h3 className="font-semibold text-sm mb-1">{children}</h3>,
                          blockquote: ({ children }) => <blockquote className="border-l-2 border-slate-400 pl-3 italic text-slate-600 my-2">{children}</blockquote>,
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    ) : loading && i === messages.length - 1 ? (
                      <span className="inline-flex gap-1 items-center h-4">
                        {[0, 150, 300].map((delay) => (
                          <span
                            key={delay}
                            className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce"
                            style={{ animationDelay: `${delay}ms` }}
                          />
                        ))}
                      </span>
                    ) : null}
                  </div>

                  {/* Sources */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {msg.sources.map((s) => {
                        const color =
                          TYPE_COLORS[s.doc_type] ?? "bg-slate-100 text-slate-600";
                        return (
                          <span
                            key={s.id}
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium ${color}`}
                          >
                            {SOURCE_LABELS[s.source] ?? s.source}
                            {s.name ? ` · ${s.name}` : ""}
                          </span>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <form
          onSubmit={handleSubmit}
          className="px-4 py-3 border-t border-slate-100 bg-slate-50"
        >
          <div className="flex gap-2 items-end">
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about the course…"
              className="flex-1 text-sm bg-white border border-slate-200 rounded-xl px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent resize-none"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="bg-indigo-600 text-white px-4 py-2.5 rounded-xl text-sm font-semibold hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </div>
          <p className="text-[10px] text-slate-400 mt-2 text-center">
            Never provides direct solutions to graded assignments
          </p>
        </form>
      </div>
    </>
  );
}
