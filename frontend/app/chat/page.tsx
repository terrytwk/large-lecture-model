"use client";

import { useState } from "react";
import ChatWindow from "@/components/ChatWindow";
import type { Message } from "@/lib/api";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(query: string) {
    const userMsg: Message = { role: "user", content: query };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, history: messages }),
    });

    if (!res.body) {
      setLoading(false);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let assistantText = "";
    let sources: Message["sources"] = [];

    setMessages((prev) => [...prev, { role: "assistant", content: "", sources: [] }]);

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      for (const line of decoder.decode(value).split("\n")) {
        if (!line.startsWith("data: ") || line === "data: [DONE]") continue;
        const payload = JSON.parse(line.slice(6));
        if (payload.type === "sources") sources = payload.sources;
        if (payload.type === "delta") {
          assistantText += payload.text;
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = { role: "assistant", content: assistantText, sources };
            return next;
          });
        }
      }
    }
    setLoading(false);
  }

  return (
    <main className="max-w-3xl mx-auto p-4 h-screen flex flex-col">
      <h1 className="text-xl font-semibold mb-4">6.1220 Study Assistant</h1>
      <ChatWindow messages={messages} loading={loading} onSubmit={handleSubmit} />
    </main>
  );
}
