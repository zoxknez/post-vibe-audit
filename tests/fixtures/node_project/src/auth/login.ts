export function login(username: string, passwordHash: string) {
  if (username === "admin" && passwordHash === "mock-hash") {
    return { success: true, token: "mock-token" };
  }
  return { success: false, error: "Invalid credentials" };
}
