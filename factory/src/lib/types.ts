// Shared API contract of the factory editor (docs/10 plan v3.3, M12). Server routes return these
// shapes as JSON; pages fetch them. Change only with the integrator.

/** One game = one skin folder skins/<skin>/ with game.json identity.gameId = id. */
export type GameSummary = {
	id: string; // identity.gameId, e.g. "seventh_veil"
	skin: string; // folder name under skins/, e.g. "oracle-of-sevens"
	displayName: string;
	version: string;
	board: { reels: number; rows: number };
	modes: { name: string; kind: 'spin' | 'buy'; cost: number }[];
	testOnly: boolean;
	frozenModes: boolean; // true for Oracle (PROJECT.md section 4): modes and math are read-only in the editor
	hasMath: boolean; // math-sdk/games/<id>/library/publish_files exists
	requiredSlots: { filled: number; total: number }; // from assets.lock.json + catalogue
};

/** GET /api/games -> GameSummary[] ; POST /api/games (NewGameRequest) -> { id } */
export type NewGameRequest = { template: string /* skin folder */; id: string; displayName: string };

/** GET /api/doctor */
export type DoctorRow = { tool: string; want: string; have: string; status: 'PASS' | 'WARN' | 'FAIL'; fix: string };

/** GET /api/game/[id]/validate -> validate.py --json */
export type Issue = { path: string; message: string };
export type ValidateResult = { ok: boolean; errors: Issue[]; warnings: Issue[] };

/** GET/PUT /api/game/[id]/definition -> editable parts of game.json + text/en.json */
export type Definition = {
	identity: { displayName: string; version: string };
	theme: Record<string, unknown>;
	texts: Record<string, string>;
	readOnly: { modes: boolean; math: boolean }; // frozen for Oracle
};

// ---- jobs ---------------------------------------------------------------------------------------
/** Whitelisted tool ids (src/lib/server/tools.ts). */
export type ToolId =
	| 'sync'
	| 'prompts'
	| 'check_art_in'
	| 'ingest_all'
	| 'ingest_slot'
	| 'contact_sheet'
	| 'sign_off'
	| 'audio'
	| 'math_preview'
	| 'math_candidate'
	| 'fe_config'
	| 'mock'
	| 'web_build'
	| 'gate_fast'
	| 'gate_full'
	| 'package'
	| 'preview_server'
	| 'test_assets'
	| 'clear_test_assets'
	| 'apply_preset'
	| 'math_freeze'
	| 'event_ids'
	| 'shots'
	| 'pack';

export type JobStatus = 'running' | 'done' | 'failed' | 'cancelled';
export type Job = {
	id: string; // "<gameId>-<timestamp>"
	game: string;
	tool: ToolId;
	args: string[];
	status: JobStatus;
	exitCode: number | null;
	started: string; // ISO
	ended: string | null;
	plain: string | null; // plain-language explanation of a failure (src/lib/server/plain.ts)
};
/** POST /api/game/[id]/jobs {tool, opts} -> Job ; GET /api/jobs/[jobId]?from=<byte> -> {job, log, next} ;
 *  POST /api/jobs/[jobId]/cancel -> Job ; GET /api/game/[id]/jobs -> Job[] (newest first) */
/** Preset choices for a new or reset game (tools/gamedef/apply_preset.py). */
export type PresetRequest = {
	board: string; // "6x6" .. "8x8"
	volatility: 'low' | 'medium' | 'high';
	wincap: number;
	bonusOneIn: number;
	modes: string[]; // subset of ['base', 'ante', 'buy']
};
export type JobOpts = { slot?: string; signer?: string; preset?: PresetRequest; version?: string };
export type StartJob = { tool: ToolId; opts?: JobOpts };

// ---- policy (core/policy.v1.json) -------------------------------------------------------------
/** stake = blocks packaging; ours = warning with a reason (owner decision 2026-11-07). */
export type PolicyLevel = 'stake' | 'ours';
export type PolicyIssue = { rule: string; level: PolicyLevel; message: string; why?: string; source?: string };

// ---- math state -------------------------------------------------------------------------------
/** GET /api/game/[id]/math-state */
export type MathState = {
	tier: 'none' | 'preview' | 'candidate' | 'frozen';
	stale: boolean; // math sections of game.json changed after the last run
	lastRun: string | null; // ISO
	frozenLookups: boolean; // skins/<skin>/math/lookups exists
};

// ---- submission pack --------------------------------------------------------------------------
/** GET /api/game/[id]/pack -> build/<id>/pack/pack.json (tools/release/pack.py) */
export type PackSummary = {
	game: string;
	version: string;
	generated: string | null;
	ready: boolean; // no Stake-level problems
	blockers: PolicyIssue[];
	warnings: PolicyIssue[];
	studioFields: { label: string; value: string }[]; // copy into the Studio submission form
	files: { label: string; path: string }[]; // submission.html, submission.md, screenshots, reports
};
export type JobLog = { job: Job; log: string; next: number };

// ---- asset desk ---------------------------------------------------------------------------------
/** One card on the desk: build/<id>/prompts.json slot + check_art_in --json status + lock record. */
export type SlotCard = {
	id: string;
	kind: 'image' | 'music' | 'sfx' | 'font';
	sitting: number;
	required: 'ship' | 'optional' | 'source';
	px: [number, number] | null;
	aspect: string | null;
	variants: number | null;
	toolLabel: string;
	toolUrl: string;
	steps: string[];
	humanEdit: 'required' | 'optional' | 'none';
	editRecipe: string[];
	source: string;
	prompt: string;
	promptSha: string;
	feeds: string[];
	have: { raw: string | null; edited: string | null };
	ingested: boolean; // assets.lock.json has a record
	complete: boolean; // check_art_in says complete
	issues: string[]; // check_art_in plain-language issues
	provenance: { licence?: string; sourceUrl?: string; editNote?: string; redo?: string };
};
export type Sitting = { id: number; title: string; minutes: number; note: string };
/** GET /api/game/[id]/assets -> AssetDesk */
export type AssetDesk = {
	game: string;
	sittings: Sitting[];
	slots: SlotCard[];
	licences: string[];
	required: { filled: number; total: number };
	signoff: { signedBy: string; date: string; current: boolean } | null;
};
/** POST /api/game/[id]/assets/upload (multipart: slot, lane=raw|edited, file) -> SlotCard
 *  PUT  /api/game/[id]/assets/provenance {slot, licence?, sourceUrl?, editNote?, redo?} -> SlotCard
 *  GET  /api/game/[id]/assets/file?slot=&lane=raw|edited|final -> image bytes (thumbnails)
 *  GET  /api/game/[id]/assets/contact/[name] -> build/<id>/contact_<name>.png */
