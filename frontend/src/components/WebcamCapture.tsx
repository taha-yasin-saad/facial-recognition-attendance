import React, { useRef, useEffect, useImperativeHandle } from "react";

export interface WebcamCaptureHandle {
  capture: () => Promise<Blob>;
}

interface WebcamCaptureProps {
  onCapture?: (blob: Blob) => void;
}

const WebcamCapture = React.forwardRef<WebcamCaptureHandle, WebcamCaptureProps>(
  ({ onCapture }, ref) => {
    const videoRef = useRef<HTMLVideoElement>(null);

    useEffect(() => {
      navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      });
    }, []);

    const doCapture = () => {
      return new Promise<Blob>((resolve) => {
        const video = videoRef.current;
        if (!video) return;
        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          canvas.toBlob((blob) => {
            if (blob) {
              if (onCapture) onCapture(blob);
              resolve(blob);
            }
          }, "image/jpeg");
        }
      });
    };

    useImperativeHandle(ref, () => ({ capture: doCapture }));

    return (
      <div>
        <video ref={videoRef} autoPlay playsInline />
        <button
          onClick={() => {
            doCapture().catch(() => {});
          }}
        >
          Capture
        </button>
      </div>
    );
  }
);

export default WebcamCapture;
