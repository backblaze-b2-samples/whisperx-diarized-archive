import Link from "next/link";
import { Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MediaLibrary } from "@/components/library/media-library";

export default function LibraryPage() {
  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="page-title">Library</h1>
          <p className="text-sm text-muted-foreground mt-1.5">
            Source media on B2 (the <code className="font-mono text-xs">media/</code> prefix).
            Transcribe a file to fan out speaker-labeled transcripts, segments, and embeddings.
          </p>
        </div>
        <Button asChild size="sm" className="h-8">
          <Link href="/upload">
            <Upload className="h-3.5 w-3.5" />
            Add media
          </Link>
        </Button>
      </div>
      <div className="animate-fade-in-up stagger-2">
        <MediaLibrary />
      </div>
    </div>
  );
}
