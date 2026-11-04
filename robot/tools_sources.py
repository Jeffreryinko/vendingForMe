"""tools_sources.py — '도구' 탭 로봇이 어디서 무엇을 가져올지 적는 표. 이 파일만 고치면 다음 회차부터 적용.

  CHANNELS  : 유튜브 채널 (채널 RSS — API 한도 안 씀). 이름, 채널 ID(UC…)
  YT_QUERIES: 하루 한 번 유튜브 검색 (최근 7일, 조회수 순). 1번 = 100단위 (무료 10,000/일)
  AWESOME   : '모음 목록' 저장소 — 새로 추가된 줄만 '새 항목'으로. full=True 는 목록 전체를 '모음집'에 보관
  CATS      : 분류 낱말 (제목·설명에 들어 있으면 그 분류). 순서대로 최대 2개
"""

CHANNELS = [
    ("성공지식백과", "UC-SyuGFlZXpGdR7WszgYBhw"),
    ("조코딩", "UCQNE2JmbasNYbjGAcuBiRRg"),
    ("오늘코드", "UCLR3sD0KB_dWpvcsrLP0aUg"),
    ("일잘러 장피엠", "UCSkpTOEl_zW6b4Y7M_Prefg"),
    ("테디노트", "UCt2wAAXgm87ACiQnDHQEW6Q"),
    ("안될공학", "UCeN2YeJcBCRJoXgzF_OU3qw"),
    ("코딩애플", "UCSLrpBAzr-ROVGHQ5EmxnUg"),
    ("노마드 코더", "UCUpJs89fSBXNolQGOYKn0YQ"),
]

YT_QUERIES = ["클로드 코드", "바이브코딩", "AI 오픈소스 추천", "AI 자동화 툴", "깃허브 오픈소스 AI"]

AWESOME = [  # (id, 이름, 저장소, 파일, 전체 보관)
    ("claude-code", "클로드 코드 모음", "hesreallyhim/awesome-claude-code", "README.md", True),
    ("claude-skills", "클로드 스킬 모음", "travisvn/awesome-claude-skills", "README.md", True),
    ("subagents", "클로드 서브에이전트 모음", "VoltAgent/awesome-claude-code-subagents", "README.md", True),
    ("mcp", "MCP 서버 모음", "punkpeye/awesome-mcp-servers", "README.md", False),
    ("ai-agents", "AI 에이전트 모음", "e2b-dev/awesome-ai-agents", "README.md", False),
]

# 분류 (id, 이름, 낱말 정규식 — 대소문자 무시)
CATS = [
    ("code", "코딩 도구", r"claude code|클로드 ?코드|cursor|커서|copilot|코파일럿|codex|vibe ?cod|바이브 ?코딩|\bide\b|\bcli\b|terminal|터미널|vs ?code|neovim|coding agent|code review|코드 리뷰|\bgit\b|github|깃허브|devtool|개발 도구|programming|코딩"),
    ("mcp", "MCP·스킬·플러그인", r"\bmcp\b|skill|스킬|plugin|플러그인|extension|확장|subagent|서브 ?에이전트|\bhooks?\b"),
    ("agent", "에이전트·자동화", r"agent|에이전트|automat|자동화|workflow|워크플로|n8n|zapier|make\.com|browser.?use|computer.?use|rpa|autonomous|crawl|scrap|크롤|스크래"),
    ("web", "웹·디자인", r"website|web ?site|웹사이트|홈페이지|landing|랜딩|\bui\b|\bux\b|design|디자인|frontend|프론트|figma|피그마|css|react|next\.?js|tailwind|clone|클론|템플릿|template"),
    ("media", "이미지·영상·음성", r"\bimages?\b|이미지|사진|\bvideos?\b|영상 (생성|편집|제작)|동영상|\bvoice|음성|\btts\b|speech|audio|오디오|\bmusic|음악|diffusion|comfyui|\b3d\b|avatar|아바타|그림|썸네일|gaussian"),
    ("llm", "모델·로컬 AI", r"\bllms?\b|\blocal\b|로컬|ollama|llama|gguf|inference|추론|fine-?tun|파인튜닝|qwen|deepseek|mistral|gemma|\brag\b|embedding|임베딩|open.?weight|언어 ?모델|\bmodels?\b|gpu"),
    ("data", "데이터·문서", r"\bpdf\b|\bocr\b|spreadsheet|엑셀|excel|database|데이터베이스|\bsql\b|postgres|documents?\b|문서|notebook|\bcsv\b|데이터|\bdata\b"),
    ("work", "생산성·업무", r"note|노트|productiv|생산성|calendar|캘린더|email|메일|obsidian|옵시디언|notion|노션|todo|할 ?일|meeting|회의|업무|일잘|slack|슬랙"),
]

# 성인·거친 것 거르기
BLOCK = r"uncensored|nsfw|nude|naked|undress|porn|hentai|erotic|\bsex|onlyfans|deepnude|18\+|adult only|성인|야한"

# 해커뉴스 '화제 글'에서 남길 것 (AI·개발 도구 관련 낱말)
HN_KEEP = r"\b(ai|llm|llms|gpt|agent|agents|agentic|claude|gemini|openai|anthropic|model|models|open.?source|tool|tools|cli|mcp|cursor|copilot|codex|coding|developer|github|rust|python|browser|automation|local)\b"

# 유튜브 영상에서 남길 것 (채널 RSS는 이 낱말이 제목·설명에 있어야)
YT_KEEP = r"\bai\b|ai로|ai가|ai를|인공지능|클로드|claude|gpt|챗gpt|제미나이|gemini|코딩|코드|오픈소스|깃허브|github|자동화|툴|도구|에이전트|바이브|커서|cursor|노코드|mcp|프롬프트|llm|앱 만들|사이트|웹|프로그램|딥시크|퍼플렉시티|노션"
