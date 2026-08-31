export interface User {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface Task {
  id: string;
  user_id: string;
  title: string;
  description: string;
  status: string;
  priority: number;
  retry_count: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface Conversation {
  id: string;
  user_id: string;
  title: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: string;
  content: string;
  tool_name: string | null;
  created_at: string;
}

export interface ApprovalRequest {
  id: string;
  user_id: string;
  action: string;
  reason: string;
  requested_operation: string;
  status: string;
  requested_at: string;
  reviewed_at: string | null;
}
