"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { usePreviewUrl } from "@/lib/queries";
import type { FileMetadata } from "@whisperx-diarized-archive/shared";

interface FilePreviewProps {
  file: FileMetadata | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function FilePreview({ file, open, onOpenChange }: FilePreviewProps) {
  // Fetch a presigned preview URL only while the dialog is open. Falls
  // back to the file's stored URL if the API call fails (e.g. the
  // `/preview` endpoint is unreachable but we still have a static URL).
  const { data, isLoading } = usePreviewUrl(file?.key, open && !!file);
  const previewUrl = data?.url ?? file?.url ?? null;

  if (!file) return null;

  // This archive ingests audio/video media, so the bucket-explorer preview
  // plays the media inline rather than rendering images or PDFs.
  const isAudio = file.content_type.startsWith("audio/");
  const isVideo = file.content_type.startsWith("video/");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="truncate">{file.filename}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="flex items-center justify-center rounded-lg border bg-muted/30 min-h-[200px]">
            {isLoading ? (
              <Skeleton className="h-48 w-full" />
            ) : isAudio && previewUrl ? (
              // Presigned URLs carry their own short-lived expiry; the
              // browser streams directly from B2 for the duration.
              <audio controls src={previewUrl} className="w-full px-4">
                Your browser does not support the audio element.
              </audio>
            ) : isVideo && previewUrl ? (
              <video
                controls
                src={previewUrl}
                className="w-full h-[400px] rounded bg-black"
              >
                Your browser does not support the video element.
              </video>
            ) : (
              <div className="text-center text-muted-foreground p-8">
                <p className="text-sm">Preview not available</p>
                <p className="text-xs mt-1">{file.content_type}</p>
              </div>
            )}
          </div>
          <div className="space-y-4">
            <div className="text-sm space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Size</span>
                <span>{file.size_human}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Type</span>
                <span>{file.content_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Uploaded</span>
                <span>
                  {new Date(file.uploaded_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Key</span>
                <span className="font-mono text-xs truncate max-w-[200px]">
                  {file.key}
                </span>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
