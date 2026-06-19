export type FileStatus = "uploading" | "complete" | "error";

export interface FileMetadata {
  key: string;
  filename: string;
  folder: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
}

export interface FileMetadataDetail {
  filename: string;
  size_bytes: number;
  size_human: string;
  mime_type: string;
  extension: string;
  md5: string;
  sha256: string;
  uploaded_at: string;
  // Image-specific
  image_width: number | null;
  image_height: number | null;
  exif: Record<string, string> | null;
  // PDF-specific
  pdf_pages: number | null;
  pdf_author: string | null;
  pdf_title: string | null;
  // Audio/Video
  duration_seconds: number | null;
  codec: string | null;
  bitrate: number | null;
}

export interface FileUploadResponse {
  key: string;
  filename: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
  metadata: FileMetadataDetail | null;
}

export interface DailyUploadCount {
  date: string;
  uploads: number;
}

export interface UploadStats {
  total_files: number;
  total_size_bytes: number;
  total_size_human: string;
  uploads_today: number;
  total_downloads: number;
}

// --- Transcript archive ---

export type JobStatus =
  | "queued"
  | "transcribing"
  | "diarizing"
  | "embedding"
  | "writing"
  | "done"
  | "error";

export type SearchMode = "keyword" | "semantic";

export interface Segment {
  start: number;
  end: number;
  text: string;
  speaker: string | null;
}

export interface Transcript {
  key: string;
  language: string | null;
  duration: number | null;
  diarized: boolean;
  speakers: string[];
  segments: Segment[];
}

export interface SearchHit {
  key: string;
  segment_index: number;
  speaker: string | null;
  start: number;
  end: number;
  text: string;
  score: number;
}

export interface TranscriptionJob {
  id: string;
  key: string;
  status: JobStatus;
  progress: number;
  message: string | null;
  error: string | null;
  diarized: boolean;
  created_at: string;
  updated_at: string;
}

export interface ArchiveItem {
  key: string;
  filename: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
  transcribed: boolean;
  diarized: boolean;
  duration: number | null;
  speakers: number | null;
}

export interface ArchiveStats {
  media_files: number;
  transcribed_files: number;
  speakers_detected: number;
  segments_indexed: number;
  hours_processed: number;
  storage_bytes: number;
  storage_human: string;
}
