from process.anonymizer import anonymize, anonymize_batch


def test_email_redacted():
    text, _ = anonymize("Email jsmith@mit.edu for details.")
    assert "@" not in text
    assert "[EMAIL]" in text


def test_person_name_replaced():
    text, _ = anonymize("John Smith submitted the assignment.")
    assert "John Smith" not in text


def test_batch_consistent_pseudonyms():
    results = anonymize_batch(["Alice asked a question.", "Alice also replied."])
    tokens_0 = [w for w in results[0].split() if w.startswith("Student_")]
    tokens_1 = [w for w in results[1].split() if w.startswith("Student_")]
    assert tokens_0 and tokens_1
    assert tokens_0[0] == tokens_1[0]
