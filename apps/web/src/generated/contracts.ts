/* Generated from contracts/schema.json. Do not edit by hand. */

export type Revision = number;
export type RoundId = string;
export type Color = string;
export type Pressure = number | null;
export type X = number;
export type Y = number;
/**
 * @maxItems 512
 */
export type Points = Point[];
export type StrokeId = string;
export type Width = number;
/**
 * @maxItems 256
 */
export type Strokes = Stroke[];
export type Code = string;
export type Message = string;
export type Retryable = boolean;
/**
 * @minItems 1
 * @maxItems 4
 */
export type Lines = [string] | [string, string] | [string, string, string] | [string, string, string, string];
export type Role = "speaker" | "drawer";
export type ChildSummary = string;
export type Stars = number | null;
export type ResultStatus = "scored" | "neutral_unscored";
export type StickerId = string;
export type DisplayName = string;
export type ImageUrl = string;
export type ModelUrl = string | null;
export type ObjectId = string;
export type PairId = string;
export type AvatarId = string;
export type ConnectionStatus = "connected" | "reconnecting" | "disconnected";
export type Nickname = string;
export type PlayerId = string;
export type RoomId = string;
export type Permissions = string[];
export type RoundPhase = "role_intro" | "collaborating" | "finalizing" | "feedback" | "exploring" | "finished";
export type PhaseVersion = number;
export type RoundId1 = string;
export type SessionPlayerId = string;
export type SnapshotId = string;
export type ActiveLocalHoldIds = string[];
export type MicPermission = "unknown" | "granted" | "denied";
export type ProviderAvailable = boolean;
export type RemoteSpeakingPlayerIds = string[];
export type CommandId = string | null;
export type EventId = string | null;
export type ProtocolVersion = 1;
export type RoundId2 = string | null;
export type Type = string;

export interface HearyDrawyContracts {
  drawing_snapshot: DrawingSnapshot;
  error_envelope: ErrorEnvelope;
  role_filtered_snapshot: RoleFilteredSnapshot;
  socket_envelope: SocketEnvelope;
}
export interface DrawingSnapshot {
  revision: Revision;
  round_id: RoundId;
  strokes?: Strokes;
}
export interface Stroke {
  color: Color;
  points?: Points;
  stroke_id: StrokeId;
  width: Width;
}
export interface Point {
  pressure?: Pressure;
  x: X;
  y: Y;
}
export interface ErrorEnvelope {
  error: ErrorDetail;
}
export interface ErrorDetail {
  code: Code;
  message: Message;
  retryable?: Retryable;
}
export interface RoleFilteredSnapshot {
  drawing: DrawingSnapshot;
  feedback?: FeedbackSnapshot | null;
  object_access?: ObjectAccess | null;
  room: RoomSummary;
  round: RoundSummary;
  session_player_id: SessionPlayerId;
  snapshot_id: SnapshotId;
  voice?: VoiceState;
}
export interface FeedbackSnapshot {
  role_feedback: RoleFeedback;
  shared_result: SharedResult;
  sticker_id: StickerId;
}
export interface RoleFeedback {
  lines: Lines;
  role: Role;
}
export interface SharedResult {
  child_summary: ChildSummary;
  stars?: Stars;
  status: ResultStatus;
}
export interface ObjectAccess {
  display_name: DisplayName;
  image_url: ImageUrl;
  model_url?: ModelUrl;
  object_id: ObjectId;
}
export interface RoomSummary {
  pair_id: PairId;
  participant: PlayerSummary;
  room_id: RoomId;
  teammate?: PlayerSummary | null;
}
export interface PlayerSummary {
  avatar_id: AvatarId;
  connection_status: ConnectionStatus;
  nickname: Nickname;
  player_id: PlayerId;
}
export interface RoundSummary {
  permissions?: Permissions;
  phase: RoundPhase;
  phase_version: PhaseVersion;
  role: Role;
  round_id: RoundId1;
}
export interface VoiceState {
  active_local_hold_ids?: ActiveLocalHoldIds;
  mic_permission?: MicPermission;
  provider_available?: ProviderAvailable;
  remote_speaking_player_ids?: RemoteSpeakingPlayerIds;
}
export interface SocketEnvelope {
  command_id?: CommandId;
  event_id?: EventId;
  payload: Payload;
  protocol_version: ProtocolVersion;
  round_id?: RoundId2;
  type: Type;
}
export interface Payload {
  [k: string]: unknown;
}
