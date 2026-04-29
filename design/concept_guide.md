# A Concept-Design Guide for Naming and Capturing Context

This document is meant to be dropped into a repository as a shared reference for the people and LLM agents working on it. It introduces a lightweight discipline — **concept design** — for naming things, designing schemas, and capturing data from many sources in a way that holds up across many downstream uses.

It is short on purpose. There is exactly one structural requirement (see §6); everything else is guidance.

---

## 1. The setting this is written for

You are building a system that scrapes course-related information from a fragmented landscape: Canvas, Slack, Piazza, course-specific static sites, Google Docs, syllabi shared as PDFs, lecture recordings, problem sets, grade books, office-hours queues, and whatever else turns up next semester. The goal is to collect enough context that downstream tools — exam-prep helpers, study planners, navigation assistants, advising views — can serve students well without each tool having to scrape the world from scratch.

That ambition has a hard naming problem at its center. Each platform models the world differently. Canvas's "submission," Piazza's "answer," Slack's "thread reply," and a Google Doc comment are sibling things in some sense and unrelated in others. If your captured data inherits each platform's vocabulary, every downstream tool will spend most of its life translating between schemas. If you reach for a synthesized vocabulary too eagerly — a single `Post` table, a universal `User` — you will spend most of your life migrating it as new sources show up.

Concept design is a way out of this bind. The bet is that **behaviors hold still even when platforms do not.** A student asking a clarifying question is the same kind of event whether it lands on Piazza or in a Slack channel. If your schema names the asking, not the platform's representation of it, the same captured data serves the exam helper, the study planner, and tools you have not yet imagined.

---

## 2. The core move: ground names in behavior

There are two ways to organize what you capture.

**Ground in state (the trap).** Have a `User` row, an `Assignment` row, a `Submission` row. Each is defined by its current properties: name, due date, grade, status. This is intuitive and familiar. It also fails open-endedly:

- The properties of `User` and `Assignment` are never finished — every new feature adds columns or migration pain.
- Two sources disagree about state and there is no principled way to reconcile (whose `due_date` wins?).
- Old snapshots are lossy. By the time you wonder *when* the due date changed, the previous value is gone.
- Cross-platform reconciliation collapses into ad-hoc joins.

**Ground in behavior (the discipline).** Name what *happened*: a posting, an asking, a submitting, an announcing, a grading, a reading, an attending. Each event is an immutable record of a behavior in the world. State is whatever currently obtains as a fold over the history of those events.

This pays off in concrete ways for your domain:

- A `Posting.posted` event is the same shape whether it came from Piazza, Canvas Announcements, or a course Slack channel. The platform is metadata, not the schema's spine.
- "When did this assignment's due date change?" is a query over events, not a forensic exercise.
- New sources extend the action log; they do not reshape it.
- Different downstream tools project the same log into different views (a calendar, a study plan, a participation graph) without requiring different captures.

---

## 3. Concepts and actions

A **concept** is a named lifecycle of behavior. Its name is a gerund — `Posting`, `Asking`, `Submitting`, `Grading`, `Announcing`, `Attending`, `Reading`, `Authoring`, `Enrolling`. The lifecycle test is: say "[ConceptName] is happening" out loud. If it lands without strain, it is a concept. If it does not — "Userring is happening," "Assignmenting is happening" — what you have is a participant or a thing, not a behavior, and it should appear as a *referent* inside other concepts' actions, not as a concept of its own.

Each concept has:

- **a name** (gerund) — the lifecycle.
- **a purpose** — one or two sentences in plain language about why this concept exists. No platform names, no implementation language.
- **a principle** — a tiny scenario showing the concept in motion with concrete actors.
- **actions** — past-tense events the concept records. Names like `posted`, `asked`, `answered`, `submitted`, `graded`, `enrolled`, `announced`. Each action lists the roles its parameters play.
- **state** — described semantically, in plain language: what currently obtains as a result of the actions ("the set of posts that have been posted and not deleted; for each, its author"). State is a derived view, not a primary table.

An example sketch:

> **Asking** — purpose: a participant asks a question of a context, expecting an answer. Principle: a student asks "is the exam cumulative?" of the 6.104 staff context; later someone answers it. Actions: `Asking.asked(asker, question, of)`. State: the set of questions that have been asked, and for each, who asked it and what they asked it of.

`Answering` is a separate concept. It references `?question` polymorphically — it does not need to know whether the question came from Piazza, Slack, or a Google Doc comment.

### Granularity: be guided by what would react to it

