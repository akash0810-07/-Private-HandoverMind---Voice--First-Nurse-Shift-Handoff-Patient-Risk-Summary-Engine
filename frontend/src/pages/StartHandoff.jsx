import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client.js";

const STAGE_LABELS = {
  QUEUED: "Queued",
  TRANSCRIBING: "Transcribing audio",
  ANALYSING: "Analysing handoff",
  RISK_DETECTION: "Detecting risk indicators",
  COMPLETED: "Summary ready",
  FAILED: "Processing failed",
};

export default function StartHandoff() {
  const navigate = useNavigate();
  const [micStatus, setMicStatus] = useState("idle"); // idle | requesting | granted | denied
  const [recording, setRecording] = useState(false);
  const [paused, setPaused] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [stage, setStage] = useState(null);
  const [error, setError] = useState(null);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const streamRef = useRef(null);

  async function startRecording() {
    setError(null);
    setMicStatus("requesting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      setMicStatus("granted");

      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.onstop = handleStopped;
      recorder.start();
      mediaRecorderRef.current = recorder;

      setRecording(true);
      setPaused(false);
      setSeconds(0);
      timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
    } catch (err) {
      setMicStatus("denied");
      setError("Microphone permission was denied or unavailable.");
    }
  }

  function pauseRecording() {
    mediaRecorderRef.current?.pause();
    setPaused(true);
    clearInterval(timerRef.current);
  }

  function resumeRecording() {
    mediaRecorderRef.current?.resume();
    setPaused(false);
    timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    clearInterval(timerRef.current);
    setRecording(false);
  }

  function cancelRecording() {
    mediaRecorderRef.current?.stop();
    clearInterval(timerRef.current);
    streamRef.current?.getTracks().forEach((t) => t.stop());
    setRecording(false);
    setSeconds(0);
    chunksRef.current = [];
  }

  async function handleStopped() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    const blob = new Blob(chunksRef.current, { type: "audio/webm" });
    await uploadAndProcess(blob);
  }

  async function uploadAndProcess(blob) {
    setProcessing(true);
    setStage("QUEUED");
    setError(null);
    try {
      // The backend runs the pipeline synchronously in v1 and returns the
      // final status directly; we still show each stage label for a
      // realistic processing experience and poll the job as a fallback.
      setStage("TRANSCRIBING");
      const result = await api.uploadHandoff(blob, "handoff.webm");
      setStage(result.status);
      if (result.status === "COMPLETED") {
        navigate(`/summary/${result.recording_id}`);
      } else if (result.job_id) {
        await pollJob(result.job_id, result.recording_id);
      }
    } catch (err) {
      setStage("FAILED");
      setError(err.payload?.message || "AI analysis could not be completed. Please try again.");
    } finally {
      setProcessing(false);
    }
  }

  async function pollJob(jobId, recordingId) {
    for (let i = 0; i < 10; i++) {
      await new Promise((r) => setTimeout(r, 1000));
      const job = await api.getJob(jobId);
      setStage(job.status);
      if (job.status === "COMPLETED") {
        navigate(`/summary/${recordingId}`);
        return;
      }
      if (job.status === "FAILED") {
        setError(job.error_message || "Processing failed.");
        return;
      }
    }
  }

  return (
    <div className="page">
      <h1>Start Handoff</h1>
      <p className="demo-notice">Academic demonstration system — uses synthetic patient data only.</p>

      {!processing && (
        <div className="recorder-card">
          <p className="mic-status">
            Microphone: <strong>{micStatus === "idle" ? "not requested" : micStatus}</strong>
          </p>
          <div className="timer">{String(Math.floor(seconds / 60)).padStart(2, "0")}:{String(seconds % 60).padStart(2, "0")}</div>

          <div className="recorder-controls">
            {!recording && (
              <button className="primary" onClick={startRecording}>Start Recording</button>
            )}
            {recording && !paused && (
              <>
                <button onClick={pauseRecording}>Pause</button>
                <button className="primary" onClick={stopRecording}>Stop</button>
                <button className="danger" onClick={cancelRecording}>Cancel</button>
              </>
            )}
            {recording && paused && (
              <>
                <button onClick={resumeRecording}>Resume</button>
                <button className="primary" onClick={stopRecording}>Stop</button>
                <button className="danger" onClick={cancelRecording}>Cancel</button>
              </>
            )}
          </div>
          {error && <div className="error-banner">{error}</div>}
        </div>
      )}

      {processing && (
        <div className="processing-card">
          <h2>Processing Handoff…</h2>
          <ol className="stage-list">
            {["QUEUED", "TRANSCRIBING", "ANALYSING", "RISK_DETECTION", "COMPLETED"].map((s) => (
              <li key={s} className={stage === s ? "active" : ""}>{STAGE_LABELS[s]}</li>
            ))}
          </ol>
          {error && <div className="error-banner">{error}</div>}
        </div>
      )}
    </div>
  );
}
