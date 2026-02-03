"use client";

import { useState, useEffect, useRef } from "react";
import { listDocuments, uploadDocument, deleteDocument } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

// Type for a document from the API
interface Document {
    id: string;
    title: string | null;
    file_path: string;
    file_size_bytes: number;
    status: "queued" | "processing" | "ready" | "failed";
    chunks_count: number;
    created_at: string;
    processed_at: string | null;
    error_message: string | null;
}

const statusStyles: Record<string, string> = {
    ready: "border-green-500/50 bg-green-500/10 text-green-400",
    processing: "border-yellow-500/50 bg-yellow-500/10 text-yellow-400",
    queued: "border-blue-500/50 bg-blue-500/10 text-blue-400",
    failed: "border-red-500/50 bg-red-500/10 text-red-400",
};

export default function DocumentsPage() {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);

    const fileRef = useRef<HTMLInputElement>(null);

    // Fetch documents — reusable for initial load + refresh after upload/delete
    function refreshDocs() {
        listDocuments().then((data) => {
            setDocuments(data.documents);
            setLoading(false);
        }).catch(() => {
            setLoading(false);
        });
    }

    useEffect(() => {
        refreshDocs();
    }, []);

    async function handleUpload(file: File) {
        setUploading(true);
        await uploadDocument(file);
        setUploading(false);
        refreshDocs();
    }

    async function handleDelete(id: string) {
        if (!window.confirm("Are you sure you want to delete this document?")) return;
        await deleteDocument(id);
        refreshDocs();
    }

    function formatFileSize(bytes: number): string {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }

    return (
        <div>
            {/* Page header */}
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-semibold text-white">Documents</h1>
                    <p className="text-sm text-gray-400 mt-1">
                        Upload and manage your documents for Q&A
                    </p>
                </div>
                <input
                    type="file"
                    ref={fileRef}
                    accept=".pdf,.docx,.txt"
                    className="hidden"
                    onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleUpload(file);
                    }}
                />
                <Button onClick={() => fileRef.current?.click()} disabled={uploading}>
                    {uploading ? "Uploading…" : "Upload Document"}
                </Button>
            </div>

            {/* Document list */}
            {loading ? (
                <div className="text-center py-12 text-gray-400">Loading documents…</div>
            ) : documents.length === 0 ? (
                <Card className="border-dashed border-white/10 bg-transparent">
                    <CardContent className="py-12 text-center">
                        <p className="text-gray-400 mb-4">No documents yet. Upload one to get started!</p>
                        <Button variant="outline" onClick={() => fileRef.current?.click()}>
                            Upload your first document
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-3">
                    {documents.map((doc) => (
                        <Card
                            key={doc.id}
                            className="border-white/10 bg-gray-900/50 hover:bg-gray-900/80 transition-colors"
                        >
                            <CardContent className="py-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4 min-w-0">
                                        <div className="min-w-0">
                                            <p className="text-sm font-medium text-white truncate">
                                                {doc.title || "Untitled Document"}
                                            </p>
                                            <p className="text-xs text-gray-500 mt-0.5">
                                                {formatFileSize(doc.file_size_bytes)} · {new Date(doc.created_at).toLocaleDateString()}
                                                {doc.chunks_count > 0 && ` · ${doc.chunks_count} chunks`}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <Badge
                                            variant="outline"
                                            className={statusStyles[doc.status] || ""}
                                        >
                                            {doc.status}
                                        </Badge>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className="text-gray-400 hover:text-red-400"
                                            onClick={() => handleDelete(doc.id)}
                                        >
                                            Delete
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}