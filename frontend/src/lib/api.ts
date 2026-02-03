import { getToken, clearToken } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// fetchAPI helper function
async function fetchAPI(path: string, options: RequestInit = {}) {
    const token = getToken();
    const headers: Record<string, string> = {
        ...(options.headers as Record<string, string>),
    };
    // 1. Build headers - merge auth token + any custom headers
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    // 2. Call fetch(API_URL + path, ...)
    const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers,
    });
    // 3. If response is 401 on a protected route -> clearToken() and redirect to /login
    //    Skip for auth endpoints where 401 means "wrong credentials", not "expired token"
    if (response.status === 401 && !path.startsWith("/api/v1/auth")) {
        clearToken();
        window.location.href = "/login";
        throw new Error("Unauthorized");
    }
    // 4. Return the response
    return response;
}

// 1. /api/v1/auth/login - POST
export async function login(email: string, password: string) {
    const res = await fetchAPI("/api/v1/auth/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error("Login failed");
    return res.json();
}

// 2. /api/v1/auth/register - POST
export async function register(email: string, password: string, orgName: string) {
    const res = await fetchAPI("/api/v1/auth/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password, organization_name: orgName }),
    });
    if (!res.ok) throw new Error("Registration failed");
    return res.json();
}

// 3. /api/v1/documents - GET
export async function listDocuments() {
    const res = await fetchAPI("/api/v1/documents", {
        method: "GET",
        headers: {
            "Content-Type": "application/json"
        },
    });
    return res.json();
}

// 4. /api/v1/documents/upload - POST
export async function uploadDocument(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetchAPI("/api/v1/documents/upload", {
        method: "POST",
        body: formData,
        // No Content-Type header! Browser sets it automatically with boundary
    });
    return res.json();
}

// 5. /api/v1/documents/{id} - DELETE
export async function deleteDocument(id: string) {
    await fetchAPI(`/api/v1/documents/${id}`, {
        method: "DELETE",
    });
}

// 6. /api/v1/query - POST
export async function queryDocuments(question: string) {
    const res = await fetchAPI("/api/v1/query", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ question }),
    });
    return res.json();
}

// 7. /api/v1/usage - GET
export async function getUsage() {
    const res = await fetchAPI("/api/v1/usage", {
        method: "GET",
        headers: {
            "Content-Type": "application/json"
        },
    });
    return res.json();
}
