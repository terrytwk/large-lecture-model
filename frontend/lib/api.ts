export interface Source {
  id: string;
  source: string;
  doc_type: string;
  name: string;
  score: number | null;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

export interface Assignment {
  id: string;
  name: string;
  due_at: string | null;
  submitted: boolean;
  score: number | null;
  max_score: number | null;
  topics: string[];
}
