"""Tool schemas for Claude tool use."""

TOOLS = [
    {
        "name": "search_materials",
        "description": "Search course materials (slides, transcripts, notes) for a topic or concept.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "doc_type": {
                    "type": "string",
                    "enum": ["slide", "transcript", "post", "any"],
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_assignments",
        "description": "List assignments with due dates and submission status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter": {"type": "string", "enum": ["upcoming", "past", "all"]},
            },
        },
    },
    {
        "name": "get_lecture_transcript",
        "description": "Retrieve the transcript for a specific lecture by title or week number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lecture_title": {"type": "string"},
                "week": {"type": "integer"},
            },
        },
    },
]
