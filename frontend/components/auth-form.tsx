"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQueryClient } from "@tanstack/react-query";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { api, send } from "@/lib/api";
import { Brand, ErrorBox } from "@/components/common";
import { Button } from "@/components/ui/button";

const schema = z.object({
  full_name: z.string(),
  email: z.email("Enter a valid email address"),
  password: z.string().min(1, "Enter your password").max(128),
  confirm: z.string(),
  company: z.string(),
});
type Values = z.infer<typeof schema>;
export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const registerMode = mode === "register",
    router = useRouter(),
    cache = useQueryClient();
  const [role, setRole] = useState<"APPLICANT" | "RECRUITER">("APPLICANT"),
    [error, setError] = useState<unknown>();
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { full_name: "", email: "", password: "", confirm: "", company: "" },
  });
  async function submit(values: Values) {
    setError(undefined);
    if (registerMode && (values.password.length < 12 || values.password !== values.confirm)) {
      form.setError("confirm", { message: "Use at least 12 characters and make sure passwords match" });
      return;
    }
    if (registerMode && values.full_name.trim().length < 2) {
      form.setError("full_name", { message: "Enter your full name" });
      return;
    }
    try {
      await api(
        `/auth/${mode}`,
        send(
          "POST",
          registerMode
            ? {
                full_name: values.full_name,
                email: values.email,
                password: values.password,
                company: values.company,
                role,
              }
            : { email: values.email, password: values.password },
        ),
      );
      cache.clear();
      router.push("/dashboard");
    } catch (e) {
      setError(e);
    }
  }
  const field = (name: keyof Values, label: string, type = "text", placeholder = "") => (
    <div className="field">
      <label htmlFor={`auth-${name}`}>{label}</label>
      <input
        id={`auth-${name}`}
        aria-invalid={!!form.formState.errors[name]}
        aria-describedby={form.formState.errors[name] ? `auth-${name}-error` : undefined}
        {...form.register(name)}
        type={type}
        placeholder={placeholder}
        autoComplete={
          name === "password"
            ? registerMode
              ? "new-password"
              : "current-password"
            : name === "email"
              ? "email"
              : name === "full_name"
                ? "name"
                : "off"
        }
      />
      {form.formState.errors[name] && (
        <span id={`auth-${name}-error`} className="field-error">
          {form.formState.errors[name]?.message}
        </span>
      )}
    </div>
  );
  return (
    <div className="auth-layout">
      <aside className="auth-story">
        <Brand />
        <div>
          <span className="eyebrow">YOUR NEXT CHAPTER STARTS HERE</span>
          <h1 className="mt-5">
            Make your experience
            <br />
            easier to see.
          </h1>
          <p>
            Bring your qualifications into focus with private resume analysis and transparent job matching.
          </p>
          <div className="row mt-8 muted">
            <ShieldCheck size={18} />
            Your data. Your consent. Your next move.
          </div>
        </div>
        <small>A portfolio project by Mashiel Khan</small>
      </aside>
      <main className="auth-form-wrap">
        <div className="auth-form">
          <Link href="/" className="text-link">
            ← Back to TalentLens
          </Link>
          <h1 className="mt-7">{registerMode ? "Create your workspace" : "Welcome back"}</h1>
          <p className="muted text-sm">
            {registerMode
              ? "A clearer view of your skills starts with one step."
              : "Sign in to pick up where you left off."}
          </p>
          <ErrorBox error={error} />
          <form onSubmit={form.handleSubmit(submit)} noValidate>
            {registerMode && (
              <>
                <div className="role-select" role="group" aria-label="Account role">
                  <button
                    type="button"
                    onClick={() => setRole("APPLICANT")}
                    aria-pressed={role === "APPLICANT"}
                    className={`role-option ${role === "APPLICANT" ? "active" : ""}`}
                  >
                    I’m exploring opportunities
                  </button>
                  <button
                    type="button"
                    onClick={() => setRole("RECRUITER")}
                    aria-pressed={role === "RECRUITER"}
                    className={`role-option ${role === "RECRUITER" ? "active" : ""}`}
                  >
                    I’m hiring
                  </button>
                </div>
                {field("full_name", "Full name", "text", "Your full name")}
                {role === "RECRUITER" && field("company", "Company name")}
              </>
            )}
            {field("email", "Email address", "email", "you@example.com")}
            {field(
              "password",
              "Password",
              "password",
              registerMode ? "At least 12 characters" : "Your password",
            )}
            {registerMode && field("confirm", "Confirm password", "password")}
            <Button disabled={form.formState.isSubmitting} type="submit">
              {form.formState.isSubmitting ? "Please wait…" : registerMode ? "Create account" : "Sign in"}
              <ArrowRight size={15} />
            </Button>
          </form>
          {!registerMode && (
            <Link className="text-link mt-5 inline-block" href="/forgot-password">
              Forgot your password?
            </Link>
          )}
          {registerMode && (
            <p className="muted text-xs mt-5">
              Public beta: review our{" "}
              <Link className="text-link" href="/privacy">
                privacy and use information
              </Link>{" "}
              before uploading personal documents.
            </p>
          )}
          <p className="muted text-xs mt-6">
            {registerMode ? "Already have an account?" : "New to TalentLens?"}{" "}
            <Link className="text-link" href={registerMode ? "/login" : "/register"}>
              {registerMode ? "Sign in" : "Create account"}
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
