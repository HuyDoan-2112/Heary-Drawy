from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Role(StrEnum):
    speaker = "speaker"
    drawer = "drawer"


class RoundPhase(StrEnum):
    role_intro = "role_intro"
    collaborating = "collaborating"
    finalizing = "finalizing"
    feedback = "feedback"
    exploring = "exploring"
    finished = "finished"


class ConnectionStatus(StrEnum):
    connected = "connected"
    reconnecting = "reconnecting"
    disconnected = "disconnected"


class ResultStatus(StrEnum):
    scored = "scored"
    neutral_unscored = "neutral_unscored"


class PlayerSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_id: str
    nickname: str
    avatar_id: str
    connection_status: ConnectionStatus


class RoomSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_id: str
    pair_id: str
    participant: PlayerSummary
    teammate: PlayerSummary | None = None


class PendingRoomSnapshot(BaseModel):
    """An admitted player without an active teammate: still waiting, or their teammate left."""

    model_config = ConfigDict(extra="forbid")

    session_player_id: str
    admission_status: Literal["waiting_for_teammate", "teammate_left"]
    room: "PendingRoomSummary"


class PendingRoomSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_id: str
    participant: PlayerSummary


class RoundSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    round_id: str
    role: Role
    phase: RoundPhase
    phase_version: int = Field(ge=0)
    # Position in the match; Play again is unavailable once round_index reaches total_rounds.
    round_index: int = Field(ge=1)
    total_rounds: int = Field(ge=1)
    permissions: list[str] = Field(default_factory=list)


class ObjectAccess(BaseModel):
    model_config = ConfigDict(extra="forbid")

    object_id: str
    display_name: str
    image_url: str
    model_url: str | None = None


class DeviceEnrollmentRequest(BaseModel):
    """A grown-up unlocks this device for a Room with the Room passcode."""

    model_config = ConfigDict(extra="forbid")

    passcode: str = Field(min_length=1, max_length=64)


class DeviceEnrollmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_id: str
    device_token: str
    expires_at: str


class LobbyResponse(BaseModel):
    """What an unlocked device may know before admission: which characters are taken."""

    model_config = ConfigDict(extra="forbid")

    taken_avatar_ids: list[str]


class GuestAdmissionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Optional; the character name is used when it is blank.
    nickname: str = Field(default="", max_length=24)
    avatar_id: str = Field(min_length=1, max_length=32)


class GuestAdmissionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_id: str
    player_id: str
    guest_session_token: str
    expires_at: str
    admission_status: Literal["admitted"]


class LeaveResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["left"]


class IntroSeenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command_id: str = Field(min_length=1, max_length=128)
    round_id: str
    expected_round_version: int = Field(ge=0)


class IntroSeenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    round_id: str
    phase: Literal["role_intro", "collaborating"]
    phase_version: int


class SubmitDrawingResponse(BaseModel):
    """The Drawer tapped Done. Without AI scoring the round goes straight to the neutral result."""

    model_config = ConfigDict(extra="forbid")

    round_id: str
    phase: Literal["exploring"]
    phase_version: int


class PlayAgainRequest(IntroSeenRequest):
    """Same command identity and version guard as the intro acknowledgement."""


class PlayAgainResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    round_id: str
    status: Literal["waiting_for_teammate", "started"]
    next_round_id: str | None = None


class ReadyState(BaseModel):
    """Who has acknowledged the current phase: role intro, or Play again while exploring."""

    model_config = ConfigDict(extra="forbid")

    self_ready: bool
    teammate_ready: bool


class Point(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: Annotated[float, Field(ge=0, le=1)]
    y: Annotated[float, Field(ge=0, le=1)]
    pressure: Annotated[float | None, Field(ge=0, le=1)] = None


class Stroke(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stroke_id: str
    color: str
    width: Annotated[float, Field(gt=0, le=64)]
    points: list[Point] = Field(default_factory=list, max_length=512)


class DrawingSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    round_id: str
    revision: int = Field(ge=0)
    strokes: list[Stroke] = Field(default_factory=list, max_length=256)


class VoiceState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mic_permission: Literal["unknown", "granted", "denied"] = "unknown"
    active_local_hold_ids: list[str] = Field(default_factory=list)
    remote_speaking_player_ids: list[str] = Field(default_factory=list)
    provider_available: bool = False


class RoleFeedback(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Role
    lines: list[str] = Field(min_length=1, max_length=4)


class SharedResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ResultStatus
    stars: Annotated[int | None, Field(ge=1, le=3)] = None
    child_summary: str

    @model_validator(mode="after")
    def scored_results_need_stars(self) -> "SharedResult":
        if self.status == ResultStatus.scored and self.stars is None:
            raise ValueError("scored results must include stars")
        if self.status == ResultStatus.neutral_unscored and self.stars is not None:
            raise ValueError("neutral unscored results must not include stars")
        return self


class FeedbackSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shared_result: SharedResult
    role_feedback: RoleFeedback
    sticker_id: str


class RoleFilteredSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    session_player_id: str
    room: RoomSummary
    round: RoundSummary
    drawing: DrawingSnapshot
    voice: VoiceState = Field(default_factory=VoiceState)
    object_access: ObjectAccess | None = None
    feedback: FeedbackSnapshot | None = None
    ready: ReadyState | None = None

    @model_validator(mode="after")
    def enforce_role_phase_visibility(self) -> "RoleFilteredSnapshot":
        before_reveal = self.round.phase in {RoundPhase.role_intro, RoundPhase.collaborating, RoundPhase.finalizing}
        if self.round.role == Role.drawer and before_reveal and "object_access" in self.model_fields_set:
            raise ValueError("drawer snapshots before reveal must omit object access")
        if self.feedback is not None and self.round.phase not in {
            RoundPhase.feedback,
            RoundPhase.exploring,
            RoundPhase.finished,
        }:
            raise ValueError("feedback is only visible at reveal or later")
        return self


class SocketEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protocol_version: Literal[1]
    type: str
    command_id: str | None = None
    event_id: str | None = None
    round_id: str | None = None
    payload: dict


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    retryable: bool = False


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail


class ContractBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_enrollment_request: DeviceEnrollmentRequest
    device_enrollment_response: DeviceEnrollmentResponse
    lobby_response: LobbyResponse
    guest_admission_request: GuestAdmissionRequest
    guest_admission_response: GuestAdmissionResponse
    leave_response: LeaveResponse
    submit_drawing_response: SubmitDrawingResponse
    intro_seen_request: IntroSeenRequest
    intro_seen_response: IntroSeenResponse
    play_again_request: PlayAgainRequest
    play_again_response: PlayAgainResponse
    pending_room_snapshot: PendingRoomSnapshot
    role_filtered_snapshot: RoleFilteredSnapshot
    drawing_snapshot: DrawingSnapshot
    socket_envelope: SocketEnvelope
    error_envelope: ErrorEnvelope
