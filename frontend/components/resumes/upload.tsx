"use client";
import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CloudUpload, LockKeyhole } from "lucide-react";
import { api } from "@/lib/api";
import { ErrorBox } from "@/components/common";
import { Button } from "@/components/ui/button";
import type { Resume } from "@/types/api";

export function Upload() {
  const fileRef = useRef<HTMLInputElement>(null),
    cache = useQueryClient();
  const [drag, setDrag] = useState(false),
    [validation, setValidation] = useState<unknown>();
  const upload = useMutation({
    mutationFn: (file: File) => {
      const body = new FormData();
      body.append("file", file);
      return api<Resume>("/resumes", { method: "POST", body });
    },
    onSuccess: () => {
      cache.invalidateQueries({ queryKey: ["resumes"] });
      cache.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
  function select(file?: File) {
    if (!file || upload.isPending) return;
    setValidation(undefined);
    upload.reset();
    if (!/\.(pdf|docx)$/i.test(file.name) || file.size > 10 * 1024 * 1024) {
      setValidation(new Error("Choose a PDF or DOCX file smaller than 10 MB."));
      return;
    }
    upload.mutate(file);
  }
  return (
    <>
      <input
        ref={fileRef}
        type="file"
        accept=".pdf,.docx"
        className="sr-only"
        aria-label="Resume file"
        onChange={(e) => {
          select(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
      <div
        className={`upload-zone ${drag ? "drag" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          select(e.dataTransfer.files[0]);
        }}
      >
        <div className="upload-icon">
          <CloudUpload size={22} />
        </div>
        <strong>{upload.isPending ? "Uploading your resume…" : "Drop your resume here, or browse"}</strong>
        <p>PDF or DOCX · Up to 10 MB</p>
        <Button variant="outline" disabled={upload.isPending} onClick={() => fileRef.current?.click()}>
          Choose a file
        </Button>
      </div>
      <div className="upload-foot">
        <LockKeyhole size={11} />
        Securely stored. Only shared with your explicit consent.
      </div>
      {upload.isSuccess && (
        <p className="text-xs text-emerald-700 mt-3" role="status">
          Upload received. Processing will start shortly.
        </p>
      )}
      <ErrorBox error={validation || upload.error} />
    </>
  );
}
