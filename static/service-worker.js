const CACHE_NAME = 'ethiosadat-cache-v3';

const STATIC_ASSETS = [
    '/static/css/style.css',
    '/static/js/main.js',
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(STATIC_ASSETS).catch(() => {});
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys.filter(k => k !== CACHE_NAME)
                    .map(k => caches.delete(k))
            )
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    // Non-GET requests (POST, PUT, DELETE, PATCH) must always go directly
    // to the network. Using event.respondWith(fetch(event.request)) ensures
    // the browser does not fall back to an empty response.
    if (event.request.method !== 'GET') {
        event.respondWith(fetch(event.request));
        return;
    }

    const url = new URL(event.request.url);

    // API GET routes: always go to network, never serve from cache.
    // If network fails, return a valid JSON error so the app won't crash.
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request).catch(() =>
                new Response(
                    JSON.stringify({ success: false, error: 'Network unavailable', items: [], count: 0, cart_count: 0 }),
                    { status: 200, headers: { 'Content-Type': 'application/json' } }
                )
            )
        );
        return;
    }

    // Static assets: cache-first, fall back to network.
    event.respondWith(
        caches.match(event.request).then(cached => {
            if (cached) return cached;
            return fetch(event.request).then(response => {
                if (response && response.status === 200) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                }
                return response;
            });
        })
    );
});
