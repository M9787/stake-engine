// Local mock RGS for demo play. Vite dev server only (apply: 'serve'); never part of the build.
// Data: .mock-rgs/<mode>.json from scripts/books_to_mock.py (real books, drawn by lookup weight).
//
// Open: https://localhost:3007/?sessionID=demo&rgs_url=localhost:3007/rgs&lang=en
// sessionID tokens (split by "_") set demo conditions:
//   b<amount>  start balance in dollars (default 1000), e.g. demo_b5
//   social     jurisdiction.socialCasino = true
//   nobuy / noturbo / noauto / nospace  matching jurisdiction.disabled* flag
//   c<CODE>    balance currency (default USD), e.g. demo_cJPY, demo_social_cXSC
//   minround<ms>  jurisdiction.minimumRoundDuration, e.g. demo_minround3000
//   timer / net / rtp / noslam  displaySessionTimer / displayNetPosition / displayRTP / disabledSlamstop
//   maxbuy<dollars>  config.gameModes maxBet for the buy modes, e.g. demo_maxbuy5
//   paused     /wallet/play answers 423 with no body (new bets paused)
//   act<n>     the first n plays answer 429 ERR_ACT (the game retries), e.g. demo_act2
//   gen / gle  /wallet/play answers 500 ERR_GEN / 400 ERR_GLE
// Force the next round: POST /rgs/mock/force {"sessionID": "...", "next": "maxwin" | "bonus" | "loss" | "win" | "big"}
// Forget a session (fresh balance, no open round): POST /rgs/mock/reset {"sessionID": "..."}
// Parity with the RGS (stake-engine.com/docs/rgs/wallet, 2026-11-06): play during an open round
// and end-round without one answer ERR_VAL; malformed JSON answers a plain-text 400.
import fs from 'node:fs';
import path from 'node:path';

import { skinDir } from '../svelte.config.js';

const AMOUNT = 1_000_000; // API units: 1_000_000 = $1 (constants-shared/bet.ts)
const BET_LEVELS = [
	0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2, 2.5, 3, 3.5, 4, 4.5, 5, 6, 7, 8,
	9, 10, 12, 14, 16, 18, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100,
].map((v) => Math.round(v * AMOUNT));

const mockRoot = path.resolve(process.cwd(), '.mock-rgs');
const modes = {};
const sessions = new Map();
const rounds = new Map();
let roundSeq = 1;

// Game id and modes come from the skin (build/<GAME>/web/modes.json, tools/gen/gen_skin_ts.py).
const SKIN_META = JSON.parse(fs.readFileSync(path.join(skinDir, 'modes.json'), 'utf-8'));
const MODE_NAMES = SKIN_META.modes.map((m) => m.name);
// Mock books per game (scripts/books_to_mock.py --game <id>): one core app serves every skin.
const dataDir = path.join(mockRoot, SKIN_META.gameId);

const loadMode = (name) => {
	const key = String(name).toLowerCase();
	if (!modes[key]) {
		const file = path.join(dataDir, `${key}.json`);
		if (!fs.existsSync(file)) return null;
		modes[key] = JSON.parse(fs.readFileSync(file, 'utf-8'));
	}
	return modes[key];
};

const session = (sessionID) => {
	if (!sessions.has(sessionID)) {
		const tokens = String(sessionID || 'demo').split('_');
		const b = tokens.find((t) => /^b\d+(\.\d+)?$/.test(t));
		sessions.set(sessionID, {
			balance: Math.round((b ? Number(b.slice(1)) : 1000) * AMOUNT),
			currency: (tokens.find((t) => /^c[A-Z]{3,5}$/.test(t)) || 'cUSD').slice(1),
			round: null,
			force: null,
			maxBuy: Number((tokens.find((t) => /^maxbuy\d+(\.\d+)?$/.test(t)) || 'maxbuy0').slice(6)) * AMOUNT,
			paused: tokens.includes('paused'),
			actLeft: Number((tokens.find((t) => /^act\d+$/.test(t)) || 'act0').slice(3)),
			failGen: tokens.includes('gen'),
			failGle: tokens.includes('gle'),
			jurisdiction: {
				socialCasino: tokens.includes('social'),
				disabledFullscreen: false,
				disabledTurbo: tokens.includes('noturbo'),
				disabledSuperTurbo: tokens.includes('noturbo'),
				disabledAutoplay: tokens.includes('noauto'),
				disabledSlamstop: tokens.includes('noslam'),
				disabledSpacebar: tokens.includes('nospace'),
				disabledBuyFeature: tokens.includes('nobuy'),
				displayNetPosition: tokens.includes('net'),
				displayRTP: tokens.includes('rtp'),
				displaySessionTimer: tokens.includes('timer'),
				minimumRoundDuration: Number((tokens.find((t) => /^minround\d+$/.test(t)) || 'minround0').slice(8)),
			},
		});
	}
	return sessions.get(sessionID);
};

const balance = (s) => ({ amount: s.balance, currency: s.currency });
const fail = (code, message, status = 400) => ({ status, body: { error: code, message } });

// config.gameModes: [{ mode, costMultiplier, maxBet }] for every mode with mock data.
const gameModes = (s) =>
	MODE_NAMES.map((name) => loadMode(name))
		.filter(Boolean)
		.map((m) => ({
			mode: String(m.mode).toUpperCase(),
			costMultiplier: m.cost,
			maxBet: m.cost >= 10 && s.maxBuy ? s.maxBuy : BET_LEVELS[BET_LEVELS.length - 1],
		}));

