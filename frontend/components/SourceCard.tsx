import type { Source } from "@/lib/api";

const SOURCE_LABELS: Record<string, string> = {
  canvas: "Canvas",
  panopto: "Lecture",
  piazza: "Piazza",
  gradescope: "Gradescope",
  manual: "Notes",
};

const TYPE_COLORS: Record<string, string> = {
  transcript: "bg-purple-100 text-purple-700",
  slide: "bg-blue-100 text-blue-700",
  post: "bg-green-100 text-green-700",
  assignment: "bg-orange-100 text-orange-700",
  announcement: "bg-gray-100 text-gray-600",
};

export default function SourceCard({ source }: { source: Source }) {
  const color = TYPE_COLORS[source.doc_type] ?? "bg-gray-100 text-gray-600";
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {SOURCE_LABELS[source.source] ?? source.source}
      {source.name ? ` · ${source.name}` : ""}
    </span>
  );
}
