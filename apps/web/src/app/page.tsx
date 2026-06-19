import Link from "next/link";
import { Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ArchiveStatsCards } from "@/components/dashboard/archive-stats-cards";
import { RecentTranscriptionsTable } from "@/components/dashboard/recent-transcriptions-table";

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1.5">
            Your transcript archive on Backblaze B2 at a glance.
          </p>
        </div>
        <Button asChild size="sm" className="h-8">
          <Link href="/upload">
            <Upload className="h-3.5 w-3.5" />
            Add media
          </Link>
        </Button>
      </div>
      <ArchiveStatsCards />
      <div className="animate-fade-in-up stagger-4">
        <RecentTranscriptionsTable />
      </div>
    </div>
  );
}
