import type { RoleFilteredSnapshot } from '../generated/contracts';

export const avatarIds = ['sky', 'mint', 'grape', 'berry', 'pepper', 'lemon', 'mango', 'plum', 'coco', 'kiwi'] as const;

export type AvatarId = (typeof avatarIds)[number];

export interface CharacterOption {
  id: AvatarId;
  name: string;
  pickedBy?: string;
}

// Order matches the approved character picker (artifact/design/Main.dc.html).
export const characterOptions: CharacterOption[] = [
  { id: 'mango', name: 'Mango' },
  { id: 'kiwi', name: 'Kiwi', pickedBy: 'teammate' },
  { id: 'plum', name: 'Plum' },
  { id: 'pepper', name: 'Pepper' },
  { id: 'berry', name: 'Berry' },
  { id: 'coco', name: 'Coco' },
  { id: 'sky', name: 'Sky' },
  { id: 'lemon', name: 'Lemon' },
  { id: 'mint', name: 'Mint' },
  { id: 'grape', name: 'Grape' },
];

export const drawerSnapshot: RoleFilteredSnapshot = {
  snapshot_id: 'ui-fixture-drawer-safe',
  session_player_id: 'player-mango',
  room: {
    room_id: 'room-fixture',
    pair_id: 'pair-fixture',
    participant: {
      player_id: 'player-mango',
      nickname: 'Mango',
      avatar_id: 'mango',
      connection_status: 'connected',
    },
    teammate: {
      player_id: 'player-kiwi',
      nickname: 'Kiwi',
      avatar_id: 'kiwi',
      connection_status: 'connected',
    },
  },
  round: {
    round_id: 'round-fixture',
    role: 'drawer',
    phase: 'collaborating',
    phase_version: 1,
    permissions: ['edit_drawing', 'hold_to_talk'],
  },
  drawing: {
    round_id: 'round-fixture',
    revision: 3,
    strokes: [
      {
        stroke_id: 'stroke-safe-1',
        color: '#6C4DF6',
        width: 10,
        points: [
          { x: 0.24, y: 0.62 },
          { x: 0.32, y: 0.54 },
          { x: 0.44, y: 0.58 },
        ],
      },
    ],
  },
  voice: {
    mic_permission: 'unknown',
    active_local_hold_ids: [],
    remote_speaking_player_ids: ['player-kiwi'],
    provider_available: false,
  },
};

export const speakerSnapshot: RoleFilteredSnapshot = {
  ...drawerSnapshot,
  snapshot_id: 'ui-fixture-speaker-safe',
  session_player_id: 'player-kiwi',
  room: {
    ...drawerSnapshot.room,
    participant: drawerSnapshot.room.teammate!,
    teammate: drawerSnapshot.room.participant,
  },
  round: {
    ...drawerSnapshot.round,
    role: 'speaker',
    permissions: ['view_object', 'view_drawing', 'hold_to_talk'],
  },
};

export const palette = [
  { color: '#E5483D', label: 'Red' },
  { color: '#FFD23F', label: 'Yellow' },
  { color: '#35B26B', label: 'Green' },
  { color: '#2F80ED', label: 'Blue' },
  { color: '#8B5A2B', label: 'Brown' },
  { color: '#1B2B4B', label: 'Black' },
] as const;

export interface FixtureStroke {
  d: string;
  color: string;
}

/** Fixture drawing from the approved design: a red circle with a brown stem, in a 760 x 680 space. */
export const fixtureDrawing: FixtureStroke[] = [
  { d: 'M169 381 A211 211 0 1 0 591 381 A211 211 0 1 0 169 381', color: '#E5483D' },
  { d: 'M380 174 C380 128 393 103 414 81', color: '#8B5A2B' },
];

export interface ResultFixture {
  /** 1-3 when scoring succeeded, null for the friendly neutral result. */
  stars: 1 | 2 | 3 | null;
  praise: string;
  question: string;
}

export const scoredResult: ResultFixture = {
  stars: 2,
  praise: 'You got the red, round shape!',
  question: 'Hmm... what else is at the top?',
};

export const neutralResult: ResultFixture = {
  stars: null,
  praise: 'Drawy had trouble checking this one, but you still finished the round together!',
  question: "Let's look at the picture and try another one.",
};
