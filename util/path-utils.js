const { parsePathString, pathToAbsolute, serializePath } = require('svg-path-commander');

function getSegs(el) {
  if (!el || !el.getAttribute) return [];
  return pathToAbsolute(parsePathString(el.getAttribute('d') || ''));
}

function setSegs(el, segs) {
  if (!el || !el.setAttribute) return;
  el.setAttribute('d', serializePath(segs));
}

const toMatrix = str => new DOMMatrix(str || '');
const transformXY = (x, y, m) => {
  const p = new DOMPoint(x, y).matrixTransform(m);
  return [p.x, p.y];
};

module.exports = { getSegs, setSegs, toMatrix, transformXY };
