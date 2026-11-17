/* 종이판 — 브로제이 영업 허브 (자료: data/hub/hub.json ← robot/hub_snapshot.py)
   허브의 읽을거리 200편·근거 572건·문자 시안·제품·문자 규칙·해외 자료를 전자잉크용 글 페이지로.
   계산기처럼 움직이는 것은 가정값 표로, 퀴즈는 '정답 보기'로 바꿨어요. 검색엔진에는 안 나오게 해요(noindex). */
"use strict";
module.exports = function (H, opt) {
  const { esc, inl, md, sec, ul, ext, page, paged, quizHtml } = H;
  const D = opt.data, B = opt.B, label = opt.label || "영업 허브", C = opt.home ? [] : [[B + "index.html", label]];
  if (!D || !D.read) return null;
  const V = D.views || {}, rows = (D.data && D.data.rows) || [], cats = (D.data && D.data.cats) || [], E = D.evx || {}, EX = E.ex || {}, GEN = E.gen || {};
  const P = (file, o) => page(file, Object.assign({ noindex: true }, o));
  const rowBy = new Map(rows.map(r => [r[0], r]));
  const pre = s => `<p class="sms">${esc(s).replace(/\n/g, "<br>")}</p>`;
  const vhtml = h => `<div class="v">${h || ""}</div>`;
  const CP = !!opt.compact;   // 아티팩트판: 근거를 분야 페이지 안에 모아 파일 수를 줄여요
  const catOf = new Map(rows.map(r => [r[0], r[1]]));
  const evHref = n => CP ? `${B}ev/c${catOf.get(n)}.html#n${n}` : `${B}ev/${n}.html`;
  const evLink = n => rowBy.has(n) ? `<a href="@${evHref(n)}">#${n} ${esc(rowBy.get(n)[2])}</a>` : `#${n}`;

  /* 읽을거리 */
  const read = D.read, artBy = new Map(read.map(a => [a.id, a]));
  const block = b => {
    switch (b[0]) {
      case "lead": return `<p class="lead">${inl(b[1])}</p>`;
      case "p": return md(b[1]);
      case "h": return `<h2>${esc(b[1])}</h2>`;
      case "num": return "";
      case "nums": return `<p class="chips"><small>근거</small> ${(b[1] || []).map(evLink).join(" · ")}</p>`;
      case "story": return `<div class="box"><h3>${esc(b[1])}</h3>${md(b[2])}</div>`;
      case "ana": return sec("비유로 보면", md(b[1]), "box");
      case "bar": { const mx = Math.max(...b[2].map(x => +x[1] || 0), 1);
        return `<div class="box"><h3>${esc(b[1])}</h3>${b[2].map(x => `<div class="bar"><span>${esc(x[0])}</span><i style="width:${Math.max(2, (+x[1] || 0) / mx * 100)}%"></i><b>${esc(x[2])}</b></div>`).join("")}<p class="note">${esc(b[3] || "")}${b[4] ? " · " + evLink(b[4]) : ""}</p></div>`; }
      case "pull": return `<blockquote>${inl(b[1])}</blockquote>`;
      case "myth": return `<div class="mis"><p><b>흔한 생각</b> ${inl(b[1])}</p><p><b>실제로는</b> ${inl(b[2])}</p></div>`;
      case "quiz": return sec("확인 문제", quizHtml([{ q: b[1], o: b[2], a: b[3], why: b[4] }]));
      case "broj": return sec(esc(b[1]), ul(b[2], inl), "box");
      case "talk": return sec("통화에서 이렇게", md(b[1]), "box");
      case "sms": return sec("보낼 문자", pre(b[1]));
      case "warn": return `<div class="mis"><p><b>주의</b> ${inl(b[1])}</p></div>`;
      case "check": return sec("통화 전에 확인할 것", ul(b[1], inl));
      case "qa": return `<h4>Q. ${esc(b[1])}</h4>${md(b[2])}`;
      case "calc": return `<p class="note">계산기는 <a href="@${B}v/calc.html">새는 매출 계산</a>에서 가정값으로 보세요.</p>`;
      case "tbl": return `<h3>${esc(b[1])}</h3><table class="kv"><tr>${b[2].map(x => `<th>${esc(x)}</th>`).join("")}</tr>${b[3].map(r => `<tr>${r.map(x => `<td>${inl(x)}</td>`).join("")}</tr>`).join("")}</table>`;
      case "steps": return sec(esc(b[1]), `<ol>${b[2].map(x => `<li>${inl(x)}</li>`).join("")}</ol>`);
      default: return typeof b[1] === "string" ? md(b[1]) : "";
    }
  };
  const topics = [...new Set(read.map(a => a.topic))];
  const order = topics.flatMap(t => read.filter(a => a.topic === t));
  const tIdx = new Map(topics.map((t, i) => [t, i]));
  const artHref = a => CP ? `${B}r/t${tIdx.get(a.topic)}.html#${a.id}` : `${B}r/${a.id}.html`;
  const artBody = a => `<p class="lead">${inl(a.dek || "")}</p>` + (a.cover ? `<p class="big">${esc(a.cover)}</p><p class="note">${esc(a.coverNote || "")}</p>` : "") + sec("세 줄 요약", ul(a.tldr, inl), "box") + (a.blocks || []).map(block).join("");
  if (CP) topics.forEach((t, ti) => { const l = read.filter(a => a.topic === t);   // 아티팩트판: 주제 하나 = 한 파일
    P(`${B}r/t${ti}.html`, { title: t, crumbs: C.concat([[`${B}read.html`, "읽을거리"]]), sub: `${l.length}편`,
      body: l.map(a => `<h1 id="${a.id}" class="art">${esc(a.title)}</h1>` + artBody(a).replace(/<h2>/g, "<h3>").replace(/<\/h2>/g, "</h3>")).join(""),
      prev: ti > 0 ? [`${B}r/t${ti - 1}.html`, "앞 주제"] : null, next: ti < topics.length - 1 ? [`${B}r/t${ti + 1}.html`, "다음 주제"] : null, up: [`${B}read.html`, "목록"] }); });
  if (!CP) order.forEach((a, i) => P(`${B}r/${a.id}.html`, { title: a.title, crumbs: C.concat([[`${B}read.html`, "읽을거리"]]), sub: esc([a.topic, (a.seg || []).join("·")].filter(Boolean).join(" · ")),
    body: `<p class="lead">${inl(a.dek || "")}</p>` + (a.cover ? `<p class="big">${esc(a.cover)}</p><p class="note">${esc(a.coverNote || "")}</p>` : "") + sec("세 줄 요약", ul(a.tldr, inl), "box") + (a.blocks || []).map(block).join(""),
    prev: order[i - 1] ? [`${B}r/${order[i - 1].id}.html`, "앞 글"] : null, next: order[i + 1] ? [`${B}r/${order[i + 1].id}.html`, "다음 글"] : null, up: [`${B}read.html`, "목록"] }));
  P(`${B}read.html`, { title: "읽을거리", crumbs: C, sub: `${read.length}편 · 통화 전 10분, 읽고 나면 할 말이 생겨요`, up: [B + "index.html", label],
    body: topics.map(t => { const l = read.filter(a => a.topic === t); return `<h2>${esc(t)} <small>${l.length}편</small></h2><ul class="list">${l.map(a => `<li><a href="@${artHref(a)}">${esc(a.title)}</a><br><small>${esc(a.cover || "")} ${esc(a.coverNote || "")}</small></li>`).join("")}</ul>`; }).join("") });

  /* 근거 572건 — 한 건에 한 장, 분야별 목록 */
  const byCat = cats.map((c, i) => rows.filter(r => r[1] === i));
  const GR = g => GEN[g] ? GEN[g].split(":")[0] : g;
  const evBody = r => { const [n, , val, plain, sol, src, url, grade, rec, code, sms] = r;
    return `<p class="tag">${esc(GR(grade))}</p><p class="lead">${inl(plain)}</p>` + (EX[n] ? sec("쉽게 말하면", md(EX[n]), "box") : "") + sec("브로제이로 연결", md(sol)) +
        sec("출처", `<p>${ext(url, src)}</p>${GEN[grade] ? `<p class="note">${esc(GEN[grade])}</p>` : ""}`) +
        (sms && sms.length ? sec("후속 문자 3가지", sms.map((m, k) => `<details><summary>${esc((D.data.evl || [])[k] || "문자 " + (k + 1))}</summary>${pre(m)}</details>`).join("")) : "") + `<p class="note">원래 번호 ${esc(code || "")}</p>`; };
  if (!CP) byCat.forEach((list, ci) => list.forEach((r, i) => {
    const [n, , val, , , , , , rec] = r;
    P(`${B}ev/${n}.html`, { title: `${val}`, crumbs: C.concat([[`${B}ev.html`, "근거"], [`${B}ev/c${ci}.html`, cats[ci]]]), sub: `#${n} · ${esc(cats[ci])}${rec ? " · 추천" : ""}`,
      body: evBody(r),
      prev: list[i - 1] ? [`${B}ev/${list[i - 1][0]}.html`, "앞 근거"] : null, next: list[i + 1] ? [`${B}ev/${list[i + 1][0]}.html`, "다음 근거"] : null, up: [`${B}ev/c${ci}.html`, "분야 목록"] });
  }));
  byCat.forEach((list, ci) => { const ct = (E.cat || {})[ci] || [];
    P(`${B}ev/c${ci}.html`, { title: cats[ci], crumbs: C.concat([[`${B}ev.html`, "근거"]]), sub: `${list.length}건`,
      body: (ct[1] ? `<p class="lead">${inl(ct[1])}</p>` : "") + ((ct[3] || []).filter(id => artBy.has(id)).length ? sec("함께 읽을 글", ul(ct[3].filter(id => artBy.has(id)), id => `<a href="@${artHref(artBy.get(id))}">${esc(artBy.get(id).title)}</a>`)) : "") +
        (CP ? list.map(r => `<h2 id="n${r[0]}">#${r[0]} ${esc(r[2])}${r[8] ? " <small>추천</small>" : ""}</h2>${evBody(r)}`).join("")
          : `<ol class="list">${list.map(r => `<li><a href="@${B}ev/${r[0]}.html">${esc(r[2])}</a> <small>${esc(GR(r[7]))}${r[8] ? " · 추천" : ""}</small><br>${inl(r[3])}</li>`).join("")}</ol>`),
      prev: ci > 0 ? [`${B}ev/c${ci - 1}.html`, "앞 분야"] : null, next: ci < cats.length - 1 ? [`${B}ev/c${ci + 1}.html`, "다음 분야"] : null, up: [`${B}ev.html`, "분야 목록"] }); });
  P(`${B}ev.html`, { title: "근거", crumbs: C, sub: `${rows.length}건 · 추천 ${rows.filter(r => r[8]).length}건`, up: [B + "index.html", label],
    body: vhtml(V.evidence) + `<h2>등급</h2>${ul(Object.keys(GEN), g => `<b>${esc(g)}</b> ${esc(GEN[g].split(":").slice(1).join(":"))} <small>${rows.filter(r => r[7] === g).length}건</small>`)}` +
      `<h2>분야</h2><ol class="list">${cats.map((c, i) => `<li><a href="@${B}ev/c${i}.html">${esc(c)}</a> <small>${byCat[i].length}건</small>${(E.cat || {})[i] ? `<br><small>${esc((E.cat[i][0]) || "")}</small>` : ""}</li>`).join("")}</ol>` });

  /* 문자 시안 */
  const SEG = { H: "헬스장", P: "PT샵", S: "스튜디오", M: "체육관" }, cards = D.cards || [], cardLinks = [];
  for (const s of Object.keys(SEG)) { const l = cards.filter(c => c.s === s); if (!l.length) continue;
    cardLinks.push([paged(`${B}cards-${s}`, `문자 시안 — ${SEG[s]}`, C, l, CP ? 1000 : 4, c => `<b>${esc(c.n)}</b><br><small>${esc([c.tm, (c.tp || []).join("·"), c.l].filter(Boolean).join(" · "))}</small>${pre(c.m)}`), SEG[s], l.length]); }
  /* 그대로 옮긴 화면들 */
  const VS = [["products", "제품·가격"], ["texts", "후속 문자 규칙"], ["proof", "근거 넣은 문자"], ["calc", "새는 매출 계산"], ["bench", "해외 솔루션 데이터"], ["global", "해외 출입 비교"], ["internal", "내부 메모"]];
  const leak = (D.data && D.data.leak) || [];
  for (const [k, t] of VS) if (V[k]) P(`${B}v/${k}.html`, { title: t, crumbs: C, up: [B + "index.html", label],
    body: vhtml(V[k]) + (k === "calc" && leak.length ? `<h2>새는 곳과 가정값</h2><p class="note">월 매출 = 회원 수 × 월 객단가, 새는 매출 = 월 매출 × 비율. 모두 가정값이라 고객 자료에는 "추정"으로.</p><table class="kv"><tr><th>새는 곳</th><th>업종</th><th>막는 법</th><th>가정</th></tr>${leak.map(l => `<tr><td><b>${esc(l[0])}</b></td><td>${esc(l[2])}</td><td>${esc(l[3])}</td><td>${esc(l[4] || "")}</td></tr>`).join("")}</table>` : "") });
  /* 허브 처음 */
  P(`${B}index.html`, { title: label, crumbs: [], sub: "브로제이 영업 허브 종이판 · 통화 전에 읽고, 끝나고 다시 보기", up: opt.home ? null : ["index.html", "처음"],
    body: vhtml(V.overview) + `<h2>읽기</h2><ul class="list home"><li><a href="@${B}read.html">읽을거리</a><br><small>${read.length}편 · ${topics.slice(0, 6).map(esc).join(" · ")} …</small></li><li><a href="@${B}ev.html">근거</a><br><small>${rows.length}건 · 분야 ${cats.length}개 · 근거마다 후속 문자 3가지</small></li></ul>` +
      `<h2>문자 시안 <small>${cards.length}개</small></h2><ul class="list">${cardLinks.map(c => `<li><a href="@${c[0]}">${esc(c[1])}</a> <small>${c[2]}개</small></li>`).join("")}</ul>` +
      `<h2>화면</h2><ul class="list">${VS.filter(([k]) => V[k]).map(([k, t]) => `<li><a href="@${B}v/${k}.html">${esc(t)}</a></li>`).join("")}</ul>` +
      (opt.home ? `<p><a class="btn" href="../index.html">‹ 원래 영업 허브로</a></p>` : "") +
      `<p class="note">원본 허브의 자료를 ${esc(opt.at || "")} 기준으로 옮겼어요.${D.withCost ? "" : " 원가 메모는 공개 사이트라 뺐어요."}</p>` });
  return [B + "index.html", label, `읽을거리 ${read.length}편 · 근거 ${rows.length}건 · 문자 시안 ${cards.length}개`];
};
