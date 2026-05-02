---
theme: default
colorSchema: dark
title: "Large Lecture Model: Course Intelligence for Students"
titleTemplate: "%s"
highlighter: shiki
drawings:
  persist: false
transition: slide-left
mdc: true
fonts:
  sans: "Inter"
  mono: "Fira Code"
layout: cover
background: "#0f172a"
---

<div class="text-left">
  <div class="text-xs text-blue-300 font-mono mb-3 tracking-widest uppercase">CMS.594 · Education Technology Studio · MIT</div>
  <h1 class="text-5xl font-bold text-white leading-tight mb-3">Large Lecture Model</h1>
  <p class="text-lg text-slate-300 max-w-xl leading-relaxed mb-5">
    A course-content intelligence platform that unifies fragmented learning environments — so students can study, not search.
  </p>
  <div class="text-slate-400 text-sm">Tae Wook (Terry) Kim · Spring 2026</div>
</div>

---
layout: default
---

# The Problem

<div class="grid grid-cols-2 gap-6 mt-3">
<div>

<div class="text-xs text-slate-400 uppercase tracking-wide font-semibold mb-2">A single course lives on 5+ platforms</div>
<div class="space-y-2">
  <div class="flex items-center gap-2 p-2 rounded-lg bg-slate-800/60 border border-slate-700 text-sm">
    <div class="w-2 h-2 rounded-full bg-blue-400 flex-shrink-0"></div>
    <span class="text-slate-200"><strong>Canvas</strong> — syllabus, slides, assignments</span>
  </div>
  <div class="flex items-center gap-2 p-2 rounded-lg bg-slate-800/60 border border-slate-700 text-sm">
    <div class="w-2 h-2 rounded-full bg-purple-400 flex-shrink-0"></div>
    <span class="text-slate-200"><strong>Gradescope</strong> — problem sets, feedback, grades</span>
  </div>
  <div class="flex items-center gap-2 p-2 rounded-lg bg-slate-800/60 border border-slate-700 text-sm">
    <div class="w-2 h-2 rounded-full bg-green-400 flex-shrink-0"></div>
    <span class="text-slate-200"><strong>Panopto</strong> — lecture recordings & transcripts</span>
  </div>
  <div class="flex items-center gap-2 p-2 rounded-lg bg-slate-800/60 border border-slate-700 text-sm">
    <div class="w-2 h-2 rounded-full bg-yellow-400 flex-shrink-0"></div>
    <span class="text-slate-200"><strong>Piazza</strong> — Q&A threads, instructor answers</span>
  </div>
</div>

</div>
<div>

<div class="text-xs text-slate-400 uppercase tracking-wide font-semibold mb-2">The cognitive cost</div>
<blockquote class="pl-3 border-l-4 border-blue-400 text-slate-300 italic text-sm leading-relaxed mb-3">
"A student cannot easily cross-reference which lectures introduced a concept, which problem sets assessed it, and which Piazza threads clarified it."
</blockquote>

<div class="p-3 rounded-lg bg-red-950/40 border border-red-800/50 mb-2">
  <p class="text-red-300 font-semibold text-xs">Sweller (1988) — Cognitive Load Theory</p>
  <p class="text-slate-300 text-xs mt-0.5">Platform fragmentation imposes <strong>extraneous load</strong> — cognitive effort spent navigating, not learning.</p>
</div>

</div>
</div>

<div class="mt-4 px-6 py-4 rounded-xl bg-blue-600/20 border border-blue-500/60 text-center" style="background: linear-gradient(135deg, rgba(37,99,235,0.25), rgba(99,102,241,0.2));">
  <p class="text-blue-100 text-lg font-semibold tracking-wide">One interface. All course sources. Cited answers.</p>
</div>

---
layout: default
---

# Why This Design?

<div class="grid grid-cols-3 gap-3 mt-3">

<div class="p-3 rounded-xl bg-blue-950/50 border border-blue-700/50">
  <div class="text-xl mb-1">🧠</div>
  <h3 class="font-bold text-blue-300 text-xs uppercase tracking-wide mb-1">Cognitive Load</h3>
  <p class="text-slate-300 text-xs leading-relaxed">Sweller (1988): reduce <em>extraneous</em> load so students direct working memory toward learning, not navigation.</p>