Concepts and actions can be very fine-grained (`Clicking`) or very broad (`Engaging`). The right grain in any particular spot is the one that matches what downstream tools or agents will want to *react to* or *query for*. If the exam helper cares about "when an assignment was posted" separately from "when its due date changed," those are two actions, not one. If nothing in your system distinguishes "posted" from "edited," fold them together until something does.

A useful heuristic: when you find yourself writing a query that needs `WHERE event_type = 'X'`, that filter is probably the action you should have named.

---

## 4. How to name parameters and capture data

These are the rules that, in our experience, do the most work for a multi-source, repurposable capture.

**Parameters name roles, not types or origins.** In `Posting.posted(author, post)`, `author` names the role this referent plays *in this action*. Avoid `user_id`, `email`, `slack_user_id` — those bake in an origin or representation and pin the concept to one source. The role is `author`. How you resolve `?author` to a Slack user, a Canvas user, or a Kerberos identity is a separate, lower-layer concern.

**References by default; literals only at the leaves.** A concept action's parameters should be references to entities. The string of a post, the timestamp of a submission, the integer of a grade — these are *literals attached to references* by separate, value-attaching concepts:

```
Posting.posted(author: <ref:alice>, post: <ref:p>)
Textualizing.textualized(entity: <ref:p>, role: <ref:body>, text: "is the exam cumulative?")
Timing.timed(entity: <ref:p>, at: 1714348800)
Sourcing.sourced(entity: <ref:p>, platform: <ref:piazza>, external_id: "abc123")
```

This looks verbose. It is, deliberately. Three things follow from it:

1. **Multi-source merging is trivial.** The same `post` reference can carry multiple `Sourcing.sourced` attachments if it shows up in two places, and multiple `Textualizing.textualized` attachments under different roles (`raw_html`, `rendered_markdown`, `summary`).
2. **History is preserved.** An edit to a post's text is a new `Textualizing.textualized` event with the same `entity` and `role`, not a destructive overwrite.
3. **Downstream tools choose what to read.** A study planner reads `Timing.timed`. A search index reads `Textualizing.textualized` under role `body`. They do not have to know about each other.

Pragmatically: feel free to compress these into a single row or JSON blob in your storage layer (SQL, a document store, a graph DB — your choice). What matters is that the *canonical* shape — the names, the events, the role of each field — follows the discipline. Compression is a representation detail.

**Past-tense action names.** `posted`, `submitted`, `enrolled`, `graded`. These are records of things that happened. Resist the temptation to name an action by its trigger or its effect; name it by what occurred.

**No optional fields; prefer variant actions.** If a parameter is sometimes present and sometimes not, it is usually a sign that two distinct actions are being conflated. `Reviewing.approved(submission)` and `Reviewing.conditioned(submission, conditions)` are clearer than one action with an optional `conditions` field.

**State is a verb choice, not a flag.** `is_published = true` should usually be the action `Posting.published(post)`, not a column. The current state ("is this published?") is a fold over the events. If two sources disagree, you have two events, attributed to two actors, and you can decide what to do with that information rather than averaging it away.

