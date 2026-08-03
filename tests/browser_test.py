from __future__ import annotations
import json, re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'index.html').read_text(encoding='utf-8')
css=(ROOT/'assets/css/srs.css').read_text(encoding='utf-8')
fsrs=(ROOT/'assets/js/fsrs6.js').read_text(encoding='utf-8')
dictionary=(ROOT/'assets/js/dictionary.js').read_text(encoding='utf-8')
srs=(ROOT/'assets/js/srs-app.js').read_text(encoding='utf-8')

memory_db=r"""
(function(global){
 const names=['notes','cards','reviews','meta','dictionary','dictionaryTerms'];
 const stores=Object.fromEntries(names.map(n=>[n,new Map()]));
 const keyOf=(name,v)=>name==='meta'?v.key:name==='dictionaryTerms'?v.key:v.id;
 const clone=v=>v==null?v:structuredClone(v);
 const match=(v,q)=>{if(q==null)return true;if(q.kind==='only')return v===q.value;if(q.kind==='bound')return v>=q.lower&&v<=q.upper;return v===q;};
 global.IDBKeyRange={only:value=>({kind:'only',value}),bound:(lower,upper)=>({kind:'bound',lower,upper})};
 global.WisteriaDB={
  open:async()=>true,persist:async()=>true,estimate:async()=>({usage:0,quota:1}),
  get:async(n,k)=>clone(stores[n].get(k)),put:async(n,v)=>{stores[n].set(keyOf(n,v),clone(v));return keyOf(n,v)},add:async(n,v)=>{stores[n].set(keyOf(n,v),clone(v));return keyOf(n,v)},
  del:async(n,k)=>stores[n].delete(k),clear:async n=>stores[n].clear(),all:async n=>[...stores[n].values()].map(clone),count:async n=>stores[n].size,
  getAllFromIndex:async(n,idx,q,count)=>[...stores[n].values()].filter(x=>match(x[idx],q)).slice(0,count||Infinity).map(clone),
  cursor:async(n,idx,q,dir,limit)=>[...stores[n].values()].filter(x=>match(x[idx],q)).sort((a,b)=>String(a[idx]).localeCompare(String(b[idx]))).slice(0,limit||Infinity).map(clone),
  bulkPut:async(n,vals)=>{for(const v of vals)stores[n].set(keyOf(n,v),clone(v))},
  exportStores:async ns=>Object.fromEntries(await Promise.all(ns.map(async n=>[n,[...stores[n].values()].map(clone)]))),
  importStores:async(data,{replace=true}={})=>{for(const [n,vals] of Object.entries(data||{})){if(!stores[n]||!Array.isArray(vals))continue;if(replace)stores[n].clear();for(const v of vals)stores[n].set(keyOf(n,v),clone(v));}},
  _stores:stores
 };
})(window);
"""
html=html.replace('<link rel="stylesheet" href="assets/css/srs.css">',f'<style>{css}</style>')
html=html.replace('<script src="assets/js/db.js"></script>',f'<script>{memory_db}</script>')
html=html.replace('<script src="assets/js/fsrs6.js"></script>',f'<script>{fsrs}</script>')
html=html.replace('<script src="assets/js/dictionary.js"></script>',f'<script>{dictionary}</script>')
html=html.replace('<script src="assets/js/srs-app.js"></script>',f'<script>{srs}</script>')
html=re.sub(r"<script>if\('serviceWorker'[\s\S]*?</script>","",html)
errors=[]
polyfill="""
(() => {
 const store={};
 Object.defineProperty(window,'localStorage',{value:{getItem:k=>Object.hasOwn(store,k)?store[k]:null,setItem:(k,v)=>store[k]=String(v),removeItem:k=>delete store[k],clear:()=>Object.keys(store).forEach(k=>delete store[k])},configurable:true});
})();
"""
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
    page=context.new_page();page.add_init_script(polyfill)
    page.on('console',lambda msg: errors.append(f'console:{msg.type}:{msg.text}') if msg.type=='error' else None)
    page.on('pageerror',lambda exc: errors.append(f'pageerror:{exc}'))
    page.set_content(html,wait_until='load');page.wait_for_function('window.__JLPT_APP__ && window.__WISTERIA_SRS__');page.wait_for_timeout(350)
    if page.locator('#welcomeClose').count() and page.locator('#welcomeClose').is_visible(): page.locator('#welcomeClose').click()
    assert page.title()=='JLPT 紫藤学习系统'
    assert page.evaluate('PLAN_DATA.schedule.length')==336
    assert page.evaluate("PLAN_DATA.schedule.find(x=>x.date==='2026-10-01').mode")=='travel'
    assert page.evaluate("PLAN_DATA.lessons.find(x=>x.number===29).scheduledDate")=='2026-10-12'
    page.evaluate("window.__JLPT_APP__.selectDate('2026-10-01')")
    assert page.evaluate("window.__JLPT_APP__.backlogForDate('2026-10-01').items.length")==0
    assert '旅行模式' in page.locator('#todayLoadText').inner_text()

    fixture={'version':'test','dictDate':'2026-08-03','commonOnly':True,'languages':['eng'],'tags':{'v1':'Ichidan verb','vt':'transitive verb'},'words':[{'id':'1001','kanji':[{'text':'食べる','common':True,'tags':[]}],'kana':[{'text':'たべる','common':True,'tags':[],'appliesToKanji':['*']}],'sense':[{'gloss':[{'lang':'eng','text':'to eat'}],'partOfSpeech':['v1','vt'],'misc':[],'field':[],'info':[],'examples':[{'japanese':'朝ご飯を食べました。','english':'I ate breakfast.'}]}]}]}
    page.evaluate("fixture=>window.WisteriaDictionary.installJson(fixture,{kind:'test',source:'browser-test'})",fixture)
    page.locator('[data-view="vocab"]').first.click();page.locator('[data-srs-tab="dictionary"]').click()
    page.locator('#dictQuery').fill('食べる');page.locator('#dictSearch').click();page.wait_for_selector('[data-use-entry]')
    assert 'to eat' in page.locator('#dictResults').inner_text();page.locator('[data-use-entry]').first.click()
    assert page.locator('#noteTerm').input_value()=='食べる';assert page.locator('#noteReading').input_value()=='たべる'
    page.locator('#noteChinese').fill('吃；进食')
    for val in ['recall','reading','cloze','audio']:page.locator(f'[name="noteTemplate"][value="{val}"]').check()
    page.locator('#noteSave').click();page.wait_for_timeout(200)
    assert page.evaluate("window.WisteriaDB.count('notes')")==1;assert page.evaluate("window.WisteriaDB.count('cards')")==5
    if not page.locator('#srsReveal').is_hidden():page.locator('#srsReveal').click()
    page.locator('[data-rating="3"]').click();page.wait_for_timeout(200)
    assert page.evaluate("window.WisteriaDB.count('reviews')")==1
    rev=page.evaluate("window.WisteriaDB.all('reviews').then(x=>x[0])");assert rev['algorithm']=='FSRS-6';assert rev['after']['state'] in [1,2];assert rev['durationMs']>=0
    page.locator('[data-srs-tab="browser"]').click();page.wait_for_timeout(100)
    page.locator(f'[data-history-card="{rev["cardId"]}"]').click();assert '1次评分' in page.locator('#srsHistorySummary').inner_text();page.locator('#srsHistoryClose').click()

    page.locator('[data-srs-tab="settings"]').click();page.locator('#srsDiagnostics').click();page.wait_for_timeout(100)
    assert '诊断通过' in page.locator('#srsDiagnosticText').inner_text()
    with page.expect_download() as info:page.locator('#srsExportAll').click()
    dest=ROOT/'tests'/'_backup_test.json';info.value.save_as(dest);data=json.loads(dest.read_text(encoding='utf-8'))
    assert data['formatVersion']==3 and not any(x.get('key')=='dictionaryMeta' for x in data['srs']['meta']);dest.unlink()
    page.screenshot(path=str(ROOT/'tests'/'desktop.png'),full_page=True)

    mobile=context.new_page();mobile.add_init_script(polyfill);mobile.set_content(html,wait_until='load');mobile.wait_for_function('window.__WISTERIA_SRS__');mobile.wait_for_timeout(350)
    if mobile.locator('#welcomeClose').count():mobile.locator('#welcomeClose').click(force=True)
    if mobile.locator('#modal.open').count():mobile.locator('#modalClose').click(force=True)
    mobile.set_viewport_size({'width':390,'height':844});mobile.locator('#menuBtn').click();mobile.locator('[data-view="vocab"]').first.click();mobile.wait_for_timeout(350)
    assert not mobile.locator('#sidebar').evaluate("el=>el.classList.contains('open')")
    mobile.screenshot(path=str(ROOT/'tests'/'mobile.png'),full_page=True);assert mobile.locator('#advancedSrsRoot').count()==1
    browser.close()
print('BROWSER ERRORS',errors)
if errors:raise SystemExit('\n'.join(errors))
print('BROWSER TESTS PASSED')
