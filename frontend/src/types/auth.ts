export type Role = "admin" | "sales" | "viewer";

export interface User {
  id: string;
  email: string;
  role: Role;
}

export interface TokenPayload {
  sub: string;
  role: Role;
  exp: number;
  iat: number;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: Role;
  user_id: string;
}
