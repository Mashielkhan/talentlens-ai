"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, send } from "@/lib/api";
import { ErrorBox, Heading, useUser } from "@/components/common";
import { Button } from "@/components/ui/button";
export default function Page() {
  const { data: user } = useUser(),
    cache = useQueryClient(),
    router = useRouter(),
    [message, setMessage] = useState("");
  const action = useMutation({
    mutationFn: ({ path, method, body }: { path: string; method: string; body: unknown }) =>
      api(`/auth/${path}`, send(method, body)),
    onSuccess: (_, vars) => {
      if (vars.path === "account") {
        cache.clear();
        router.push("/");
      } else {
        cache.invalidateQueries({ queryKey: ["me"] });
        setMessage("Changes saved.");
      }
    },
  });
  if (!user) return null;
  return (
    <>
      <Heading title="Your settings" subtitle="Manage your profile, account, and privacy." />
      <div className="stack">
        <ErrorBox error={action.error} />
        {message && (
          <p role="status" className="notice">
            {message}
          </p>
        )}
        <form
          className="panel stack"
          action={(form) =>
            action.mutate({ path: "profile", method: "PATCH", body: Object.fromEntries(form) })
          }
        >
          <h2>Profile</h2>
          <div className="form-grid">
            <label className="field">
              Full name
              <input name="full_name" defaultValue={user.full_name} required minLength={2} maxLength={120} />
            </label>
            {["headline", "location", "company"].map((key) => (
              <label key={key} className="field capitalize">
                {key}
                <input name={key} defaultValue={user.profile[key] || ""} maxLength={160} />
              </label>
            ))}
            <label className="field full">
              About you
              <textarea name="bio" defaultValue={user.profile.bio || ""} maxLength={2000} />
            </label>
          </div>
          <div>
            <Button disabled={action.isPending}>Save profile</Button>
          </div>
        </form>
        <form
          className="panel stack"
          action={(form) =>
            action.mutate({ path: "password", method: "POST", body: Object.fromEntries(form) })
          }
        >
          <h2>Change password</h2>
          <div className="form-grid">
            <label className="field">
              Current password
              <input name="current_password" type="password" autoComplete="current-password" required />
            </label>
            <label className="field">
              New password
              <input
                name="new_password"
                type="password"
                autoComplete="new-password"
                required
                minLength={12}
                maxLength={128}
              />
            </label>
          </div>
          <p className="muted text-xs">
            Changing your password signs out all other sessions. Use at least 12 characters.
          </p>
          <div>
            <Button variant="outline" disabled={action.isPending}>
              Update password
            </Button>
          </div>
        </form>
        <section className="panel">
          <h2>Privacy & data</h2>
          <p className="muted text-sm">
            Your resumes are private by default. Each application shares one resume with the recruiter
            responsible for that job. Manage or withdraw this consent from Applications.
          </p>
          <p className="muted text-xs">
            Email verification and email password recovery are not configured in this release. Keep your
            password safe.
          </p>
        </section>
        <form
          className="panel stack"
          action={(form) => {
            if (
              window.confirm(
                "Permanently delete your account, resumes, applications, and analyses? This cannot be undone.",
              )
            )
              action.mutate({
                path: "account",
                method: "DELETE",
                body: { email: user.email, password: String(form.get("password")) },
              });
          }}
        >
          <h2>Delete account</h2>
          <p className="muted text-xs">
            Access is revoked immediately. Private files are queued for removal by the worker. Backups follow
            the deployment’s retention policy.
          </p>
          <label className="field">
            Confirm your password
            <input type="password" name="password" required autoComplete="current-password" />
          </label>
          <div>
            <Button variant="destructive" disabled={action.isPending}>
              Delete my account and data
            </Button>
          </div>
        </form>
      </div>
    </>
  );
}
