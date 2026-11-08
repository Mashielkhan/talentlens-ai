"use client";
import { useMutation } from "@tanstack/react-query";
import { api, send } from "@/lib/api";
import { ErrorBox, Heading } from "@/components/common";
import { Button } from "@/components/ui/button";

export default function FeedbackPage() {
  const submit = useMutation({
    mutationFn: (body: unknown) => api<{ message: string }>("/feedback", send("POST", body)),
  });
  return (
    <>
      <Heading
        title="Beta feedback"
        subtitle="Tell us what worked, what failed and what would make this useful."
      />
      <section className="panel stack max-w-2xl">
        <p className="muted">
          Feedback is private to the beta team. Avoid pasting your CV, passwords or other sensitive
          information. Up to five submissions per day.
        </p>
        <ErrorBox error={submit.error} />
        {submit.data ? (
          <p role="status" className="notice">
            {submit.data.message}
          </p>
        ) : (
          <form
            className="stack"
            onSubmit={(e) => {
              e.preventDefault();
              submit.mutate(Object.fromEntries(new FormData(e.currentTarget)));
            }}
          >
            <label className="field">
              Category
              <select name="category">
                <option value="bug">Something went wrong</option>
                <option value="suggestion">Suggestion</option>
                <option value="other">Other feedback</option>
              </select>
            </label>
            <label className="field">
              Your feedback
              <textarea name="message" required minLength={10} maxLength={3000} rows={7} />
            </label>
            <Button type="submit" disabled={submit.isPending}>
              {submit.isPending ? "Saving…" : "Send feedback"}
            </Button>
          </form>
        )}
      </section>
    </>
  );
}
