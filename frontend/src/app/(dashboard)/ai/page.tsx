"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  useAIJobs,
  useCreateAIJob,
  useGeneratedContent,
  useReviewContent,
} from "@/hooks/useAI";

export default function AIPage() {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: jobs } = useAIJobs();
  const { data: content } = useGeneratedContent();
  const createJob = useCreateAIJob();
  const review = useReviewContent();

  async function handleCreate(formData: FormData) {
    setError(null); setMessage(null);
    try {
      await createJob.mutateAsync({
        job_type: String(formData.get("job_type") ?? "MATERIAL_GEN"),
        input: {
          prompt: String(formData.get("prompt") ?? ""),
          title: String(formData.get("title") ?? "Generated content"),
          content_type: String(formData.get("content_type") ?? "MATERIAL"),
        },
      });
      setMessage("Job queued and generated. Review the content below.");
    } catch (err) {
      setError((err as Error)?.message ?? "Could not create job.");
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="AI" description="Generate content with mandatory human review before publication." />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Request generation</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" onSubmit={(e) => { e.preventDefault(); void handleCreate(new FormData(e.currentTarget)); }}>
            <div className="space-y-1">
              <Label>Job type</Label>
              <select name="job_type" className="h-9 w-full rounded-md border bg-background px-2 text-sm">
                <option value="MATERIAL_GEN">Material gen</option>
                <option value="QUESTION_GEN">Question gen</option>
                <option value="SUMMARIZE">Summarize</option>
                <option value="MARKING_ASSIST">Marking assist</option>
              </select>
            </div>
            <div className="space-y-1">
              <Label>Content type</Label>
              <select name="content_type" className="h-9 w-full rounded-md border bg-background px-2 text-sm">
                <option value="MATERIAL">Material</option>
                <option value="QUESTION">Question</option>
                <option value="SUMMARY">Summary</option>
              </select>
            </div>
            <div className="space-y-1">
              <Label>Title</Label>
              <Input name="title" />
            </div>
            <div className="space-y-1">
              <Label>Prompt</Label>
              <Input name="prompt" required />
            </div>
            <div className="flex items-end gap-2 sm:col-span-2 lg:col-span-4">
              <Button type="submit" disabled={createJob.isPending}>{createJob.isPending ? "Generating…" : "Generate"}</Button>
            </div>
          </form>
          {message ? <p className="mt-3 text-sm text-green-700">{message}</p> : null}
          {error ? <p className="mt-3 text-sm text-destructive">{error}</p> : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Generated content (review queue)</CardTitle>
        </CardHeader>
        <CardContent>
          {!content || content.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">No generated content yet.</p>
          ) : (
            <ul className="space-y-3">
              {content.map((c) => (
                <li key={c.id} className="rounded-md border p-3 text-sm">
                  <div className="flex items-center justify-between">
                    <div className="font-medium">{c.title}</div>
                    <Badge variant={c.status === "APPROVED" ? "default" : "secondary"}>{c.status}</Badge>
                  </div>
                  <pre className="mt-2 whitespace-pre-wrap text-xs text-muted-foreground">{c.body}</pre>
                  {c.status === "PENDING_REVIEW" ? (
                    <div className="mt-2 flex gap-2">
                      <Button size="sm" onClick={async () => {
                        try { await review.mutateAsync({ id: c.id, decision: "approve", note: "OK" }); setMessage("Approved."); }
                        catch (err) { setError((err as Error)?.message ?? "Approve failed."); }
                      }}>
                        Approve
                      </Button>
                      <Button size="sm" variant="outline" onClick={async () => {
                        try { await review.mutateAsync({ id: c.id, decision: "reject", note: "Needs work" }); setMessage("Rejected."); }
                        catch (err) { setError((err as Error)?.message ?? "Reject failed."); }
                      }}>
                        Reject
                      </Button>
                    </div>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          {!jobs || jobs.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">No jobs yet.</p>
          ) : (
            <ul className="space-y-1 text-sm">
              {jobs.map((j) => (
                <li key={j.id} className="flex items-center justify-between border-b py-1 last:border-0">
                  <span>{j.job_type}</span>
                  <Badge variant={j.status === "SUCCESS" ? "default" : "secondary"}>{j.status}</Badge>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
