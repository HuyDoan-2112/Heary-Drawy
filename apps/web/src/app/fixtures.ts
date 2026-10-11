import type { RoleFilteredSnapshot } from '../generated/contracts';

export const avatarIds = ['sky', 'mint', 'grape', 'berry', 'pepper', 'lemon', 'mango', 'plum', 'coco', 'kiwi'] as const;

export type AvatarId = (typeof avatarIds)[number];

export interface CharacterOption {
  id: AvatarId;
  name: string;
  pickedBy?: string;
}

export const characterOptions: CharacterOption[] = [
  { id: 'sky', name: 'Sky' },
  { id: 'mint', name: 'Mint' },
  { id: 'grape', name: 'Grape' },
  { id: 'berry', name: 'Berry' },
  { id: 'pepper', name: 'Pepper' },
  { id: 'lemon', name: 'Lemon' },
  { id: 'mango', name: 'Mango' },
  { id: 'plum', name: 'Plum' },
  { id: 'coco', name: 'Coco' },
  { id: 'kiwi', name: 'Kiwi', pickedBy: 'teammate' },
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

export const palette = ['#1B2B4B', '#6C4DF6', '#FF6F59', '#2EC4A0', '#FFC83D', '#FFFFFF'];
