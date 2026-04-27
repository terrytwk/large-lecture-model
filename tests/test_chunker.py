from ingest.base import RawDocument
from process.chunker import chunk_documents


def _doc(content: str, doc_type: str = "file") -> RawDocument:
    return RawDocument(id="test", source="manual", course_id="6.1220", doc_type=doc_type, content=content)


def test_short_assignment_is_single_chunk():
    chunks = chunk_documents([_doc("hello world", "assignment")])
    assert len(chunks) == 1
    assert chunks[0].text == "hello world"


def test_long_doc_splits():
    chunks = chunk_documents([_doc(" ".join(["word"] * 2000), "file")])
    assert len(chunks) > 1


def test_chunk_inherits_metadata():
    doc = _doc("content", "slide")
    doc.metadata = {"page": 3}
    chunks = chunk_documents([doc])
    assert chunks[0].metadata["page"] == 3