</div>

<div class="p-3 rounded-xl bg-purple-950/50 border border-purple-700/50">
  <div class="text-xl mb-1">🎯</div>
  <h3 class="font-bold text-purple-300 text-xs uppercase tracking-wide mb-1">Self-Regulated Learning</h3>
  <p class="text-slate-300 text-xs leading-relaxed">Zimmerman (2002): learners who plan, monitor, and evaluate their own study process outperform passive consumers.</p>
</div>

<div class="p-3 rounded-xl bg-green-950/50 border border-green-700/50">
  <div class="text-xl mb-1">🔄</div>
  <h3 class="font-bold text-green-300 text-xs uppercase tracking-wide mb-1">Retrieval Practice</h3>
  <p class="text-slate-300 text-xs leading-relaxed">Roediger & Karpicke (2006): actively recalling information produces superior long-term retention vs. re-reading.</p>
</div>

</div>

<div class="grid grid-cols-2 gap-3 mt-3">

<div class="p-3 rounded-xl bg-slate-800/60 border border-slate-600">
  <p class="text-slate-200 text-xs"><strong class="text-white">Why RAG?</strong> A general LLM hallucinates course-specific facts. Retrieval-Augmented Generation (Lewis et al., 2020) grounds every answer in actual course documents with inline citations.</p>
</div>

<div class="p-3 rounded-xl bg-amber-950/40 border border-amber-700/50">
  <p class="text-slate-200 text-xs"><strong class="text-amber-300">Behavioral concept design</strong> (6.1040 TA, 2025): model <em>behaviors</em> — asking, posting, submitting — not platform schemas. "Behaviors hold still even when platforms do not."</p>
</div>

</div>

---
layout: default
---

# How It Works

<div class="flex justify-center mt-2">
  <img src="./img/system-diagram.png" class="h-96 object-contain rounded-xl" />
</div>

---
layout: default
---

# The Knowledge Graph (6.1220)

<div class="flex justify-center mt-1">
  <img src="./img/graph-visualization.png" class="rounded-xl object-contain" style="max-height:320px; width:100%;" />
</div>

<p class="text-slate-500 text-xs mt-1.5 text-center">Auto-built from Canvas + Panopto</p>

<blockquote class="mt-3 pl-4 border-l-4 border-purple-400 text-slate-300 italic text-sm leading-relaxed">
  "Students who study with concept maps outperform those who re-read — the map makes prerequisite structure visible."
  <span class="not-italic text-slate-500 text-xs block mt-0.5">— Chi, Feltovich & Glaser (1981); Novak & Gowin (1984)</span>
</blockquote>

---
layout: default
---

# The Web Interface

<div class="grid grid-cols-2 gap-5 mt-3">

<div class="flex flex-col gap-2">
  <div class="text-xs text-blue-300 uppercase tracking-wide font-semibold">Study Assistant — Chat</div>
  <img src="./img/chatbot-frontend.png" class="rounded-xl border border-slate-700 object-contain mx-auto" style="max-height:310px;" />
  <div class="px-2 py-1.5 rounded bg-red-950/30 border border-red-800/40 text-xs text-slate-300">
    <span class="text-red-400 font-semibold">Guardrail: </span>"Solve PS4 Q2" → blocked, redirects to lecture material.
  </div>
</div>

<div class="flex flex-col gap-2">
  <div class="text-xs text-purple-300 uppercase tracking-wide font-semibold">Dashboard — Assignments & Timeline</div>
  <img src="./img/assignment-frontend.png" class="rounded-xl border border-slate-700 w-full object-contain" style="max-height:310px;" />
  <div class="px-2 py-1.5 rounded bg-purple-950/30 border border-purple-800/40 text-xs text-slate-300">
    <span class="text-purple-400 font-semibold">Study planner: </span>Full semester timeline with topic map and "Ask assistant" per assignment.
  </div>
</div>

</div>

---
layout: default
---

# Feedback: Srini (Professor, MIT 6.1220)

<div class="grid grid-cols-2 gap-3 mt-3">

