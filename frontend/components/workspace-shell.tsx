"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  LayoutDashboard,
  FileText,
  BriefcaseBusiness,
  ScanLine,
  Settings,
  ShieldCheck,
  Search,
  ChevronRight,
  Menu,
  X,
  LogOut,
  Users,
  ArrowUpRight,
} from "lucide-react";
import { api, send, ApiError } from "@/lib/api";
import { Brand, ErrorBox, Loading, useUser } from "@/components/common";
import { Button } from "@/components/ui/button";

export function WorkspaceShell({ children }: { children: React.ReactNode }) {
  const { data: user, error, isPending } = useUser();
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => api<{ demo_mode: boolean }>("/health"),
  });
  const router = useRouter(),
    path = usePathname(),
    cache = useQueryClient();
  const [open, setOpen] = useState(false),
    [actionError, setActionError] = useState<unknown>();
  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) router.replace("/login");
  }, [error, router]);
  if (isPending)
    return (
      <main className="content">
        <Loading />
      </main>
    );
  if (!user)
    return (
      <main className="content">
        <ErrorBox error={error} />
        <Button asChild>
          <Link href="/login">Sign in</Link>
        </Button>
      </main>
    );
  const recruiter = user.role === "RECRUITER";
  const links = [
    { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
    ...(!recruiter ? [{ href: "/resumes", label: "My resumes", icon: FileText }] : []),
    { href: "/jobs", label: recruiter ? "Job management" : "Explore jobs", icon: BriefcaseBusiness },
    { href: "/matches", label: recruiter ? "Candidate matching" : "My analyses", icon: ScanLine },
    { href: "/applications", label: "Applications", icon: Users },
  ];
  const active = links.find((link) => path.startsWith(link.href))?.label || "Settings";
  async function logout() {
    try {
      await api("/auth/logout", send("POST"));
      cache.clear();
      router.push("/login");
    } catch (e) {
      setActionError(e);
    }
  }
  return (
    <>
      <a href="#main" className="skip">
        Skip to content
      </a>
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="row between">
          <Brand />
          {open && (
            <Button
              variant="ghost"
              className="mobile-menu"
              onClick={() => setOpen(false)}
              aria-label="Close menu"
            >
              <X size={18} />
            </Button>
          )}
        </div>
        <div className="eyebrow workspace-label">{recruiter ? "Recruiter" : "Applicant"} workspace</div>
        <nav className="side-nav" aria-label="Main navigation">
          {links.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={`side-link ${path.startsWith(href) ? "active" : ""}`}
              aria-current={path.startsWith(href) ? "page" : undefined}
              onClick={() => setOpen(false)}
            >
              <Icon />
              {label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="privacy-card">
            <ShieldCheck size={22} />
            <strong>Private by design</strong>Your documents stay yours. Share only when you choose to apply.
          </div>
          <Link
            href="/settings"
            onClick={() => setOpen(false)}
            className={`side-link ${path === "/settings" ? "active" : ""}`}
          >
            <Settings />
            Settings
          </Link>
          <button onClick={logout} className="side-link w-full">
            <LogOut />
            Sign out
          </button>
          <div className="user-badge">
            <span className="avatar">{user.full_name.slice(0, 1)}</span>
            <div>
              <strong>{user.full_name}</strong>
              <small>{user.role.toLowerCase()} account</small>
            </div>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="row">
            <Button
              variant="ghost"
              className="mobile-menu"
              onClick={() => setOpen(true)}
              aria-label="Open navigation"
            >
              <Menu size={20} />
            </Button>
            <span className="crumb">
              Workspace <ChevronRight size={12} className="inline mx-2" /> <strong>{active}</strong>
            </span>
          </div>
          <div className="topbar-tools">
            <Link href="/jobs" className="search-link">
              <Search size={14} />
              Find your next opportunity
            </Link>
            <Link href="/" className="text-link">
              About TalentLens <ArrowUpRight size={12} className="inline" />
            </Link>
            <Link href="/settings" className="avatar" aria-label="Account settings">
              {user.full_name.slice(0, 1)}
            </Link>
          </div>
        </header>
        <main id="main" className="content">
          {health?.demo_mode && (
            <div className="notice mb-5">
              Synthetic demo workspace. These fictional records use the real processing pipeline. Do not
              upload personal data here.
            </div>
          )}
          <ErrorBox error={actionError} />
          {children}
        </main>
      </div>
    </>
  );
}
