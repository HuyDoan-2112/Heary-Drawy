import { useEffect, useState } from 'react';
import { neutralResult } from '../../app/fixtures';
import { CheckingScreen, ResultScreen } from '../../app/screens/Finish';
import { MicScreen, ModeScreen, TeamScreen } from '../../app/screens/JoinFlow';
import { DrawerPlayView, SpeakerPlayView } from '../../app/screens/Play';
import { ArrowIcon, HomeIcon } from '../../app/ui/icons';
import { SecretModel } from '../../app/ui/model';
import type { RoleFilteredSnapshot } from '../../generated/contracts';
import { fetchSecretFile, leaveRoom, uploadClip, type GuestSession } from '../rooms/api';
import { useRoomConnection, type RoomSnapshot } from '../rooms/useRoomConnection';
import { hasMicrophone, requestMicrophone, useVoice } from '../voice/voice';
import { toScreenStroke, toServerStroke } from './strokes';

type Step = 'mic' | 'mode' | 'game';

function teamStatus(snapshot: RoomSnapshot | null, connection: string): string {
  if (connection === 'reconnecting') return 'Reconnecting... Please wait.';
  if (!snapshot) return 'Connecting to your room...';
  if ('admission_status' in snapshot) {
    return snapshot.admission_status === 'teammate_left'
      ? 'Your teammate had to go. Tap Done to finish.'
      : `Hi ${snapshot.room.participant.nickname}! Waiting for a teammate...`;
  }
  const name = snapshot.room.teammate?.nickname ?? 'your teammate';
  const away = snapshot.room.teammate?.connection_status !== 'connected' ? ` ${name} is not connected right now.` : '';
  if (snapshot.ready?.self_ready) return `Waiting for ${name} to be ready...${away}`;
  if (snapshot.ready?.teammate_ready) return `${name} is ready!${away}`;
  return `Round ${snapshot.round.round_index} of ${snapshot.round.total_rounds}. You ${snapshot.round.role === 'speaker' ? 'talk' : 'draw'}!${away}`;
}

