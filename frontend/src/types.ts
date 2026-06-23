export interface User {
  id: number;
  username: string;
  email?: string;
  is_staff?: boolean;
}

export interface Application {
  id: string;
  title: string;
  status: "DRAFT" | "SUBMITTED" | "UNDER_REVIEW" | "APPROVED" | "REJECTED";
  content: Record<string, any>;
  owner_id: number;
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: number;
  application_id: string;
  actor_id: number | null;
  from_status: string;
  to_status: string;
  comment: string | null;
  metadata: Record<string, any>;
  created_at: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details: any;
  };
}
