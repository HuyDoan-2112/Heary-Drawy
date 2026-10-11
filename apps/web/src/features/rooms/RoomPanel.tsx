import { TeamScreen } from '../../app/screens/JoinFlow';
import { ArrowIcon, SwapIcon } from '../../app/ui/icons';
import type { GuestSession } from './api';
import { useRoomConnection } from './useRoomConnection';

const ROLE_LABEL = { speaker: 'Speaker', drawer: 'Drawer' } as const;

/** Live room state for an admitted guest, shown on the approved "meet your teammate" screen. */
export function RoomPanel({ session }: { session: GuestSession }) {
  const { snapshot, connection, notice, sendRoundCommand } = useRoomConnection(session);

  function statusText(): string {
    if (connection === 'ended') return 'Your room session ended.';
    if (connection === 'reconnecting') return 'Reconnecting... Please wait before continuing.';
    if (!snapshot) return 'Connecting to your room...';
    if ('admission_status' in snapshot) return `Hi ${snapshot.room.participant.nickname}! Waiting for a teammate...`;
    const mate = snapshot.room.teammate;
    const name = mate?.nickname ?? 'your teammate';
    const away = mate && mate.connection_status !== 'connected' ? ` ${name} is not connected right now.` : '';
    const ready = snapshot.ready;
    switch (snapshot.round.phase) {
      case 'role_intro':
        if (ready?.self_ready) return `Waiting for ${name} to be ready...${away}`;
        return `Playing as ${snapshot.room.participant.nickname}. You are the ${ROLE_LABEL[snapshot.round.role]}. Teammate: ${name}.${away}${ready?.teammate_ready ? ` ${name} is ready!` : ''}`;
      case 'collaborating':
        return `You and ${name} are both ready. Drawing and talking come in later features.${away}`;
      case 'exploring':
        if (ready?.self_ready) return `Waiting for ${name} to be ready...${away}`;
        return ready?.teammate_ready ? `${name} wants to play again!` : 'Ready for another round?';
      default:
        return `Round step: ${snapshot.round.phase}.${away}`;
    }
  }

  const canAcknowledge = snapshot && 'round' in snapshot && connection === 'live' && !snapshot.ready?.self_ready;
  const phase = snapshot && 'round' in snapshot ? snapshot.round.phase : null;
  const participant = snapshot?.room.participant;
  const teammate = snapshot && 'round' in snapshot ? snapshot.room.teammate : null;

  let action = null;
  if (canAcknowledge && phase === 'role_intro') {
    action = (
      <button type="button" className="big-button" onClick={() => sendRoundCommand('round.intro.seen')}>
        <ArrowIcon strokeWidth={2.6} />
        Let&apos;s play!
      </button>
    );
  } else if (canAcknowledge && phase === 'exploring') {
    action = (
      <button type="button" className="big-button" onClick={() => sendRoundCommand('round.play_again')}>
        <SwapIcon strokeWidth={2.6} />
        Play again
      </button>
    );
  }

  return (
    <TeamScreen
      self={participant ? { name: participant.nickname, avatarId: participant.avatar_id } : null}
      teammate={teammate ? { name: teammate.nickname, avatarId: teammate.avatar_id } : null}
      status={(
        <div className="room-status" aria-live="polite">
          <p role="status">{statusText()}</p>
          {notice ? <p role="alert">{notice}</p> : null}
        </div>
      )}
      action={action}
    />
  );
}
