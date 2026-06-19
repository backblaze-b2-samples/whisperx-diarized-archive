"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ApiError,
  deleteFile,
  getArchiveItems,
  getArchiveStats,
  getFiles,
  getFileStats,
  getJobs,
  getPreviewUrl,
  getTranscript,
  getUploadActivity,
  searchArchive,
  startTranscription,
} from "@/lib/api-client";
import type {
  ArchiveItem,
  ArchiveStats,
  FileMetadata,
  SearchHit,
  SearchMode,
  Transcript,
  TranscriptionJob,
} from "@whisperx-diarized-archive/shared";

// Single source of truth for query keys. Keep these tightly scoped so that
// invalidating "files" doesn't blow away unrelated caches, and so an IDE
// "find usages" of `qk.files` reveals every consumer.
export const qk = {
  all: ["b2"] as const,
  files: (prefix?: string, limit?: number) =>
    [...qk.all, "files", prefix ?? "", limit ?? 100] as const,
  stats: () => [...qk.all, "stats"] as const,
  uploadActivity: (days: number) =>
    [...qk.all, "stats", "activity", days] as const,
  preview: (key: string) => [...qk.all, "preview", key] as const,
  archiveItems: () => [...qk.all, "archive", "items"] as const,
  archiveStats: () => [...qk.all, "archive", "stats"] as const,
  transcript: (key: string) => [...qk.all, "archive", "transcript", key] as const,
  jobs: () => [...qk.all, "archive", "jobs"] as const,
  search: (q: string, mode: SearchMode, k: number) =>
    [...qk.all, "archive", "search", mode, q, k] as const,
};

export function useFiles(prefix = "", limit = 100) {
  return useQuery<FileMetadata[], ApiError>({
    queryKey: qk.files(prefix, limit),
    queryFn: () => getFiles(prefix, limit),
  });
}

export function useFileStats() {
  return useQuery({
    queryKey: qk.stats(),
    queryFn: getFileStats,
  });
}

export function useUploadActivity(days = 7) {
  return useQuery({
    queryKey: qk.uploadActivity(days),
    queryFn: () => getUploadActivity(days),
  });
}

// Presigned preview URL — only fetched when `enabled` is true (e.g., when
// the dialog opens for a specific file). Kept short-lived (60s) because
// the URL itself has a presigned expiry and is cheap to regenerate.
export function usePreviewUrl(key: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: qk.preview(key ?? ""),
    queryFn: () => getPreviewUrl(key as string),
    enabled: enabled && !!key,
    staleTime: 60_000,
  });
}

export function useDeleteFile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fileKey: string) => deleteFile(fileKey),
    // After delete, blow away every cached file list + stats. Cheap and
    // correct — the dashboard re-fetches lazily as components remount.
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.all });
    },
  });
}

// --- Transcript archive ---

export function useArchiveItems() {
  return useQuery<ArchiveItem[], ApiError>({
    queryKey: qk.archiveItems(),
    queryFn: getArchiveItems,
  });
}

export function useArchiveStats() {
  return useQuery<ArchiveStats, ApiError>({
    queryKey: qk.archiveStats(),
    queryFn: getArchiveStats,
  });
}

export function useTranscript(key: string | undefined, enabled = true) {
  return useQuery<Transcript, ApiError>({
    queryKey: qk.transcript(key ?? ""),
    queryFn: () => getTranscript(key as string),
    enabled: enabled && !!key,
  });
}

// Polls while any job is still running so the Library progress badges and
// the dashboard refresh live as the background pipeline advances.
export function useJobs(poll = false) {
  return useQuery<TranscriptionJob[], ApiError>({
    queryKey: qk.jobs(),
    queryFn: getJobs,
    refetchInterval: poll ? 2000 : false,
  });
}

export function useStartTranscription() {
  const qc = useQueryClient();
  return useMutation<TranscriptionJob, ApiError, string>({
    mutationFn: (key: string) => startTranscription(key),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.jobs() });
      qc.invalidateQueries({ queryKey: qk.archiveItems() });
    },
  });
}

// Search only fires when explicitly enabled (after the user submits a query)
// to avoid loading every embedding on each keystroke.
export function useArchiveSearch(
  q: string,
  mode: SearchMode,
  k: number,
  enabled: boolean,
) {
  return useQuery<SearchHit[], ApiError>({
    queryKey: qk.search(q, mode, k),
    queryFn: () => searchArchive(q, mode, k),
    enabled: enabled && q.trim().length > 0,
  });
}