/** Loads an authorized secret file (picture or 3D model) for this round, if the snapshot grants one. */
function useSecretFile(session: GuestSession, url: string | null | undefined) {
  const [picture, setPicture] = useState<{ url: string; src: string } | null>(null);
  useEffect(() => {
    if (!url) return undefined;
    let cancelled = false;
    let objectUrl: string | null = null;
    fetchSecretFile(session, url)
      .then((src) => {
        objectUrl = src;
        if (cancelled) URL.revokeObjectURL(src);
        else setPicture({ url, src });
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [session, url]);
  return url && picture?.url === url ? picture.src : null;
}

/**
 * The real game for an admitted child. Everything shown comes from the latest server snapshot;
 * the only local steps are the mic and mode screens right after joining.
 */
export function LiveGame({ session, justJoined, onExit }: { session: GuestSession; justJoined: boolean; onExit: () => void }) {
  // The mic prompt only shows reliably on iOS from a tap, so every page load without the mic,
  // including a resumed session after a reload, starts at the mic screen.
  const [step, setStep] = useState<Step>(() => (hasMicrophone() ? 'game' : 'mic'));
  const { snapshot, connection, notice, send, sendRoundCommand, onRelay } = useRoomConnection(session);
  const round = snapshot && 'round' in snapshot ? (snapshot as RoleFilteredSnapshot) : null;
  const teammate = round?.room.teammate ?? null;

  // Voice starts after the mic screen; otherwise it would connect listen-only and the partner
  // could never hear this child.
  const voice = useVoice({
    active: step === 'game' && Boolean(round && teammate?.connection_status === 'connected'),
    polite: Boolean(teammate && session.player_id < teammate.player_id),
    send,
    onRelay,
    onClip: (clip) => {
      if (round) void uploadClip(session, round.round.round_id, clip);
    },
  });
  const access = round?.object_access;
  const pictureSrc = useSecretFile(session, access?.image_url);
  // Only the Speaker spins the model, and only while describing it.
  const speakerDescribing = round?.round.role === 'speaker' && round.round.phase === 'collaborating';
  const modelSrc = useSecretFile(session, speakerDescribing ? access?.model_url : null);

  useEffect(() => {
    if (connection === 'ended') onExit();
  }, [connection, onExit]);

  const leave = () => {
    void leaveRoom(session).finally(onExit);
  };

  if (step === 'mic') {
    // A resumed session already chose its mode, so it goes straight back to the game.
    return <MicScreen onContinue={() => void requestMicrophone().finally(() => setStep(justJoined ? 'mode' : 'game'))} />;
  }
  if (step === 'mode') return <ModeScreen onContinue={() => setStep('game')} />;

  const self = snapshot?.room.participant;
  const mate = teammate ? { name: teammate.nickname, avatarId: teammate.avatar_id } : null;
  const label = access?.display_name ?? 'Picture';
  const picture = pictureSrc ? <img className="secret-picture" src={pictureSrc} alt={label} /> : null;
  const strokes = round ? (round.drawing.strokes ?? []).map(toScreenStroke) : [];
  const talk = { holding: voice.holding, start: voice.startTalking, stop: voice.stopTalking };
  const status = (
    <div className="room-status" aria-live="polite">
      <p role="status">{teamStatus(snapshot, connection)}</p>
      {notice ? <p role="alert">{notice}</p> : null}
    </div>
  );

  if (!round || !mate || round.round.phase === 'role_intro' || round.round.phase === 'finished') {
    const left = snapshot && 'admission_status' in snapshot && snapshot.admission_status === 'teammate_left';
    const canStart = round?.round.phase === 'role_intro' && !round.ready?.self_ready && connection === 'live';
    let action = null;
    if (left) {
      action = (
        <button type="button" className="big-button" onClick={leave}>
          <HomeIcon />
          Done
        </button>
      );
    } else if (canStart) {
      action = (
        <button type="button" className="big-button" onClick={() => sendRoundCommand('round.intro.seen')}>
          <ArrowIcon strokeWidth={2.6} />
          Let&apos;s play!
        </button>
      );
    }
    return (
      <TeamScreen
        self={self ? { name: self.nickname, avatarId: self.avatar_id } : null}
        teammate={left ? null : mate}
        status={status}
        action={action}
      />
    );
  }

  const { phase, role, round_id: roundId } = round.round;
  if (phase === 'collaborating' && role === 'speaker') {
    return (
      <SpeakerPlayView
        selfAvatarId={self!.avatar_id}
        teammate={mate}
        picture={<SecretModel modelSrc={modelSrc} pictureSrc={pictureSrc} label={label} />}
        strokes={strokes}
        teammateTalking={voice.teammateTalking}
        talk={talk}
      />
    );
  }
  if (phase === 'collaborating') {
    return (
      <DrawerPlayView
        selfAvatarId={self!.avatar_id}
        teammate={mate}
        strokes={strokes}
        teammateTalking={voice.teammateTalking}
        talk={talk}
        onStroke={(stroke) => send('drawing.add', { stroke: toServerStroke(stroke) }, roundId)}
        onUndo={() => send('drawing.undo', {}, roundId)}
        onClear={() => send('drawing.clear', {}, roundId)}
        onDone={() => sendRoundCommand('round.submit')}
      />
    );
  }
  if (phase !== 'exploring') return <CheckingScreen live drawing={strokes} />;

  const lines = round.feedback?.role_feedback.lines ?? [neutralResult.praise, neutralResult.question];
  const canPlayAgain = round.round.permissions?.includes('play_again') && !round.ready?.self_ready;
  let resultStatus: string | undefined;
  if (round.ready?.self_ready) resultStatus = `Waiting for ${mate.name} to be ready...`;
  else if (round.ready?.teammate_ready) resultStatus = `${mate.name} wants to play again!`;
  return (
    <ResultScreen
      result={{ stars: (round.feedback?.shared_result.stars as 1 | 2 | 3 | undefined) ?? null, praise: lines[0], question: lines[1] ?? '' }}
      picture={picture}
      drawing={strokes}
      drawingLabel={role === 'drawer' ? 'Your drawing' : `${mate.name}'s drawing`}
      actions={{
        onPlayAgain: canPlayAgain ? () => sendRoundCommand('round.play_again') : undefined,
        onDone: leave,
        status: resultStatus,
      }}
    />
  );
}