<div class="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
  <div class="text-blue-400 text-xs font-semibold uppercase tracking-wide mb-1">The core tension</div>
  <p class="text-slate-200 text-xs italic mb-1">"LLMs are most powerful once students already have enough understanding to use and verify them well. The challenge is helping students get there through practice."</p>
  <p class="text-slate-500 text-xs">→ Reframed the system: assist <em>after</em> the student has engaged, not instead of engaging.</p>
</div>

<div class="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
  <div class="text-blue-400 text-xs font-semibold uppercase tracking-wide mb-1">Productive struggle risk</div>
  <p class="text-slate-200 text-xs italic mb-1">"Students may use the LLM to bypass the productive struggle — that's where the learning happens."</p>
  <p class="text-slate-500 text-xs">→ Prompted approach-first tutoring: system asks what the student has tried before helping.</p>
</div>

<div class="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
  <div class="text-blue-400 text-xs font-semibold uppercase tracking-wide mb-1">LLM verification weakness</div>
  <p class="text-slate-200 text-xs italic mb-1">"LLMs often say an approach 'could work' — they are weak at rigorous verification."</p>
  <p class="text-slate-500 text-xs">→ Added explicit verification mode: checks runtime, edge cases, and proof gaps rather than endorsing.</p>
</div>

<div class="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
  <div class="text-blue-400 text-xs font-semibold uppercase tracking-wide mb-1">High-value use cases</div>
  <p class="text-slate-200 text-xs italic mb-1">"Concept maps, notation guides, connecting ideas across the semester — these are where it genuinely helps."</p>
  <p class="text-slate-500 text-xs">→ Prioritized concept map view and notation cheatsheet generation as first-class features.</p>
</div>

</div>

---
layout: default
---

# Feedback: Eagon (TA, 6.1040 & Agentic Harness Researcher)

<div class="grid grid-cols-2 gap-3 mt-3">

<div class="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
  <div class="text-amber-400 text-xs font-semibold uppercase tracking-wide mb-1">Design philosophy</div>
  <p class="text-slate-200 text-xs italic mb-1">"Design the way you can't fail — capture useful learning signals rather than trying to solve personalized learning immediately."</p>
  <p class="text-slate-500 text-xs">→ Shifted focus to building structured representations first; chatbot is a later layer on top.</p>
</div>

<div class="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
  <div class="text-amber-400 text-xs font-semibold uppercase tracking-wide mb-1">Intermediate system first</div>
  <p class="text-slate-200 text-xs italic mb-1">"Don't start by building a full end-to-end chatbot. Build something that captures and structures the learning process."</p>
  <p class="text-slate-500 text-xs">→ Reinforced behavioral event-log design: concepts, prompts, chunks, and student questions as structured data.</p>
</div>

<div class="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
  <div class="text-amber-400 text-xs font-semibold uppercase tracking-wide mb-1">Metadata & access control</div>
  <p class="text-slate-200 text-xs italic mb-1">"Think carefully about metadata, access control, and what each retrieved chunk is <em>allowed to do</em>."</p>
  <p class="text-slate-500 text-xs">→ Extended content-gating: each chunk carries allowed actions (explain, hint, block) alongside its metadata.</p>
</div>

<div class="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
  <div class="text-amber-400 text-xs font-semibold uppercase tracking-wide mb-1">Previous exams</div>
  <p class="text-slate-200 text-xs italic mb-1">"Previous exams help students understand what they need to know — but must be handled carefully."</p>
  <p class="text-slate-500 text-xs">→ Past exams enabled in concept-map mode only; solution paths remain gated behind <code class="bg-slate-700 px-0.5 rounded">protected: true</code>.</p>
</div>

</div>

---
layout: default
---

# How Feedback Was Implemented

<div class="grid grid-cols-3 gap-3 mt-3">

<div class="p-3 rounded-xl bg-blue-950/50 border border-blue-700/50">
  <div class="text-lg mb-1">🤔</div>
  <div class="font-bold text-blue-300 text-xs mb-1">Approach-first tutoring</div>
  <p class="text-slate-300 text-xs leading-relaxed">System asks what the student has already tried before providing help — protecting productive struggle (Srini).</p>
</div>

