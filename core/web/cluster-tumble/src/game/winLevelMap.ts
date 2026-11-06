import { SECOND } from 'constants-shared/time';

// Banner words are skin texts (skins/<skin>/text/en.json winlevel.*): the core holds keys only.

export const winLevelMap = {
	1: {
		level: 1,
		alias: 'zero',
		type: 'small',
		textKey: null,
		presentDuration: 0,
		sound: { sfx: undefined, bgm: undefined },
		animation: undefined,
	},
	2: {
		level: 2,
		alias: 'standard',
		type: 'small',
		textKey: null,
		presentDuration: 0.6 * SECOND,
		sound: { sfx: undefined, bgm: undefined },
		animation: undefined,
	},
	3: {
		level: 3,
		alias: 'small',
		type: 'small',
		textKey: null,
		presentDuration: 1 * SECOND,
		sound: { sfx: undefined, bgm: undefined },
		animation: undefined,
	},
	4: {
		level: 4,
		alias: 'nice',
		type: 'medium',
		textKey: null,
		presentDuration: 1.5 * SECOND,
		sound: { sfx: undefined, bgm: undefined },
		animation: undefined,
	},
	5: {
		level: 5,
		alias: 'substantial',
		type: 'medium',
		textKey: null,
		presentDuration: 2.0 * SECOND,
		sound: { sfx: undefined, bgm: undefined },
		animation: undefined,
	},
	6: {
		level: 6,
		alias: 'big',
		type: 'big',
		textKey: 'winlevel.big',
		presentDuration: 6 * SECOND,
		sound: { sfx: undefined, bgm: 'bgm_winlevel_big' },
		animation: { intro: 'big_win_intro', idle: 'big_win_idle', outro: 'big_win_exit' },
	},
	7: {
		level: 7,
		alias: 'superwin',
		type: 'big',
		textKey: 'winlevel.superwin',
		presentDuration: 18 * SECOND,
		sound: { sfx: undefined, bgm: 'bgm_winlevel_superwin' },
		animation: { intro: 'super_win_intro', idle: 'super_win_idle', outro: 'super_win_exit' },
	},
	8: {
		level: 8,
		alias: 'mega',
		type: 'big',
		textKey: 'winlevel.mega',
		presentDuration: 20 * SECOND,
		sound: { sfx: undefined, bgm: 'bgm_winlevel_mega' },
		animation: { intro: 'mega_win_intro', idle: 'mega_win_idle', outro: 'mega_win_exit' },
	},
	9: {
		level: 9,
		alias: 'epic',
		type: 'big',
		textKey: 'winlevel.epic',
		presentDuration: 26 * SECOND,
		sound: { sfx: undefined, bgm: 'bgm_winlevel_epic' },
		animation: { intro: 'epic_win_intro', idle: 'epic_win_idle', outro: 'epic_win_exit' },
	},
	10: {
		level: 10,
		alias: 'max',
		type: 'big',
		textKey: 'winlevel.max',
		presentDuration: 32 * SECOND,
		sound: { sfx: undefined, bgm: 'bgm_winlevel_max' },
		animation: { intro: 'max_win_intro', idle: 'max_win_idle', outro: 'max_win_exit' },
	},
} as const;

export type WinLevelMap = typeof winLevelMap;
export type WinLevel = keyof typeof winLevelMap;
export type WinLevelData = WinLevelMap[WinLevel];
export type WinLevelAlias = WinLevelData['alias'];
