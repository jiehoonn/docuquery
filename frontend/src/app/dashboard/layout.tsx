"use client";

import { useEffect, useSyncExternalStore } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { getToken, clearToken } from "@/lib/auth";
import { Button } from "@/components/ui/button";

// Read auth token from localStorage — SSR-safe, no hydration mismatch
function useIsAuthenticated() {
    return useSyncExternalStore(
        (onStoreChange) => {
            window.addEventListener("storage", onStoreChange);
            return () => window.removeEventListener("storage", onStoreChange);
        },
        () => !!getToken(),   // client: check localStorage
        () => false            // server: always false
    );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const pathname = usePathname();
    const isAuthenticated = useIsAuthenticated();

    // Redirect to login if not authenticated
    useEffect(() => {
        if (!isAuthenticated) {
            router.push("/login");
        }
    }, [isAuthenticated, router]);

    // Server and client both render this initially → no hydration mismatch
    if (!isAuthenticated) return <div className="dark min-h-screen bg-gray-950" />;

    function handleLogout() {
        clearToken();
        router.push("/login");
    }

    // Sidebar nav items
    const navItems = [
        { label: "Documents", href: "/dashboard" },
        { label: "Query", href: "/dashboard/query" },
        { label: "Usage", href: "/dashboard/usage" },
    ];

    return (
        <div className="dark min-h-screen flex bg-gray-950">
            {/* Sidebar */}
            <aside className="flex flex-col w-64 border-r border-white/10 bg-gray-900/50 px-4 py-6">
                {/* Brand */}
                <Link href="/dashboard" className="flex items-center gap-3 px-3 mb-8">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white text-xs font-bold">
                        DQ
                    </div>
                    <span className="text-lg font-semibold text-white">DocuQuery</span>
                </Link>

                {/* Nav links */}
                <nav className="flex-1">
                    <ul className="space-y-1">
                        {navItems.map((item) => {
                            const isActive = item.href === "/dashboard"
                                ? pathname === item.href
                                : pathname.startsWith(item.href);
                            return (
                                <li key={item.href}>
                                    <Link
                                        href={item.href}
                                        className={`block py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
                                            isActive
                                                ? "bg-white/10 text-white"
                                                : "text-gray-400 hover:text-white hover:bg-white/5"
                                        }`}
                                    >
                                        {item.label}
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                </nav>

                {/* Logout */}
                <Button
                    variant="ghost"
                    className="w-full justify-start text-gray-400 hover:text-white hover:bg-white/5"
                    onClick={handleLogout}
                >
                    Logout
                </Button>
            </aside>

            {/* Main content area */}
            <main className="flex-1 p-8 overflow-auto">
                {children}
            </main>
        </div>
    );
}