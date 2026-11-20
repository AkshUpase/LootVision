import { RefObject } from "react";

interface Props {
  videoRef: RefObject<HTMLVideoElement>;
  status: "idle" | "requesting" | "ready" | "denied" | "unsupported";
}

export function CameraFeed({ videoRef, status }: Props) {
  return (
    <div className="relative w-full h-full overflow-hidden bg-black">
      <video
        ref={videoRef}
        playsInline
        muted
        className="w-full h-full object-cover"
      />
      {status === "ready" && <div className="scanline" style={{ top: 0 }} />}

      {status !== "ready" && (
        <div className="absolute inset-0 flex items-center justify-center bg-void/90 px-8 text-center">
          {status === "requesting" && (
            <p className="text-scan mono text-sm tracking-wide">Requesting camera access…</p>
          )}
          {status === "denied" && (
            <p className="text-loss mono text-sm tracking-wide">
              Camera access denied. Enable it in your browser settings to start scanning.
            </p>
          )}
          {status === "unsupported" && (
            <p className="text-loss mono text-sm tracking-wide">
              This browser doesn't support camera access. Try Chrome or Safari on mobile.
            </p>
          )}
          {status === "idle" && (
            <p className="text-white/50 mono text-sm tracking-wide">Starting camera…</p>
          )}
        </div>
      )}
    </div>
  );
}
