"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Search as SearchIcon, SearchX } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { useArchiveSearch } from "@/lib/queries";
import { formatTimestamp } from "@/lib/archive-format";
import type { SearchHit, SearchMode } from "@whisperx-diarized-archive/shared";

export function SearchPanel() {
  const [draft, setDraft] = useState("");
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<SearchMode>("keyword");

  const enabled = query.trim().length > 0;
  const { data: hits = [], isLoading, error, refetch } = useArchiveSearch(
    query,
    mode,
    30,
    enabled,
  );

  const grouped = useMemo(() => {
    const map = new Map<string, SearchHit[]>();
    for (const h of hits) {
      const list = map.get(h.key) ?? [];
      list.push(h);
      map.set(h.key, list);
    }
    return [...map.entries()];
  }, [hits]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setQuery(draft);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="p-5 space-y-4">
          <form onSubmit={submit} className="flex gap-2">
            <div className="relative flex-1">
              <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Search transcripts…"
                className="pl-9"
              />
            </div>
            <Button type="submit" disabled={!draft.trim()}>
              Search
            </Button>
          </form>
          <Tabs value={mode} onValueChange={(v) => setMode(v as SearchMode)}>
            <TabsList>
              <TabsTrigger value="keyword">Keyword</TabsTrigger>
              <TabsTrigger value="semantic">Semantic</TabsTrigger>
            </TabsList>
          </Tabs>
          <p className="text-xs text-muted-foreground">
            {mode === "keyword"
              ? "Exact case-insensitive substring match over every transcript segment."
              : "Ranks segments by meaning using sentence-transformer embeddings (cosine similarity)."}
          </p>
        </CardContent>
      </Card>

      {!enabled ? null : isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : error ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : grouped.length === 0 ? (
        <EmptyState
          icon={SearchX}
          title="No matches"
          description="Try a different query or switch between keyword and semantic search."
        />
      ) : (
        <div className="space-y-4">
          {grouped.map(([key, fileHits]) => {
            const filename = key.split("/").pop() ?? key;
            return (
              <Card key={key}>
                <CardHeader className="border-b border-border py-3 px-5 flex flex-row items-center justify-between space-y-0">
                  <CardTitle className="card-title">{filename}</CardTitle>
                  <Link
                    href={`/library/${encodeURIComponent(key)}`}
                    className="text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Open transcript
                  </Link>
                </CardHeader>
                <CardContent className="p-0 divide-y divide-border">
                  {fileHits.map((h) => (
                    <div key={`${h.segment_index}`} className="flex gap-3 px-5 py-3 text-sm">
                      <span className="shrink-0 font-mono text-xs text-muted-foreground tabular-nums pt-0.5 w-12">
                        {formatTimestamp(h.start)}
                      </span>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          {h.speaker && (
                            <span className="text-xs font-semibold text-[var(--primary)]">
                              {h.speaker}
                            </span>
                          )}
                          {mode === "semantic" && (
                            <Badge variant="outline" className="text-[10px]">
                              {h.score.toFixed(3)}
                            </Badge>
                          )}
                        </div>
                        <p>{h.text}</p>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
