import { SearchPanel } from "@/components/search/search-panel";

export default function SearchPage() {
  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5">
        <h1 className="page-title">Search</h1>
        <p className="text-sm text-muted-foreground mt-1.5">
          Search the whole archive by exact keyword or semantic meaning. Results group by
          source file and link to the speaker-attributed transcript.
        </p>
      </div>
      <div className="animate-fade-in-up stagger-2">
        <SearchPanel />
      </div>
    </div>
  );
}
