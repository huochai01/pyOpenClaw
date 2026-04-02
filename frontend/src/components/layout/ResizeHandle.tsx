"use client";

type ResizeHandleProps = {
  onResize: (next: number) => void;
  side?: "left" | "right";
};

export function ResizeHandle({ onResize, side = "left" }: ResizeHandleProps) {
  return (
    <div
      className="group relative hidden w-[4px] cursor-col-resize bg-slate-200/90 xl:block"
      onMouseDown={(event) => {
        const startX = event.clientX;
        const target =
          side === "left"
            ? ((event.currentTarget.previousElementSibling as HTMLElement | null) ?? null)
            : ((event.currentTarget.nextElementSibling as HTMLElement | null) ?? null);
        const startWidth = target?.offsetWidth ?? 0;
        const move = (moveEvent: MouseEvent) => {
          const delta = moveEvent.clientX - startX;
          onResize(side === "left" ? startWidth + delta : startWidth - delta);
        };
        const up = () => {
          window.removeEventListener("mousemove", move);
          window.removeEventListener("mouseup", up);
        };
        window.addEventListener("mousemove", move);
        window.addEventListener("mouseup", up);
      }}
    >
      <div className="absolute inset-y-0 left-0 right-0 bg-transparent transition group-hover:bg-[var(--accent)]/40" />
    </div>
  );
}
