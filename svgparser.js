(function(root){
  'use strict';

  const { parsePathString, pathToAbsolute, serializePath } = require('svg-path-commander');
  const GeometryUtil = require('./util/geometryutil.js');
  const { getSegs, setSegs, toMatrix, transformXY } = require('./util/path-utils.js');

  function SvgParser(){
    this.svg = null;
    this.svgRoot = null;
    this.allowedElements = ['svg','circle','ellipse','path','polygon','polyline','rect','line'];
    this.conf = { tolerance: 2, toleranceSvg: 0.005 };
  }

  SvgParser.prototype.config = function(c){
    if(c && c.tolerance) this.conf.tolerance = c.tolerance;
  };

  SvgParser.prototype.load = function(svgString){
    if(!svgString || typeof svgString !== 'string') throw Error('invalid SVG string');
    const parser = new DOMParser();
    const svg = parser.parseFromString(svgString, 'image/svg+xml');
    this.svg = svg;
    for(const child of Array.from(svg.childNodes)){
      if(child.tagName && child.tagName === 'svg'){ this.svgRoot = child; break; }
    }
    if(!this.svgRoot) throw new Error('SVG has no children');
    return this.svgRoot;
  };

  SvgParser.prototype.getStyle = function(){
    return this.svgRoot ? this.svgRoot.querySelector('style') : null;
  };

  function transformSegment(seg, matrix, scale, rotate){
    const d = seg.data.slice();
    switch(seg.key){
      case 'M':
      case 'L':
        [d[0],d[1]] = transformXY(d[0],d[1],matrix); break;
      case 'H':
        [d[0],d[0]] = transformXY(d[0],0,matrix); seg.key='L'; d[1]=d[0]; break;
      case 'V':
        [d[0],d[0]] = transformXY(0,d[0],matrix); seg.key='L'; d[1]=d[0]; break;
      case 'C':
        [d[0],d[1]] = transformXY(d[0],d[1],matrix);
        [d[2],d[3]] = transformXY(d[2],d[3],matrix);
        [d[4],d[5]] = transformXY(d[4],d[5],matrix);
        break;
      case 'S':
        [d[0],d[1]] = transformXY(d[0],d[1],matrix);
        [d[2],d[3]] = transformXY(d[2],d[3],matrix);
        break;
      case 'Q':
        [d[0],d[1]] = transformXY(d[0],d[1],matrix);
        [d[2],d[3]] = transformXY(d[2],d[3],matrix);
        break;
      case 'T':
        [d[0],d[1]] = transformXY(d[0],d[1],matrix);
        break;
      case 'A':
        [d[5],d[6]] = transformXY(d[5],d[6],matrix);
        d[0] = d[0]*scale; d[1] = d[1]*scale; d[2] = d[2]+rotate;
        break;
    }
    return { key: seg.key, data: d };
  }

  function applyTransform(element, parent){
    const local = element.getAttribute('transform') || '';
    const matrix = toMatrix((parent||'') + local);
    const scale = Math.sqrt(matrix.a*matrix.a + matrix.c*matrix.c);
    const rotate = Math.atan2(matrix.b, matrix.d)*180/Math.PI;
    element.removeAttribute('transform');

    if(['g','svg','defs','clipPath'].includes(element.tagName)){
      for(const child of Array.from(element.childNodes)){
        if(child.tagName) applyTransform(child, (parent||'') + local);
      }
      return;
    }

    switch(element.tagName){
      case 'path':{
        let segs = getSegs(element);
        segs = segs.map(s => transformSegment(s, matrix, scale, rotate));
        setSegs(element, segs);
        break;}
      case 'polygon':
      case 'polyline':{
        let pts='';
        for(let i=0;i<element.points.numberOfItems;i++){
          const p=element.points.getItem(i);
          const t=transformXY(p.x,p.y,matrix);
          pts+= t[0]+','+t[1]+' ';
        }
        element.setAttribute('points', pts.trim());
        break;}
      case 'circle':{
        let [cx,cy]=transformXY(element.getAttribute('cx'),element.getAttribute('cy'),matrix);
        element.setAttribute('cx',cx); element.setAttribute('cy',cy);
        element.setAttribute('r', parseFloat(element.getAttribute('r'))*scale);
        break;}
      case 'rect':{
        const x=parseFloat(element.getAttribute('x'))||0;
        const y=parseFloat(element.getAttribute('y'))||0;
        const w=parseFloat(element.getAttribute('width'));
        const h=parseFloat(element.getAttribute('height'));
        const pts=[[x,y],[x+w,y],[x+w,y+h],[x,y+h]].map(p=>transformXY(p[0],p[1],matrix));
        const poly=element.ownerDocument.createElementNS(element.namespaceURI,'polygon');
        poly.setAttribute('points',pts.map(p=>p.join(',')).join(' '));
        if(element.getAttribute('id')) poly.setAttribute('id',element.getAttribute('id'));
        if(element.getAttribute('class')) poly.setAttribute('class',element.getAttribute('class'));
        element.parentNode.replaceChild(poly,element);
        break;}
      case 'line':{
        let [x1,y1]=transformXY(element.getAttribute('x1'),element.getAttribute('y1'),matrix);
        let [x2,y2]=transformXY(element.getAttribute('x2'),element.getAttribute('y2'),matrix);
        element.setAttribute('x1',x1); element.setAttribute('y1',y1);
        element.setAttribute('x2',x2); element.setAttribute('y2',y2);
        break;}
      case 'ellipse':{
        const cx=parseFloat(element.getAttribute('cx'));
        const cy=parseFloat(element.getAttribute('cy'));
        const rx=parseFloat(element.getAttribute('rx'));
        const ry=parseFloat(element.getAttribute('ry'));
        let segs=[
          {key:'M',data:[cx-rx,cy]},
          {key:'A',data:[rx,ry,0,1,0,cx+rx,cy]},
          {key:'A',data:[rx,ry,0,1,0,cx-rx,cy]},
          {key:'Z',data:[]}
        ];
        segs=segs.map(s=>transformSegment(s,matrix,scale,rotate));
        const path=element.ownerDocument.createElementNS(element.namespaceURI,'path');
        path.setAttribute('d',serializePath(segs));
        if(element.getAttribute('id')) path.setAttribute('id',element.getAttribute('id'));
        if(element.getAttribute('class')) path.setAttribute('class',element.getAttribute('class'));
        element.parentNode.replaceChild(path,element);
        break;}
    }
  }

  function flatten(el){
    for(let i=0;i<el.childNodes.length;i++){
      flatten(el.childNodes[i]);
    }
    if(el.tagName!=='svg'){
      while(el.childNodes.length>0){
        el.parentElement.appendChild(el.childNodes[0]);
      }
    }
  }

  function filter(whitelist, el){
    el = el || this.svgRoot;
    for(let i=0;i<el.childNodes.length;i++){
      filter(whitelist, el.childNodes[i]);
    }
    if(el.childNodes.length===0 && whitelist.indexOf(el.tagName)<0){
      el.parentElement.removeChild(el);
    }
  }

  function recurse(el, func){
    const children = Array.from(el.childNodes);
    for(const c of children) recurse(c, func);
    func(el);
  }

  function splitPath(path){
    const segs = pathToAbsolute(parsePathString(path.getAttribute('d')));
    let current=[]; const paths=[];
    for(const seg of segs){
      if(seg.key==='M' && current.length){
        const p=path.cloneNode();
        p.setAttribute('d',serializePath(current));
        paths.push(p); current=[seg];
      }else{ current.push(seg); }
    }
    if(current.length){
      const p=path.cloneNode();
      p.setAttribute('d',serializePath(current));
      paths.push(p);
    }
    if(paths.length>1){
      for(const p of paths){ path.parentElement.insertBefore(p,path); }
      path.remove();
      return paths;
    }
    return false;
  }

  SvgParser.prototype.cleanInput = function(){
    applyTransform(this.svgRoot);
    flatten(this.svgRoot);
    filter.call(this,this.allowedElements,this.svgRoot);
    recurse(this.svgRoot, splitPath);
    return this.svgRoot;
  };

  SvgParser.prototype.polygonify = function(el){
    const poly=[];
    switch(el.tagName){
      case 'polygon':
      case 'polyline':
        for(let i=0;i<el.points.numberOfItems;i++){ const pt=el.points.getItem(i); poly.push({x:pt.x,y:pt.y}); }
        break;
      case 'rect':{
        const x=parseFloat(el.getAttribute('x'))||0;
        const y=parseFloat(el.getAttribute('y'))||0;
        const w=parseFloat(el.getAttribute('width'));
        const h=parseFloat(el.getAttribute('height'));
        poly.push({x:x,y:y},{x:x+w,y:y},{x:x+w,y:y+h},{x:x,y:y+h});
        break;}
      case 'circle':{
        const r=parseFloat(el.getAttribute('r'));
        const cx=parseFloat(el.getAttribute('cx'));
        const cy=parseFloat(el.getAttribute('cy'));
        let num=Math.ceil((2*Math.PI)/Math.acos(1-(this.conf.tolerance/r)));
        if(num<3) num=3;
        for(let i=0;i<num;i++){ const th=i*((2*Math.PI)/num); poly.push({x:r*Math.cos(th)+cx,y:r*Math.sin(th)+cy}); }
        break;}
      case 'ellipse':{
        const rx=parseFloat(el.getAttribute('rx')); const ry=parseFloat(el.getAttribute('ry'));
        const maxr=Math.max(rx,ry); const cx=parseFloat(el.getAttribute('cx')); const cy=parseFloat(el.getAttribute('cy'));
        let num=Math.ceil((2*Math.PI)/Math.acos(1-(this.conf.tolerance/maxr)));
        if(num<3) num=3;
        for(let i=0;i<num;i++){ const th=i*((2*Math.PI)/num); poly.push({x:rx*Math.cos(th)+cx,y:ry*Math.sin(th)+cy}); }
        break;}
      case 'path':{
        const segs = getSegs(el);
        let x=0,y=0,x0=0,y0=0,x1=0,y1=0,x2=0,y2=0,prevx=0,prevy=0,prevx1=0,prevy1=0,prevx2=0,prevy2=0;
        for(let i=0;i<segs.length;i++){
          const s=segs[i]; const command=s.key; const d=s.data;
          prevx=x; prevy=y; prevx1=x1; prevy1=y1; prevx2=x2; prevy2=y2;
          switch(command){
            case 'M': case 'L': x=d[0]; y=d[1]; poly.push({x,y}); break;
            case 'H': x=d[0]; poly.push({x,y}); break;
            case 'V': y=d[0]; poly.push({x,y}); break;
            case 'Q': x1=d[0]; y1=d[1]; x=d[2]; y=d[3]; var pts=GeometryUtil.QuadraticBezier.linearize({x:prevx,y:prevy},{x:x,y:y},{x:x1,y:y1},this.conf.tolerance); pts.shift(); poly.push(...pts); break;
            case 'T': if(i>0 && /[QqTt]/.test(segs[i-1].key)){ x1=prevx+(prevx-prevx1); y1=prevy+(prevy-prevy1);} else { x1=prevx; y1=prevy; } x=d[0]; y=d[1]; var pts=GeometryUtil.QuadraticBezier.linearize({x:prevx,y:prevy},{x:x,y:y},{x:x1,y:y1},this.conf.tolerance); pts.shift(); poly.push(...pts); break;
            case 'C': x1=d[0]; y1=d[1]; x2=d[2]; y2=d[3]; x=d[4]; y=d[5]; var pts=GeometryUtil.CubicBezier.linearize({x:prevx,y:prevy},{x:x,y:y},{x:x1,y:y1},{x:x2,y:y2},this.conf.tolerance); pts.shift(); poly.push(...pts); break;
            case 'S': if(i>0 && /[CcSs]/.test(segs[i-1].key)){ x1=prevx+(prevx-prevx2); y1=prevy+(prevy-prevy2);} else { x1=prevx; y1=prevy; } x2=d[0]; y2=d[1]; x=d[2]; y=d[3]; var pts=GeometryUtil.CubicBezier.linearize({x:prevx,y:prevy},{x:x,y:y},{x:x1,y:y1},{x:x2,y:y2},this.conf.tolerance); pts.shift(); poly.push(...pts); break;
            case 'A': var pts=GeometryUtil.Arc.linearize({x:prevx,y:prevy},{x:d[5],y:d[6]},d[0],d[1],d[2],d[3],d[4],this.conf.tolerance); pts.shift(); poly.push(...pts); x=d[5]; y=d[6]; break;
            case 'Z': x=x0; y=y0; break;
          }
          if (command==='M') { x0=x; y0=y; }
        }
        break;}
    }
    while(poly.length>0 && GeometryUtil.almostEqual(poly[0].x,poly[poly.length-1].x,this.conf.toleranceSvg) && GeometryUtil.almostEqual(poly[0].y,poly[poly.length-1].y,this.conf.toleranceSvg)){
      poly.pop();
    }
    return poly;
  };

  const parser = new SvgParser();
  root.SvgParser = {
    config: parser.config.bind(parser),
    load: parser.load.bind(parser),
    getStyle: parser.getStyle.bind(parser),
    clean: parser.cleanInput.bind(parser),
    polygonify: parser.polygonify.bind(parser)
  };
})(typeof window !== 'undefined' ? window : this);
