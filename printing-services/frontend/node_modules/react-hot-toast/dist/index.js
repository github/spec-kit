"use client";
"use strict";var se=Object.create;var k=Object.defineProperty;var ae=Object.getOwnPropertyDescriptor;var ie=Object.getOwnPropertyNames;var ne=Object.getPrototypeOf,ce=Object.prototype.hasOwnProperty;var pe=(e,t)=>{for(var o in t)k(e,o,{get:t[o],enumerable:!0})},G=(e,t,o,s)=>{if(t&&typeof t=="object"||typeof t=="function")for(let a of ie(t))!ce.call(e,a)&&a!==o&&k(e,a,{get:()=>t[a],enumerable:!(s=ae(t,a))||s.enumerable});return e};var j=(e,t,o)=>(o=e!=null?se(ne(e)):{},G(t||!e||!e.__esModule?k(o,"default",{value:e,enumerable:!0}):o,e)),de=e=>G(k({},"__esModule",{value:!0}),e);var Ue={};pe(Ue,{CheckmarkIcon:()=>U,ErrorIcon:()=>C,LoaderIcon:()=>L,ToastBar:()=>N,ToastIcon:()=>$,Toaster:()=>oe,default:()=>Le,resolveValue:()=>g,toast:()=>i,useToaster:()=>M,useToasterStore:()=>w});module.exports=de(Ue);var me=e=>typeof e=="function",g=(e,t)=>me(e)?e(t):e;var J=(()=>{let e=0;return()=>(++e).toString()})(),_=(()=>{let e;return()=>{if(e===void 0&&typeof window<"u"){let t=matchMedia("(prefers-reduced-motion: reduce)");e=!t||t.matches}return e}})();var A=require("react");var le=20,Y="default";var K=(e,t)=>{let{toastLimit:o}=e.settings;switch(t.type){case 0:return{...e,toasts:[t.toast,...e.toasts].slice(0,o)};case 1:return{...e,toasts:e.toasts.map(r=>r.id===t.toast.id?{...r,...t.toast}:r)};case 2:let{toast:s}=t;return K(e,{type:e.toasts.find(r=>r.id===s.id)?1:0,toast:s});case 3:let{toastId:a}=t;return{...e,toasts:e.toasts.map(r=>r.id===a||a===void 0?{...r,dismissed:!0,visible:!1}:r)};case 4:return t.toastId===void 0?{...e,toasts:[]}:{...e,toasts:e.toasts.filter(r=>r.id!==t.toastId)};case 5:return{...e,pausedAt:t.time};case 6:let n=t.time-(e.pausedAt||0);return{...e,pausedAt:void 0,toasts:e.toasts.map(r=>({...r,pauseDuration:r.pauseDuration+n}))}}},V=[],Z={toasts:[],pausedAt:void 0,settings:{toastLimit:le}},T={},ee=(e,t=Y)=>{T[t]=K(T[t]||Z,e),V.forEach(([o,s])=>{o===t&&s(T[t])})},Q=e=>Object.keys(T).forEach(t=>ee(e,t)),te=e=>Object.keys(T).find(t=>T[t].toasts.some(o=>o.id===e)),P=(e=Y)=>t=>{ee(t,e)},ue={blank:4e3,error:4e3,success:2e3,loading:1/0,custom:4e3},w=(e={},t=Y)=>{let[o,s]=(0,A.useState)(T[t]||Z),a=(0,A.useRef)(T[t]);(0,A.useEffect)(()=>(a.current!==T[t]&&s(T[t]),V.push([t,s]),()=>{let r=V.findIndex(([u])=>u===t);r>-1&&V.splice(r,1)}),[t]);let n=o.toasts.map(r=>{var u,x,y;return{...e,...e[r.type],...r,removeDelay:r.removeDelay||((u=e[r.type])==null?void 0:u.removeDelay)||(e==null?void 0:e.removeDelay),duration:r.duration||((x=e[r.type])==null?void 0:x.duration)||(e==null?void 0:e.duration)||ue[r.type],style:{...e.style,...(y=e[r.type])==null?void 0:y.style,...r.style}}});return{...o,toasts:n}};var Te=(e,t="blank",o)=>({createdAt:Date.now(),visible:!0,dismissed:!1,type:t,ariaProps:{role:"status","aria-live":"polite"},message:e,pauseDuration:0,...o,id:(o==null?void 0:o.id)||J()}),D=e=>(t,o)=>{let s=Te(t,e,o);return P(s.toasterId||te(s.id))({type:2,toast:s}),s.id},i=(e,t)=>D("blank")(e,t);i.error=D("error");i.success=D("success");i.loading=D("loading");i.custom=D("custom");i.dismiss=(e,t)=>{let o={type:3,toastId:e};t?P(t)(o):Q(o)};i.dismissAll=e=>i.dismiss(void 0,e);i.remove=(e,t)=>{let o={type:4,toastId:e};t?P(t)(o):Q(o)};i.removeAll=e=>i.remove(void 0,e);i.promise=(e,t,o)=>{let s=i.loading(t.loading,{...o,...o==null?void 0:o.loading});return typeof e=="function"&&(e=e()),e.then(a=>{let n=t.success?g(t.success,a):void 0;return n?i.success(n,{id:s,...o,...o==null?void 0:o.success}):i.dismiss(s),a}).catch(a=>{let n=t.error?g(t.error,a):void 0;n?i.error(n,{id:s,...o,...o==null?void 0:o.error}):i.dismiss(s)}),e};var l=require("react");var ye=1e3,M=(e,t="default")=>{let{toasts:o,pausedAt:s}=w(e,t),a=(0,l.useRef)(new Map).current,n=(0,l.useCallback)((c,m=ye)=>{if(a.has(c))return;let p=setTimeout(()=>{a.delete(c),r({type:4,toastId:c})},m);a.set(c,p)},[]);(0,l.useEffect)(()=>{if(s)return;let c=Date.now(),m=o.map(p=>{if(p.duration===1/0)return;let I=(p.duration||0)+p.pauseDuration-(c-p.createdAt);if(I<0){p.visible&&i.dismiss(p.id);return}return setTimeout(()=>i.dismiss(p.id,t),I)});return()=>{m.forEach(p=>p&&clearTimeout(p))}},[o,s,t]);let r=(0,l.useCallback)(P(t),[t]),u=(0,l.useCallback)(()=>{r({type:5,time:Date.now()})},[r]),x=(0,l.useCallback)((c,m)=>{r({type:1,toast:{id:c,height:m}})},[r]),y=(0,l.useCallback)(()=>{s&&r({type:6,time:Date.now()})},[s,r]),d=(0,l.useCallback)((c,m)=>{let{reverseOrder:p=!1,gutter:I=8,defaultPosition:X}=m||{},W=o.filter(f=>(f.position||X)===(c.position||X)&&f.height),re=W.findIndex(f=>f.id===c.id),q=W.filter((f,H)=>H<re&&f.visible).length;return W.filter(f=>f.visible).slice(...p?[q+1]:[0,q]).reduce((f,H)=>f+(H.height||0)+I,0)},[o]);return(0,l.useEffect)(()=>{o.forEach(c=>{if(c.dismissed)n(c.id,c.removeDelay);else{let m=a.get(c.id);m&&(clearTimeout(m),a.delete(c.id))}})},[o,n]),{toasts:o,handlers:{updateHeight:x,startPause:u,endPause:y,calculateOffset:d}}};var h=j(require("react")),v=require("goober");var S=j(require("react")),E=require("goober");var R=require("goober"),ge=R.keyframes`
from {
  transform: scale(0) rotate(45deg);
	opacity: 0;
}
to {
 transform: scale(1) rotate(45deg);
  opacity: 1;
}`,he=R.keyframes`
from {
  transform: scale(0);
  opacity: 0;
}
to {
  transform: scale(1);
  opacity: 1;
}`,xe=R.keyframes`
from {
  transform: scale(0) rotate(90deg);
	opacity: 0;
}
to {
  transform: scale(1) rotate(90deg);
	opacity: 1;
}`,C=(0,R.styled)("div")`
  width: 20px;
  opacity: 0;
  height: 20px;
  border-radius: 10px;
  background: ${e=>e.primary||"#ff4b4b"};
  position: relative;
  transform: rotate(45deg);

  animation: ${ge} 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
  animation-delay: 100ms;

  &:after,
  &:before {
    content: '';
    animation: ${he} 0.15s ease-out forwards;
    animation-delay: 150ms;
    position: absolute;
    border-radius: 3px;
    opacity: 0;
    background: ${e=>e.secondary||"#fff"};
    bottom: 9px;
    left: 4px;
    height: 2px;
    width: 12px;
  }

  &:before {
    animation: ${xe} 0.15s ease-out forwards;
    animation-delay: 180ms;
    transform: rotate(90deg);
  }
`;var F=require("goober"),be=F.keyframes`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`,L=(0,F.styled)("div")`
  width: 12px;
  height: 12px;
  box-sizing: border-box;
  border: 2px solid;
  border-radius: 100%;
  border-color: ${e=>e.secondary||"#e0e0e0"};
  border-right-color: ${e=>e.primary||"#616161"};
  animation: ${be} 1s linear infinite;
`;var O=require("goober"),Se=O.keyframes`
from {
  transform: scale(0) rotate(45deg);
	opacity: 0;
}
to {
  transform: scale(1) rotate(45deg);
	opacity: 1;
}`,Ae=O.keyframes`
0% {
	height: 0;
	width: 0;
	opacity: 0;
}
40% {
  height: 0;
	width: 6px;
	opacity: 1;
}
100% {
  opacity: 1;
  height: 10px;
}`,U=(0,O.styled)("div")`
  width: 20px;
  opacity: 0;
  height: 20px;
  border-radius: 10px;
  background: ${e=>e.primary||"#61d345"};
  position: relative;
  transform: rotate(45deg);

  animation: ${Se} 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
  animation-delay: 100ms;
  &:after {
    content: '';
    box-sizing: border-box;
    animation: ${Ae} 0.2s ease-out forwards;
    opacity: 0;
    animation-delay: 200ms;
    position: absolute;
    border-right: 2px solid;
    border-bottom: 2px solid;
    border-color: ${e=>e.secondary||"#fff"};
    bottom: 6px;
    left: 6px;
    height: 10px;
    width: 6px;
  }
`;var Pe=(0,E.styled)("div")`
  position: absolute;
`,Re=(0,E.styled)("div")`
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 20px;
  min-height: 20px;
`,Ee=E.keyframes`
from {
  transform: scale(0.6);
  opacity: 0.4;
}
to {
  transform: scale(1);
  opacity: 1;
}`,ve=(0,E.styled)("div")`
  position: relative;
  transform: scale(0.6);
  opacity: 0.4;
  min-width: 20px;
  animation: ${Ee} 0.3s 0.12s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
`,$=({toast:e})=>{let{icon:t,type:o,iconTheme:s}=e;return t!==void 0?typeof t=="string"?S.createElement(ve,null,t):t:o==="blank"?null:S.createElement(Re,null,S.createElement(L,{...s}),o!=="loading"&&S.createElement(Pe,null,o==="error"?S.createElement(C,{...s}):S.createElement(U,{...s})))};var De=e=>`
0% {transform: translate3d(0,${e*-200}%,0) scale(.6); opacity:.5;}
100% {transform: translate3d(0,0,0) scale(1); opacity:1;}
`,Oe=e=>`
0% {transform: translate3d(0,0,-1px) scale(1); opacity:1;}
100% {transform: translate3d(0,${e*-150}%,-1px) scale(.6); opacity:0;}
`,Ie="0%{opacity:0;} 100%{opacity:1;}",ke="0%{opacity:1;} 100%{opacity:0;}",_e=(0,v.styled)("div")`
  display: flex;
  align-items: center;
  background: #fff;
  color: #363636;
  line-height: 1.3;
  will-change: transform;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1), 0 3px 3px rgba(0, 0, 0, 0.05);
  max-width: 350px;
  pointer-events: auto;
  padding: 8px 10px;
  border-radius: 8px;
`,Ve=(0,v.styled)("div")`
  display: flex;
  justify-content: center;
  margin: 4px 10px;
  color: inherit;
  flex: 1 1 auto;
  white-space: pre-line;
`,we=(e,t)=>{let s=e.includes("top")?1:-1,[a,n]=_()?[Ie,ke]:[De(s),Oe(s)];return{animation:t?`${(0,v.keyframes)(a)} 0.35s cubic-bezier(.21,1.02,.73,1) forwards`:`${(0,v.keyframes)(n)} 0.4s forwards cubic-bezier(.06,.71,.55,1)`}},N=h.memo(({toast:e,position:t,style:o,children:s})=>{let a=e.height?we(e.position||t||"top-center",e.visible):{opacity:0},n=h.createElement($,{toast:e}),r=h.createElement(Ve,{...e.ariaProps},g(e.message,e));return h.createElement(_e,{className:e.className,style:{...a,...o,...e.style}},typeof s=="function"?s({icon:n,message:r}):h.createElement(h.Fragment,null,n,r))});var B=require("goober"),b=j(require("react"));(0,B.setup)(b.createElement);var Me=({id:e,className:t,style:o,onHeightUpdate:s,children:a})=>{let n=b.useCallback(r=>{if(r){let u=()=>{let x=r.getBoundingClientRect().height;s(e,x)};u(),new MutationObserver(u).observe(r,{subtree:!0,childList:!0,characterData:!0})}},[e,s]);return b.createElement("div",{ref:n,className:t,style:o},a)},Ce=(e,t)=>{let o=e.includes("top"),s=o?{top:0}:{bottom:0},a=e.includes("center")?{justifyContent:"center"}:e.includes("right")?{justifyContent:"flex-end"}:{};return{left:0,right:0,display:"flex",position:"absolute",transition:_()?void 0:"all 230ms cubic-bezier(.21,1.02,.73,1)",transform:`translateY(${t*(o?1:-1)}px)`,...s,...a}},Fe=B.css`
  z-index: 9999;
  > * {
    pointer-events: auto;
  }
`,z=16,oe=({reverseOrder:e,position:t="top-center",toastOptions:o,gutter:s,children:a,toasterId:n,containerStyle:r,containerClassName:u})=>{let{toasts:x,handlers:y}=M(o,n);return b.createElement("div",{"data-rht-toaster":n||"",style:{position:"fixed",zIndex:9999,top:z,left:z,right:z,bottom:z,pointerEvents:"none",...r},className:u,onMouseEnter:y.startPause,onMouseLeave:y.endPause},x.map(d=>{let c=d.position||t,m=y.calculateOffset(d,{reverseOrder:e,gutter:s,defaultPosition:t}),p=Ce(c,m);return b.createElement(Me,{id:d.id,key:d.id,onHeightUpdate:y.updateHeight,className:d.visible?Fe:"",style:p},d.type==="custom"?g(d.message,d):a?a(d):b.createElement(N,{toast:d,position:c}))}))};var Le=i;0&&(module.exports={CheckmarkIcon,ErrorIcon,LoaderIcon,ToastBar,ToastIcon,Toaster,resolveValue,toast,useToaster,useToasterStore});
//# sourceMappingURL=index.js.map