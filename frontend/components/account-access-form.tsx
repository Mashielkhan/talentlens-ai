"use client";
import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, send } from "@/lib/api";
import { Brand, ErrorBox } from "@/components/common";
import { Button } from "@/components/ui/button";

export function AccountAccessForm({ mode }: { mode: "forgot" | "reset" | "verify" }) {
  const [message, setMessage] = useState("");
  const cache = useQueryClient();
  const config = useQuery({
    queryKey: ["auth-config"],
    queryFn: () => api<{ email_available: boolean }>("/auth/config"),
  });
  const action = useMutation({
    mutationFn: async (form: FormData) => {
      if (mode === "forgot")
        return api<{ message: string }>(
          "/auth/request-password-reset",
          send("POST", { email: form.get("email") }),
        );
      const token = new URLSearchParams(window.location.hash.slice(1)).get("token");
      if (!token)
        throw new Error(
          "Open the complete link from your email, including its token. Request a new link if needed.",
        );
      if (mode === "reset" && form.get("password") !== form.get("confirm"))
        throw new Error("Passwords must match");
      await api(
        `/auth/${mode === "verify" ? "verify-email" : "reset-password"}`,
        send("POST", mode === "verify" ? { token } : { token, new_password: form.get("password") }),
      );
      window.history.replaceState(null, "", window.location.pathname);
      cache.invalidateQueries({ queryKey: ["me"] });
      return {
        message:
          mode === "verify"
            ? "Email verified. Return to your workspace to continue."
            : "Password updated. All previous sessions are signed out. Sign in with your new password.",
      };
    },
    onSuccess: (result) => setMessage(result.message),
  });
  const title =
    mode === "forgot"
      ? "Recover your account"
      : mode === "reset"
        ? "Choose a new password"
        : "Verify your email";
  return (
    <main className="content max-w-xl mx-auto">
      <Brand />
      <section className="panel stack mt-8">
        <h1>{title}</h1>
        <ErrorBox error={action.error || config.error} />
        {message ? (
          <p role="status" className="notice">
            {message}
          </p>
        ) : (
          <form
            className="stack"
            onSubmit={(e) => {
              e.preventDefault();
              action.mutate(new FormData(e.currentTarget));
            }}
          >
            {mode === "forgot" && (
              <>
                <p className="muted">We’ll send a single-use link if this email has an eligible account.</p>
                <label className="field">
                  Email address
                  <input name="email" type="email" autoComplete="email" required />
                </label>
                {config.data && !config.data.email_available && (
                  <p className="notice">
                    Email delivery has not been connected on this deployment. Password recovery will become
                    available after setup.
                  </p>
                )}
              </>
            )}
            {mode === "reset" && (
              <>
                <label className="field">
                  New password
                  <input
                    name="password"
                    type="password"
                    autoComplete="new-password"
                    required
                    minLength={12}
                    maxLength={128}
                  />
                </label>
                <label className="field">
                  Confirm new password
                  <input
                    name="confirm"
                    type="password"
                    autoComplete="new-password"
                    required
                    minLength={12}
                    maxLength={128}
                  />
                </label>
              </>
            )}
            {mode === "verify" && <p>Confirm that you opened this link from your own mailbox.</p>}
            <Button
              type="submit"
              disabled={action.isPending || (mode === "forgot" && !config.data?.email_available)}
            >
              {action.isPending
                ? "Please wait…"
                : mode === "forgot"
                  ? "Send recovery link"
                  : mode === "reset"
                    ? "Reset password"
                    : "Confirm email address"}
            </Button>
          </form>
        )}
        <Link className="text-link" href="/login">
          Back to sign in
        </Link>
        <Link className="text-link" href="/account-access">
          Account access
        </Link>
      </section>
    </main>
  );
}
