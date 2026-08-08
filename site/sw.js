const CACHE = "ai-pm-v2";
const ASSETS = ["./", "./index.html", "./learn.html", "./quiz.html", "./cases.html", "./progress.html", "./manifest.webmanifest", "./assets/app.js", "./assets/style.css"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
});
self.addEventListener("fetch", e => {
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
