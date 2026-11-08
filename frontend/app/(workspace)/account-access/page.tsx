"use client";
import Link from "next/link";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, send } from "@/lib/api";
import { ErrorBox, Heading, useUser } from "@/components/common";
import { Button } from "@/components/ui/button";

export default function AccountAccessPage() {
  const { data: user } = useUser();
  const config = useQuery({
    queryKey: ["auth-config"],
    queryFn: () => api<{ email_available: boolean; verification_required: boolean }>("/auth/config"),
  });
  const request = useMutation({
    mutationFn: () => api<{ message: string }>("/auth/request-verification", send("POST")),
  });
  return (
    <>
      <Heading title="Account access" subtitle="Verify your email and keep your account recoverable." />
      <section className="panel stack">
        <ErrorBox error={config.error || request.error} />
        <h2>{user?.email_verified ? "Email verified" : "Verify your email"}</h2>
        <p>{user?.email}</p>
        {config.data && !config.data.email_available && (
          <div className="notice">
            Email delivery is not connected on this deployment yet. Verification and password recovery require
            the operator to complete email setup.
          </div>
        )}
        {config.data?.verification_required && !user?.email_verified && (
          <p>Verify your email before uploading documents, using CV Studio or publishing jobs.</p>
        )}
        {!user?.email_verified && (
          <Button
            disabled={!config.data?.email_available || request.isPending}
            onClick={() => request.mutate()}
          >
            {request.isPending ? "Sending…" : "Send verification email"}
          </Button>
        )}
        {request.data && (
          <p role="status" className="notice">
            {request.data.message}
          </p>
        )}
        <Link className="text-link" href="/forgot-password">
          Request a password recovery link
        </Link>
        <Link className="text-link" href="/settings">
          Change password or delete account
        </Link>
      </section>
    </>
  );
}
