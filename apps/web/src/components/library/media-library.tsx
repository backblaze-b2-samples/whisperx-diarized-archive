"use client";

import { useMemo } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { FileAudio, Inbox, Loader2, Mic, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import {
  useArchiveItems,
  useJobs,
  useStartTranscription,
} from "@/lib/queries";
import { formatDuration } from "@/lib/archive-format";
import type { ArchiveItem, TranscriptionJob } from "@whisperx-diarized-archive/shared";

function StatusBadge({
  item,
  job,
}: {
  item: ArchiveItem;
  job: TranscriptionJob | undefined;
}) {
  if (job && job.status !== "done" && job.status !== "error") {
    return (
      <Badge variant="secondary" className="gap-1 capitalize">
        <Loader2 className="h-3 w-3 animate-spin" />
        {job.status}
        {job.progress > 0 ? ` ${Math.round(job.progress * 100)}%` : ""}
      </Badge>
    );
  }
  if (job && job.status === "error") {
    return <Badge variant="destructive">Error</Badge>;
  }
  if (item.transcribed) {
    return (
      <Badge variant="outline" className="gap-1 border-[var(--success)] text-[var(--success)]">
        {item.diarized ? <Users className="h-3 w-3" /> : <Mic className="h-3 w-3" />}
        {item.diarized ? "Diarized" : "Transcribed"}
      </Badge>
    );
  }
  return <Badge variant="secondary">Not transcribed</Badge>;
}

export function MediaLibrary() {
  const { data: items = [], isLoading, error, refetch } = useArchiveItems();
  const anyActive = items.length > 0;
  const { data: jobs = [] } = useJobs(anyActive);
  const startMutation = useStartTranscription();

  // Latest job per media key (jobs come newest-first from the API).
  const jobByKey = useMemo(() => {
    const map = new Map<string, TranscriptionJob>();
    for (const j of jobs) {
      if (!map.has(j.key)) map.set(j.key, j);
    }
    return map;
  }, [jobs]);

  const handleTranscribe = (item: ArchiveItem) => {
    startMutation.mutate(item.key, {
      onSuccess: () => toast.success(`Queued ${item.filename} for transcription`),
      onError: (err) => toast.error(err.message || "Failed to start transcription"),
    });
  };

  return (
    <Card>
      <CardHeader className="border-b border-border py-4 px-5">
        <CardTitle className="card-title">Media files</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : error ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : items.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="No media yet"
            description="Upload an audio or video file to start building your transcript archive."
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/40 hover:bg-muted/40">
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  File
                </TableHead>
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Size
                </TableHead>
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Duration
                </TableHead>
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Status
                </TableHead>
                <TableHead className="text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Actions
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item) => {
                const job = jobByKey.get(item.key);
                const busy =
                  !!job && job.status !== "done" && job.status !== "error";
                return (
                  <TableRow key={item.key} className="table-row-hover">
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2 truncate">
                        <FileAudio className="h-4 w-4 shrink-0 text-muted-foreground" />
                        <span className="truncate">{item.filename}</span>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground tabular-nums whitespace-nowrap">
                      {item.size_human}
                    </TableCell>
                    <TableCell className="text-muted-foreground whitespace-nowrap">
                      {formatDuration(item.duration)}
                    </TableCell>
                    <TableCell className="whitespace-nowrap">
                      <StatusBadge item={item} job={job} />
                    </TableCell>
                    <TableCell className="text-right whitespace-nowrap">
                      {item.transcribed ? (
                        <Button asChild variant="outline" size="sm" className="h-7 text-xs">
                          <Link href={`/library/${encodeURIComponent(item.key)}`}>
                            View transcript
                          </Link>
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          className="h-7 text-xs"
                          disabled={busy || startMutation.isPending}
                          onClick={() => handleTranscribe(item)}
                        >
                          {busy ? "Transcribing…" : "Transcribe"}
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