**Provenance matters.** Every captured event should carry who or what claimed it (the scraper agent, the platform's audit log, a human report). Open-world: anyone can claim anything; trust is a downstream decision based on the claimer.

---

## 5. A worked example: the exam-prep tool

The collaborator team has described an exam-prep tool that should:

1. Take an upcoming exam and break it down in terms of what a student needs to know.
2. Identify where the student is, given their history of interactions in the course.
3. Suggest a tailored learning plan to close the gap.

Notice that none of these three jobs can be done well from a per-platform schema. They all need the same underlying behavioral history, projected three different ways. Here is a sketch of the concepts that naturally fall out — not a final list, just enough to show the shape.

### Concepts that show up on the exam side

- **Examining** — `Examining.scheduled(exam, course, at)`, `Examining.covered(exam, topic)`. The exam is announced; topics are claimed to be covered. Multiple sources may make these claims (the syllabus, an announcement on Piazza, a TA's Slack message); each is its own event with its own attestor.
- **Topicking** (or whatever gerund the team prefers — `Surveying`, `Curriculuming`) — `Topicking.introduced(topic, course)`, `Topicking.related(topic, prerequisite)`. Builds the topic graph the exam draws from.
- **Defining** — `Defining.defined(entity, kind)`. For attaching kinds to questions, problems, topics — "this is a proof question," "this topic is computational."

### Concepts that show up on the student-history side

- **Reading** — `Reading.read(reader, artifact)`. The student opened a lecture note, watched a recording, viewed a Piazza thread.
- **Asking** / **Answering** — `Asking.asked(asker, question, of)`, `Answering.answered(answerer, answer, to)`. Cross-platform out of the box.
- **Submitting** — `Submitting.submitted(submitter, submission, for)`. The student turned in pset 4.
- **Grading** — `Grading.graded(grader, submission, score)` (with `score` itself attached via `Quantifying.quantified` if you want to be strict). Captures both staff feedback and self-assessments.
- **Attending** — `Attending.attended(attender, session)`. Lectures, recitations, office hours.

### Concepts that show up on the planning side

- **Recommending** — `Recommending.recommended(recommender, action, to)`. The tool's outputs are themselves first-class events; "the planner suggested this reading" is a recordable claim, attributable to the planner agent.
- **Sequencing** — `Sequencing.sequenced(plan, role: study_order, items: [...])`. A study plan is an ordered list of items committed to a role.
- **Targeting** — `Targeting.targeted(plan, gap)`. Which gaps the plan is aimed at.

### How the three jobs read this log

1. **Exam breakdown.** Project from `Examining.covered` and `Topicking.related` over the relevant exam. The output is a topic graph — derived, not stored as such.
2. **Student state.** Project from `Reading.read`, `Asking.asked`, `Submitting.submitted`, `Grading.graded`, `Attending.attended` filtered by the student. The output is a coverage map over the same topics.
3. **Plan.** Compare (1) and (2); emit `Recommending.recommended` and `Sequencing.sequenced` events. Those become part of the log too — so a *next* run can see what was recommended, whether the student followed through, and adjust.

The point is not these specific concepts. It is that **the same captured event log serves all three jobs without a re-scrape and without a per-tool schema**. If the team later adds a participation visualizer, an advising view, or a course-quality dashboard, those tools read the same log and project differently.

---

## 6. The one structural requirement

> **Maintain a `concepts/` folder at the repository root. It is the source of truth for any meaningful name used to model data or events anywhere in the system.**

Each concept lives in its own file (e.g. `concepts/posting.md`, `concepts/asking.md`, `concepts/submitting.md`). Each file contains, at minimum:

- the concept's **name** (gerund),
- its **purpose** (one or two sentences, in plain language, no platform names),
- its **principle** (a short scenario in concrete terms),
- its **actions** (past-tense, with named role parameters),
- its **state** (described semantically, as prose).

When an agent (human or LLM) is about to introduce a new name for an entity, an event, a column, a table, a JSON field, or a model class, it should:

1. **Look in `concepts/` first.** If a concept already covers this behavior, use it.
2. **If a new concept is needed, write the file.** A few minutes of writing the four elements (name, purpose, principle, actions) almost always exposes whether the concept is real or whether you are about to bake in a platform assumption.
3. **If a concept needs to evolve, edit its file.** Renames are cheap early; the cost compounds the moment a name is referenced elsewhere.

Nothing else is mandated. Use whatever storage backend, whatever language, whatever pipeline you want. Compress the canonical event shape however you like at the wire. The discipline lives in the names, and the names live in `concepts/`.

---

## 7. A checklist for agents reading this file

When you are about to capture data, design a schema, name a column, define a model class, write a scraper, or build a downstream tool, run through this:

- [ ] Is this a behavior happening over time? If yes, it is a concept; name it with a gerund and write `concepts/<name>.md`. If no, it is a participant or a referent; locate the concept whose action it appears in.
- [ ] Have I named parameters by their *role* in the action, not by their type or origin (no `user_id`, `slack_user_id`, `email`, `payload`)?
- [ ] Have I avoided embedding literals (strings, integers, timestamps) inside domain concepts? Are they attached via value-attaching concepts (`Textualizing`, `Timing`, `Quantifying`, `Sourcing`)?
- [ ] Are my action names past-tense events? Could a downstream tool react to them?
- [ ] Have I avoided optional fields by splitting variant actions, or by polymorphic role parameters?
- [ ] Does each captured event carry provenance — who or what attested it?
- [ ] If I am tempted to overwrite or update a row, would an additional event preserve the history I am about to throw away?
- [ ] Is the new name I am introducing already in `concepts/`? If not, am I about to add it there?

If you find yourself bending these guidelines, write down the case. The places where this discipline strains are exactly the places we want to learn from — they are how the concept catalog grows.

---

## 8. Why this is worth doing here

A capture pipeline is a long-lived asset. Schemas baked into it shape every downstream tool for years. The platforms you scrape will change underneath you; new platforms will appear; tools you have not yet imagined will want to read the same data. A vocabulary grounded in behavior survives all of that, because behaviors — students asking questions, staff posting announcements, submissions being graded — are stable across the platforms that come and go.

The cost is small: one folder, one habit. The payoff is that captured context becomes an asset that compounds rather than a substrate that has to be re-shaped for every new use. We would love to see the concepts that fall out of your domain, and we expect they will teach us as much as this guide is meant to offer.
