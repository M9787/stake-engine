<script lang="ts">
	// Pay table + rules. Every value comes from config.ts (generated from the math),
	// so what the player reads always matches the published math (docs/08-compliance.md).
	import config from '../game/config';
	import { t } from '../game/wording';

	type Props = { section: 'payTable' | 'gameRules' };
	const props: Props = $props();

	const SYMBOL_NAMES: Record<string, string> = {
		H1: 'The High Priestess',
		H2: 'The Tower',
		H3: 'The Moon',
		H4: 'The Magician',
		L1: 'Fehu',
		L2: 'Ansuz',
		L3: 'Raido',
		L4: 'Kenaz',
	};
	const BANDS = [
		{ label: '5', size: '5' },
		{ label: '6-8', size: '6' },
		{ label: '9-12', size: '9' },
		{ label: '13+', size: '13' },
	];

	type Paytable = { [size: string]: number }[] | null;
	const payFor = (paytable: Paytable, size: string) =>
		paytable?.find((entry) => size in entry)?.[size];

	const paySymbols = Object.entries(config.symbols as Record<string, { paytable: Paytable }>)
		.filter(([name]) => name in SYMBOL_NAMES)
		.sort(([a], [b]) => Object.keys(SYMBOL_NAMES).indexOf(a) - Object.keys(SYMBOL_NAMES).indexOf(b));

	const MODE_LABELS: Record<string, string> = {
		base: 'Fate: Veil',
		omen: 'Fate: Omen',
		prophecy: 'Fate: Prophecy',
		star: 'Star Bonus (buy)',
		tower: 'Tower Bonus (buy)',
	};
	const modes = Object.entries(config.betModes);
	const fmt = (value: number) => value.toLocaleString('en-US');
	const minPay = Math.min(
		...paySymbols.flatMap(([, symbol]) => (symbol.paytable ?? []).flatMap((entry) => Object.values(entry))),
	);
	const BUTTONS: [string, string][] = [
		['Spin', 'Starts a round at the current bet. Space also spins where allowed; holding Space keeps spinning.'],
		['Stop', 'Pressing Spin during a round shows the result at once, where allowed. Results are the same.'],
		['+ / -', 'Raise or lower the bet through the available bet levels.'],
		['Bet', 'Shows the current bet. The price of a round is the bet times the mode price.'],
		['Balance', 'Your balance in your currency.'],
		['Win', 'The win of the current round.'],
		['Turbo', 'Faster animations. Results are the same.'],
		['Auto spin', 'Plays a chosen number of rounds after you confirm; stops on your loss or win limits.'],
		['Buy bonus', 'Opens the Fate modes (Omen, Prophecy) and the Star and Tower bonus buys, with price, RTP and max win.'],
		['Menu', 'Pay table, game rules, settings and sound.'],
		['Settings', 'Master, music and sound effect volume.'],
		['Sound', 'Turns all sound on or off.'],
		['Replay', 'In a replay, plays the same round again. Replays never place a bet.'],
	];
</script>

