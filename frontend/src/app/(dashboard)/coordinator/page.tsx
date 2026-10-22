"use client";

import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  useCoordinatorDashboard,
  useCoordinatorTasks,
  useCreateCoordinatorTask,
  useCompleteCoordinatorTask,
} from "@/hooks/useCoordinator";

const LABELS: Record<string, string> = {
  substitutions: "Substitutions",
  timetable_changes: "Timetable approvals",
  leave_requests: "Leave requests",
  ai_reviews: "AI reviews",
  grading: "Assessments to review",
  tasks: "Open tasks",
};

export default function CoordinatorPage() {
  const { data: dashboard, isLoading } = useCoordinatorDashboard();
  const { data: tasks } = useCoordinatorTasks();
  const createTask = useCreateCoordinatorTask();
  const completeTask = useCompleteCoordinatorTask();
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function addTask() {
    if (!title.trim()) return;
    setError(null);
    try {
      await createTask.mutateAsync({ task_type: "GENERAL", title: title.trim() });
      setTitle("");
    } catch (e) {
      setError((e as Error).message || "Could not create task.");
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Coordinator command center" description="Pending approvals and follow-up tasks for your institution." />
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Object.entries(dashboard?.pending ?? {}).map(([key, count]) => (
          <Card key={key}>
            <CardContent className="p-4">
              <div className="text-sm text-muted-foreground">{LABELS[key] ?? key}</div>
              <div className="mt-1 text-2xl font-semibold">{count}</div>
            </CardContent>
          </Card>
        ))}
        {!isLoading && !dashboard ? <p className="text-sm text-destructive">Unable to load coordinator metrics.</p> : null}
      </div>

      <Card>
        <CardHeader><CardTitle className="text-base">Coordinator tasks</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Add a follow-up task" onKeyDown={(e) => { if (e.key === "Enter") void addTask(); }} />
            <Button onClick={addTask} disabled={createTask.isPending}>{createTask.isPending ? "Adding…" : "Add task"}</Button>
          </div>
          {error ? <p className="text-sm text-destructive">{error}</p> : null}
          {!tasks || tasks.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">No tasks yet.</p>
          ) : (
            <ul className="space-y-2">
              {tasks.map((task) => (
                <li key={task.id} className="flex items-center justify-between rounded-md border p-3 text-sm">
                  <div>
                    <div className="font-medium">{task.title}</div>
                    <div className="mt-1 text-xs text-muted-foreground">{task.task_type.replaceAll("_", " ")}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={task.status === "DONE" ? "default" : "secondary"}>{task.status}</Badge>
                    {task.status !== "DONE" ? (
                      <Button size="sm" variant="outline" disabled={completeTask.isPending} onClick={() => completeTask.mutate(task.id)}>Complete</Button>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
