"""baedat_gate.py — 배댓 창고 규칙 (기획서 '배댓 수집 개편' 3·4단계). 로컬 수집기와 매일 로봇이 같이 씀.

영상 관문: 상위 댓글 10개 중 웃음 표시(ㅋㅋ·ㅎㅎ·😂·🤣)가 20% 이상 + 음악 영상·아이돌/음악방송 채널 제외
댓글 거르기: 응원·칭찬·감동 낱말이 든 댓글 제외 → 같은 영상에서 글자가 35% 이상 겹치는 댓글은 하나로 → 좋아요 상위 5개
"""
import re

MUSIC = re.compile(r"(?i)(M/?V\b|official|뮤직비디오|lyric|live clip|가사|커버|cover|\bLIVE\b|라이브|노래|stage|무대|엠카운트다운|음악중심|인기가요|뮤직뱅크|쇼챔피언|더 시즌즈|더 ?리슨|불후의|복면가왕|싱어|열린음악회)")
IDOL = re.compile(r"Mnet|\bM2\b|CHOOM|INKIGAYO|KPOP|K-POP|엠넷|1theK|HYBE|SMTOWN|JYP|YG ENTERTAINMENT|STARSHIP|직캠|fancam|MBCkpop|KBS Kpop|SBS KPOP|뮤직뱅크|음악중심|인기가요", re.I)
LAUGH = re.compile(r"ㅋㅋ|ㅎㅎ|😂|🤣")
FAN = re.compile(r"응원|화이팅|파이팅|사랑해|고마워|감사합니다|축하|수고|덕분|힘내|컴백|데뷔|우리 ?애|최애|입덕|직캠|비주얼|예쁘|이쁘|잘생|멋있|멋지|귀여|귀엽|존예|존잘|여신|왕자|미모|실력|음색|춤선|라이브|무대|❤|💜|🩷|💙|🔥|😍|🥰"
                 r"|눈물|울컥|감동|뭉클|소름|위로|힐링|ㅠㅠ|ㅜㅜ|😭|🥹"
                 r"|대박|미쳤|레전드|최고|천재|갓|대단|존경|잘한다|잘하네|연기|편집|퀄리티|고퀄")
TS = re.compile(r"(?<!\d)(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?!\d)")
PER_VIDEO = 5
LAUGH_MIN = 0.2


# 아이돌 영상: 채널 이름이 아니어도 제목에 그룹 이름·안무·챌린지가 나오면 뺌
IDOL_T = re.compile(r"안무|챌린지|challenge|댄스|dance|직캠|팬캠|아일릿|illit|뉴진스|newjeans|아이브|\bIVE\b|에스파|aespa|르세라핌|le ?sserafim|세븐틴|seventeen|방탄|\bBTS\b|블랙핑크|blackpink|트와이스|twice|스트레이 ?키즈|stray ?kids|\bNCT\b|엔시티|라이즈|riize|투어스|\bTWS\b|베이비몬스터|babymonster|키스오브라이프|\bITZY\b|있지|엔믹스|nmixx|제베원|제로베이스원|보이넥스트도어|투바투|\bTXT\b|엔하이픈|enhypen|올데이 ?프로젝트|키키|kiiikiii|하츠투하츠|코르티스|cortis|아이들|i-?dle|레드벨벳|에이티즈|ateez|더보이즈|트리플에스|tripleS|프로미스나인|fromis|케플러|kep1er|빌리프|아이돌|idol|케이팝|컴백|데뷔", re.I)
IDOL_C = re.compile(r"케이위키|kwiki|DIVE Studios|덕질|스튜디오 춤|STUDIO CHOOM|K-?pop", re.I)


def video_ok(title, channel, cat):
    return cat not in ("음악", "10") and not MUSIC.search(title or "") and not IDOL.search(channel or "") \
        and not IDOL_T.search(title or "") and not IDOL_C.search(channel or "")


def laugh_ratio(texts):
    top = texts[:10]
    return sum(1 for t in top if LAUGH.search(t)) / len(top) if top else 0.0


def _bg(t):
    t = re.sub(r"[\sㅋㅎㅠㅜ!?.~,]+", "", t.lower())
    return {t[i:i + 2] for i in range(len(t) - 1)}


def pick(comments, k=PER_VIDEO):
    """comments: 좋아요 내림차순 dict 목록(text·likes 포함) → 살아남은 최대 k개"""
    out, sets = [], []
    for c in comments:
        if FAN.search(c["text"]):
            continue
        b = _bg(c["text"])
        if any(b and s and len(b & s) / len(b | s) >= 0.35 for s in sets):
            continue
        out.append(c); sets.append(b)
        if len(out) >= k:
            break
    return out


PROMO = re.compile(r"https?://|www\.|^#|^@|^[-=_*▶►■●]+$|구독|subscribe|instagram|tiktok|문의|contact|e-?mail|협찬|paid promotion|광고|제공|최저가|할인|예약|쿠폰|이벤트|구매|판매|링크|출처|정보$|음악|BGM|music|촬영|편집|출연|제작|copyright|ⓒ|©|채널|멤버십|후원|혜택|보험|프리오더|마감|굿즈|티셔츠|풀버전|시청|스토어|쇼핑|PPL|제품|증상|장학생|가입|신청|공식|다운로드|모집|방송|녹화|STAGE|홈페이지|카드|\d{6}|\d{1,2}:\d{2}", re.I)


def short_line(desc):
    """영상 설명에서 링크·태그·홍보·제작진·시간표 줄을 빼고 한글 문장 한 줄 (80자까지)"""
    for ln in (desc or "").splitlines()[:12]:
        s = ln.strip()
        if not s or PROMO.search(s) or "|" in s: continue
        if len(re.findall("[가-힣]", s)) < 8: continue
        return (s[:80] + "…") if len(s) > 80 else s
    return ""