<div class="p-3 rounded-xl bg-purple-950/50 border border-purple-700/50">
  <div class="text-lg mb-1">💡</div>
  <div class="font-bold text-purple-300 text-xs mb-1">Hint-based guidance</div>
  <p class="text-slate-300 text-xs leading-relaxed">Responses offer the next step or a clarifying question rather than a full solution. Solution requests redirect to office hours.</p>
</div>

<div class="p-3 rounded-xl bg-green-950/50 border border-green-700/50">
  <div class="text-lg mb-1">🔍</div>
  <div class="font-bold text-green-300 text-xs mb-1">Verification mode</div>
  <p class="text-slate-300 text-xs leading-relaxed">Dedicated mode checks an approach for correctness, runtime complexity, edge cases, and proof gaps — not endorsement (Srini).</p>
</div>

</div>

<div class="grid grid-cols-3 gap-3 mt-3">

<div class="p-3 rounded-xl bg-amber-950/50 border border-amber-700/50">
  <div class="text-lg mb-1">🗺️</div>
  <div class="font-bold text-amber-300 text-xs mb-1">Concept maps & notation</div>
  <p class="text-slate-300 text-xs leading-relaxed">Topic-map view and notation cheatsheet generation promoted to first-class features — Srini's highest-confidence use cases.</p>
</div>

<div class="p-3 rounded-xl bg-red-950/40 border border-red-700/50">
  <div class="text-lg mb-1">🔒</div>
  <div class="font-bold text-red-300 text-xs mb-1">Chunk-level access control</div>
  <p class="text-slate-300 text-xs leading-relaxed">Each retrieved chunk carries an allowed-actions flag (explain / hint / block). Past exams visible in concept-map mode only (Eagon).</p>
</div>

<div class="p-3 rounded-xl bg-cyan-950/40 border border-cyan-700/50">
  <div class="text-lg mb-1">📊</div>
  <div class="font-bold text-cyan-300 text-xs mb-1">Staff misunderstanding dashboard</div>
  <p class="text-slate-300 text-xs leading-relaxed">Aggregate view of common questions and blocked topics helps staff spot recurring confusions without seeing individual student data.</p>
</div>

</div>

---
layout: default
---

# Open Questions

<div class="grid grid-cols-2 gap-3 mt-3">

<div class="p-3 rounded-xl bg-slate-800/60 border border-slate-600">
  <div class="flex items-center gap-1.5 mb-1">
    <span class="text-yellow-400 font-bold">?</span>
    <span class="text-white font-semibold text-sm">When is LLM help actually safe?</span>
  </div>
  <p class="text-slate-300 text-xs leading-relaxed">Srini's framing: LLMs are valuable once students can verify the output. How do we detect that threshold — and should we gate assistance behind it?</p>
</div>

<div class="p-3 rounded-xl bg-slate-800/60 border border-slate-600">
  <div class="flex items-center gap-1.5 mb-1">
    <span class="text-yellow-400 font-bold">?</span>
    <span class="text-white font-semibold text-sm">Measuring productive struggle bypass</span>
  </div>
  <p class="text-slate-300 text-xs leading-relaxed">Approach-first tutoring is a policy — but can we measure whether students actually attempt problems before querying? What signals exist in the event log?</p>
</div>

<div class="p-3 rounded-xl bg-slate-800/60 border border-slate-600">
  <div class="flex items-center gap-1.5 mb-1">
    <span class="text-yellow-400 font-bold">?</span>
    <span class="text-white font-semibold text-sm">Rigorous verification reliability</span>
  </div>
  <p class="text-slate-300 text-xs leading-relaxed">Verification mode is only useful if it catches real errors. How do we evaluate whether the LLM reliably identifies wrong runtimes, missed edge cases, and proof gaps?</p>
</div>

<div class="p-3 rounded-xl bg-slate-800/60 border border-slate-600">
  <div class="flex items-center gap-1.5 mb-1">
    <span class="text-yellow-400 font-bold">?</span>
    <span class="text-white font-semibold text-sm">Old exam / pset material risk</span>
  </div>
  <p class="text-slate-300 text-xs leading-relaxed">Past exams are useful for scope — but they may contain isomorphic problems to current psets. What metadata and gating rules prevent accidental leakage?</p>
