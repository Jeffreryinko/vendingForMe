/* tour.js — 자판기 홈 '둘러보기': 폰 시연(카드 넘기기 → ✎ 생각 → 보관함) + 앱 여섯 개 한눈에. 토큰 0, 외부 코드 없음.
 *  만든 방식: Stageshow(benjitaylor/skills, MIT)의 제작 규칙을 따라 손으로 그림 —
 *   · 진짜 글자는 이야기가 걸린 곳에만(카드 제목·생각·저장), 나머지는 회색 막대
 *   · 폰은 위에서 고정하고 아래로 잘라 냄(무대가 곧 장면, 받침판 없음), 보관함 카드는 폰 가장자리에 반쯤 걸침
 *   · 손가락은 '터치' 원, 4박자 + 결과 2초 유지, 되돌리기는 다음 카드가 들어오는 것으로(거꾸로 재생 없음)
 *   · 움직임 줄이기 설정이면 결과 장면 한 장만
 */
(function () {
  "use strict";
  var host = document.getElementById("tour"); if (!host) return;
  var W = 358, H = 340;
  var esc = function (t) { return String(t).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var CARDS = [
    { tag: "시사", cls: "s", meta: "🇺🇸 🇩🇪 🇯🇵 · 18개국", t: "미국 중간선거 개표, 첫 당선자 나왔어요", note: "해설 뒤 새 기사 3개" },
    { tag: "역사", cls: "h", meta: "1592~1598 · 동아시아 · 한국", t: "임진왜란", note: "" }
  ];
  var THINK = "해전 보급로가 승패를 갈랐다", Q = "전쟁이 기술을 어떻게 바꾸나?";

  function card(c) {
    return '<div class="vt-card"><div class="vt-k"><span class="vt-tag ' + c.cls + '">' + c.tag + '</span><span class="vt-m">' + esc(c.meta) + "</span></div>" +
      '<div class="vt-t">' + esc(c.t) + "</div>" + (c.note ? '<div class="vt-since">' + esc(c.note) + "</div>" : "") +
      '<i class="vt-bar" style="width:92%"></i><i class="vt-bar" style="width:78%"></i><i class="vt-bar" style="width:64%"></i>' +
      '<div class="vt-acts"><span>♡ 좋아요</span><span class="vt-think" data-tg="think">✎ 생각</span><span>↗ 공유</span></div></div>';
  }
  var css = document.createElement("style");
  css.textContent =
    ".vt{margin:4px 0 12px;word-break:keep-all}.vt-sum{display:flex;align-items:center;gap:8px;width:100%;border:0;background:var(--ap-surface);border-radius:14px;padding:12px 14px;font:inherit;color:var(--ap-label);text-align:left}" +
    ".vt-sum b{flex:1;font-size:15px}.vt-sum small{color:var(--ap-label2);font-size:13px}.vt-sum i{font-style:normal;color:var(--ap-label2);transition:transform .25s}.vt.open .vt-sum i{transform:rotate(90deg)}" +
    ".vt-body{display:none}.vt.open .vt-body{display:block}" +
    ".vt-stage{position:relative;width:100%;max-width:420px;margin:10px auto 0;aspect-ratio:" + W + "/" + H + ";overflow:hidden;border-radius:18px}" +
    ".vt-in{position:absolute;left:0;top:0;width:" + W + "px;height:" + H + "px;transform-origin:0 0}" +
    /* 폰: 위에서 고정, 아래로 잘림 */
    ".vt-phone{position:absolute;z-index:1;left:20px;top:20px;width:232px;height:440px;border-radius:38px;background:#0b0b0c;padding:8px;box-sizing:border-box;box-shadow:0 18px 40px rgba(0,0,0,.18),0 2px 6px rgba(0,0,0,.12)}" +
    ".vt-scr{position:relative;width:100%;height:100%;border-radius:30px;overflow:hidden;background:var(--ap-bg)}" +
    ".vt-sb{display:flex;justify-content:space-between;align-items:center;padding:9px 18px 0;font:600 11px/1 var(--ap-font);color:var(--ap-label)}.vt-isl{position:absolute;left:50%;top:7px;width:66px;height:18px;border-radius:10px;background:#0b0b0c;transform:translateX(-50%)}" +
    ".vt-sb .r{display:flex;gap:3px}.vt-sb .r i{display:block;width:12px;height:7px;border-radius:2px;background:var(--ap-label)}" +
    ".vt-hd{padding:16px 14px 0}.vt-dt{font:600 10px/1.3 var(--ap-font);color:var(--ap-label2)}.vt-h1{font:800 24px/1.15 var(--ap-font);letter-spacing:-.03em;color:var(--ap-label);margin-top:1px}" +
    ".vt-sr{margin:8px 14px 0;height:24px;border-radius:8px;background:var(--ap-fill)}" +
    ".vt-deck{position:absolute;z-index:2;left:10px;right:10px;top:122px}" +
    ".vt-card{position:absolute;left:0;right:0;top:0;background:var(--ap-surface);border-radius:16px;padding:12px 12px 10px;box-shadow:0 1px 3px rgba(0,0,0,.06);font-family:var(--ap-font)}" +
    ".vt-k{display:flex;gap:6px;align-items:center;font-size:9.5px;color:var(--ap-label2)}.vt-tag{font-weight:700;font-size:9.5px;padding:2px 7px;border-radius:99px}" +
    ".vt-tag.s{background:color-mix(in srgb,var(--ap-blue) 15%,transparent);color:var(--ap-blue-t)}.vt-tag.h{background:rgba(162,132,94,.18);color:#8a5a2b}" +
    ".vt-t{font-weight:800;font-size:15px;line-height:1.3;letter-spacing:-.02em;color:var(--ap-label);margin:7px 0 6px}" +
    ".vt-since{display:inline-block;font-size:9.5px;font-weight:700;color:var(--ap-orange-t);background:color-mix(in srgb,var(--ap-orange) 15%,transparent);border-radius:6px;padding:3px 7px;margin:0 0 8px}" +
    ".vt-bar{display:block;height:6px;border-radius:3px;background:var(--ap-fill);margin:0 0 7px}" +
    ".vt-acts{display:flex;gap:6px;margin-top:10px}.vt-acts span{flex:1;text-align:center;font-size:10px;font-weight:600;padding:7px 0;border-radius:9px;background:var(--ap-fill);color:var(--ap-label)}" +
    ".vt-think.on{background:var(--ap-blue);color:#fff}" +
    /* 생각 남기기 창 */
    ".vt-sheet{position:absolute;z-index:5;left:0;right:0;bottom:0;top:150px;background:var(--ap-bg);border-radius:18px 18px 0 0;box-shadow:0 -6px 20px rgba(0,0,0,.14);padding:8px 12px;transform:translateY(105%);font-family:var(--ap-font)}" +
    ".vt-grab{width:28px;height:4px;border-radius:2px;background:var(--ap-label3);margin:0 auto 8px}.vt-sh{font-weight:800;font-size:15px;color:var(--ap-label)}" +
    ".vt-qc{display:inline-block;margin:8px 0 8px;font-size:10px;font-weight:700;padding:5px 9px;border-radius:99px;background:var(--ap-blue);color:#fff}" +
    ".vt-lb{font-size:9.5px;font-weight:700;color:var(--ap-label);margin:2px 1px 3px}.vt-ta{min-height:30px;border-radius:9px;background:var(--ap-fill);padding:7px 8px;font-size:11px;color:var(--ap-label);box-sizing:border-box}" +
    ".vt-ta .caret{display:inline-block;width:1px;height:11px;background:var(--ap-blue);vertical-align:-1px;margin-left:1px}" +
    ".vt-ta.ph{color:transparent}.vt-save{margin-top:10px;text-align:center;font-size:12px;font-weight:700;padding:9px 0;border-radius:10px;background:var(--ap-blue);color:#fff}" +
    ".vt-toast{position:absolute;z-index:6;left:50%;bottom:22px;transform:translate(-50%,10px);opacity:0;white-space:nowrap;font:600 10px/1 var(--ap-font);background:rgba(30,30,32,.9);color:#fff;padding:8px 11px;border-radius:99px}" +
    /* 보관함 카드: 폰 오른쪽 가장자리에 반쯤 걸침 */
    ".vt-sat{position:absolute;z-index:3;left:184px;top:58px;width:152px;background:var(--ap-surface);border-radius:14px;padding:11px 12px;box-shadow:0 10px 28px rgba(0,0,0,.16),0 1px 3px rgba(0,0,0,.08);font-family:var(--ap-font);opacity:0;transform:translateY(14px) scale(.96)}" +
    ".vt-sat .a{font-size:9.5px;font-weight:700;color:var(--ap-label2)}.vt-sat .q{font-size:11.5px;font-weight:800;line-height:1.35;color:var(--ap-label);margin:4px 0 7px}" +
    ".vt-sat .l{display:flex;gap:6px;align-items:baseline;font-size:10px;color:var(--ap-label);border-top:.5px solid var(--ap-sep);padding-top:6px}.vt-sat .l b{flex:none;white-space:nowrap;font-size:9px;color:var(--ap-label2)}" +
    ".vt-sat .n{display:flex;gap:10px;margin-top:8px}.vt-sat .n span{font-size:9.5px;color:var(--ap-label2)}.vt-sat .n b{display:block;font-size:17px;color:var(--ap-label)}" +
    /* 손가락 */
    ".vt-touch{position:absolute;z-index:7;left:0;top:0;width:34px;height:34px;margin:-17px 0 0 -17px;border-radius:50%;background:rgba(120,120,128,.34);box-shadow:0 0 0 1.5px rgba(255,255,255,.75) inset;opacity:0;pointer-events:none}" +
    /* 여섯 앱 한눈에 */
    ".vt-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:12px 0 2px}" +
    ".vt-tile{position:relative;border:0;padding:0;background:var(--ap-surface);border-radius:16px;overflow:hidden;text-align:left;font:inherit;color:var(--ap-label);height:168px;cursor:pointer}" +
    ".vt-art{position:absolute;left:12px;right:-14px;top:12px;height:96px;border-radius:11px 0 0 11px;background:var(--ap-bg);overflow:hidden;padding:9px 26px 9px 10px;box-sizing:border-box}" +
    ".vt-cap{position:absolute;left:12px;right:12px;bottom:11px}.vt-cap b{display:block;font-size:14px}.vt-cap small{display:block;font-size:11.5px;color:var(--ap-label2);line-height:1.35;margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}" +
    ".vt-art .bar{display:block;height:5px;border-radius:3px;background:var(--ap-fill);margin:0 0 6px}" +
    ".vt-art .pill{display:inline-block;font-size:9.5px;font-weight:700;padding:3px 7px;border-radius:6px}" +
    ".vt-art .t{font-size:11.5px;font-weight:800;line-height:1.3;margin:0 0 6px;color:var(--ap-label)}" +
    ".vt-seg{display:flex;gap:2px;padding:2px;border-radius:7px;background:var(--ap-fill);margin:0 0 9px}.vt-seg span{flex:1;font-size:8.5px;text-align:center;padding:4px 0;border-radius:5px;white-space:nowrap}.vt-seg span.on{background:var(--ap-seg-on);font-weight:700;box-shadow:0 1px 3px rgba(0,0,0,.12)}" +
    ".vt-pop{position:absolute;left:44px;top:34px;display:flex;gap:2px;background:rgba(30,30,32,.92);border-radius:8px;padding:3px}.vt-pop span{font-size:9px;color:#fff;padding:4px 6px;border-radius:5px}.vt-pop span:first-child{background:rgba(255,255,255,.18)}" +
    ".vt-u{border-bottom:1.5px solid var(--ap-purple);font-weight:700}" +
    ".vt-g{position:relative;height:13px;margin:0 0 6px}.vt-g i{position:absolute;top:0;height:13px;border-radius:4px;background:rgba(162,132,94,.24);font-style:normal;font-size:8.5px;font-weight:700;color:#8a5a2b;padding-left:4px;line-height:13px;white-space:nowrap}" +
    ".vt-star{font-size:10px;font-weight:800;color:var(--ap-teal)}" +
    "@media (prefers-color-scheme:dark){.vt-tag.h,.vt-g i{color:#d8b28a}.vt-phone{box-shadow:0 0 0 1px rgba(255,255,255,.14),0 18px 40px rgba(0,0,0,.5)}}";
  document.head.appendChild(css);

  var open = true; try { open = localStorage.getItem("vfm:tour") !== "0" && !Object.keys(JSON.parse(localStorage.getItem("vfm:seen:mix") || "{}")).length; if (localStorage.getItem("vfm:tour") === "1") open = true; } catch (e) { }
  var tiles = [
    ["sisa", "시사", "세계 뉴스를 한국어로", '<span class="pill" style="background:color-mix(in srgb,var(--ap-blue) 15%,transparent);color:var(--ap-blue-t)">시사</span><div class="t" style="margin-top:6px">이 해설을 쓴 뒤<br>새 기사 3개</div><i class="bar" style="width:80%"></i><i class="bar" style="width:58%"></i>'],
    ["iyagi", "이야기", "깊이를 골라 읽기", '<div class="vt-seg"><span class="on">한눈에</span><span>자세히</span><span>너머</span></div><div class="t">오르페우스</div><i class="bar" style="width:86%"></i><i class="bar" style="width:62%"></i>'],
    ["ai", "AI", "낱말 눌러 용어장", '<i class="bar" style="width:70%"></i><div style="font-size:10.5px;margin:2px 0 7px">모델의 <span class="vt-u">추론</span> 속도를</div><i class="bar" style="width:84%"></i><i class="bar" style="width:52%"></i><div class="vt-pop"><span>용어카드</span><span>메모</span><span>검색</span></div>'],
    ["history", "역사", "나라의 일생·나란히", '<div class="vt-g"><i style="left:0;width:44%">고려</i><i style="left:46%;width:52%">조선</i></div><div class="vt-g"><i style="left:12%;width:30%;background:color-mix(in srgb,var(--ap-blue) 14%,transparent);color:var(--ap-blue-t)">송</i><i style="left:50%;width:22%;background:color-mix(in srgb,var(--ap-blue) 14%,transparent);color:var(--ap-blue-t)">명</i></div><i class="bar" style="width:66%"></i><i class="bar" style="width:48%"></i>'],
    ["tools", "도구", "요즘 뜨는 도구", '<div style="display:flex;justify-content:space-between;align-items:baseline"><div class="t" style="margin:0">stageshow</div><span class="vt-star">★ +1.2천</span></div><i class="bar" style="width:76%;margin-top:7px"></i><i class="bar" style="width:54%"></i><div class="pill" style="background:color-mix(in srgb,var(--ap-teal) 16%,transparent);color:var(--ap-teal)">오늘 뜨는 것</div>'],
    ["box", "보관함", "내 질문과 생각", '<div class="t">전쟁이 기술을 어떻게 바꾸나?</div><div style="font-size:9.5px;margin:0 0 5px"><b style="color:var(--ap-label2)">발견</b> 해전 보급로가 승패를…</div><i class="bar" style="width:72%"></i><i class="bar" style="width:50%"></i>']
  ];
  host.className = "vt" + (open ? " open" : "");
  host.innerHTML = '<button type="button" class="vt-sum" data-vt="toggle"><b>자판기 둘러보기</b><small>10초 시연 · 앱 여섯 개</small><i>›</i></button>' +
    '<div class="vt-body"><div class="vt-stage" aria-label="자판기 사용 시연: 카드를 넘기고, 생각을 남기면 보관함에 모여요" role="img"><div class="vt-in">' +
    '<div class="vt-phone"><div class="vt-scr"><div class="vt-isl"></div><div class="vt-sb"><span>9:41</span><span class="r"><i></i><i></i></span></div>' +
    '<div class="vt-hd"><div class="vt-dt">11월 5일 목요일</div><div class="vt-h1">자판기</div></div><div class="vt-sr"></div>' +
    '<div class="vt-deck"><div data-c="0">' + card(CARDS[0]) + '</div><div data-c="1">' + card(CARDS[1]) + "</div></div>" +
    '<div class="vt-sheet"><div class="vt-grab"></div><div class="vt-sh">생각 남기기</div><div class="vt-qc">' + esc(Q) + '</div>' +
    '<div class="vt-lb">내가 발견한 점</div><div class="vt-ta" data-ta></div><div class="vt-lb" style="margin-top:7px">내 일에 적용한다면</div><div class="vt-ta ph">.</div><div class="vt-save" data-tg="save">저장</div></div>' +
    '<div class="vt-toast">생각을 남겼어요 · 보관함에 모여요</div></div></div>' +
    '<div class="vt-sat"><div class="a">보관함 · 이번 주</div><div class="q">' + esc(Q) + '</div><div class="l"><b>발견</b><span>' + esc(THINK) + '</span></div></div>' +
    '<div class="vt-touch"></div></div></div>' +
    '<div class="vt-grid">' + tiles.map(function (t) { return '<button type="button" class="vt-tile" data-vt-go="' + t[0] + '"><div class="vt-art">' + t[3] + '</div><div class="vt-cap"><b>' + t[1] + "</b><small>" + t[2] + "</small></div></button>"; }).join("") + "</div>" +
    '<p class="cap" style="margin:8px 4px 0;font-size:11.5px">가입 없이 바로 써요. 기록은 이 폰 안에만 있고, 구글로 로그인하면 PC와 이어져요.</p></div>';

  var stage = host.querySelector(".vt-stage"), inner = host.querySelector(".vt-in");
  function fit() { var w = stage.clientWidth || W; inner.style.transform = "scale(" + (w / W) + ")"; }
  window.addEventListener("resize", fit);

  host.addEventListener("click", function (e) {
    var t = e.target.closest("[data-vt],[data-vt-go]"); if (!t) return;
    if (t.hasAttribute("data-vt-go")) { var a = t.getAttribute("data-vt-go"); try { sessionStorage.setItem("vfm:fromHome", "1"); } catch (x) { } location.href = a + "/"; return; }
    var on = !host.classList.contains("open"); host.classList.toggle("open", on);
    try { localStorage.setItem("vfm:tour", on ? "1" : "0"); } catch (x) { }
    if (on) { fit(); start(); } else stop();
  });

  /* ── 시연 (4박자 + 결과 유지, 약 12초) ── */
  var $ = function (s) { return host.querySelector(s); };
  var touch = $(".vt-touch"), c0 = $('[data-c="0"]'), c1 = $('[data-c="1"]'), sheet = $(".vt-sheet"), ta = $("[data-ta]"), toast = $(".vt-toast"), sat = $(".vt-sat");
  var EASE = "cubic-bezier(0.3, 0.75, 0.1, 1)", ARRIVE = "cubic-bezier(0.25, 0.8, 0.25, 1)", TRAVEL = "cubic-bezier(0.45, 0, 0.1, 1)";
  var timers = [], running = false, front = 0, reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  function at(ms, f) { timers.push(setTimeout(f, ms)); }
  function stop() { running = false; timers.forEach(clearTimeout); timers = []; }
  function anim(el, kf, o) { return el.animate(kf, Object.assign({ fill: "forwards" }, o)); }
  function pos(el) { var r = el.getBoundingClientRect(), b = inner.getBoundingClientRect(), s = b.width / W; return [(r.left - b.left + r.width / 2) / s, (r.top - b.top + r.height / 2) / s]; }
  var tx = 170, ty = 300;
  function moveTo(x, y, d) { anim(touch, [{ transform: "translate(" + tx + "px," + ty + "px)", opacity: getComputedStyle(touch).opacity }, { transform: "translate(" + x + "px," + y + "px)", opacity: 1 }], { duration: d || 700, easing: TRAVEL }); tx = x; ty = y; }
  function press() { anim(touch, [{ transform: "translate(" + tx + "px," + ty + "px) scale(1)" }, { transform: "translate(" + tx + "px," + ty + "px) scale(.78)" }, { transform: "translate(" + tx + "px," + ty + "px) scale(1)" }], { duration: 260, easing: "ease-out" }); }
  function hideTouch() { anim(touch, [{ opacity: 1, transform: "translate(" + tx + "px," + ty + "px)" }, { opacity: 0, transform: "translate(" + tx + "px," + ty + "px)" }], { duration: 300 }); }
  function cards() { return front === 0 ? [c0, c1] : [c1, c0]; }
  function layout() { var p = cards(); p[0].style.cssText = "position:relative;z-index:2"; p[1].style.cssText = "position:absolute;left:0;right:0;top:0;z-index:1;transform:translateY(8px) scale(.96);opacity:.0"; p[0].getAnimations().forEach(function (a) { a.cancel(); }); p[1].getAnimations().forEach(function (a) { a.cancel(); }); }
  function reset() {
    [sheet, toast, sat, touch].forEach(function (el) { el.getAnimations().forEach(function (a) { a.cancel(); }); });
    ta.textContent = ""; host.querySelectorAll(".vt-think").forEach(function (b) { b.classList.remove("on"); });
    layout();
  }
  function poster() {                                                  // 결과 장면 (움직임 줄이기·첫 화면)
    reset(); ta.textContent = THINK; sat.style.opacity = 1; sat.style.transform = "none";
  }
  function loop() {
    if (!running) return;
    var p = cards(), think = p[0].querySelector(".vt-think");
    // 1. 카드를 옆으로 밀어 다음 카드
    at(500, function () { moveTo(206, 216, 650); });
    at(1250, function () { anim(touch, [{ transform: "translate(206px,216px) scale(1)" }, { transform: "translate(206px,216px) scale(.86)" }], { duration: 120 }); });
    at(1380, function () {
      moveTo(70, 220, 320);
      anim(p[0], [{ transform: "translateX(0) rotate(0)", opacity: 1 }, { transform: "translateX(-260px) rotate(-6deg)", opacity: .9 }], { duration: 420, easing: "cubic-bezier(0.25, 1, 0.5, 1)" });
      anim(p[1], [{ transform: "translateY(8px) scale(.96)", opacity: 0 }, { transform: "none", opacity: 1 }], { duration: 480, easing: EASE, delay: 80 });
    });
    at(1900, function () { front = 1 - front; var q = cards(); q[0].style.zIndex = 2; q[1].style.zIndex = 1; think = q[0].querySelector(".vt-think"); });
    // 2. ✎ 생각 누르기 → 창이 올라옴
    at(2400, function () { var xy = pos(think); moveTo(xy[0], xy[1], 700); });
    at(3150, function () { press(); think.classList.add("on"); });
    at(3350, function () { anim(sheet, [{ transform: "translateY(105%)" }, { transform: "translateY(0)" }], { duration: 500, easing: EASE }); hideTouch(); });
    // 3. 글자 들어감
    at(3950, function () { var i = 0; (function ty1() { if (!running) return; ta.innerHTML = esc(THINK.slice(0, ++i)) + '<span class="caret"></span>'; if (i < THINK.length) timers.push(setTimeout(ty1, 70)); })(); });
    // 4. 저장 → 창 닫힘, 보관함 카드가 생각을 싣고 도착
    at(6100, function () { ta.textContent = THINK; var xy = pos($('[data-tg="save"]')); tx = xy[0] + 40; ty = xy[1] + 50; moveTo(xy[0], xy[1], 500); });
    at(6700, function () { press(); });
    at(6900, function () {
      anim(sheet, [{ transform: "translateY(0)" }, { transform: "translateY(105%)" }], { duration: 420, easing: EASE }); think.classList.remove("on"); hideTouch();
      anim(toast, [{ opacity: 0, transform: "translate(-50%,10px)" }, { opacity: 1, transform: "translate(-50%,0)" }], { duration: 300, easing: ARRIVE });
      anim(sat, [{ opacity: 0, transform: "translateY(14px) scale(.96)" }, { opacity: 1, transform: "none" }], { duration: 850, easing: ARRIVE, delay: 250 });
    });
    // 결과 유지 2초+ → 보관함 카드·알림이 함께 물러나고, 다음 카드로 이어짐
    at(10200, function () { anim(toast, [{ opacity: 1 }, { opacity: 0 }], { duration: 300 }); anim(sat, [{ opacity: 1, transform: "none" }, { opacity: 0, transform: "translateY(10px)" }], { duration: 380, delay: 60, easing: TRAVEL }); });
    at(10800, function () { reset(); tx = 170; ty = 300; loop(); });
  }
  function start() { if (!host.classList.contains("open")) return; stop(); fit(); if (reduce || !inner.animate) { poster(); return; } running = true; reset(); loop(); }
  // 화면에 보일 때만 돌림 (배터리)
  if ("IntersectionObserver" in window) new IntersectionObserver(function (es) { es.forEach(function (en) { if (en.isIntersecting) { if (!running) start(); } else stop(); }); }, { threshold: .3 }).observe(stage);
  else start();
  document.addEventListener("visibilitychange", function () { if (document.hidden) stop(); else start(); });
  fit(); if (!open) poster();
})();
