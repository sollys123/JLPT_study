'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const context={window:{WisteriaDB:{}},console,TextDecoder,Blob,Response,File:global.File,DecompressionStream:global.DecompressionStream,IDBKeyRange:{}};context.window=context;
vm.createContext(context);
vm.runInContext(fs.readFileSync('assets/js/dictionary.js','utf8'),context);
const D=context.WisteriaDictionary;assert(D);
const entry=D.normalizeWord({id:'1001',kanji:[{text:'食べる',common:true,tags:[]}],kana:[{text:'たべる',common:true,tags:[],appliesToKanji:['*']}],sense:[{gloss:[{lang:'eng',text:'to eat'}],partOfSpeech:['v1'],misc:[],field:[],info:[],examples:[{japanese:'朝ご飯を食べました。',english:'I ate breakfast.'}]}]},{v1:'Ichidan verb'});
assert.strictEqual(entry.headword,'食べる');assert.strictEqual(entry.reading,'たべる');assert.strictEqual(entry.common,true);assert.strictEqual(entry.senses[0].glosses[0],'to eat');assert.strictEqual(entry.senses[0].pos[0],'Ichidan verb');

// Real jmdict-simplified WordWithExamples shape: ex.text is only the matched surface form.
const actualShape={id:'1002',kanji:[{text:'食べる',common:true,tags:[]}],kana:[{text:'たべる',common:true,tags:[],appliesToKanji:['*']}],sense:[{gloss:[{lang:'eng',text:'to eat'}],partOfSpeech:['v1'],misc:[],field:[],info:[],examples:[{source:{type:'tatoeba',value:'123'},text:'食べる',sentences:[{lang:'jpn',text:'私は毎朝パンを食べます。'},{lang:'eng',text:'I eat bread every morning.'}]}]}]};
const normalizedActual=D.normalizeWord(actualShape,{v1:'Ichidan verb'});
assert.strictEqual(normalizedActual.senses[0].examples[0].jp,'私は毎朝パンを食べます。');
assert.strictEqual(normalizedActual.senses[0].examples[0].en,'I eat bread every morning.');
assert.notStrictEqual(normalizedActual.senses[0].examples[0].jp,'食べる','Surface form must not be mistaken for a full example sentence');

console.log('DICTIONARY TESTS PASSED');
