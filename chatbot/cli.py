"""Interactive CLI REPL — dev interface without spinning up the full web stack."""
from __future__ import annotations
import sys
from pathlib import Path
import yaml
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent


def main(course_id: str = "6.1220") -> None:
    settings = yaml.safe_load((ROOT / "config/settings.yaml").read_text())
    courses = yaml.safe_load((ROOT / "config/courses.yaml").read_text())
    course_cfg = courses["courses"][course_id]

    from retrieval.vector_store import get_client, get_collection
    from retrieval.vector_retriever import VectorRetriever
    from llm.client import LLMClient
    from llm.guardrails import check
    from llm.prompts import CHAT_SYSTEM, SOURCE_TEMPLATE

    collection = get_collection(get_client(settings["chroma_db_path"]), course_id)
    retriever = VectorRetriever(
        collection=collection,
        embed_model=settings["embedding"]["model"],
        device=settings["embedding"]["device"],
    )
    llm = LLMClient(model=settings["llm"]["model"], max_tokens=settings["llm"]["max_tokens"])
    protected = course_cfg.get("protected_assignments", [])
    system = CHAT_SYSTEM.format(course_name=course_cfg["name"])
    history: list[dict] = []

    print(f"LLM Study Assistant — {course_cfg['name']}")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not query or query.lower() == "exit":
            break

        blocked, reason = check(query, protected, settings["guardrails"]["sensitivity"])
        if blocked:
            print(f"Assistant: {reason}\n")
            continue

        chunks = retriever.retrieve(query, top_k=settings["retrieval"]["top_k"])
        context = "\n".join(
            SOURCE_TEMPLATE.format(
                source=c.source,
                doc_type=c.doc_type,
                name=c.metadata.get("name") or c.metadata.get("lecture_title", ""),
                text=c.text,
            )
            for c in chunks
        )

        user_msg = f"{context}\n\nQuestion: {query}"
        history.append({"role": "user", "content": user_msg})
        response = llm.complete(system=system, user=user_msg)
        history.append({"role": "assistant", "content": response})
        print(f"\nAssistant: {response}\n")


if __name__ == "__main__":
    course = sys.argv[1] if len(sys.argv) > 1 else "6.1220"
    main(course)
