const CACHE_NAME = 'parish-mkw-v1';
const offlineFallbackPage = '/static/offline.html';  // Ensure it matches the new location

const urlsToCache = [
  '/',
  '/static/images/church.png',
  '/static/css/style.css',
  '/static/js/main.js',
  offlineFallbackPage
];

// Install Service Worker & Cache Resources
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('✅ Caching resources...');
        return cache.addAll(urlsToCache);
      })
  );
  self.skipWaiting();
});

// Activate Service Worker
self.addEventListener('activate', event => {
  console.log('✅ Service Worker activated.');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cache => {
          if (cache !== CACHE_NAME) {
            console.log('🗑️ Removing old cache:', cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Fetch Cached Files First, Then Network
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        return response || fetch(event.request);
      })
      .catch(() => {
        return caches.match(offlineFallbackPage);
      })
  );
});
