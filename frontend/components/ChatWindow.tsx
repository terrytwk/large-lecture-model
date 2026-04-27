"use client";

import { useEffect, useRef, useState } from "react";
import SourceCard from "./SourceCard";
import type { Message } from "@/lib/api";

interface Props {
  messages: Message[];
  loading: boolean;
  onSubmit: (query: string) => void;
}

export default function ChatWindow({ messages, loading, onSubmit }: Props) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSubmit(input.trim());
    setInput("");
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 && (
          <p className="text-gray-400 text-sm text-center mt-16">
            Ask anything about lectures, assignments, or course concepts.
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={msg.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-xl px-4 py-2 rounded-lg text-sm whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-white border border-gray-200 text-gray-800"
              }`}
            >
              {msg.content || (loading && i === messages.length - 1 ? "..." : "")}
            </div>
            {msg.sources && msg.sources.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {msg.sources.map((s) => (
                  <SourceCard key={s.id} source={s} />
                ))}
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={handleSubmit} className="flex gap-2 pt-2 border-t border-gray-200">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about the course..."
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
