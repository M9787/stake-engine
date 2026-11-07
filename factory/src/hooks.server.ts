// Local-only guard (plan v3.3 M12): the editor runs tools on this machine, so it answers only to its own
// origin. Host must be 127.0.0.1:<port> (blocks DNS rebinding); every non-GET/HEAD request must carry
// Origin http://127.0.0.1:<port> (blocks cross-site requests). Unknown or invalid game ids -> 404 JSON.
import { json, type Handle } from '@sveltejs/kit';

import { skinOf } from '$lib/server/repo';

const PORT = process.env.FACTORY_PORT ?? '5174';
const HOST = `127.0.0.1:${PORT}`;
const ORIGIN = `http://${HOST}`;

export const handle: Handle = async ({ event, resolve }) => {
	const { request } = event;
	if (request.headers.get('host') !== HOST) return json({ error: 'forbidden host' }, { status: 403 });
	if (request.method !== 'GET' && request.method !== 'HEAD' && request.headers.get('origin') !== ORIGIN)
		return json({ error: 'forbidden origin' }, { status: 403 });
	const id = event.params?.id;
	if (id !== undefined && event.url.pathname.startsWith('/api/')) {
		try {
			skinOf(id);
		} catch (e) {
			return json({ error: (e as Error).message }, { status: 404 });
		}
	}
	return resolve(event);
};
