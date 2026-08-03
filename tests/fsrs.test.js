'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const context={window:{},console,Date,Math};context.window=context;
vm.createContext(context);
vm.runInContext(fs.readFileSync('assets/js/fsrs6.js','utf8'),context);
const F=context.WisteriaFSRS;
const DAY=86400000;
const minutes=(a,b)=>(new Date(a)-new Date(b))/60000;

assert(F,'FSRS global missing');
assert.strictEqual(F.VERSION,'FSRS-6');
assert.strictEqual(F.REFERENCE,'open-spaced-repetition/ts-fsrs 5.4.1');
assert.strictEqual(F.DEFAULT_WEIGHTS.length,21);
assert.strictEqual(F.validate(),true);

// Core FSRS invariants.
assert(Math.abs(F.retrievability(10,10,F.DEFAULT_WEIGHTS)-0.9)<1e-10);
assert.strictEqual(F.intervalFromStability(10,.9,F.DEFAULT_WEIGHTS),10);
assert(F.intervalFromStability(10,.8,F.DEFAULT_WEIGHTS)>F.intervalFromStability(10,.9,F.DEFAULT_WEIGHTS));
assert.throws(()=>F.validateWeights([1,2,3]),/21/);

const t0=new Date('2026-08-03T12:00:00Z');
let c=F.createCard(t0);

// Anki learning steps: Hard uses the midpoint on the first step, then repeats the current step.
let hardNew=F.schedule(c,F.Rating.Hard,t0,{learningSteps:[1,10],relearningSteps:[10]});
assert.strictEqual(minutes(hardNew.due,t0),6,'First-step Hard must average 1m and 10m');
let a=F.schedule(c,F.Rating.Good,t0,{learningSteps:[1,10],relearningSteps:[10]});
assert.strictEqual(a.state,F.State.Learning);
assert.strictEqual(minutes(a.due,t0),10);
let hardSecond=F.schedule(a,F.Rating.Hard,new Date(a.due),{learningSteps:[1,10],relearningSteps:[10]});
assert.strictEqual(minutes(hardSecond.due,a.due),10,'Hard on a later learning step must repeat that step');
assert.strictEqual(hardSecond.learningStep,1,'Hard must stay on the current learning step');

// Good at the final learning step graduates to Review.
let b=F.schedule(a,F.Rating.Good,new Date(a.due),{learningSteps:[1,10],relearningSteps:[10]});
assert.strictEqual(b.state,F.State.Review);
assert(b.scheduledDays>=1);

// Review outcomes must remain strictly ordered.
let late=new Date(new Date(b.due).getTime()+DAY*2);
const p=F.preview(b,late,{learningSteps:[1,10],relearningSteps:[10]});
assert(new Date(p[1].due)<new Date(p[2].due),'Again must precede Hard');
assert(p[2].scheduledDays<p[3].scheduledDays,'Hard interval must be shorter than Good');
assert(p[3].scheduledDays<p[4].scheduledDays,'Good interval must be shorter than Easy');

// A lapse enters relearning and is counted once, not on every repeated learning failure.
let fail=F.schedule(b,F.Rating.Again,late,{relearningSteps:[10]});
assert.strictEqual(fail.state,F.State.Relearning);
assert.strictEqual(fail.lapses,1);
assert.strictEqual(minutes(fail.due,late),10);
let failAgain=F.schedule(fail,F.Rating.Again,new Date(fail.due),{relearningSteps:[10]});
assert.strictEqual(failAgain.lapses,1,'Repeated Again inside relearning must not double-count lapses');

// FSRS short-term behavior uses calendar-day elapsed time. Hard is a remembered answer.
const sameDay={...b,state:F.State.Review,stability:4,difficulty:5,lastReview:'2026-08-03T00:01:00Z',due:'2026-08-03T00:01:00Z'};
const sameDayHard=F.schedule(sameDay,F.Rating.Hard,new Date('2026-08-03T23:59:00Z'));
assert.strictEqual(sameDayHard.elapsedDays,0);
assert(sameDayHard.stability>=sameDay.stability,'Same-day Hard must not reduce stability');
const nextDayHard=F.schedule(sameDay,F.Rating.Hard,new Date('2026-08-04T00:01:00Z'));
assert.strictEqual(nextDayHard.elapsedDays,1,'Elapsed days must use UTC calendar days with UTC calendar-day handling');

// New-card initial stability follows the 21 official defaults.
const initial=[1,2,3,4].map(r=>F.schedule(F.createCard(t0),r,t0).stability);
const expected=[0.212,1.2931,2.3065,8.2956];
initial.forEach((v,i)=>assert(Math.abs(v-expected[i])<1e-8));

for(const r of [1,2,3,4]){
  assert(Number.isFinite(p[r].stability)&&p[r].stability>0&&p[r].stability<=36500);
  assert(Number.isFinite(p[r].difficulty)&&p[r].difficulty>=1&&p[r].difficulty<=10);
  assert(Number.isFinite(new Date(p[r].due).getTime()));
}

// Property-style stress test: no NaN, illegal state, negative stability, or backwards due dates.
let seed=0x5f3759df;
const random=()=>{seed=(1664525*seed+1013904223)>>>0;return seed/4294967296;};
for(let run=0;run<200;run++){
  let card=F.createCard(new Date(t0.getTime()+run*60000));
  let when=new Date(card.due);
  for(let i=0;i<160;i++){
    const rating=1+Math.floor(random()*4);
    when=new Date(Math.max(when.getTime(),new Date(card.due).getTime()));
    card=F.schedule(card,rating,when,{learningSteps:[1,10],relearningSteps:[10],requestRetention:.9,enableFuzz:false});
    assert([0,1,2,3].includes(card.state));
    assert(Number.isFinite(card.stability)&&card.stability>0&&card.stability<=36500);
    assert(Number.isFinite(card.difficulty)&&card.difficulty>=1&&card.difficulty<=10);
    assert(new Date(card.due)>=when,'Due date must not move backwards');
    const jump=card.state===F.State.Review?Math.floor(random()*Math.max(1,card.scheduledDays+8)):0;
    when=new Date(new Date(card.due).getTime()+jump*DAY);
  }
}

console.log('FSRS TESTS PASSED');
