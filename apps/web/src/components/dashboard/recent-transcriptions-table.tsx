"use client";

import { useMemo } from "react";
import Link from "next/link";
import { ArrowRight, Inbox, Mic, Users } from "lucide-react";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
import { useArchiveItems } from "@/lib/queries";
import { formatDate } from "@/lib/utils";
import { formatDuration } from "@/lib/archive-format";

export function RecentTranscriptionsTable() {
  const { data: items = [], isLoading, error, refetch } = useArchiveItems();

  const transcribed = useMemo(
    () => items.filter((i) => i.transcribed).slice(0, 10),
    [items],
  );

  return (
    <Card>
      <CardHeader className="border-b border-border py-4 px-5">
        <CardTitle className="card-title">Recent Transcriptions</CardTitle>
        <CardAction className="self-center">
          <Link
            href="/library"
            className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            View library
            <ArrowRight className="h-3 w-3" />
          </Link>
        </CardAction>
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
        ) : transcribed.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="Nothing transcribed yet"
            description="Upload media and transcribe it from the Library to populate your archive."
          />
        ) : (
          <Table className="table-fixed">
            <TableHeader>
              <TableRow className="bg-muted/40 hover:bg-muted/40">
                <TableHead className="w-[38%] text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  File
                </TableHead>
                <TableHead className="w-[16%] text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Duration
                </TableHead>
                <TableHead className="w-[20%] text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Speakers
                </TableHead>
                <TableHead className="w-[26%] text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Uploaded
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {transcribed.map((item) => (
                <TableRow key={item.key} className="table-row-hover">
                  <TableCell className="font-medium">
                    <Link
                      href={`/library/${encodeURIComponent(item.key)}`}
                      className="truncate hover:underline block"
                    >
                      {item.filename}
                    </Link>
                  </TableCell>
                  <TableCell className="text-muted-foreground whitespace-nowrap">
                    {formatDuration(item.duration)}
                  </TableCell>
                  <TableCell className="whitespace-nowrap">
                    {item.diarized ? (
                      <Badge variant="outline" className="gap-1">
                        <Users className="h-3 w-3" />
                        {item.speakers ?? 0}
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="gap-1">
                        <Mic className="h-3 w-3" />
                        transcribe-only
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground whitespace-nowrap">
                    {formatDate(item.uploaded_at)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
