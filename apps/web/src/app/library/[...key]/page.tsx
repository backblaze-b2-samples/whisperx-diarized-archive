import { TranscriptViewer } from "@/components/library/transcript-viewer";

export default async function TranscriptPage({
  params,
}: {
  params: Promise<{ key: string[] }>;
}) {
  const { key } = await params;
  // The media key can contain slashes (e.g. "media/ep1.mp3"); a catch-all
  // segment captures every part, which we re-join into the original key.
  const mediaKey = key.map((p) => decodeURIComponent(p)).join("/");
  return <TranscriptViewer mediaKey={mediaKey} />;
}
