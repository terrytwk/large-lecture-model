import AssignmentList from "@/components/AssignmentList";

export default function DashboardPage() {
  return (
    <main className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-semibold mb-6">6.1220 Dashboard</h1>
      <AssignmentList courseId="6.1220" />
    </main>
  );
}