</div>

</div>

---
layout: default
---

# Why Should You Use This?

<div class="grid grid-cols-2 gap-5 mt-3">
<div>

<div class="text-xs text-blue-300 uppercase tracking-wide font-semibold mb-2">For students</div>
<div class="space-y-2">
  <div class="p-2.5 rounded-lg bg-blue-950/40 border border-blue-800/40 text-xs text-slate-200">
    <strong class="text-blue-300">Helps you think, not think for you.</strong> Approach-first tutoring and hint-based guidance protect the productive struggle where learning happens (Srini, 2026).
  </div>
  <div class="p-2.5 rounded-lg bg-blue-950/40 border border-blue-800/40 text-xs text-slate-200">
    <strong class="text-blue-300">Verify your reasoning.</strong> Dedicated verification mode checks your approach for correctness, runtime, and edge cases — the kind of critique a good tutor gives.
  </div>
  <div class="p-2.5 rounded-lg bg-blue-950/40 border border-blue-800/40 text-xs text-slate-200">
    <strong class="text-blue-300">See the shape of the course.</strong> Concept maps and notation guides surface prerequisite structure so you can close gaps before an exam (Chi et al., 1981).
  </div>
</div>

</div>
<div>

<div class="text-xs text-amber-300 uppercase tracking-wide font-semibold mb-2">For instructors & programs</div>
<div class="space-y-2">
  <div class="p-2.5 rounded-lg bg-amber-950/40 border border-amber-800/40 text-xs text-slate-200">
    <strong class="text-amber-300">Surface what students are confused about.</strong> Staff dashboard aggregates common questions and blocked topics — without any PII — so you know where to spend office hours.
  </div>
  <div class="p-2.5 rounded-lg bg-amber-950/40 border border-amber-800/40 text-xs text-slate-200">
    <strong class="text-amber-300">Fine-grained content control.</strong> Per-chunk access rules and configurable date-windows keep restricted material gated — even past exams can be unlocked just for concept review.
  </div>
  <div class="p-2.5 rounded-lg bg-amber-950/40 border border-amber-800/40 text-xs text-slate-200">
    <strong class="text-amber-300">Structured learning signals, not just a chatbot.</strong> The behavioral event-log captures concepts, prompts, and student questions as data you can build on (Eagon, 2026).
  </div>
</div>

</div>
</div>

---
layout: default
---

# What's Left

<div class="grid grid-cols-2 gap-5 mt-3">

<div>
<div class="text-xs text-green-300 uppercase tracking-wide font-semibold mb-2">✅ Completed</div>
<div class="space-y-1 text-xs text-slate-300">
  <div class="flex gap-2"><span class="text-green-400">✓</span> Canvas + Panopto + Piazza ingestors</div>
  <div class="flex gap-2"><span class="text-green-400">✓</span> spaCy PII anonymization</div>
  <div class="flex gap-2"><span class="text-green-400">✓</span> HuggingFace embeddings + ChromaDB</div>
  <div class="flex gap-2"><span class="text-green-400">✓</span> Neo4j knowledge graph</div>
  <div class="flex gap-2"><span class="text-green-400">✓</span> Hybrid retriever (vector + graph)</div>
  <div class="flex gap-2"><span class="text-green-400">✓</span> Configurable guardrails</div>
  <div class="flex gap-2"><span class="text-green-400">✓</span> FastAPI backend + Next.js 14 UI</div>
  <div class="flex gap-2"><span class="text-green-400">✓</span> Inline citations + feedback logging</div>
  <div class="flex gap-2"><span class="text-green-400">✓</span> Behavioral concept design</div>
</div>
</div>

