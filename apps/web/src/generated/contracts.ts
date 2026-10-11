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
export type CommandId = string;
export type ExpectedRoundVersion = number;
export type RoundId1 = string;
export type Phase = "role_intro" | "collaborating";
export type PhaseVersion = number;
export type RoundId2 = string;
export type AvatarId = string;
export type Nickname = string;
/**
 * @minItems 3
 * @maxItems 3
 */
export type ShapeCode = [string, string, string];
export type AdmissionStatus = "admitted";
export type ExpiresAt = string;
export type GuestSessionToken = string;
export type PlayerId = string;
export type RoomId = string;
export type AdmissionStatus1 = "waiting_for_teammate";
export type AvatarId1 = string;
export type ConnectionStatus = "connected" | "reconnecting" | "disconnected";
export type Nickname1 = string;
export type PlayerId1 = string;
export type RoomId1 = string;
export type SessionPlayerId = string;
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
export type RoomId2 = string;
export type Permissions = string[];
export type RoundPhase = "role_intro" | "collaborating" | "finalizing" | "feedback" | "exploring" | "finished";
export type PhaseVersion1 = number;
export type RoundId3 = string;
export type SessionPlayerId1 = string;
export type SnapshotId = string;
export type ActiveLocalHoldIds = string[];
export type MicPermission = "unknown" | "granted" | "denied";
export type ProviderAvailable = boolean;
export type RemoteSpeakingPlayerIds = string[];
export type CommandId1 = string | null;
export type EventId = string | null;
export type ProtocolVersion = 1;
export type RoundId4 = string | null;
export type Type = string;

export interface HearyDrawyContracts {
  drawing_snapshot: DrawingSnapshot;
  error_envelope: ErrorEnvelope;
  intro_seen_request: IntroSeenRequest;
  intro_seen_response: IntroSeenResponse;
  join_room_request: JoinRoomRequest;
  join_room_response: JoinRoomResponse;
  pending_room_snapshot: PendingRoomSnapshot;
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
export interface IntroSeenRequest {
  command_id: CommandId;
  expected_round_version: ExpectedRoundVersion;
  round_id: RoundId1;
}
export interface IntroSeenResponse {
  phase: Phase;
  phase_version: PhaseVersion;
  round_id: RoundId2;
}
export interface JoinRoomRequest {
  avatar_id: AvatarId;
  nickname: Nickname;
  shape_code: ShapeCode;
}
export interface JoinRoomResponse {
  admission_status: AdmissionStatus;
  expires_at: ExpiresAt;
  guest_session_token: GuestSessionToken;
  player_id: PlayerId;
  room_id: RoomId;
}
export interface PendingRoomSnapshot {
  admission_status: AdmissionStatus1;
  room: PendingRoomSummary;
  session_player_id: SessionPlayerId;
}
export interface PendingRoomSummary {
  participant: PlayerSummary;
  room_id: RoomId1;
}
export interface PlayerSummary {
  avatar_id: AvatarId1;
  connection_status: ConnectionStatus;
  nickname: Nickname1;
  player_id: PlayerId1;
}
export interface RoleFilteredSnapshot {
  drawing: DrawingSnapshot;
  feedback?: FeedbackSnapshot | null;
  object_access?: ObjectAccess | null;
  room: RoomSummary;
  round: RoundSummary;
  session_player_id: SessionPlayerId1;
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
  room_id: RoomId2;
  teammate?: PlayerSummary | null;
}
export interface RoundSummary {
  permissions?: Permissions;
  phase: RoundPhase;
  phase_version: PhaseVersion1;
  role: Role;
  round_id: RoundId3;
}
export interface VoiceState {
  active_local_hold_ids?: ActiveLocalHoldIds;
  mic_permission?: MicPermission;
  provider_available?: ProviderAvailable;
  remote_speaking_player_ids?: RemoteSpeakingPlayerIds;
}
export interface SocketEnvelope {
  command_id?: CommandId1;
  event_id?: EventId;
  payload: Payload;
  protocol_version: ProtocolVersion;
  round_id?: RoundId4;
  type: Type;
}
export interface Payload {
  [k: string]: unknown;
}
