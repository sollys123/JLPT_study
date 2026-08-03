(function(global){
  'use strict';
  const DB=global.WisteriaDB;
  const RELEASE='3.6.2+20260727141257';
  const CONFIG={
    common:{label:'JMdict English 常用词库',local:`data/jmdict-eng-common-${RELEASE}.json.tgz`,remote:`https://github.com/scriptin/jmdict-simplified/releases/download/3.6.2%2B20260727141257/jmdict-eng-common-${RELEASE}.json.tgz`,compressedMB:1.37,examples:false,sha256:'a7f9e1f6fd14ff361fa86fbeafa2261ee215c6ffff7e4b2625df26b7fba47173'},
    examples:{label:'JMdict English 完整例句词库',local:`data/jmdict-examples-eng-${RELEASE}.json.tgz`,remote:`https://github.com/scriptin/jmdict-simplified/releases/download/3.6.2%2B20260727141257/jmdict-examples-eng-${RELEASE}.json.tgz`,compressedMB:13.4,examples:true,sha256:'508d41af24121624d69b2cf35aa9e5dc214a3272c529f688518c1025bf870f11'}
  };
  const enc=new TextDecoder('utf-8');
  const norm=s=>String(s||'').normalize('NFKC').trim().toLowerCase();
  async function sha256Hex(buffer){if(!global.crypto?.subtle)return null;const hash=await global.crypto.subtle.digest('SHA-256',buffer);return [...new Uint8Array(hash)].map(x=>x.toString(16).padStart(2,'0')).join('');}
  async function verifySha256(buffer,expected,onProgress){if(!expected)return null;onProgress?.('校验 SHA-256…',18);const actual=await sha256Hex(buffer);if(actual&&actual.toLowerCase()!==expected.toLowerCase())throw new Error(`词典校验失败：SHA-256 不匹配。实际 ${actual}`);return actual;}
  function tarExtract(buffer){
    const u8=new Uint8Array(buffer),files=[];let off=0;
    while(off+512<=u8.length){
      const header=u8.slice(off,off+512);if(header.every(b=>b===0))break;
      const name=enc.decode(header.slice(0,100)).replace(/\0.*$/,'');
      const sizeText=enc.decode(header.slice(124,136)).replace(/\0.*$/,'').trim();const size=parseInt(sizeText,8)||0;
      const start=off+512,end=start+size;if(end>u8.length)throw new Error('TAR 文件不完整');
      files.push({name,data:u8.slice(start,end)});off=start+Math.ceil(size/512)*512;
    }
    return files;
  }
  async function ungzip(buffer){
    if(typeof DecompressionStream==='undefined')throw new Error('当前浏览器不支持直接解压 .tgz，请先在电脑上解压为 .json 再导入。');
    const stream=new Blob([buffer]).stream().pipeThrough(new DecompressionStream('gzip'));
    return await new Response(stream).arrayBuffer();
  }
  async function fileToJson(file,onProgress){
    const name=(file.name||'').toLowerCase();onProgress?.('读取文件…',5);
    let buffer=await file.arrayBuffer();
    if(name.endsWith('.tgz')||name.endsWith('.tar.gz')){onProgress?.('解压词典…',12);buffer=await ungzip(buffer);const files=tarExtract(buffer);const f=files.find(x=>x.name.endsWith('.json'));if(!f)throw new Error('压缩包内没有 JSON 文件');buffer=f.data.buffer.slice(f.data.byteOffset,f.data.byteOffset+f.data.byteLength);}
    else if(name.endsWith('.gz'))buffer=await ungzip(buffer);
    onProgress?.('解析 JSON…',20);return JSON.parse(enc.decode(buffer));
  }
  function collectExampleStrings(node,out=[]){
    if(node==null)return out;
    if(typeof node==='string'){if(node.trim())out.push(node.trim());return out;}
    if(Array.isArray(node)){node.forEach(x=>collectExampleStrings(x,out));return out;}
    if(typeof node==='object'){
      for(const [k,v] of Object.entries(node)){
        if(['source','id','type','tags','appliesToKanji','appliesToKana'].includes(k))continue;
        collectExampleStrings(v,out);
      }
    }
    return out;
  }
  const hasJP=s=>/[\u3040-\u30ff\u3400-\u9fff]/.test(s);
  const hasLatin=s=>/[A-Za-z]/.test(s);
  function extractExamples(sense){
    const source=sense.examples||sense.example||sense.sentences||[];
    const out=[];
    const push=(jp,en,sourceId='')=>{
      jp=String(jp||'').trim();en=String(en||'').trim();
      if(!jp&&!en)return;
      if(out.some(x=>x.jp===jp&&x.en===en))return;
      out.push({jp,en,sourceId});
    };
    for(const ex of Array.isArray(source)?source:[]){
      if(!ex)continue;
      if(typeof ex==='string'){if(hasJP(ex))push(ex,'');continue;}
      if(typeof ex!=='object')continue;
      // jmdict-simplified WordWithExamples:
      // { text: <surface form>, sentences: [{lang:'jpn',text:'完整句'}, {lang:'eng',text:'translation'}] }
      // `text` is deliberately not used as the sentence.
      if(Array.isArray(ex.sentences)){
        const pick=(langs)=>ex.sentences.find(x=>x&&langs.includes(String(x.lang||'').toLowerCase())&&x.text)?.text||'';
        const jp=pick(['jpn','ja','jp']);
        const en=pick(['eng','en']);
        const id=ex.source?.value||ex.source?.id||'';
        push(jp,en,id);
        continue;
      }
      // Friendly fallback for manually imported or older fixture shapes.
      const jp=ex.japanese||ex.jp||ex.sentenceJP||ex.textJP||'';
      const en=ex.english||ex.en||ex.translation||ex.sentenceEN||ex.textEN||'';
      if(jp||en){push(jp,en,ex.id||'');continue;}
      const strings=collectExampleStrings(ex);
      push(strings.find(hasJP)||'',strings.find(hasLatin)||'');
    }
    return out.slice(0,6);
  }
  function normalizeWord(w,tags={}){
    const spellings=(w.kanji||[]).map(x=>({text:x.text,common:!!x.common,tags:x.tags||[]}));
    const readings=(w.kana||[]).map(x=>({text:x.text,common:!!x.common,tags:x.tags||[],appliesToKanji:x.appliesToKanji||['*']}));
    const headword=(spellings.find(x=>x.common)||spellings[0]||readings.find(x=>x.common)||readings[0]||{}).text||'';
    const reading=(readings.find(x=>x.common)||readings[0]||{}).text||'';
    const senses=(w.sense||w.senses||[]).map((s,i)=>({
      index:i+1,
      glosses:(s.gloss||[]).filter(g=>!g.lang||g.lang==='eng').map(g=>typeof g==='string'?g:g.text).filter(Boolean),
      pos:(s.partOfSpeech||[]).map(p=>tags[p]||p),
      misc:(s.misc||[]).map(p=>tags[p]||p),
      field:(s.field||[]).map(p=>tags[p]||p),
      info:s.info||[],
      appliesToKanji:s.appliesToKanji||['*'],appliesToKana:s.appliesToKana||['*'],
      examples:extractExamples(s)
    })).filter(s=>s.glosses.length||s.examples.length);
    return {id:String(w.id),headword,reading,spellings,readings,common:[...spellings,...readings].some(x=>x.common),senses};
  }
  function termRows(entry){const vals=[];for(const x of entry.spellings||[])vals.push({term:x.text,type:'spelling',common:x.common});for(const x of entry.readings||[])vals.push({term:x.text,type:'reading',common:x.common});return [...new Map(vals.filter(x=>x.term).map(x=>[x.term,x])).values()].map(x=>({key:`${norm(x.term)}\u0000${entry.id}\u0000${x.type}`,term:x.term,normalized:norm(x.term),entryId:entry.id,type:x.type,common:!!x.common}));}
  async function installJson(json,{kind='custom',source='local',onProgress}={}){
    if(!json||!Array.isArray(json.words)||!json.words.length)throw new Error('这不是可识别的 jmdict-simplified JSON');
    await DB.put('meta',{key:'dictionaryInstallState',status:'installing',kind,source,startedAt:new Date().toISOString(),count:json.words.length});
    await DB.clear('dictionary');await DB.clear('dictionaryTerms');await DB.del('meta','dictionaryMeta');
    const tags=json.tags||{},total=json.words.length,batchSize=500;
    try{
      for(let i=0;i<total;i+=batchSize){
        const slice=json.words.slice(i,i+batchSize),entries=slice.map(w=>normalizeWord(w,tags)).filter(x=>x.headword||x.reading),terms=entries.flatMap(termRows);
        await DB.bulkPut('dictionary',entries,500);await DB.bulkPut('dictionaryTerms',terms,1000);
        const pct=25+Math.round((i+slice.length)/total*70);onProgress?.(`建立本地索引 ${Math.min(total,i+slice.length).toLocaleString()} / ${total.toLocaleString()}`,pct);
      }
      const meta={key:'dictionaryMeta',kind,source,installedAt:new Date().toISOString(),version:json.version||'',dictDate:json.dictDate||'',count:total,commonOnly:!!json.commonOnly,languages:json.languages||[],license:'JMdict / EDRDG, CC BY-SA 4.0'};
      await DB.put('meta',meta);await DB.del('meta','dictionaryInstallState');onProgress?.('词典安装完成',100);return meta;
    }catch(error){
      await DB.clear('dictionary');await DB.clear('dictionaryTerms');await DB.del('meta','dictionaryMeta');
      await DB.put('meta',{key:'dictionaryInstallState',status:'failed',kind,source,failedAt:new Date().toISOString(),message:String(error?.message||error)});
      throw error;
    }
  }
  async function fetchWithFallback(kind,onProgress){const c=CONFIG[kind];if(!c)throw new Error('未知词典类型');let response;
    for(const url of [c.local,c.remote]){try{onProgress?.(`下载 ${c.label}…`,5);response=await fetch(url);if(response.ok)break;}catch(e){response=null;}}
    if(!response||!response.ok)throw new Error('下载失败。可将词典 .tgz 放入 data/ 目录，或使用“导入本地词典”。');
    const buffer=await response.arrayBuffer();await verifySha256(buffer,c.sha256,onProgress);const file=new File([buffer],c.local.split('/').pop(),{type:response.headers.get('content-type')||'application/gzip'});const json=await fileToJson(file,onProgress);return installJson(json,{kind,source:response.url,onProgress});
  }
  async function importFile(file,onProgress){const matched=Object.values(CONFIG).find(c=>c.local.endsWith(file.name));if(matched)await verifySha256(await file.arrayBuffer(),matched.sha256,onProgress);const json=await fileToJson(file,onProgress);return installJson(json,{kind:matched?(matched.examples?'examples':'common'):'custom',source:file.name,onProgress});}
  async function search(query,{limit=24,prefix=true}={}){
    const q=norm(query);if(!q)return [];
    const exact=await DB.getAllFromIndex('dictionaryTerms','normalized',IDBKeyRange.only(q),100);
    let rows=[...exact];
    if(prefix&&rows.length<limit){const hi=q+'\uffff';const more=await DB.cursor('dictionaryTerms','normalized',IDBKeyRange.bound(q,hi),'next',limit*8);const seen=new Set(rows.map(x=>x.key));for(const r of more)if(!seen.has(r.key)){rows.push(r);seen.add(r.key);}}
    rows.sort((a,b)=>(b.common-a.common)||a.term.length-b.term.length);const ids=[...new Set(rows.slice(0,limit*2).map(x=>x.entryId))];const entries=[];for(const id of ids){const e=await DB.get('dictionary',id);if(e)entries.push(e);if(entries.length>=limit)break;}return entries;
  }
  async function meta(){return DB.get('meta','dictionaryMeta');}
  async function clear(){await DB.clear('dictionary');await DB.clear('dictionaryTerms');await DB.del('meta','dictionaryMeta');}
  global.WisteriaDictionary={CONFIG,RELEASE,installJson,fetchWithFallback,importFile,search,meta,clear,normalizeWord,tarExtract,ungzip,sha256Hex,verifySha256};
})(window);
