// Shared label style for win / bonus screens: skin UI font, palette accent with a dark stroke.
import { palette } from '../../slots/slots';
import { UI_FONT } from '../../slots/fonts';

export const labelStyle = (fontSize: number, fill: string = palette[2] ?? '#ffffff') => ({
	fontFamily: UI_FONT,
	fontSize,
	fontWeight: 'bold' as const,
	fill,
	align: 'center' as const,
	letterSpacing: Math.round(fontSize * 0.06),
	stroke: { color: palette[0] ?? '#000000', width: Math.max(2, fontSize * 0.12) },
});
