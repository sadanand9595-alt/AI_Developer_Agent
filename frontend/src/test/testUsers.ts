import type { User } from "../api/types";

export const regularUser: User = {
  id: "user-1",
  email: "user@example.com",
  name: "Regular User",
  is_active: true,
  is_admin: false,
  created_at: "2026-01-01T00:00:00Z",
};

export const adminUser: User = {
  id: "admin-1",
  email: "admin@example.com",
  name: "Admin User",
  is_active: true,
  is_admin: true,
  created_at: "2026-01-01T00:00:00Z",
};
