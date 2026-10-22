"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  useSubstitutionRequests,
  useRecommendations,
  useGenerateRecommendations,
  useAssignSubstitute,
  useHandover,
  useRecordOutcome,
  useCancelSubstitution,
} from "@/hooks/useSubstitution";

const STATUS_COLOR: Record<string, string> = {
  OPEN: "bg-blue-500/15 text-blue-700",
  PROPOSED: "bg-amber-500/15 text-amber-700",
  APPROVED: "bg-green-500/15 text-green-700",
  COMPLETED: "bg-emerald-500/15 text-emerald-700",
  UNRESOLVED: "bg-red-500/15 text-red-700",
  CANCELLED: "bg-gray-500/15 text-gray-700",
};

export default function SubstitutionPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const { data: requests, isLoading } = useSubstitutionRequests();

  return (
    <div className="space-y-6">
      <PageHeader title="Substitution" description="Recommend, approve, hand over and record substitute classes." />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Substitution requests</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="py-6 text-center text-sm text-muted-foreground">Loading…</p>
          ) : !requests || requests.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              No substitution requests. They are auto-created when a teacher is marked absent.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 pr-3 font-medium">Date</th>
                    <th className="py-2 pr-3 font-medium">Absent teacher</th>
                    <th className="py-2 pr-3 font-medium">Subject</th>
                    <th className="py-2 pr-3 font-medium">Status</th>
                    <th className="py-2 pr-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {requests.map((r) => (
                    <tr key={r.id} className="border-b last:border-0">
                      <td className="py-2 pr-3 font-mono text-xs">{r.date}</td>
                      <td className="py-2 pr-3">{r.absent_teacher_detail?.full_name ?? `#${r.absent_teacher}`}</td>
                      <td className="py-2 pr-3">{r.entry_detail?.subject?.name ?? "—"}</td>
                      <td className="py-2 pr-3">
                        <Badge className={STATUS_COLOR[r.status]}>{r.status}</Badge>
                      </td>
                      <td className="py-2 pr-3">
                        <Button size="sm" variant="outline" onClick={() => setSelectedId(r.id)}>
                          {selectedId === r.id ? "Close" : "Manage"}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {selectedId ? <ManagePanel requestId={selectedId} onClose={() => setSelectedId(null)} /> : null}
    </div>
  );
}

function ManagePanel({ requestId, onClose }: { requestId: number; onClose: () => void }) {
  const { data: recs } = useRecommendations(requestId);
  const generate = useGenerateRecommendations();
  const assign = useAssignSubstitute();
  const handover = useHandover();
  const outcome = useRecordOutcome();
  const cancel = useCancelSubstitution();

  const [notes, setNotes] = useState("");
  const [outcomeStatus, setOutcomeStatus] = useState("COMPLETED");
  const [outcomeNotes, setOutcomeNotes] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleAssign(teacherId: number) {
    setError(null);
    setMessage(null);
    try {
      await assign.mutateAsync({ id: requestId, substitute_teacher: teacherId });
      setMessage("Substitute assigned.");
    } catch (err) {
      setError((err as Error)?.message ?? "Assign failed.");
    }
  }

  async function handleHandover() {
    setError(null);
    setMessage(null);
    try {
      await handover.mutateAsync({ id: requestId, notes });
      setMessage("Handover saved.");
    } catch (err) {
      setError((err as Error)?.message ?? "Handover failed.");
    }
  }

  async function handleOutcome() {
    setError(null);
    setMessage(null);
    try {
      await outcome.mutateAsync({ id: requestId, status: outcomeStatus, notes: outcomeNotes });
      setMessage("Outcome recorded.");
    } catch (err) {
      setError((err as Error)?.message ?? "Outcome failed.");
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">Manage request #{requestId}</CardTitle>
        <Button size="sm" variant="ghost" onClick={onClose}>
          Close
        </Button>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold">Recommendations</h3>
            <Button
              size="sm"
              variant="outline"
              onClick={async () => {
                try {
                  await generate.mutateAsync({ id: requestId, limit: 3, strict_subject: true });
                } catch (err) {
                  setError((err as Error)?.message ?? "Generate failed.");
                }
              }}
            >
              {generate.isPending ? "Generating…" : "Generate"}
            </Button>
          </div>
          {!recs || recs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No recommendations yet. Click Generate.</p>
          ) : (
            <ul className="space-y-2">
              {recs.map((r) => (
                <li key={r.id} className="flex items-center justify-between rounded-md border p-2 text-sm">
                  <div>
                    <div className="font-medium">{r.teacher_detail?.full_name ?? `#${r.teacher}`}</div>
                    <div className="text-xs text-muted-foreground">
                      Score {r.score} · rank {r.rank}
                    </div>
                  </div>
                  <Button size="sm" onClick={() => handleAssign(r.teacher)}>
                    Assign
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="space-y-2">
          <h3 className="text-sm font-semibold">Handover notes</h3>
          <Input
            placeholder="Notes for the substitute"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
          <Button size="sm" onClick={handleHandover} disabled={handover.isPending}>
            {handover.isPending ? "Saving…" : "Save handover"}
          </Button>
        </div>

        <div className="space-y-2">
          <h3 className="text-sm font-semibold">Record outcome</h3>
          <div className="flex gap-2">
            <select
              className="h-9 rounded-md border bg-background px-2 text-sm"
              value={outcomeStatus}
              onChange={(e) => setOutcomeStatus(e.target.value)}
            >
              <option value="COMPLETED">Completed</option>
              <option value="PARTIAL">Partial</option>
              <option value="SKIPPED">Skipped</option>
            </select>
            <Input
              placeholder="Notes"
              value={outcomeNotes}
              onChange={(e) => setOutcomeNotes(e.target.value)}
            />
            <Button size="sm" onClick={handleOutcome} disabled={outcome.isPending}>
              {outcome.isPending ? "Saving…" : "Save outcome"}
            </Button>
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={async () => {
              try {
                await cancel.mutateAsync(requestId);
                setMessage("Request cancelled.");
              } catch (err) {
                setError((err as Error)?.message ?? "Cancel failed.");
              }
            }}
          >
            Cancel request
          </Button>
        </div>

        {message ? <p className="text-sm text-green-700">{message}</p> : null}
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
      </CardContent>
    </Card>
  );
}
