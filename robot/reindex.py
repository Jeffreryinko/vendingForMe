"""reindex.py — data/sisa 의 _index.json 들을 다시 만듦 (편집장 예약 작업이 판을 고친 뒤 실행)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sisa_run import reindex
reindex(); print("reindex ok")
