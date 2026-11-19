// Tạo MP3 hàng loạt trên Vbee Studio — dán NGUYÊN file này vào tab studio.vbee.vn (đã đăng nhập) bằng
// javascript_tool của Claude in Chrome. File chỉ khai báo window.__vb, chưa gửi gì, chưa tốn điểm.
// Rồi gọi từng bước, mỗi lệnh một lần javascript_tool (KHÔNG await quá ~15 giây trong một lệnh: máy ít RAM
// từng treo renderer 5 phút vì await 40 giây):
//   1. await __vb.timToken()           -> {tok:true, ganDay:[…]}  (chỉ đọc; xem 8 request gần nhất)
//   2. __vb.moONap()                   -> tạo ô chọn file; dùng công cụ file_upload đưa vbee_<bộ>.json vào ô #__vbin
//      __vb.daNap()                    -> số bài đã nạp
//   3. await __vb.taoThu()             -> tạo bài đầu tiên (tốn điểm), trả id
//      await __vb.trangThai()          -> gọi vài lần tới khi bài 1 SUCCESS; __vb.links(1,1) lấy link nghe thử
//   4. __vb.taoLoat()                  -> Web Worker gửi các bài còn lại, cách nhau 1,5 s (chạy được cả khi tab ẩn)
//      __vb.tienDo()                   -> đã gửi bao nhiêu, có lỗi không
//   5. await __vb.trangThai()          -> {st:{SUCCESS:n,…}, bad:[…], nlinks}; Vbee xếp hàng, chờ 1–2 phút
//   6. __vb.goc()                      -> đầu link S3 (vd https://vbee-studio2-3.s3.ap-southeast-1.amazonaws.com/synthesis/)
//      __vb.links(1,9), __vb.links(10,18) … -> "NN|YYYY/MM/DD/ten_file.mp3" theo lô 9 bài (kết quả dài ~1000 ký tự bị cắt)
//      ghi các dòng đó vào links.txt rồi chạy tai_mp3.py (--goc nếu đầu link khác mặc định).
// Token chỉ dùng trong trang, không in ra. Thiết lập giọng nằm ở __vb.CFG.
window.__vb = {
  CFG: {
    voiceCode: 'hn_female_ngochuyen_full_48k-fhg', speed: 1.1, audioType: 'mp3', bitrate: 128,
    backgroundMusic: {volume: 80},
    clientPause: {majorBreak: 0.15, mediumBreak: 0.1, paragraphBreak: 0.25, sentenceBreak: 0.2}
  },
  API: 'https://vbee.vn/api',
  ids: {}, linksMap: {}, log: [], done: false, t0: null,

  // Redux store nằm sâu trong cây React: duyệt child + sibling từ #root (cách đi child||return không ra).
  timStore() {
    const root = document.getElementById('root') || document.body.firstElementChild;
    const k = Object.keys(root).find(k => k.startsWith('__reactContainer') || k.startsWith('__reactFiber'));
    let start = root[k]; if (start && start.current) start = start.current;
    const stack = [start]; let n = 0;
    while (stack.length && n < 20000) {
      const f = stack.pop(); n++; if (!f) continue;
      const p = f.memoizedProps; if (p && p.store && typeof p.store.getState === 'function') return p.store;
      if (f.sibling) stack.push(f.sibling); if (f.child) stack.push(f.child);
    }
    return null;
  },
  H() { return {'Content-Type': 'application/json', Authorization: 'Bearer ' + this.tok}; },

  async timToken() {
    const st = this.timStore(); const s = st && st.getState();
    this.tok = s && s.auth && s.auth.accessToken;
    if (!this.tok) return {tok: false, goiY: 'Chưa đăng nhập Vbee, hoặc trang chưa tải xong. Tải lại trang rồi gọi lại.'};
    return {tok: true, ganDay: await this.ganDay(8)};
  },
  async ganDay(n) {
    const r = await fetch(`${this.API}/v2/requests?limit=${n}&fields=id,title,status,speed,voice,characters,createdAt&sort=createdAt_desc`,
      {headers: this.H()}).then(r => r.json());
    const arr = (r.result && (r.result.requests || r.result)) || [];
    return (Array.isArray(arr) ? arr : []).map(x => [x.title, x.status, x.voice && (x.voice.code || x.voice.name), x.speed, x.created_at || x.createdAt]);
  },

  moONap() {
    let inp = document.getElementById('__vbin');
    if (!inp) {
      inp = document.createElement('input'); inp.type = 'file'; inp.id = '__vbin';
      inp.setAttribute('aria-label', 'nap du lieu kich ban');
      inp.style.cssText = 'position:fixed;top:0;left:0;z-index:99999';
      document.body.appendChild(inp);
    }
    inp.onchange = async () => { this.data = JSON.parse(await inp.files[0].text()); };
    return 'đã tạo ô #__vbin — dùng file_upload đưa vbee_<bộ>.json vào';
  },
  daNap() {
    const d = this.data || [];
    return {n: d.length, dau: d[0] && d[0].title, cuoi: d.length && d[d.length - 1].title};
  },
  body(x) { return Object.assign({title: x.title, text: x.text}, this.CFG); },

  async taoThu() {
    this.t0 = new Date().toISOString();
    const x = this.data[0];
    const r = await fetch(`${this.API}/v1/synthesis`, {method: 'POST', headers: this.H(), body: JSON.stringify(this.body(x))});
    const j = await r.json();
    const id = j && j.result && j.result.request_id;     // mã request nằm ở result.request_id (regex "id" bắt nhầm id lồng)
    if (id) this.ids[x.n] = id;
    return {http: r.status, ok: j.status, id, diem: j.result && j.result.credits};
  },

  taoLoat(tu) {
    const items = this.data.filter(x => !this.ids[x.n] && (!tu || x.n >= tu)).map(x => ({n: x.n, body: this.body(x)}));
    const code = `onmessage=async(e)=>{const {tok,items,api}=e.data;for(const it of items){try{
      const r=await fetch(api+'/v1/synthesis',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+tok},body:JSON.stringify(it.body)});
      const j=await r.json();postMessage({n:it.n,id:j&&j.result&&j.result.request_id,st:r.status,diem:j&&j.result&&j.result.credits});
    }catch(err){postMessage({n:it.n,err:String(err)});}await new Promise(r=>setTimeout(r,1500));}postMessage({done:true});};`;
    const w = new Worker(URL.createObjectURL(new Blob([code], {type: 'application/javascript'})));
    this.done = false;
    w.onmessage = (e) => { if (e.data.done) { this.done = true; return; } this.log.push(e.data); if (e.data.id) this.ids[e.data.n] = e.data.id; };
    w.postMessage({tok: this.tok, items, api: this.API});
    this.w = w;
    return 'bắt đầu gửi ' + items.length + ' bài (mỗi bài ~1,5 s)';
  },
  tienDo() {
    return {xong: this.done, daGui: this.log.length, coId: Object.keys(this.ids).length,
            loi: this.log.filter(x => x.err || x.st !== 200).map(x => x.n + ':' + (x.err || x.st))};
  },

  async trangThai() {
    const n = Math.min(100, Object.keys(this.ids).length + 10);
    const r = await fetch(`${this.API}/v2/requests?limit=${n}&fields=id,title,progress,status,audioLink,createdAt,characters,speed,voice&sort=createdAt_desc`,
      {headers: this.H()}).then(r => r.json());
    const by = {}; for (const q of ((r.result && r.result.requests) || [])) by[q.id] = q;
    const st = {}; const bad = [];
    for (const [nn, id] of Object.entries(this.ids)) {
      const q = by[id]; if (!q) { bad.push(nn + ':chưa thấy'); continue; }
      st[q.status] = (st[q.status] || 0) + 1;
      if (q.status === 'SUCCESS') this.linksMap[nn] = q.audio_link || q.audioLink;
      else bad.push(nn + ':' + q.status + ':' + (q.progress || ''));
      if (q.speed != this.CFG.speed || (q.voice && q.voice.code && q.voice.code !== this.CFG.voiceCode)) bad.push(nn + ':sai giọng/tốc độ');
    }
    return {st, bad, nlinks: Object.keys(this.linksMap).length, tong: (this.data || []).length};
  },
  goc() {
    const u = Object.values(this.linksMap)[0] || ''; const i = u.indexOf('/synthesis/');
    return i >= 0 ? u.slice(0, i + 11) : u;
  },
  links(tu, den) {
    const out = [];
    for (const nn of Object.keys(this.linksMap).map(Number).sort((a, b) => a - b)) {
      if (nn < tu || nn > den) continue;
      const u = this.linksMap[nn]; const i = u.indexOf('/synthesis/');
      out.push(String(nn).padStart(2, '0') + '|' + (i >= 0 ? u.slice(i + 11) : u));   // "NN|YYYY/MM/DD/ten_file.mp3"
    }
    return out.join('\n');
  }
};
'đã nạp __vb — gọi __vb.timToken()';
