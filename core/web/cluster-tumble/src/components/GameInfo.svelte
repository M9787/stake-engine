<script lang="ts">
	// Pay table + rules. Every number and every game-specific text comes from the skin
	// ($skin/skin.generated: tools/gen/gen_rules.py fills them from game.json and the published math),
	// so what the player reads always matches the published math (docs/08-compliance.md).
	import skin from '$skin/skin.generated';
	import config from '$skin/config';
	import { t } from '../game/wording';

	type Props = { section: 'payTable' | 'gameRules' };
	const props: Props = $props();

	const texts: Record<string, string> = skin.rules.texts;
	const text = (key: string, fallback = '') => texts[key] ?? fallback;
	const { bands, rows } = skin.rules.paytable;
	const modes = skin.rules.modes;
	const fmt = (value: number) => value.toLocaleString('en-US');
	const minCluster = skin.rules.paytable.bands[0].replace('+', '').split('-')[0];
	// Panel colours from the skin (game.json theme.ui); neutral core defaults when missing.
	const ui: { text?: string; heading?: string; rule?: string } = (skin.theme as Record<string, any>).ui ?? {};
	const cssVars = `--ct-text:${ui.text ?? '#ffffff'};--ct-heading:${ui.heading ?? '#ffffff'};--ct-rule:${ui.rule ?? '#ffffff4d'}`;
	const BUTTONS: [string, string][] = [
		['Spin', 'Starts a round at the current bet. Space also spins where allowed; holding Space keeps spinning.'],
		['Stop', 'Pressing Spin during a round shows the result at once, where allowed. Results are the same.'],
		['+ / -', 'Raise or lower the bet through the available bet levels.'],
		['Bet', 'Shows the current bet. The price of a round is the bet times the mode price.'],
		['Balance', 'Your balance in your currency.'],
		['Win', 'The win of the current round.'],
		['Turbo', 'Faster animations. Results are the same.'],
		['Auto spin', 'Plays a chosen number of rounds after you confirm; stops on your loss or win limits.'],
		['Buy bonus', text('button.buyBonus', 'Opens the game modes and bonus buys, with price, RTP and max win.')],
		['Menu', 'Pay table, game rules, settings and sound.'],
		['Settings', 'Master, music and sound effect volume.'],
		['Sound', 'Turns all sound on or off.'],
		['Replay', 'In a replay, plays the same round again. Replays never place a bet.'],
	];
</script>

<div class="info" style={cssVars}>
	{#if props.section === 'payTable'}
		<h2>{t('PAY TABLE')}</h2>
		<p>{t(`Pays for clusters of ${minCluster} or more touching symbols, as multiples of the bet.`)}</p>
		<table>
			<thead>
				<tr>
					<th>Symbol</th>
					{#each bands as band}<th>{band}</th>{/each}
				</tr>
			</thead>
			<tbody>
				{#each rows as row}
					<tr>
						<td>{row.name}</td>
						{#each row.pays as pay}<td>{pay}x</td>{/each}
					</tr>
				{/each}
			</tbody>
		</table>
		{#if texts['rules.scatter']}<p>{t(text('rules.scatter'))}</p>{/if}
		{#if texts['rules.minPay']}<p>{t(text('rules.minPay'))}</p>{/if}
	{:else}
		<h2>{t('GAME RULES')}</h2>
		<h3>Clusters and tumbles</h3>
		<p>
			{t(`${skin.board.reels}x${skin.board.rows} grid. ${minCluster} or more touching identical symbols form a cluster and pay. Winning symbols explode
			and new symbols fall in. This repeats until no cluster remains.`)}
		</p>
		{#if texts['rules.charged']}
			<h3>{text('rules.charged.title', 'Charged grid')}</h3>
			<p>{t(text('rules.charged'))}</p>
		{/if}
		{#if texts['rules.bonuses']}
			<h3>{text('rules.bonuses.title', 'Bonuses')}</h3>
			<p>{t(text('rules.bonuses'))}</p>
		{/if}
		<h3>Modes</h3>
		<table>
			<thead>
				<tr><th>Mode</th><th>{t('Price')}</th><th>RTP</th><th>Max win</th></tr>
			</thead>
			<tbody>
				{#each modes as mode}
					<tr>
						<td>{t(mode.label)}</td>
						<td>{t(`${mode.cost}x bet`)}</td>
						<td>{((mode.rtp ?? 0) * 100).toFixed(2)}%</td>
						<td>{fmt(mode.maxWin ?? 0)}x</td>
					</tr>
				{/each}
			</tbody>
		</table>
		{#if texts['rules.modes']}<p>{t(text('rules.modes'))}</p>{/if}
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
			reaches the maximum win of ${fmt(modes[0].maxWin ?? 0)}x. Wins are shown in your currency
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
		color: var(--ct-text);
		font-family: 'proxima-nova', sans-serif;
		padding: 1rem;
		max-width: 48rem;
	}
	h2 {
		color: var(--ct-heading);
		margin: 0 0 0.75rem;
	}
	h3 {
		color: var(--ct-heading);
		margin: 1rem 0 0.25rem;
	}
	table {
		border-collapse: collapse;
		width: 100%;
		margin: 0.5rem 0;
	}
	th,
	td {
		border-bottom: 1px solid var(--ct-rule);
		padding: 0.3rem 0.5rem;
		text-align: left;
	}
</style>
