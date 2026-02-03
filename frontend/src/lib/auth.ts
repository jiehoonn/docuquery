// Read Token from localStorage
export function getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("auth_token");
}

// Save Token to localStorage
export function setToken(token: string): void {
    if (typeof window === "undefined") return;
    localStorage.setItem("auth_token", token);
}

// Clear Token from localStorage
export function clearToken(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem("auth_token");
}