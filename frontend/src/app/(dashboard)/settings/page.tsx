"use client";

import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuditLogs, useCreateSystemSetting, useSystemSettings } from "@/hooks/useAuditOps";

export default function SettingsPage() {
  const { data: settings } = useSystemSettings();
  const { data: auditLogs } = useAuditLogs();
  const createSetting = useCreateSystemSetting();
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function save(formData: FormData) {
    setError(null); setMessage(null);
    let value: Record<string, unknown>;
    try {
      value = JSON.parse(String(formData.get("value") ?? "{}")) as Record<string, unknown>;
    } catch {
      setError("Value must be valid JSON (for example: {\"enabled\": true}).");
      return;
    }
    try {
      await createSetting.mutateAsync({
        key: String(formData.get("key") ?? ""),
        value,
        description: String(formData.get("description") ?? ""),
      });
      setMessage("Setting saved.");
    } catch (e) {
      setError((e as Error).message || "Could not save setting.");
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Operations & settings" description="Institution settings and a traceable audit history." />

      <Card>
        <CardHeader><CardTitle className="text-base">Add system setting</CardTitle></CardHeader>
        <CardContent>
          <form className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" onSubmit={(e) => { e.preventDefault(); void save(new FormData(e.currentTarget)); }}>
            <div className="space-y-1"><Label>Key</Label><Input name="key" placeholder="attendance.grace_minutes" required /></div>
            <div className="space-y-1"><Label>JSON value</Label><Input name="value" placeholder='{"minutes": 10}' required /></div>
            <div className="space-y-1"><Label>Description</Label><Input name="description" /></div>
            <div className="flex items-end"><Button type="submit" disabled={createSetting.isPending}>{createSetting.isPending ? "Saving…" : "Save setting"}</Button></div>
          </form>
          {message ? <p className="mt-3 text-sm text-green-700">{message}</p> : null}
          {error ? <p className="mt-3 text-sm text-destructive">{error}</p> : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Institution settings</CardTitle></CardHeader>
        <CardContent>
          {!settings || settings.length === 0 ? <p className="text-sm text-muted-foreground">No custom settings configured.</p> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="border-b text-left text-muted-foreground"><th className="py-2 pr-3">Key</th><th className="py-2 pr-3">Value</th><th className="py-2">Description</th></tr></thead>
              <tbody>{settings.map((s) => <tr key={s.id} className="border-b last:border-0"><td className="py-2 pr-3 font-mono">{s.key}</td><td className="py-2 pr-3 font-mono text-xs">{JSON.stringify(s.value)}</td><td className="py-2">{s.description}</td></tr>)}</tbody>
            </table></div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Recent audit history</CardTitle></CardHeader>
        <CardContent>
          {!auditLogs || auditLogs.length === 0 ? <p className="text-sm text-muted-foreground">No audit entries yet.</p> : (
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr className="border-b text-left text-muted-foreground"><th className="py-2 pr-3">When</th><th className="py-2 pr-3">Actor</th><th className="py-2 pr-3">Action</th><th className="py-2 pr-3">Record</th><th className="py-2">Change</th></tr></thead>
              <tbody>{auditLogs.map((log) => <tr key={log.id} className="border-b last:border-0 align-top"><td className="py-2 pr-3 whitespace-nowrap">{new Date(log.created_at).toLocaleString()}</td><td className="py-2 pr-3">{log.actor_detail?.full_name ?? "System"}</td><td className="py-2 pr-3">{log.action}</td><td className="py-2 pr-3">{log.model} #{log.object_id}</td><td className="max-w-sm py-2 text-xs"><div>Before: {JSON.stringify(log.before)}</div><div>After: {JSON.stringify(log.after)}</div></td></tr>)}</tbody>
            </table></div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
