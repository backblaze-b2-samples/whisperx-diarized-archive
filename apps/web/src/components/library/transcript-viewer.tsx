"use client";

import Link from "next/link";
import { ArrowLeft, FileText, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { useTranscript } from "@/lib/queries";
import { formatTimestamp } from "@/lib/archive-format";

// Stable color per speaker label so the same speaker reads the same down
// the transcript. Tailwind tokens keep it theme-aware.
const SPEAKER_CLASSES = [
  "text-[var(--primary)]",
  "text-[var(--success)]",
  "text-[var(--attention)]",
  "text-blue-500",
  "text-purple-500",
  "text-pink-500",
];

function speakerClass(speaker: string | null, speakers: string[]): string {
  if (!speaker) return "text-muted-foreground";
  const idx = speakers.indexOf(speaker);
  return SPEAKER_CLASSES[(idx < 0 ? 0 : idx) % SPEAKER_CLASSES.length];
}

export function TranscriptViewer({ mediaKey }: { mediaKey: string }) {
  const { data: transcript, isLoading, error, refetch } = useTranscript(mediaKey);
  const filename = mediaKey.split("/").pop() ?? mediaKey;

  return (
    <div className="space-y-6">
      <div className="animate-fade-in border-b border-border pb-5">
        <Button asChild variant="ghost" size="sm" className="h-7 -ml-2 mb-2 text-xs">
          <Link href="/library">
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Library
          </Link>
        </Button>
        <h1 className="page-title flex items-center gap-2">
          <FileText className="h-5 w-5 text-muted-foreground" />
          {filename}
        </h1>
        {transcript && (
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <Badge variant="outline">{transcript.segments.length} segments</Badge>
            {transcript.language && <Badge variant="outline">{transcript.language}</Badge>}
            {transcript.diarized ? (
              <Badge variant="outline" className="gap-1">
                <Users className="h-3 w-3" />
                {transcript.speakers.length} speakers
              </Badge>
            ) : (
              <Badge variant="secondary">transcribe-only</Badge>
            )}
          </div>
        )}
      </div>

      <Card>
        <CardHeader className="border-b border-border py-4 px-5">
          <CardTitle className="card-title">Transcript</CardTitle>
        </CardHeader>
        <CardContent className="p-5">
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-6 w-full" />
              ))}
            </div>
          ) : error ? (
            <ErrorState error={error} onRetry={() => refetch()} />
          ) : !transcript || transcript.segments.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="No transcript content"
              description="This file has no transcribed segments yet."
            />
          ) : (
            <div className="space-y-3">
              {transcript.segments.map((seg, i) => (
                <div key={i} className="flex gap-3 text-sm">
                  <span className="shrink-0 font-mono text-xs text-muted-foreground tabular-nums pt-0.5 w-12">
                    {formatTimestamp(seg.start)}
                  </span>
                  <div>
                    {seg.speaker && (
                      <span
                        className={`mr-2 text-xs font-semibold ${speakerClass(
                          seg.speaker,
                          transcript.speakers,
                        )}`}
                      >
                        {seg.speaker}
                      </span>
                    )}
                    <span>{seg.text}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