<div class="info">
	{#if props.section === 'payTable'}
		<h2>{t('PAY TABLE')}</h2>
		<p>{t('Pays for clusters of 5 or more touching symbols, as multiples of the bet.')}</p>
		<table>
			<thead>
				<tr>
					<th>Symbol</th>
					{#each BANDS as band}<th>{band.label}</th>{/each}
				</tr>
			</thead>
			<tbody>
				{#each paySymbols as [name, symbol]}
					<tr>
						<td>{SYMBOL_NAMES[name]}</td>
						{#each BANDS as band}<td>{payFor(symbol.paytable, band.size)}x</td>{/each}
					</tr>
				{/each}
			</tbody>
		</table>
		<p>{t('Crystal Ball (scatter): 3-4 start the Star Bonus, 5 or more start the Tower Bonus.')}</p>
		<p>
			{t(`In Fate: Veil the smallest pay is ${minPay}x, so every winning spin pays more than the bet.`)}
		</p>
	{:else}
		<h2>{t('GAME RULES')}</h2>
		<h3>Clusters and tumbles</h3>
		<p>
			{t(`7x7 grid. 5 or more touching identical symbols form a cluster and pay. Winning symbols explode
			and new symbols fall in. This repeats until no cluster remains.`)}
		</p>
		<h3>Charged grid</h3>
		<p>
			{t(`A win on an empty spot marks it with a sigil. A win on a marked spot charges it to x2. Each
			later win on that spot doubles it: x4, x8, x16, x32, x64, x128, x256, x512, up to x1024. A
			cluster's pay is multiplied by the sum of the charged spots under it. In the base game the grid
			clears after each spin.`)}
		</p>
		<h3>Bonuses</h3>
		<p>
			{t(`Star Bonus: 12 free spins (3 Crystal Balls) or 15 (4 Crystal Balls), starting with 5 spots
			already charged at x2. Tower Bonus: 15-18 free
			spins, starting with 12 spots already charged at x2. In both bonuses the grid persists for the
			whole bonus. 3 or more Crystal Balls during a bonus add 5 spins.`)}
		</p>
		<h3>Modes</h3>
		<table>
			<thead>
				<tr><th>Mode</th><th>{t('Price')}</th><th>RTP</th><th>Max win</th></tr>
			</thead>
			<tbody>
				{#each modes as [key, mode]}
					<tr>
						<td>{t(MODE_LABELS[key] ?? key)}</td>
						<td>{t(`${mode.cost}x bet`)}</td>
						<td>{(mode.rtp * 100).toFixed(2)}%</td>
						<td>{fmt(mode.max_win)}x</td>
					</tr>
				{/each}
			</tbody>
		</table>
		<p>
			{t(`Fate: Omen and Fate: Prophecy raise the price of each spin in exchange for more frequent
			bonuses. In these modes many wins return less than the spin price; the value comes mostly from
			the bonuses. RTP is the same in every mode.`)}
		</p>
		<p>
			{t(`Bonus buys start a bonus at once. A bonus can pay less than its price.`)}
		</p>
		<h3>Buttons</h3>
		<table>
			<tbody>
				{#each BUTTONS as [name, text]}
					<tr><td>{t(name)}</td><td>{t(text)}</td></tr>
				{/each}
			</tbody>
		</table>
		<h3>General</h3>
		<p>
			{t(`Game RTP ${(config.rtp * 100).toFixed(2)}%. Each round is independent. A round ends when it
			reaches the maximum win of ${fmt(config.betModes.base.max_win)}x. Wins are shown in your currency
			and added to your balance when the round ends.`)}
		</p>
		<p>
			<!-- Engine general disclaimer template, verbatim (Engine [185];
				stake-engine.com/docs/approval-guidelines/general-disclaimer, 2026-10-28). -->
			{t(`Malfunction voids all wins and plays. A consistent internet connection is required. In the
			event of a disconnection, reload the game to finish any uncompleted rounds. The expected return
			is calculated over many plays. The game display is not representative of any physical device and
			is for illustrative purposes only. Winnings are settled according to the amount received from the
			Remote Game Server and not from events within the web browser. TM and © 2026 Engine.`)}
		</p>
	{/if}
</div>

<style>
	.info {
		color: #f3e9ff;
		font-family: 'proxima-nova', sans-serif;
		padding: 1rem;
		max-width: 48rem;
	}
	h2 {
		color: #e7c77a;
		margin: 0 0 0.75rem;
	}
	h3 {
		color: #e7c77a;
		margin: 1rem 0 0.25rem;
	}
	table {
		border-collapse: collapse;
		width: 100%;
		margin: 0.5rem 0;
	}
	th,
	td {
		border-bottom: 1px solid rgba(231, 199, 122, 0.3);
		padding: 0.3rem 0.5rem;
		text-align: left;
	}
</style>
