/* Read bounded SFNT naming metadata; font files remain in the browser. */
((scope) => {
  function readFontInfo(buffer) {
    const view = new DataView(buffer);
    const within = (offset, length, limit = view.byteLength) =>
      Number.isSafeInteger(offset) && Number.isSafeInteger(length) && offset >= 0 && length >= 0 && offset <= limit - length;
    if (!within(0, 12)) throw new Error('The font file is incomplete.');
    const signature = view.getUint32(0);
    if (![0x00010000, 0x4f54544f, 0x74727565].includes(signature)) throw new Error('Choose an individual .ttf or .otf font, not a ZIP or font collection.');
    const tables = view.getUint16(4);
    if (!tables || tables > 256 || !within(12, tables * 16)) throw new Error('The font table directory is invalid.');
    let start, length;
    for (let index = 0; index < tables; index++) {
      const offset = 12 + index * 16;
      if (view.getUint32(offset) !== 0x6e616d65) continue; // name
      start = view.getUint32(offset + 8); length = view.getUint32(offset + 12); break;
    }
    if (start === undefined || !within(start, length) || length < 6) throw new Error('This font has no readable name table.');
    const format = view.getUint16(start), count = view.getUint16(start + 2), strings = view.getUint16(start + 4);
    if (format > 1 || count > 4096 || 6 + count * 12 > length || strings < 6 + count * 12 || strings > length) throw new Error('The font name table is invalid.');
    const names = new Map();
    for (let index = 0; index < count; index++) {
      const offset = start + 6 + index * 12;
      const platform = view.getUint16(offset), encoding = view.getUint16(offset + 2), language = view.getUint16(offset + 4), id = view.getUint16(offset + 6);
      if (![1, 2, 6, 16, 17].includes(id)) continue;
      const size = view.getUint16(offset + 8), relative = strings + view.getUint16(offset + 10);
      if (!within(relative, size, length) || size > 4096) continue;
      let label;
      if ((platform === 0 || platform === 3) && size % 2 === 0) label = 'utf-16be';
      else if (platform === 1 && encoding === 0) label = 'macintosh';
      else continue;
      let text;
      try {text = new TextDecoder(label, {fatal: true}).decode(new Uint8Array(buffer, start + relative, size)).trim();}
      catch {continue;}
      if (!text || text.length > 256 || /[|\r\n\x00-\x1f]/.test(text)) continue;
      const score = platform === 3 && language === 0x409 ? 40 : platform === 0 ? 30 : platform === 3 ? 20 : 10;
      if (!names.has(id) || score > names.get(id).score) names.set(id, {text, score});
    }
    const name = id => names.get(id)?.text;
    const family = name(16) || name(1), style = name(17) || name(2) || 'Regular';
    if (!family) throw new Error('The font has no usable family name.');
    return {family, style, postscriptName: name(6) || family + '-' + style, format: signature === 0x4f54544f ? 'otf' : 'ttf'};
  }
  if (typeof module === 'object' && module.exports) module.exports = readFontInfo;
  else scope.vectorcraftReadFontInfo = readFontInfo;
})(typeof window === 'object' ? window : globalThis);
