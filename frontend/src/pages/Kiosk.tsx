import React, { useState, useEffect, useRef } from "react";
import api from "../api";
import WebcamCapture, { WebcamCaptureHandle } from "../components/WebcamCapture";
import LivenessChallengeCard from "../components/LivenessChallengeCard";
import MotionButton from "../components/MotionButton";
import { CheckCircle, XCircle } from "lucide-react";
import { motion } from "framer-motion";
import { useToast } from "../components/ToastProvider";
import Skeleton from "../components/Skeleton";

interface ChallengeData {
  challenge_id: string;
  challenge_type: string;
}

const Kiosk: React.FC = () => {
  const [challenge, setChallenge] = useState<ChallengeData | null>(null);
  const [livenessPassed, setLivenessPassed] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [statusSuccess, setStatusSuccess] = useState<boolean | null>(null);
  const [loadingChallenge, setLoadingChallenge] = useState(false);

  const webcamRef = useRef<WebcamCaptureHandle>(null);

  const { showToast } = useToast();
  const getChallenge = async () => {
    setLoadingChallenge(true);
    try {
      const resp = await api.get("/kiosk/challenge", {
        headers: { "device-id": "kiosk1" },
      });
      setChallenge(resp.data);
      setLivenessPassed(false);
      setMessage(null);
      setStatusSuccess(null);
      showToast("Challenge ready", 'info');
    } catch (err) {
      setMessage("Failed to load challenge");
      showToast("Failed to load challenge", 'error');
    } finally {
      setLoadingChallenge(false);
    }
  };

  useEffect(() => {
    getChallenge();
  }, []);

  const captureFrame = async (): Promise<Blob | null> => {
    if (webcamRef.current) {
      try {
        return await webcamRef.current.capture();
      } catch {
        return null;
      }
    }
    return null;
  };

  const handleCapture = async () => {
    setMessage(null);
    if (!challenge) return;

    if (!livenessPassed) {
      try {
        const frames: Blob[] = [];
        for (let i = 0; i < 5; i++) {
          const b = await captureFrame();
          if (b) frames.push(b);
          await new Promise((r) => setTimeout(r, 200));
        }
        const form = new FormData();
        frames.forEach((f) => form.append("files", f));
        const res = await api.post("/kiosk/liveness", form, {
          headers: {
            "challenge-id": challenge.challenge_id,
            "device-id": "kiosk1",
          },
        });
        setLivenessPassed(res.data.passed);
        if (!res.data.passed) {
          setMessage(res.data.reason);
          showToast(`Liveness failed: ${res.data.reason}`, 'error');
        } else {
          showToast('Liveness passed', 'success');
        }
      } catch (err: any) {
        let detail = err.response?.data?.detail;
        if (typeof detail === 'object') {
          detail = JSON.stringify(detail);
        }
        const msg = detail || "Liveness check failed";
        setMessage(msg);
        showToast(msg, 'error');
      }
    } else {
      try {
        const blob = await captureFrame();
        if (!blob) return;
        const form = new FormData();
        form.append("frame", blob);
        const res = await api.post("/kiosk/recognize", form, {
          headers: { type: "IN", "device-id": "kiosk1" },
        });
        const info = res.data;
        setMessage(info.message || "Recorded");
        setStatusSuccess(true);
        showToast('Recognition success', 'success');
        setTimeout(() => {
          getChallenge();
        }, 2000);
      } catch (err: any) {
        let detail = err.response?.data?.detail;
        if (typeof detail === 'object') {
          detail = JSON.stringify(detail);
        }
        const msg = detail || "Recognition failed";
        setMessage(msg);
        setStatusSuccess(false);
        showToast(msg, 'error');
      }
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-full">
      <div className="w-full max-w-lg">
        {loadingChallenge ? (
          <Skeleton className="h-20" />
        ) : challenge ? (
          <LivenessChallengeCard
            type={challenge.challenge_type}
            passed={livenessPassed}
            reason={message || undefined}
          />
        ) : null}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
          <WebcamCapture ref={webcamRef} />
        </div>
        <div className="mt-4 flex flex-col items-center gap-4">
          <MotionButton
            className={`w-48 ${livenessPassed ? 'bg-success text-white' : 'bg-accent text-white'}`}
            onClick={handleCapture}
          >
            {livenessPassed ? 'Verify Identity' : 'Perform Liveness'}
          </MotionButton>
          {statusSuccess !== null && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="flex items-center gap-2"
            >
              {statusSuccess ? (
                <CheckCircle className="text-success" />
              ) : (
                <XCircle className="text-error" />
              )}
              <span>{message}</span>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Kiosk;
