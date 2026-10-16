export default function Loading() {
  return (
    <div className="flex flex-1 items-center justify-center py-16">
      <span
        role="status"
        aria-label="Loading"
        className="border-muted-foreground/30 border-t-foreground size-6 animate-spin rounded-full border-2"
      />
    </div>
  );
}
