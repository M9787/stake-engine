// Plain-language explanations of tool failures (plan v2.1 runtime). Agent S extends the table.
// Rules are checked in order; the first match wins, so specific messages come before generic ones.
import type { ToolId } from '$lib/types';

const RULES: [RegExp, string][] = [
	// math
	[/no valid book after/i, 'A math target is (nearly) unreachable on this board: lower the max win, raise its quota, or change the reel strips.'],
	[/Math output missing/i, 'The math for this game has not been built yet. Run "Math preview" first, then retry.'],
	[/(No such file|FileNotFoundError|missing).*lookUpTable_\w+\.csv/i, 'A math lookup table is missing or unreadable. Re-run the math (preview or candidate) for this game.'],
	[/could not compile|error\[E\d{4}\]|cargo.*(error|failed)/i, 'The math optimizer (Rust) failed. Run the environment check (doctor) and see docs/01 optimizer setup.'],
	[/MemoryError|out of memory/i, 'The computer ran out of memory. Close other programs or use the smaller math preview.'],
	// packaging and art
	[/REFUSED: precheck failed/i, 'Packaging was refused: some required art, edits, licences or the sign-off are missing (see the list above).'],
	[/already exists: bump identity\.version/i, 'This version was already packaged. Raise the version number on the Definition page, then package again.'],
	[/Not signed: check_art_in --gate must pass first/i, 'The art cannot be signed yet: some required slots are still incomplete. Finish them on the asset desk first.'],
	[/GATE FAIL: every required slot/i, 'Some required art slots are not complete yet (see the list above). Add the missing files on the asset desk.'],
	[/Unknown slot '/i, 'That slot id does not exist for this game. Render the prompts again so the slot list is current.'],
	[/licence '.*' not on the allowlist/i, 'A file has no licence, or one that is not allowed. Set the licence in its provenance line.'],
	[/rembg|onnxruntime/i, 'Background removal (rembg) failed. Check that the asset tools are installed (.venv-assets), or ingest with a transparent PNG.'],
	[/ffmpeg|ffprobe/i, 'The audio tool ffmpeg was not found or failed. Install ffmpeg (see docs/09) and retry.'],
	[/cannot identify image file|UnidentifiedImageError|image file is truncated/i, 'An image file is damaged or not a real image. Export it again as PNG and replace it.'],
	// web
	[/web build .* did not finish/i, 'The web build did not finish; open the log above for the first error.'],
	[/App folder missing/i, 'The web app has not been prepared yet. Run "Sync core + skin" first, then retry.'],
	[/EADDRINUSE|Port \d+ is in use|address already in use/i, 'The preview port is already in use. Stop the other preview (or the program using that port) and retry.'],
	[/ERR_PNPM|pnpm(\.cmd)?' is not recognized|pnpm: command not found/i, 'pnpm failed or is missing. Run the environment check (doctor) and follow its fix column.'],
	[/error TS\d{4}/i, 'The web code has a type error (see the first error in the log).'],
	// sync, game lookup, definition
	[/no skin with gameId|No skin has identity\.gameId/i, 'No skin folder has this game id. Check identity.gameId in game.json.'],
	[/FAIL\s+tools\\gen\\gen_shim\.py/i, 'Generating the math entry for this game failed. Validate the definition, fix its errors, then sync again.'],
	[/robocopy \d+/i, 'Copying files during sync failed. Close programs that hold files in the game folders and retry.'],
	[/jsonschema\.exceptions|Failed validating/i, 'The game definition does not match the schema. Open the Definition page and fix the listed errors.'],
	[/JSONDecodeError|Expecting (value|property name|',' delimiter)/i, 'A JSON file is broken (a missing comma or quote). Restore it from History or fix it by hand.'],
	// environment
	[/ModuleNotFoundError|No module named/i, 'A Python package is missing in the tool environment. Run the environment check (doctor) and reinstall the env as PROJECT.md section 7 says.'],
	[/spawn .* ENOENT|ENOENT.*python|is not recognized as an internal or external command/i, 'A program the tool needs was not found. Run the environment check (doctor).'],
	[/PermissionError|being used by another process|EBUSY|EPERM/i, 'A file is locked by another program (editor, preview or antivirus). Close it and retry.'],
	[/FileNotFoundError|No such file or directory/i, 'A file the tool needs is missing (see the path in the last lines). Earlier steps may not have run yet.'],
	[/UnicodeDecodeError|UnicodeEncodeError/i, 'A file has an unexpected text encoding. Save it as UTF-8 and retry.'],
];

export const explain = (tool: ToolId, log: string): string => {
	for (const [re, msg] of RULES) if (re.test(log)) return msg;
	const last = log.trim().split(/\r?\n/).filter(Boolean).pop() ?? '';
	return `${tool} failed. Last line: ${last.slice(0, 300)}`;
};
