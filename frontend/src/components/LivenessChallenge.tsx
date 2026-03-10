import React, { useState, useEffect } from "react";

interface LivenessChallengeProps {
  type: string;
  onComplete: (passed: boolean) => void;
}

const LivenessChallenge: React.FC<LivenessChallengeProps> = ({
  type,
  onComplete,
}) => {
  const [status, setStatus] = useState("");

  useEffect(() => {
    // placeholder: real logic handled by server
  }, [type]);

  return (
    <div>
      <p>Challenge: {type}</p>
      <p>Status: {status}</p>
      <button onClick={() => onComplete(true)}>Mark Passed</button>
      <button onClick={() => onComplete(false)}>Fail</button>
    </div>
  );
};

export default LivenessChallenge;
