"use client";
var Z=e=>typeof e=="function",h=(e,t)=>Z(e)?e(t):e;var W=(()=>{let e=0;return()=>(++e).toString()})(),E=(()=>{let e;return()=>{if(e===void 0&&typeof window<"u"){let t=matchMedia("(prefers-reduced-motion: reduce)");e=!t||t.matches}return e}})();import{useEffect as ee,useState as te,useRef as oe}from"react";var re=20,k="default";var H=(e,t)=>{let{toastLimit:o}=e.settings;switch(t.type){case 0:return{...e,toasts:[t.toast,...e.toasts].slice(0,o)};case 1:return{...e,toasts:e.toasts.map(r=>r.id===t.toast.id?{...r,...t.toast}:r)};case 2:let{toast:s}=t;return H(e,{type:e.toasts.find(r=>r.id===s.id)?1:0,toast:s});case 3:let{toastId:a}=t;return{...e,toasts:e.toasts.map(r=>r.id===a||a===void 0?{...r,dismissed:!0,visible:!1}:r)};case 4:return t.toastId===void 0?{...e,toasts:[]}:{...e,toasts:e.toasts.filter(r=>r.id!==t.toastId)};case 5:return{...e,pausedAt:t.time};case 6:let i=t.time-(e.pausedAt||0);return{...e,pausedAt:void 0,toasts:e.toasts.map(r=>({...r,pauseDuration:r.pauseDuration+i}))}}},v=[],j={toasts:[],pausedAt:void 0,settings:{toastLimit:re}},f={},Y=(e,t=k)=>{f[t]=H(f[t]||j,e),v.forEach(([o,s])=>{o===t&&s(f[t])})},_=e=>Object.keys(f).forEach(t=>Y(e,t)),Q=e=>Object.keys(f).find(t=>f[t].toasts.some(o=>o.id===e)),S=(e=k)=>t=>{Y(t,e)},se={blank:4e3,error:4e3,success:2e3,loading:1/0,custom:4e3},V=(e={},t=k)=>{let[o,s]=te(f[t]||j),a=oe(f[t]);ee(()=>(a.current!==f[t]&&s(f[t]),v.push([t,s]),()=>{let r=v.findIndex(([l])=>l===t);r>-1&&v.splice(r,1)}),[t]);let i=o.toasts.map(r=>{var l,g,T;return{...e,...e[r.type],...r,removeDelay:r.removeDelay||((l=e[r.type])==null?void 0:l.removeDelay)||(e==null?void 0:e.removeDelay),duration:r.duration||((g=e[r.type])==null?void 0:g.duration)||(e==null?void 0:e.duration)||se[r.type],style:{...e.style,...(T=e[r.type])==null?void 0:T.style,...r.style}}});return{...o,toasts:i}};var ie=(e,t="blank",o)=>({createdAt:Date.now(),visible:!0,dismissed:!1,type:t,ariaProps:{role:"status","aria-live":"polite"},message:e,pauseDuration:0,...o,id:(o==null?void 0:o.id)||W()}),P=e=>(t,o)=>{let s=ie(t,e,o);return S(s.toasterId||Q(s.id))({type:2,toast:s}),s.id},n=(e,t)=>P("blank")(e,t);n.error=P("error");n.success=P("success");n.loading=P("loading");n.custom=P("custom");n.dismiss=(e,t)=>{let o={type:3,toastId:e};t?S(t)(o):_(o)};n.dismissAll=e=>n.dismiss(void 0,e);n.remove=(e,t)=>{let o={type:4,toastId:e};t?S(t)(o):_(o)};n.removeAll=e=>n.remove(void 0,e);n.promise=(e,t,o)=>{let s=n.loading(t.loading,{...o,...o==null?void 0:o.loading});return typeof e=="function"&&(e=e()),e.then(a=>{let i=t.success?h(t.success,a):void 0;return i?n.success(i,{id:s,...o,...o==null?void 0:o.success}):n.dismiss(s),a}).catch(a=>{let i=t.error?h(t.error,a):void 0;i?n.error(i,{id:s,...o,...o==null?void 0:o.error}):n.dismiss(s)}),e};import{useEffect as X,useCallback as A,useRef as ne}from"react";var ce=1e3,w=(e,t="default")=>{let{toasts:o,pausedAt:s}=V(e,t),a=ne(new Map).current,i=A((c,m=ce)=>{if(a.has(c))return;let p=setTimeout(()=>{a.delete(c),r({type:4,toastId:c})},m);a.set(c,p)},[]);X(()=>{if(s)return;let c=Date.now(),m=o.map(p=>{if(p.duration===1/0)return;let R=(p.duration||0)+p.pauseDuration-(c-p.createdAt);if(R<0){p.visible&&n.dismiss(p.id);return}return setTimeout(()=>n.dismiss(p.id,t),R)});return()=>{m.forEach(p=>p&&clearTimeout(p))}},[o,s,t]);let r=A(S(t),[t]),l=A(()=>{r({type:5,time:Date.now()})},[r]),g=A((c,m)=>{r({type:1,toast:{id:c,height:m}})},[r]),T=A(()=>{s&&r({type:6,time:Date.now()})},[s,r]),d=A((c,m)=>{let{reverseOrder:p=!1,gutter:R=8,defaultPosition:z}=m||{},O=o.filter(u=>(u.position||z)===(c.position||z)&&u.height),K=O.findIndex(u=>u.id===c.id),B=O.filter((u,I)=>I<K&&u.visible).length;return O.filter(u=>u.visible).slice(...p?[B+1]:[0,B]).reduce((u,I)=>u+(I.height||0)+R,0)},[o]);return X(()=>{o.forEach(c=>{if(c.dismissed)i(c.id,c.removeDelay);else{let m=a.get(c.id);m&&(clearTimeout(m),a.delete(c.id))}})},[o,i]),{toasts:o,handlers:{updateHeight:g,startPause:l,endPause:T,calculateOffset:d}}};import*as y from"react";import{styled as J,keyframes as G}from"goober";import*as b from"react";import{styled as U,keyframes as xe}from"goober";import{styled as pe,keyframes as M}from"goober";var de=M`
from {
  transform: scale(0) rotate(45deg);
	opacity: 0;
}
to {
 transform: scale(1) rotate(45deg);
  opacity: 1;
}`,me=M`
from {
  transform: scale(0);
  opacity: 0;
}
to {
  transform: scale(1);
  opacity: 1;
}`,le=M`
from {
  transform: scale(0) rotate(90deg);
	opacity: 0;
}
to {
  transform: scale(1) rotate(90deg);
	opacity: 1;
}`,C=pe("div")`
  width: 20px;
  opacity: 0;
  height: 20px;
  border-radius: 10px;
  background: ${e=>e.primary||"#ff4b4b"};
  position: relative;
  transform: rotate(45deg);

  animation: ${de} 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
  animation-delay: 100ms;

  &:after,
  &:before {
    content: '';
    animation: ${me} 0.15s ease-out forwards;
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
    animation: ${le} 0.15s ease-out forwards;
    animation-delay: 180ms;
    transform: rotate(90deg);
  }
`;import{styled as ue,keyframes as fe}from"goober";var Te=fe`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`,F=ue("div")`
  width: 12px;
  height: 12px;
  box-sizing: border-box;
  border: 2px solid;
  border-radius: 100%;
  border-color: ${e=>e.secondary||"#e0e0e0"};
  border-right-color: ${e=>e.primary||"#616161"};
  animation: ${Te} 1s linear infinite;
`;import{styled as ye,keyframes as q}from"goober";var ge=q`
from {
  transform: scale(0) rotate(45deg);
	opacity: 0;
}
to {
  transform: scale(1) rotate(45deg);
	opacity: 1;
}`,he=q`
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
}`,L=ye("div")`
  width: 20px;
  opacity: 0;
  height: 20px;
  border-radius: 10px;
  background: ${e=>e.primary||"#61d345"};
  position: relative;
  transform: rotate(45deg);

  animation: ${ge} 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
  animation-delay: 100ms;
  &:after {
    content: '';
    box-sizing: border-box;
    animation: ${he} 0.2s ease-out forwards;
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
`;var be=U("div")`
  position: absolute;
`,Se=U("div")`
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 20px;
  min-height: 20px;
`,Ae=xe`
from {
  transform: scale(0.6);
  opacity: 0.4;
}
to {
  transform: scale(1);
  opacity: 1;
}`,Pe=U("div")`
  position: relative;
  transform: scale(0.6);
  opacity: 0.4;
  min-width: 20px;
  animation: ${Ae} 0.3s 0.12s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
`,$=({toast:e})=>{let{icon:t,type:o,iconTheme:s}=e;return t!==void 0?typeof t=="string"?b.createElement(Pe,null,t):t:o==="blank"?null:b.createElement(Se,null,b.createElement(F,{...s}),o!=="loading"&&b.createElement(be,null,o==="error"?b.createElement(C,{...s}):b.createElement(L,{...s})))};var Re=e=>`
0% {transform: translate3d(0,${e*-200}%,0) scale(.6); opacity:.5;}
100% {transform: translate3d(0,0,0) scale(1); opacity:1;}
`,Ee=e=>`
0% {transform: translate3d(0,0,-1px) scale(1); opacity:1;}
100% {transform: translate3d(0,${e*-150}%,-1px) scale(.6); opacity:0;}
`,ve="0%{opacity:0;} 100%{opacity:1;}",De="0%{opacity:1;} 100%{opacity:0;}",Oe=J("div")`
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
`,Ie=J("div")`
  display: flex;
  justify-content: center;
  margin: 4px 10px;
  color: inherit;
  flex: 1 1 auto;
  white-space: pre-line;
`,ke=(e,t)=>{let s=e.includes("top")?1:-1,[a,i]=E()?[ve,De]:[Re(s),Ee(s)];return{animation:t?`${G(a)} 0.35s cubic-bezier(.21,1.02,.73,1) forwards`:`${G(i)} 0.4s forwards cubic-bezier(.06,.71,.55,1)`}},N=y.memo(({toast:e,position:t,style:o,children:s})=>{let a=e.height?ke(e.position||t||"top-center",e.visible):{opacity:0},i=y.createElement($,{toast:e}),r=y.createElement(Ie,{...e.ariaProps},h(e.message,e));return y.createElement(Oe,{className:e.className,style:{...a,...o,...e.style}},typeof s=="function"?s({icon:i,message:r}):y.createElement(y.Fragment,null,i,r))});import{css as _e,setup as Ve}from"goober";import*as x from"react";Ve(x.createElement);var we=({id:e,className:t,style:o,onHeightUpdate:s,children:a})=>{let i=x.useCallback(r=>{if(r){let l=()=>{let g=r.getBoundingClientRect().height;s(e,g)};l(),new MutationObserver(l).observe(r,{subtree:!0,childList:!0,characterData:!0})}},[e,s]);return x.createElement("div",{ref:i,className:t,style:o},a)},Me=(e,t)=>{let o=e.includes("top"),s=o?{top:0}:{bottom:0},a=e.includes("center")?{justifyContent:"center"}:e.includes("right")?{justifyContent:"flex-end"}:{};return{left:0,right:0,display:"flex",position:"absolute",transition:E()?void 0:"all 230ms cubic-bezier(.21,1.02,.73,1)",transform:`translateY(${t*(o?1:-1)}px)`,...s,...a}},Ce=_e`
  z-index: 9999;
  > * {
    pointer-events: auto;
  }
`,D=16,Fe=({reverseOrder:e,position:t="top-center",toastOptions:o,gutter:s,children:a,toasterId:i,containerStyle:r,containerClassName:l})=>{let{toasts:g,handlers:T}=w(o,i);return x.createElement("div",{"data-rht-toaster":i||"",style:{position:"fixed",zIndex:9999,top:D,left:D,right:D,bottom:D,pointerEvents:"none",...r},className:l,onMouseEnter:T.startPause,onMouseLeave:T.endPause},g.map(d=>{let c=d.position||t,m=T.calculateOffset(d,{reverseOrder:e,gutter:s,defaultPosition:t}),p=Me(c,m);return x.createElement(we,{id:d.id,key:d.id,onHeightUpdate:T.updateHeight,className:d.visible?Ce:"",style:p},d.type==="custom"?h(d.message,d):a?a(d):x.createElement(N,{toast:d,position:c}))}))};var zt=n;export{L as CheckmarkIcon,C as ErrorIcon,F as LoaderIcon,N as ToastBar,$ as ToastIcon,Fe as Toaster,zt as default,h as resolveValue,n as toast,w as useToaster,V as useToasterStore};
//# sourceMappingURL=index.mjs.map