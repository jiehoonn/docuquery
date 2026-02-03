"use client";

import { useState, useEffect } from "react";
import { getUsage } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface RateLimit {
    current_requests_this_hour: number;
    limit_per_hour: number;
    remaining: number;
}

interface UsageData {
    storage_used_mb: number;
    storage_limit_mb: number;
    queries_this_month: number;
    total_documents: number;
    documents_ready: number;
    documents_processing: number;
    documents_failed: number;
    rate_limit: RateLimit;
}

function getUsageLevel(current: number, limit: number): {
    color: string;
    bg: string;
    border: string;
    label: string;
} {
    const percentage = (current / limit) * 100;

    if (percentage < 50) {
        return { color: "text-green-400", bg: "bg-green-500", border: "border-green-500/50", label: "Healthy" };
    } else if (percentage < 80) {
        return { color: "text-yellow-400", bg: "bg-yellow-500", border: "border-yellow-500/50", label: "Warning" };
    } else {
        return { color: "text-red-400", bg: "bg-red-500", border: "border-red-500/50", label: "Critical" };
    }
}

export default function UsagePage() {
    const [usage, setUsage] = useState<UsageData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getUsage()
            .then((data) => {
                setUsage(data);
                setLoading(false);
            })
            .catch(() => {
                setLoading(false);
            });
    }, []);

    if (loading) {
        return (
            <div className="max-w-4xl">
                <div className="mb-8">
                    <h1 className="text-2xl font-semibold text-white">Usage</h1>
                    <p className="text-sm text-gray-400 mt-1">
                        Monitor your storage, documents, and rate limits
                    </p>
                </div>
                <div className="text-center py-12 text-gray-400">Loading usage data…</div>
            </div>
        );
    }

    if (!usage) {
        return (
            <div className="max-w-4xl">
                <div className="mb-8">
                    <h1 className="text-2xl font-semibold text-white">Usage</h1>
                </div>
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-lg p-3">
                    Failed to load usage data.
                </div>
            </div>
        );
    }

    const storageLevel = getUsageLevel(usage.storage_used_mb, usage.storage_limit_mb);
    const rateLevel = getUsageLevel(usage.rate_limit.current_requests_this_hour, usage.rate_limit.limit_per_hour);
    const storagePercent = Math.min((usage.storage_used_mb / usage.storage_limit_mb) * 100, 100);
    const ratePercent = Math.min((usage.rate_limit.current_requests_this_hour / usage.rate_limit.limit_per_hour) * 100, 100);

    return (
        <div className="max-w-4xl">
            {/* Page header */}
            <div className="mb-8">
                <h1 className="text-2xl font-semibold text-white">Usage</h1>
                <p className="text-sm text-gray-400 mt-1">
                    Monitor your storage, documents, and rate limits
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Storage Card */}
                <Card className="border-white/10 bg-gray-900/50">
                    <CardContent className="pt-6">
                        <div className="flex justify-between items-center mb-3">
                            <p className="text-sm font-medium text-gray-400">Storage</p>
                            <Badge variant="outline" className={`${storageLevel.border} ${storageLevel.color}`}>
                                {storageLevel.label}
                            </Badge>
                        </div>
                        <p className="text-2xl font-semibold text-white mb-1">
                            {usage.storage_used_mb} <span className="text-sm text-gray-500">/ {usage.storage_limit_mb} MB</span>
                        </p>
                        {/* Progress bar */}
                        <div className="w-full h-2 bg-gray-800 rounded-full mt-3">
                            <div
                                className={`h-2 rounded-full transition-all ${storageLevel.bg}`}
                                style={{ width: `${storagePercent}%` }}
                            />
                        </div>
                    </CardContent>
                </Card>

                {/* Rate Limit Card */}
                <Card className="border-white/10 bg-gray-900/50">
                    <CardContent className="pt-6">
                        <div className="flex justify-between items-center mb-3">
                            <p className="text-sm font-medium text-gray-400">Rate Limit</p>
                            <Badge variant="outline" className={`${rateLevel.border} ${rateLevel.color}`}>
                                {rateLevel.label}
                            </Badge>
                        </div>
                        <p className="text-2xl font-semibold text-white mb-1">
                            {usage.rate_limit.remaining} <span className="text-sm text-gray-500">remaining this hour</span>
                        </p>
                        <div className="w-full h-2 bg-gray-800 rounded-full mt-3">
                            <div
                                className={`h-2 rounded-full transition-all ${rateLevel.bg}`}
                                style={{ width: `${ratePercent}%` }}
                            />
                        </div>
                        <p className="text-xs text-gray-500 mt-2">
                            {usage.rate_limit.current_requests_this_hour} / {usage.rate_limit.limit_per_hour} requests used
                        </p>
                    </CardContent>
                </Card>

                {/* Documents Breakdown Card */}
                <Card className="border-white/10 bg-gray-900/50">
                    <CardContent className="pt-6">
                        <p className="text-sm font-medium text-gray-400 mb-3">Documents</p>
                        <p className="text-2xl font-semibold text-white mb-4">{usage.total_documents}</p>
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-400">Ready</span>
                                <span className="text-green-400">{usage.documents_ready}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-400">Processing</span>
                                <span className="text-yellow-400">{usage.documents_processing}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-400">Failed</span>
                                <span className="text-red-400">{usage.documents_failed}</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Queries This Month Card */}
                <Card className="border-white/10 bg-gray-900/50">
                    <CardContent className="pt-6">
                        <p className="text-sm font-medium text-gray-400 mb-3">Queries This Month</p>
                        <p className="text-2xl font-semibold text-white">{usage.queries_this_month}</p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}