<div>
<div class="text-xs text-yellow-300 uppercase tracking-wide font-semibold mb-2">🔧 Remaining</div>
<div class="space-y-1.5 text-xs">
  <div class="px-2 py-1.5 rounded bg-slate-800/60 border border-slate-700 text-slate-300">
    <span class="text-yellow-400 font-semibold">WCAG 2.1 AA audit</span> — keyboard nav, streaming focus, contrast
  </div>
  <div class="px-2 py-1.5 rounded bg-slate-800/60 border border-slate-700 text-slate-300">
    <span class="text-yellow-400 font-semibold">Staff analytics view</span> — common questions + guardrail monitoring
  </div>
  <div class="px-2 py-1.5 rounded bg-slate-800/60 border border-slate-700 text-slate-300">
    <span class="text-yellow-400 font-semibold">Retrieval A/B eval</span> — vector-only vs. hybrid on gold Q&A set
  </div>
  <div class="px-2 py-1.5 rounded bg-slate-800/60 border border-slate-700 text-slate-300">
    <span class="text-yellow-400 font-semibold">Gradescope ingestor</span> — rubric feedback + anonymization
  </div>
  <div class="px-2 py-1.5 rounded bg-slate-800/60 border border-slate-700 text-slate-300">
    <span class="text-yellow-400 font-semibold">Setup docs</span> — instructor guide, one-command pipeline
  </div>
</div>
</div>

</div>

---
layout: default
---

# References

<div class="grid grid-cols-2 gap-2 mt-3 text-xs text-slate-300">

<div class="px-3 py-2 rounded-lg bg-slate-800/40 border border-slate-700">
  Cavoukian, A. (2009). <em>Privacy by design: The 7 foundational principles.</em> IPC Ontario.
</div>

<div class="px-3 py-2 rounded-lg bg-slate-800/40 border border-slate-700">
  Chi, M. T. H., Feltovich, P. J., & Glaser, R. (1981). Categorization of physics problems. <em>Cognitive Science, 5</em>(2), 121–152.
</div>

<div class="px-3 py-2 rounded-lg bg-slate-800/40 border border-slate-700">
  Lewis, P., et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP. <em>NeurIPS, 33,</em> 9459–9474.
</div>

<div class="px-3 py-2 rounded-lg bg-slate-800/40 border border-slate-700">
  Mayer, R. E. (2009). <em>Multimedia learning</em> (2nd ed.). Cambridge University Press.
</div>

<div class="px-3 py-2 rounded-lg bg-slate-800/40 border border-slate-700">
  MIT CMS.594 Staff. (2025). <em>A concept-design guide for naming and capturing context</em>. MIT.
</div>

<div class="px-3 py-2 rounded-lg bg-slate-800/40 border border-slate-700">
  Roediger, H. L., & Karpicke, J. D. (2006). Test-enhanced learning. <em>Psych. Science, 17</em>(3), 249–255.
</div>

<div class="px-3 py-2 rounded-lg bg-slate-800/40 border border-slate-700">
  Sweller, J. (1988). Cognitive load during problem solving. <em>Cognitive Science, 12</em>(2), 257–285.
</div>

<div class="px-3 py-2 rounded-lg bg-slate-800/40 border border-slate-700">
  Zimmerman, B. J. (2002). Becoming a self-regulated learner. <em>Theory Into Practice, 41</em>(2), 64–70.
</div>

</div>

---
layout: cover
background: "#0f172a"
---

<div class="text-center">
  <div class="text-xs text-blue-300 font-mono mb-4 tracking-widest uppercase">Q & A</div>
  <h1 class="text-4xl font-bold text-white mb-3">Thank You</h1>
  <p class="text-slate-300 text-base max-w-xl mx-auto mb-5">
    Large Lecture Model — so students can learn, not search.
  </p>
  <div class="grid grid-cols-2 gap-4 max-w-lg mx-auto">
    <div class="p-3 rounded-lg bg-slate-800/60 border border-slate-700 text-left">
      <span class="text-blue-400 block font-semibold text-xs mb-1">Anticipated Q1</span>
      <span class="text-slate-300 text-sm">How do you prevent students from gaming the guardrails?</span>
    </div>
    <div class="p-3 rounded-lg bg-slate-800/60 border border-slate-700 text-left">
      <span class="text-purple-400 block font-semibold text-xs mb-1">Anticipated Q2</span>
      <span class="text-slate-300 text-sm">What happens when the AI gives a wrong answer about course content?</span>
    </div>
  </div>
  <div class="mt-5 text-slate-500 text-xs">
    Tae Wook (Terry) Kim · CMS.594 · MIT Spring 2026
  </div>
</div>
