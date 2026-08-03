(function(global){
  'use strict';
  const DB_NAME='jlpt-wisteria-db';
  const DB_VERSION=4;
  let dbPromise=null;
  function open(){
    if(dbPromise) return dbPromise;
    dbPromise=new Promise((resolve,reject)=>{
      const req=indexedDB.open(DB_NAME,DB_VERSION);
      req.onupgradeneeded=()=>{
        const db=req.result;
        if(!db.objectStoreNames.contains('notes')){
          const s=db.createObjectStore('notes',{keyPath:'id'});
          s.createIndex('createdAt','createdAt');s.createIndex('updatedAt','updatedAt');
          s.createIndex('lesson','lesson');s.createIndex('deckId','deckId');
        }
        if(!db.objectStoreNames.contains('cards')){
          const s=db.createObjectStore('cards',{keyPath:'id'});
          s.createIndex('due','due');s.createIndex('noteId','noteId');s.createIndex('deckId','deckId');
          s.createIndex('state','state');s.createIndex('suspended','suspended');s.createIndex('template','template');
        }
        if(!db.objectStoreNames.contains('reviews')){
          const s=db.createObjectStore('reviews',{keyPath:'id'});
          s.createIndex('cardId','cardId');s.createIndex('reviewedAt','reviewedAt');s.createIndex('noteId','noteId');
        }
        if(!db.objectStoreNames.contains('meta')) db.createObjectStore('meta',{keyPath:'key'});
        if(!db.objectStoreNames.contains('dictionary')){
          const s=db.createObjectStore('dictionary',{keyPath:'id'});
          s.createIndex('headword','headword');s.createIndex('reading','reading');s.createIndex('common','common');
        }
        if(!db.objectStoreNames.contains('dictionaryTerms')){
          const s=db.createObjectStore('dictionaryTerms',{keyPath:'key'});
          s.createIndex('term','term');s.createIndex('normalized','normalized');s.createIndex('entryId','entryId');
        }
      };
      req.onsuccess=()=>resolve(req.result);
      req.onerror=()=>reject(req.error);
      req.onblocked=()=>reject(new Error('数据库升级被其他标签页阻塞，请关闭旧页面后刷新。'));
    });
    return dbPromise;
  }
  async function tx(storeNames,mode,fn){
    const db=await open();
    const t=db.transaction(storeNames,mode);
    const stores=Array.isArray(storeNames)?Object.fromEntries(storeNames.map(n=>[n,t.objectStore(n)])):t.objectStore(storeNames);
    const value=await fn(stores,t);
    return new Promise((resolve,reject)=>{t.oncomplete=()=>resolve(value);t.onerror=()=>reject(t.error);t.onabort=()=>reject(t.error||new Error('事务已中止'));});
  }
  function reqP(req){return new Promise((resolve,reject)=>{req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);});}
  const api={
    open,
    get:(store,key)=>tx(store,'readonly',s=>reqP(s.get(key))),
    put:(store,value)=>tx(store,'readwrite',s=>reqP(s.put(value))),
    add:(store,value)=>tx(store,'readwrite',s=>reqP(s.add(value))),
    del:(store,key)=>tx(store,'readwrite',s=>reqP(s.delete(key))),
    clear:(store)=>tx(store,'readwrite',s=>reqP(s.clear())),
    all:(store)=>tx(store,'readonly',s=>reqP(s.getAll())),
    count:(store)=>tx(store,'readonly',s=>reqP(s.count())),
    getAllFromIndex:(store,index,query,count)=>tx(store,'readonly',s=>reqP(s.index(index).getAll(query,count))),
    cursor:async(store,index,range,direction,limit=Infinity)=>tx(store,'readonly',s=>new Promise((resolve,reject)=>{
      const out=[];const source=index?s.index(index):s;const req=source.openCursor(range,direction);
      req.onsuccess=()=>{const c=req.result;if(!c||out.length>=limit)return resolve(out);out.push(c.value);c.continue();};req.onerror=()=>reject(req.error);
    })),
    bulkPut:async(store,values,batchSize=500,onProgress)=>{
      const db=await open();
      for(let i=0;i<values.length;i+=batchSize){
        const batch=values.slice(i,i+batchSize);
        await new Promise((resolve,reject)=>{const t=db.transaction(store,'readwrite'),s=t.objectStore(store);batch.forEach(v=>s.put(v));t.oncomplete=resolve;t.onerror=()=>reject(t.error);t.onabort=()=>reject(t.error);});
        if(onProgress)onProgress(Math.min(values.length,i+batch.length),values.length);
        await new Promise(r=>setTimeout(r,0));
      }
    },
    exportStores:async(storeNames)=>{const out={};for(const n of storeNames)out[n]=await api.all(n);return out;},
    importStores:async(data,{replace=true}={})=>{for(const [name,rows] of Object.entries(data||{})){if(!Array.isArray(rows)||!['notes','cards','reviews','meta'].includes(name))continue;if(replace)await api.clear(name);await api.bulkPut(name,rows);}},
    estimate:()=>navigator.storage?.estimate?navigator.storage.estimate():Promise.resolve({usage:0,quota:0}),
    persist:()=>navigator.storage?.persist?navigator.storage.persist():Promise.resolve(false),
  };
  global.WisteriaDB=api;
})(window);
