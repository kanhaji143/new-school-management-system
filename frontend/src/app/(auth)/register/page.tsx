"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AxiosError } from "axios";
import { api, apiErrorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const schema = z.object({
  institution_name: z.string().min(2, "Institution name is required"),
  institution_type: z.enum(["SCHOOL", "COLLEGE"]),
  email: z.string().email(),
  first_name: z.string().optional(),
  last_name: z.string().optional(),
  password: z.string().min(8, "Use at least 8 characters"),
});

type Form = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { institution_type: "SCHOOL" },
  });

  async function onSubmit(values: Form) {
    try {
      await api.post("/auth/register/", values);
      router.push("/login?registered=1");
    } catch (err) {
      setError("root", { message: apiErrorMessage(err as AxiosError) });
    }
  }

  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      <h1 className="text-2xl font-semibold">Create institution</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Registers your school/college and the first admin account.
      </p>
      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
        <div className="space-y-2">
          <Label htmlFor="institution_name">Institution name</Label>
          <Input id="institution_name" {...register("institution_name")} />
          {errors.institution_name && (
            <p className="text-sm text-destructive">{errors.institution_name.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Admin email</Label>
          <Input id="email" type="email" {...register("email")} />
          {errors.email && (
            <p className="text-sm text-destructive">{errors.email.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" {...register("password")} />
          {errors.password && (
            <p className="text-sm text-destructive">{errors.password.message}</p>
          )}
        </div>
        {errors.root && <p className="text-sm text-destructive">{errors.root.message}</p>}
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Creating…" : "Create institution"}
        </Button>
      </form>
    </div>
  );
}
