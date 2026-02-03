"use client";

import { useState } from "react";
import { queryDocuments } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

interface Source {
    document_id: string;
    text: string;
    chunk_index: number;
    score: number;
}

interface QueryResponse {
    answer: string;
    sources: Source[];
    cached: boolean;
}

export default function QueryPage() {
    const [question, setQuestion] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<QueryResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    async function handleQuery(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        if (!question.trim()) {
            setError("Please enter a question.");
            return;
        }
        setLoading(true);
        setError(null);
        setResult(null);
        try {
            const res = await queryDocuments(question);
            setResult(res);
        } catch {
            setError("An error occurred while querying documents.");
        }
        setLoading(false);
    }

    return (
        <div className="max-w-3xl">
            {/* Page header */}
            <div className="mb-8">
                <h1 className="text-2xl font-semibold text-white">Query Documents</h1>
                <p className="text-sm text-gray-400 mt-1">
                    Ask questions about your uploaded documents
                </p>
            </div>

            {/* Search form */}
            <form onSubmit={handleQuery} className="flex gap-3 mb-8">
                <Input
                    type="text"
                    placeholder="e.g. What file types does DocuQuery support?"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    className="flex-1 text-white"
                />
                <Button type="submit" disabled={loading}>
                    {loading ? "Thinking…" : "Ask"}
                </Button>
            </form>

            {/* Error display */}
            {error && (
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-lg p-3 mb-6">
                    {error}
                </div>
            )}

            {/* Loading state */}
            {loading && (
                <Card className="border-white/10 bg-gray-900/50 mb-6">
                    <CardContent className="py-8 text-center text-gray-400">
                        Searching documents and generating answer…
                    </CardContent>
                </Card>
            )}

            {/* Answer */}
            {result && (
                <div className="space-y-6">
                    <Card className="border-white/10 bg-gray-900/50">
                        <CardContent className="pt-6">
                            <p className="text-sm font-medium text-gray-400 mb-3">Answer</p>
                            <p className="text-white leading-relaxed whitespace-pre-wrap">
                                {result.answer}
                            </p>
                            {/* Metadata badges */}
                            <div className="flex gap-2 mt-4 pt-4 border-t border-white/10">
                                {result.cached && (
                                    <Badge variant="outline" className="border-green-500/50 bg-green-500/10 text-green-400">
                                        cached
                                    </Badge>
                                )}
                                <Badge variant="outline" className="border-gray-600 text-gray-400">
                                    {result.sources.length} sources
                                </Badge>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Source chunks */}
                    {result.sources.length > 0 && (
                        <div>
                            <p className="text-sm font-medium text-gray-400 mb-3">Sources</p>
                            <div className="space-y-3">
                                {result.sources.map((source, i) => (
                                    <Card key={i} className="border-white/10 bg-gray-900/30">
                                        <CardContent className="py-4">
                                            <div className="flex items-center gap-2 mb-2">
                                                <Badge variant="outline" className="border-blue-500/50 bg-blue-500/10 text-blue-400">
                                                    [{i + 1}]
                                                </Badge>
                                                <span className="text-xs text-gray-500">
                                                    chunk #{source.chunk_index} · {(source.score * 100).toFixed(0)}% match
                                                </span>
                                            </div>
                                            <p className="text-sm text-gray-300 leading-relaxed">
                                                {source.text}
                                            </p>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}