const CACHE='jlpt-wisteria-v4.1.0';
const SHELL=[
  './','./index.html','./manifest.webmanifest',
  './assets/css/srs.css','./assets/js/db.js','./assets/js/fsrs6.js',
  './assets/js/dictionary.js','./assets/js/srs-app.js',
  './assets/icons/icon-192.png','./assets/icons/icon-512.png',
  './assets/icons/icon-192.svg','./assets/icons/icon-512.svg'
];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET')return;
  const url=new URL(event.request.url);
  if(url.hostname==='github.com'||url.pathname.endsWith('.tgz'))return;
  event.respondWith(caches.match(event.request).then(cached=>cached||fetch(event.request).then(response=>{
    if(response.ok&&url.origin===location.origin){const copy=response.clone();caches.open(CACHE).then(c=>c.put(event.request,copy));}
    return response;
  }).catch(()=>caches.match('./index.html'))));
});
