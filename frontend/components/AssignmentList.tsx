"use client";

import { useEffect, useState } from "react";
import type { Assignment } from "@/lib/api";

export default function AssignmentList({ courseId }: { courseId: string }) {
  const [assignments, setAssignments] = useState<Assignment[]>([]);

  useEffect(() => {
    fetch(`/api/assignments?course_id=${courseId}`)
      .then((r) => r.json())
      .then((d) => setAssignments(d.assignments));
  }, [courseId]);

  if (assignments.length === 0) {
    return (
      <p className="text-gray-400 text-sm">
        No assignments loaded yet. Run the ingestion pipeline first.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {assignments.map((a) => (
        <div key={a.id} className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex justify-between items-start">
            <h3 className="font-medium text-sm">{a.name}</h3>
            <span
              className={`text-xs px-2 py-0.5 rounded ${
                a.submitted
                  ? "bg-green-100 text-green-700"
                  : "bg-yellow-100 text-yellow-700"
              }`}
            >
              {a.submitted ? "Submitted" : "Pending"}
            </span>
          </div>
          {a.due_at && (
            <p className="text-xs text-gray-400 mt-1">
              Due: {new Date(a.due_at).toLocaleDateString()}
            </p>
          )}
          {a.topics.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {a.topics.map((t) => (
                <span key={t} className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">
                  {t}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
