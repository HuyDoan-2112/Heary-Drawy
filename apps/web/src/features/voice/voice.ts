import { useEffect, useRef, useState } from 'react';
import type { RelayListener } from '../rooms/useRoomConnection';

let microphone: MediaStream | null = null;

/** Ask for the microphone once, from the "Turn on mic" tap. Returns false if it is unavailable. */
export async function requestMicrophone(): Promise<boolean> {
  if (microphone) return true;
  if (!navigator.mediaDevices?.getUserMedia) return false;
  try {
    microphone = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
    return true;
  } catch {
    return false;
  }
}

interface VoiceOptions {
  /** Connect while paired and the teammate is online. */
  active: boolean;
  /** Exactly one side is polite so simultaneous offers resolve (perfect negotiation). */
  polite: boolean;
  send: (type: string, payload: Record<string, unknown>) => void;
  onRelay: (listener: RelayListener) => () => void;
  /** Receives each held clip after release, for transcription. Partner audio never waits for it. */
  onClip?: (clip: Blob) => void;
}

const MIN_CLIP_MS = 400; // Shorter holds are taps, not speech.

/** Records one hold of the same mic stream (Safari: audio/mp4, Chrome: audio/webm). */
function startClip(onClip: (clip: Blob) => void): (() => void) | null {
  if (!microphone || typeof MediaRecorder === 'undefined') return null;
  const recorder = new MediaRecorder(microphone);
  const chunks: Blob[] = [];
  const startedAt = Date.now();
  recorder.ondataavailable = (event) => chunks.push(event.data);
  recorder.onstop = () => {
    if (Date.now() - startedAt >= MIN_CLIP_MS) onClip(new Blob(chunks, { type: recorder.mimeType }));
  };
  recorder.start();
  return () => recorder.stop();
}

/**
 * Live push-to-talk audio straight between the two devices (WebRTC), with the room socket only
 * carrying connection setup. The microphone track stays muted except while the child holds the
 * talk button, so nothing is sent otherwise. Demo scope: no TURN relay, so both devices need a
 * direct network path (for example the same Wi-Fi).
 */
export function useVoice({ active, polite, send, onRelay, onClip }: VoiceOptions) {
  const [teammateTalking, setTeammateTalking] = useState(false);
  const [holding, setHolding] = useState(false);
  const peerRef = useRef<RTCPeerConnection | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const stopClip = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!active || typeof RTCPeerConnection === 'undefined') return undefined;
    let makingOffer = false;
    let ignoreOffer = false;

    const peer = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });
    peerRef.current = peer;
    const track = microphone?.getAudioTracks()[0];
    if (track && microphone) {
      track.enabled = false;
      peer.addTrack(track, microphone);
    } else {
      peer.addTransceiver('audio', { direction: 'recvonly' });
    }
    peer.ontrack = ({ streams }) => {
      if (!audioRef.current) {
        audioRef.current = new Audio();
        audioRef.current.autoplay = true;
      }
      audioRef.current.srcObject = streams[0];
      void audioRef.current.play().catch(() => undefined);
    };
    peer.onicecandidate = ({ candidate }) => {
      if (candidate) send('voice.signal', { candidate: candidate.toJSON() });
    };
    peer.onnegotiationneeded = async () => {
      try {
        makingOffer = true;
        await peer.setLocalDescription();
        send('voice.signal', { description: peer.localDescription?.toJSON() });
      } finally {
        makingOffer = false;
      }
    };

    const unsubscribe = onRelay(async (type, payload) => {
      if (type === 'voice.talking') {
        setTeammateTalking(payload.talking === true);
        return;
      }
      const description = payload.description as RTCSessionDescriptionInit | undefined;
      const candidate = payload.candidate as RTCIceCandidateInit | undefined;
      try {
        if (description) {
          const collision = description.type === 'offer' && (makingOffer || peer.signalingState !== 'stable');
          ignoreOffer = !polite && collision;
          if (ignoreOffer) return;
          await peer.setRemoteDescription(description);
          if (description.type === 'offer') {
            await peer.setLocalDescription();
            send('voice.signal', { description: peer.localDescription?.toJSON() });
          }
        } else if (candidate) {
          await peer.addIceCandidate(candidate).catch((error) => {
            if (!ignoreOffer) throw error;
          });
        }
      } catch {
        // A failed negotiation step is retried by the next offer; voice is best effort in the demo.
      }
    });

    // The polite side asks the other to (re)start negotiation when it joins late.
    if (polite) send('voice.signal', { hello: true });

    return () => {
      unsubscribe();
      peer.close();
      peerRef.current = null;
      setTeammateTalking(false);
    };
  }, [active, polite, send, onRelay]);

  // An impolite peer that hears "hello" makes sure a late joiner gets an offer: it resends one that
  // went out before the teammate was listening, or restarts negotiation if it was already connected.
  useEffect(() => {
    if (!active) return undefined;
    return onRelay((type, payload) => {
      const peer = peerRef.current;
      if (type !== 'voice.signal' || !payload.hello || polite || !peer) return;
      if (peer.signalingState === 'have-local-offer' && peer.localDescription) {
        send('voice.signal', { description: peer.localDescription.toJSON() });
      } else {
        peer.restartIce();
      }
    });
  }, [active, polite, send, onRelay]);

  const setTalking = (talking: boolean) => {
    const track = microphone?.getAudioTracks()[0];
    if (track) track.enabled = talking;
    stopClip.current?.();
    stopClip.current = talking && onClip ? startClip(onClip) : null;
    setHolding(talking);
    send('voice.talking', { talking });
  };

  return {
    teammateTalking,
    holding,
    startTalking: () => setTalking(true),
    stopTalking: () => setTalking(false),
  };
}
