export type User = {
  id: string;
  full_name: string;
  email: string;
  role: "APPLICANT" | "RECRUITER";
  profile: Record<string, string>;
  email_verified: boolean;
};

export type CvContent = Record<
  | "name"
  | "email"
  | "phone"
  | "links"
  | "summary"
  | "skills"
  | "experience"
  | "education"
  | "projects"
  | "certifications",
  string
>;
export type CvDraft = {
  id: string;
  resume_id: string;
  source_version: number;
  source_outdated: boolean;
  title: string;
  target_description: string;
  original: CvContent;
  content: CvContent;
  revision: number;
  approved_revision: number | null;
  created_at: string;
  guidance: {
    method: string;
    prompts: string[];
    documented_target_skills: string[];
    not_documented_target_skills: string[];
    suggestions: {
      id: number;
      section: keyof CvContent;
      original: string;
      replacement: string;
      reason: string;
    }[];
  };
};
export type Skill = {
  name: string;
  category: string;
  source_section: string;
  evidence: string;
  user_verified: boolean;
};
export type Resume = {
  id: string;
  original_filename: string;
  file_size: number;
  status: string;
  stage: string;
  error_code: string | null;
  version: number;
  created_at: string;
  corrections: Record<string, unknown>;
  parsed_data: {
    contact?: Record<string, string | string[]>;
    skills?: Skill[];
    sections?: Record<string, string>;
    education?: string;
    projects?: string;
    certifications?: string;
    total_experience_months?: number;
    uncertainties?: string[];
  };
};
export type Requirement = { name: string; weight: number };
export type JobInput = {
  title: string;
  company: string;
  description: string;
  location: string;
  employment_type: string;
  remote_policy: string;
  status: string;
  required_skills: Requirement[];
  preferred_skills: Requirement[];
  min_experience_months: number;
  education_requirement: string;
  requirements_confirmed: boolean;
};
export type Job = JobInput & { id: string; recruiter_id: string; version: number; created_at: string };
export type Application = {
  id: string;
  job_id: string;
  resume_id: string;
  candidate_name: string;
  job_title: string;
  company: string;
  status: string;
  resume_status: string;
  created_at: string;
  consent_at: string;
};
export type Task = {
  id: string;
  kind: string;
  status: string;
  progress: number;
  error_code: string | null;
  result: { match_ids?: string[]; candidate_count?: number };
};
export type Match = {
  id: string;
  job_id: string;
  resume_id: string;
  application_id: string | null;
  candidate_name: string;
  created_at: string;
  job_title: string;
  company: string;
  resume_filename: string;
  compatibility_index: number;
  score_breakdown: Record<string, number | null>;
  effective_weights: Record<string, number>;
  matched_skills: string[];
  not_documented_required_skills: string[];
  not_documented_preferred_skills: string[];
  evidence: Skill[];
  relevant_experience_months: number | null;
  education_evidence: string;
  uncertainties: string[];
  recommendations: { skill: string; action: string; url: string | null }[];
  disclaimer: string;
  model_version: string;
  scoring_version: string;
  as_of_date: string;
};
export type Analytics = {
  resumes: number;
  applications: number;
  active_jobs: number;
  analyses: number;
  documented_skills: number;
  ready_resumes: number;
  skills: { name: string; count: number }[];
  gaps: { name: string; count: number }[];
  score_distribution: { name: string; count: number }[];
};
