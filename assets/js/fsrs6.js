(function(global){
  'use strict';

  // FSRS-6 browser core using the public 21-parameter model and defaults.
  // Learning/relearning transitions follow the current Anki manual. The app keeps
  // the scheduler local so GitHub Pages continues to work offline.
  const W=Object.freeze([
    0.212,1.2931,2.3065,8.2956,6.4133,0.8334,3.0194,0.001,
    1.8722,0.1666,0.796,1.4835,0.0614,0.2629,1.6483,0.6014,
    1.8729,0.5425,0.0912,0.0658,0.1542
  ]);
  const Rating=Object.freeze({Again:1,Hard:2,Good:3,Easy:4});
  const State=Object.freeze({New:0,Learning:1,Review:2,Relearning:3});
  const DAY=86400000;
  const S_MIN=0.001;
  const S_MAX=36500;

  const clamp=(x,a,b)=>Math.min(Math.max(x,a),b);
  const round8=x=>Math.round(x*1e8)/1e8;
  const addMinutes=(d,m)=>new Date(new Date(d).getTime()+m*60000);
  const addDays=(d,n)=>new Date(new Date(d).getTime()+n*DAY);

  function dateDiffInDays(last,current){
    if(!last||!current)return 0;
    const a=new Date(last),b=new Date(current);
    const utcA=Date.UTC(a.getUTCFullYear(),a.getUTCMonth(),a.getUTCDate());
    const utcB=Date.UTC(b.getUTCFullYear(),b.getUTCMonth(),b.getUTCDate());
    return Math.max(0,Math.floor((utcB-utcA)/DAY));
  }

  function validateRetention(value){
    if(!Number.isFinite(value)||value<=0||value>1)throw new Error('目标记忆率必须在 0 与 1 之间');
    return value;
  }

  function validateWeights(weights){
    if(!Array.isArray(weights)||weights.length!==21||weights.some(x=>!Number.isFinite(x)))throw new Error('FSRS-6 参数必须是 21 个有限数字');
    const ranges=[
      [S_MIN,100],[S_MIN,100],[S_MIN,100],[S_MIN,100],[1,10],[0.001,4],[0.001,4],[0.001,0.75],
      [0,4.5],[0,0.8],[0.001,3.5],[0.001,5],[0.001,0.25],[0.001,0.9],[0,4],
      [0,1],[1,6],[0,2],[0,2],[0.01,0.8],[0.1,0.8]
    ];
    weights.forEach((v,i)=>{if(v<ranges[i][0]||v>ranges[i][1])throw new Error(`FSRS 参数 w${i} 超出安全范围`);});
    return true;
  }

  function defaults(overrides={}){
    const out={
      requestRetention:.9,
      maxInterval:36500,
      learningSteps:[1,10],
      relearningSteps:[10],
      enableFuzz:false,
      enableShortTerm:true,
      weights:[...W],
      ...overrides
    };
    validateRetention(out.requestRetention);
    validateWeights(out.weights);
    out.maxInterval=clamp(Math.round(Number(out.maxInterval)||36500),1,36500);
    return out;
  }

  function createCard(now=new Date()){
    return {
      state:State.New,
      due:new Date(now).toISOString(),
      stability:0,
      difficulty:0,
      elapsedDays:0,
      scheduledDays:0,
      reps:0,
      lapses:0,
      learningStep:0,
      lastReview:null
    };
  }

  function decayFactor(w=W){
    const decay=-w[20];
    const factor=Math.exp(Math.log(.9)/decay)-1;
    return {decay,factor:round8(factor)};
  }

  function retrievability(stability,elapsedDays,w=W){
    if(!Number.isFinite(stability)||stability<S_MIN)return 0;
    const {decay,factor}=decayFactor(w);
    return round8(Math.pow(1+factor*Math.max(0,elapsedDays)/stability,decay));
  }

  function intervalModifier(retention=.9,w=W){
    validateRetention(retention);
    const {decay,factor}=decayFactor(w);
    return round8((Math.pow(retention,1/decay)-1)/factor);
  }

  function intervalFromStability(stability,retention=.9,w=W,maxInterval=36500){
    return clamp(Math.round(stability*intervalModifier(retention,w)),1,maxInterval);
  }

  function initialStability(rating,w=W){
    return Math.max(w[rating-1],.1);
  }

  function initialDifficulty(rating,w=W){
    const value=w[4]-Math.exp((rating-1)*w[5])+1;
    return clamp(round8(value),1,10);
  }

  function meanReversion(initial,current,w=W){
    return round8(w[7]*initial+(1-w[7])*current);
  }

  function nextDifficulty(difficulty,rating,w=W){
    const delta=-w[6]*(rating-3);
    const next=difficulty+round8(delta*(10-difficulty)/9);
    return clamp(meanReversion(initialDifficulty(Rating.Easy,w),next,w),1,10);
  }

  function nextRecallStability(difficulty,stability,rating,R,w=W){
    const hardPenalty=rating===Rating.Hard?w[15]:1;
    const easyBonus=rating===Rating.Easy?w[16]:1;
    const value=stability*(1+
      Math.exp(w[8])*(11-difficulty)*Math.pow(stability,-w[9])*
      (Math.exp((1-R)*w[10])-1)*hardPenalty*easyBonus
    );
    return round8(clamp(value,S_MIN,S_MAX));
  }

  function rawForgetStability(difficulty,stability,R,w=W){
    const value=w[11]*Math.pow(difficulty,-w[12])*
      (Math.pow(stability+1,w[13])-1)*Math.exp((1-R)*w[14]);
    return round8(clamp(value,S_MIN,S_MAX));
  }

  function nextForgetStability(difficulty,stability,R,w=W,enableShortTerm=true){
    const afterFail=rawForgetStability(difficulty,stability,R,w);
    const w17=enableShortTerm?w[17]:0;
    const w18=enableShortTerm?w[18]:0;
    const upper=Math.max(S_MIN,round8(stability/Math.exp(w17*w18)));
    return round8(clamp(afterFail,S_MIN,upper));
  }

  function nextShortTermStability(stability,rating,w=W){
    const increment=Math.pow(stability,-w[19])*Math.exp(w[17]*(rating-3+w[18]));
    // FSRS treats Hard as a successful recall. It must not shrink stability.
    const masked=rating>=Rating.Hard?Math.max(increment,1):increment;
    return round8(clamp(stability*masked,S_MIN,S_MAX));
  }

  function memoryUpdate(card,rating,now,settings){
    const w=settings.weights;
    const elapsed=card.state===State.New?0:dateDiffInDays(card.lastReview||card.due,now);
    let stability=Number(card.stability)||0;
    let difficulty=Number(card.difficulty)||0;

    if(card.state===State.New||(difficulty===0&&stability===0)){
      stability=initialStability(rating,w);
      difficulty=initialDifficulty(rating,w);
    }else{
      const R=retrievability(stability,elapsed,w);
      if(elapsed===0&&settings.enableShortTerm){
        stability=nextShortTermStability(stability,rating,w);
      }else if(rating===Rating.Again){
        stability=nextForgetStability(difficulty,stability,R,w,settings.enableShortTerm);
      }else{
        stability=nextRecallStability(difficulty,stability,rating,R,w);
      }
      difficulty=nextDifficulty(difficulty,rating,w);
    }
    return {stability:round8(stability),difficulty:round8(difficulty),elapsedDays:elapsed};
  }

  function hardLearningMinutes(steps){
    if(!steps.length)return 0;
    if(steps.length===1)return Math.round(steps[0]*1.5);
    return Math.round((steps[0]+steps[1])/2);
  }

  function learningOutcome(card,rating,steps){
    const current=Math.max(0,Number(card.learningStep)||0);
    if(!steps.length||current>=steps.length)return {minutes:0,nextStep:0};
    if(rating===Rating.Again)return {minutes:steps[0],nextStep:0};
    if(rating===Rating.Hard){
      // Anki: first learning step uses the midpoint of the first two steps;
      // later learning steps repeat the current step.
      const minutes=current===0?hardLearningMinutes(steps):steps[current];
      return {minutes,nextStep:current};
    }
    if(rating===Rating.Good&&steps[current+1]!=null)return {minutes:steps[current+1],nextStep:current+1};
    return {minutes:0,nextStep:0};
  }

  function fuzzRange(interval,elapsed,maxInterval){
    const ranges=[{start:2.5,end:7,factor:.15},{start:7,end:20,factor:.1},{start:20,end:Infinity,factor:.05}];
    let delta=1;
    for(const range of ranges)delta+=range.factor*Math.max(Math.min(interval,range.end)-range.start,0);
    interval=Math.min(interval,maxInterval);
    let min=Math.max(2,Math.round(interval-delta));
    const max=Math.min(Math.round(interval+delta),maxInterval);
    if(interval>elapsed)min=Math.max(min,elapsed+1);
    return {min:Math.min(min,max),max};
  }

  function maybeFuzz(days,elapsed,settings){
    if(!settings.enableFuzz||days<2.5)return Math.round(days);
    const {min,max}=fuzzRange(days,elapsed,settings.maxInterval);
    return Math.floor(Math.random()*(max-min+1)+min);
  }

  function reviewIntervals(card,now,settings){
    const results={};
    for(const rating of [Rating.Hard,Rating.Good,Rating.Easy]){
      const memory=memoryUpdate(card,rating,now,settings);
      results[rating]={memory,days:maybeFuzz(intervalFromStability(memory.stability,settings.requestRetention,settings.weights,settings.maxInterval),memory.elapsedDays,settings)};
    }
    results[Rating.Hard].days=Math.min(results[Rating.Hard].days,results[Rating.Good].days);
    results[Rating.Good].days=Math.max(results[Rating.Good].days,results[Rating.Hard].days+1);
    results[Rating.Easy].days=Math.max(results[Rating.Easy].days,results[Rating.Good].days+1);
    return results;
  }

  function graduate(next,now,settings){
    const days=maybeFuzz(intervalFromStability(next.stability,settings.requestRetention,settings.weights,settings.maxInterval),next.elapsedDays,settings);
    next.state=State.Review;
    next.learningStep=0;
    next.scheduledDays=days;
    next.due=addDays(now,days).toISOString();
  }

  function applyLearning(next,previous,rating,now,settings,toState,steps){
    const result=learningOutcome(previous,rating,steps);
    if(result.minutes>0&&result.minutes<1440){
      next.state=toState;
      next.learningStep=result.nextStep;
      next.scheduledDays=0;
      next.due=addMinutes(now,result.minutes).toISOString();
    }else if(result.minutes>=1440){
      next.state=State.Review;
      next.learningStep=result.nextStep;
      next.scheduledDays=Math.floor(result.minutes/1440);
      next.due=addMinutes(now,result.minutes).toISOString();
    }else{
      graduate(next,now,settings);
    }
  }

  function schedule(card,rating,now=new Date(),options={}){
    if(![1,2,3,4].includes(rating))throw new Error('评分必须是 Again、Hard、Good 或 Easy');
    const settings=defaults(options);
    const reviewedAt=new Date(now);
    if(!Number.isFinite(reviewedAt.getTime()))throw new Error('复习时间无效');
    const next={...card};
    const memory=memoryUpdate(card,rating,reviewedAt,settings);
    Object.assign(next,memory);
    next.reps=(Number(card.reps)||0)+1;
    next.lastReview=reviewedAt.toISOString();

    if(card.state===State.New){
      applyLearning(next,card,rating,reviewedAt,settings,State.Learning,settings.learningSteps);
    }else if(card.state===State.Learning||card.state===State.Relearning){
      const steps=card.state===State.Relearning?settings.relearningSteps:settings.learningSteps;
      applyLearning(next,card,rating,reviewedAt,settings,card.state,steps);
    }else if(card.state===State.Review&&rating===Rating.Again){
      next.lapses=(Number(card.lapses)||0)+1;
      applyLearning(next,{...card,learningStep:0},rating,reviewedAt,settings,State.Relearning,settings.relearningSteps);
    }else if(card.state===State.Review){
      const ordered=reviewIntervals(card,reviewedAt,settings);
      const selected=ordered[rating];
      Object.assign(next,selected.memory);
      next.state=State.Review;
      next.learningStep=0;
      next.scheduledDays=selected.days;
      next.due=addDays(reviewedAt,selected.days).toISOString();
    }else{
      throw new Error('卡片状态无效');
    }
    return next;
  }

  function preview(card,now=new Date(),options={}){
    const out={};
    for(const rating of [1,2,3,4])out[rating]=schedule(card,rating,now,options);
    return out;
  }

  function formatInterval(now,due){
    const ms=new Date(due)-new Date(now);
    if(ms<90000)return '< 2分';
    if(ms<3600000)return `${Math.round(ms/60000)}分`;
    if(ms<DAY)return `${Math.round(ms/3600000)}小时`;
    const days=Math.round(ms/DAY);
    if(days<31)return `${days}天`;
    if(days<365)return `${Math.round(days/30)}个月`;
    return `${(days/365).toFixed(days<730?1:0)}年`;
  }

  function validate(){
    const settings=defaults();
    if(Math.abs(retrievability(10,10,settings.weights)-.9)>1e-8)throw new Error('FSRS 遗忘曲线不变量失败');
    if(intervalFromStability(10,.9,settings.weights)!==10)throw new Error('FSRS 间隔不变量失败');
    if(!(initialStability(1)<initialStability(2)&&initialStability(2)<initialStability(3)&&initialStability(3)<initialStability(4)))throw new Error('初始稳定性顺序失败');
    const hardSameDay=nextShortTermStability(4,Rating.Hard,settings.weights);
    if(hardSameDay<4)throw new Error('Hard 不应在同日降低稳定性');
    return true;
  }

  global.WisteriaFSRS={
    VERSION:'FSRS-6',
    REFERENCE:'open-spaced-repetition/ts-fsrs 5.4.1',
    DEFAULT_WEIGHTS:[...W],
    Rating,State,defaults,createCard,schedule,preview,retrievability,
    intervalFromStability,formatInterval,dateDiffInDays,validateWeights,validate
  };
})(window);
