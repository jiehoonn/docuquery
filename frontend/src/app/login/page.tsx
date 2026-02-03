"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, register } from "@/lib/api";
import { setToken } from "@/lib/auth";

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from "@/components/ui/dialog";


export default function LoginPage() {

    // States
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [orgName, setOrgName] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [apiKey, setApiKey] = useState<string | null>(null);
    const router = useRouter();

    // Login Handler
    async function handleLogin(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            const data = await login(email, password);
            setToken(data.access_token);
            router.push("/dashboard");
        } catch {
            setError("Invalid credentials");
            setLoading(false);
        }
    }

    // Register Handler
    async function handleRegister(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            const data = await register(email, password, orgName);
            setToken(data.access_token);
            setApiKey(data.api_key);
        } catch {
            setError("Registration failed");
        }
        setLoading(false);
    }

    return (
        <div className="dark min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 px-4">
            {/* Decorative background glow */}
            <div className="pointer-events-none absolute inset-0 overflow-hidden">
                <div className="absolute -top-40 left-1/2 -translate-x-1/2 h-80 w-[600px] rounded-full bg-blue-600/10 blur-3xl" />
            </div>

            <Card className="relative w-full max-w-md border-white/10 bg-gray-900/80 backdrop-blur-sm shadow-2xl">
                <CardHeader className="text-center pb-2">
                    {/* Brand icon */}
                    <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 text-white text-lg font-bold">
                        DQ
                    </div>
                    <CardTitle className="text-2xl font-semibold text-white">DocuQuery</CardTitle>
                    <CardDescription>
                        Document Q&A powered by RAG
                    </CardDescription>
                </CardHeader>

                <CardContent>
                    {/* Error display */}
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-lg p-3 mb-4">
                            {error}
                        </div>
                    )}

                    <Tabs defaultValue="login" onValueChange={() => setError(null)}>
                        <TabsList className="grid w-full grid-cols-2 mb-6">
                            <TabsTrigger value="login">Login</TabsTrigger>
                            <TabsTrigger value="register">Register</TabsTrigger>
                        </TabsList>

                        {/* Login Tab */}
                        <TabsContent value="login">
                            <form onSubmit={handleLogin} className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="login-email" className="text-gray-300">Email</Label>
                                    <Input
                                        id="login-email"
                                        type="email"
                                        placeholder="you@example.com"
                                        value={email}
                                        onChange={e => setEmail(e.target.value)}
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="login-password" className="text-gray-300">Password</Label>
                                    <Input
                                        id="login-password"
                                        type="password"
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={e => setPassword(e.target.value)}
                                        required
                                    />
                                </div>
                                <Button type="submit" className="w-full mt-2" disabled={loading}>
                                    {loading ? "Signing in…" : "Login"}
                                </Button>
                            </form>
                        </TabsContent>

                        {/* Register Tab */}
                        <TabsContent value="register">
                            <form onSubmit={handleRegister} className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="register-email" className="text-gray-300">Email</Label>
                                    <Input
                                        id="register-email"
                                        type="email"
                                        placeholder="you@example.com"
                                        value={email}
                                        onChange={e => setEmail(e.target.value)}
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="register-password" className="text-gray-300">Password</Label>
                                    <Input
                                        id="register-password"
                                        type="password"
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={e => setPassword(e.target.value)}
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="register-org" className="text-gray-300">Organization Name</Label>
                                    <Input
                                        id="register-org"
                                        type="text"
                                        placeholder="Acme Corp"
                                        value={orgName}
                                        onChange={e => setOrgName(e.target.value)}
                                        required
                                    />
                                </div>
                                <Button type="submit" className="w-full mt-2" disabled={loading}>
                                    {loading ? "Creating account…" : "Create Account"}
                                </Button>
                            </form>
                        </TabsContent>
                    </Tabs>
                </CardContent>
            </Card>

            {/* API Key Dialog — shown after successful registration */}
            <Dialog open={!!apiKey} onOpenChange={() => { setApiKey(null); router.push("/dashboard"); }}>
                <DialogContent className="dark sm:max-w-md border-white/10 bg-gray-900">
                    <DialogHeader>
                        <DialogTitle className="text-white">Your API Key</DialogTitle>
                        <DialogDescription>
                            Copy this key and store it somewhere safe — it won&apos;t be shown again.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="rounded-lg bg-gray-800 border border-white/10 p-4 font-mono text-sm text-green-400 break-all select-all">
                        {apiKey}
                    </div>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            className="mr-2"
                            onClick={() => { navigator.clipboard.writeText(apiKey ?? ""); }}
                        >
                            Copy
                        </Button>
                        <Button onClick={() => { setApiKey(null); router.push("/dashboard"); }}>
                            Continue to Dashboard
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}