const routes = {
	'/wallet/authenticate': (body) => {
		const s = session(body.sessionID);
		return {
			body: {
				balance: balance(s),
				config: {
					gameID: SKIN_META.gameId,
					minBet: BET_LEVELS[0],
					maxBet: BET_LEVELS[BET_LEVELS.length - 1],
					stepBet: 100_000,
					defaultBetLevel: AMOUNT,
					betLevels: BET_LEVELS,
					betModes: {},
					gameModes: gameModes(s),
					jurisdiction: s.jurisdiction,
				},
				round: s.round && s.round.active ? s.round : null,
			},
		};
	},
	'/wallet/play': (body) => {
		const s = session(body.sessionID);
		if (s.paused) return { status: 423, raw: '' };
		if (s.actLeft > 0) {
			s.actLeft--;
			return fail('ERR_ACT', 'provably fair draw not taken', 429);
		}
		if (s.failGen) return fail('ERR_GEN', 'general server error', 500);
		if (s.failGle) return fail('ERR_GLE', 'gambling limits exceeded');
		const mode = loadMode(body.mode);
		if (!mode) return fail('ERR_VAL', `unknown mode ${body.mode}`);
		if (s.round && s.round.active) return fail('ERR_VAL', 'round already active');
		if (!BET_LEVELS.includes(body.amount)) return fail('ERR_VAL', 'invalid bet amount');
		const modeMax = gameModes(s).find((m) => m.mode === String(body.mode).toUpperCase())?.maxBet;
		if (modeMax && body.amount > modeMax) return fail('ERR_VAL', 'bet above mode maxBet');
		if (mode.cost >= 10 && s.jurisdiction.disabledBuyFeature) return fail('ERR_VAL', 'bonus buy disabled');
		const charge = Math.round(body.amount * mode.cost);
		if (charge > s.balance) return fail('ERR_IPB', 'insufficient balance');
		// Book id 0 is valid (buy-mode bonus books), so test for null/undefined, not falsy.
		const forcedId = s.force ? mode.forced[s.force] : undefined;
		const id = forcedId ?? mode.ids[Math.floor(Math.random() * mode.ids.length)];
		s.force = null;
		const book = mode.books[id];
		const payout = Math.round((body.amount * book.payoutMultiplier) / 100);
		s.balance -= charge;
		const roundID = roundSeq++;
		s.round = {
			roundID,
			betID: roundID,
			amount: body.amount,
			payout,
			payoutMultiplier: book.payoutMultiplier / 100,
			costMultiplier: mode.cost,
			active: true,
			mode: String(body.mode).toUpperCase(),
			event: null,
			state: book.events,
		};
		rounds.set(String(roundID), { mode: mode.mode, round: s.round });
		// Losing rounds close at once, like the RGS (no end-round call needed).
		if (payout === 0) s.round = { ...s.round, active: false };
		return { body: { balance: balance(s), round: s.round } };
	},
	'/wallet/end-round': (body) => {
		const s = session(body.sessionID);
		if (!s.round || !s.round.active) return fail('ERR_VAL', 'no active round');
		s.balance += s.round.payout;
		s.round = { ...s.round, active: false };
		return { body: { balance: balance(s) } };
	},
	'/wallet/balance': (body) => ({ body: { balance: balance(session(body.sessionID)) } }),
	'/bet/event': (body) => {
		const s = session(body.sessionID);
		if (s.round) s.round.event = body.event;
		return { body: { event: body.event } };
	},
	'/mock/reset': (body) => {
		sessions.delete(body.sessionID);
		return { body: { ok: true } };
	},
	'/mock/force': (body) => {
		session(body.sessionID).force = body.next;
		return { body: { ok: true, next: body.next } };
	},
};

const send = (res, status, body) => {
	res.statusCode = status;
	res.setHeader('Content-Type', 'application/json');
	res.setHeader('Access-Control-Allow-Origin', '*');
	res.setHeader('Access-Control-Allow-Headers', '*');
	res.end(JSON.stringify(body));
};

const sendRaw = (res, status, text) => {
	res.statusCode = status;
	res.setHeader('Content-Type', 'text/plain');
	res.setHeader('Access-Control-Allow-Origin', '*');
	res.setHeader('Access-Control-Allow-Headers', '*');
	res.end(text);
};

export default function mockRgs() {
	return {
		name: 'cluster-tumble-mock-rgs',
		apply: 'serve',
		configureServer(server) {
			server.middlewares.use('/rgs', (req, res) => {
				if (req.method === 'OPTIONS') return send(res, 204, {});
				const url = (req.url || '').split('?')[0];
				// GET /bet/replay/{game}/{version}/{mode}/{event}
				const replay = url.match(/^\/bet\/replay\/[^/]+\/[^/]+\/([^/]+)\/([^/]+)$/);
				if (req.method === 'GET' && replay) {
					const hit = rounds.get(replay[2]);
					if (!hit) return send(res, 404, { error: 'ERR_BNF', message: 'round not found' });
					const { amount, payout, payoutMultiplier, costMultiplier, state } = hit.round;
					return send(res, 200, { amount, payout, payoutMultiplier, costMultiplier, state });
				}
				const handler = routes[url];
				if (!handler) return send(res, 404, { error: 'ERR_VAL', message: `no route ${url}` });
				let raw = '';
				req.on('data', (c) => (raw += c));
				req.on('end', () => {
					let body = {};
					try {
						body = raw ? JSON.parse(raw) : {};
					} catch {
						return sendRaw(res, 400, 'Bad Request');
					}
					const out = handler(body);
					if (out.raw !== undefined) return sendRaw(res, out.status, out.raw);
					send(res, out.status || 200, out.body);
				});
			});
		},
	};
}
