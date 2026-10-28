<script lang="ts">
	import { type Snippet } from 'svelte';
	import { GlobalStyle } from 'components-ui-html';
	import { LoadI18n } from 'components-shared';
	import '../assets/fonts/fonts.css';
	import Authenticate from '../components/Authenticate.svelte';
	import Game from '../components/Game.svelte';
	import JurisdictionHud from '../components/JurisdictionHud.svelte';
	import { setContext } from '../game/context';

	import messagesMap from '../i18n/messagesMap';

	type Props = { children: Snippet };

	const props: Props = $props();

	setContext();
</script>

<GlobalStyle>
	<Authenticate>
		<LoadI18n {messagesMap}>
			<Game />
			<JurisdictionHud />
		</LoadI18n>
	</Authenticate>
</GlobalStyle>

{@render props.children()}