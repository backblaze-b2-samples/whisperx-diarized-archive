"use client";

import { FileAudio, FileText, Users, ListTree, Clock, HardDrive } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { useArchiveStats } from "@/lib/queries";

export function ArchiveStatsCards() {
  const { data: stats, isLoading, error, refetch } = useArchiveStats();

  // Surface fetch failures inline rather than lying with "0" everywhere when
  // the API is just unreachable.
  if (error) {
    return (
      <Card>
        <CardContent className="p-0">
          <ErrorState error={error} onRetry={() => refetch()} />
        </CardContent>
      </Card>
    );
  }

  const cards = [
    { title: "Files in archive", value: stats?.media_files ?? 0, icon: FileAudio },
    { title: "Files transcribed", value: stats?.transcribed_files ?? 0, icon: FileText },
    { title: "Speakers detected", value: stats?.speakers_detected ?? 0, icon: Users },
    { title: "Segments indexed", value: stats?.segments_indexed ?? 0, icon: ListTree },
    { title: "Hours processed", value: `${stats?.hours_processed ?? 0}h`, icon: Clock },
    { title: "Storage used", value: stats?.storage_human ?? "0 B", icon: HardDrive },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {cards.map((card, i) => (
        <Card
          key={card.title}
          className={`card-hover animate-fade-in-up stagger-${(i % 4) + 1}`}
        >
          <CardHeader className="flex flex-row items-center justify-between pt-4 pb-2 px-4 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground">
              {card.title}
            </CardTitle>
            <div className="stat-icon-wrap">
              <card.icon className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent className="pb-5 px-4">
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <div className="stat-value">{card.value}</div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
