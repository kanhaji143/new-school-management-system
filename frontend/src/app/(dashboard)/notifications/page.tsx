"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  useNotificationTemplates,
  useCreateNotificationTemplate,
  useNotifications,
  useRetryNotification,
} from "@/hooks/useNotifications";

export default function NotificationsPage() {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: templates } = useNotificationTemplates();
  const { data: notifications } = useNotifications();
  const createTemplate = useCreateNotificationTemplate();
  const retry = useRetryNotification();

  async function handleCreateTemplate(formData: FormData) {
    setError(null); setMessage(null);
    try {
      await createTemplate.mutateAsync({
        event: String(formData.get("event") ?? ""),
        channel: String(formData.get("channel") ?? "EMAIL"),
        subject: String(formData.get("subject") ?? ""),
        body: String(formData.get("body") ?? ""),
        is_active: true,
      });
      setMessage("Template created.");
    } catch (err) {
      setError((err as Error)?.message ?? "Could not create template.");
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Notifications" description="Templates, outbox, delivery logs and retries." />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Create template</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" onSubmit={(e) => { e.preventDefault(); void handleCreateTemplate(new FormData(e.currentTarget)); }}>
            <div className="space-y-1">
              <Label>Event</Label>
              <Input name="event" placeholder="student.absent" required />
            </div>
            <div className="space-y-1">
              <Label>Channel</Label>
              <select name="channel" className="h-9 w-full rounded-md border bg-background px-2 text-sm">
                <option value="EMAIL">Email</option>
                <option value="SMS">SMS</option>
                <option value="WHATSAPP">WhatsApp</option>
                <option value="PUSH">Push</option>
              </select>
            </div>
            <div className="space-y-1">
              <Label>Subject</Label>
              <Input name="subject" />
            </div>
            <div className="space-y-1">
              <Label>Body</Label>
              <Input name="body" required />
            </div>
            <div className="flex items-end gap-2 sm:col-span-2 lg:col-span-4">
              <Button type="submit" disabled={createTemplate.isPending}>{createTemplate.isPending ? "Saving…" : "Create template"}</Button>
            </div>
          </form>
          {message ? <p className="mt-3 text-sm text-green-700">{message}</p> : null}
          {error ? <p className="mt-3 text-sm text-destructive">{error}</p> : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Templates</CardTitle>
        </CardHeader>
        <CardContent>
          {!templates || templates.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">No templates yet.</p>
          ) : (
            <ul className="space-y-1 text-sm">
              {templates.map((t) => (
                <li key={t.id} className="flex items-center justify-between border-b py-1 last:border-0">
                  <span>{t.event} [{t.channel}]</span>
                  <Badge variant={t.is_active ? "default" : "secondary"}>{t.is_active ? "Active" : "Inactive"}</Badge>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Outbox</CardTitle>
        </CardHeader>
        <CardContent>
          {!notifications || notifications.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">No notifications yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 pr-3 font-medium">Recipient</th>
                    <th className="py-2 pr-3 font-medium">Channel</th>
                    <th className="py-2 pr-3 font-medium">Subject</th>
                    <th className="py-2 pr-3 font-medium">Status</th>
                    <th className="py-2 pr-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {notifications.map((n) => (
                    <tr key={n.id} className="border-b last:border-0">
                      <td className="py-2 pr-3">{n.recipient_detail?.full_name ?? `#${n.recipient}`}</td>
                      <td className="py-2 pr-3">{n.channel}</td>
                      <td className="py-2 pr-3">{n.subject}</td>
                      <td className="py-2 pr-3">
                        <Badge variant={n.status === "SENT" ? "default" : "secondary"}>{n.status}</Badge>
                      </td>
                      <td className="py-2 pr-3">
                        {n.status !== "SENT" ? (
                          <Button size="sm" variant="outline" onClick={async () => {
                            try { await retry.mutateAsync(n.id); setMessage("Queued for retry."); }
                            catch (err) { setError((err as Error)?.message ?? "Retry failed."); }
                          }}>
                            Retry
                          </Button>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
