"use client";
import Link from "next/link";
import { FileText, ArrowUpRight } from "lucide-react";
import { dateLabel, Empty, Status } from "@/components/common";
import type { Resume } from "@/types/api";
export function ResumeTable({ resumes }: { resumes: Resume[] }) {
  if (!resumes.length)
    return (
      <Empty title="Your story starts here">
        Upload your first resume to extract and review your qualifications.
      </Empty>
    );
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>DOCUMENT</th>
            <th>UPLOADED</th>
            <th>STATUS</th>
            <th>
              <span className="sr-only">Open</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {resumes.map((r) => (
            <tr key={r.id}>
              <td>
                <Link href={`/resumes/${r.id}`} className="row">
                  <FileText size={34} className="file-icon" />
                  <div>
                    <span className="table-title">{r.original_filename}</span>
                    <span className="table-sub">
                      {Math.ceil(r.file_size / 1024)} KB · Version {r.version}
                    </span>
                  </div>
                </Link>
              </td>
              <td className="table-sub">{dateLabel(r.created_at)}</td>
              <td>
                <Status value={r.status} />
              </td>
              <td>
                <Link href={`/resumes/${r.id}`} aria-label={`Review ${r.original_filename}`}>
                  <ArrowUpRight size={15} className="muted" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
