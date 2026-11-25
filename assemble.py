"""통합 빌드의 마지막 단계: 배포할 사이트(_site) 묶기.
- parts/pwa-<셀러>/ : 이번 실행에서 새로 만든 셀러 → 그대로 사용
- 이번에 안 만든(또는 빌드 실패한) 셀러 : 지금 원래 주소에 배포돼 있는 것을 복사(없으면 조직 주소에서)
- admin : 조직 저장소 trizcommerce-team/admin (브랜치 배포) 파일을 복사"""
import shutil
import sys
from pathlib import Path

import mirror

OUT = Path("_site")
LIVE = "https://trizcommerce.github.io"


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    built, copied = [], []
    for s in mirror.SELLERS:
        part = Path("parts") / f"pwa-{s}"
        if (part / "index.html").exists():
            shutil.copytree(part, OUT / s)
            built.append(s)
            continue
        try:   # 이번에 안 만든 셀러: 지금 배포된 원래 주소 것을 그대로
            mirror.copy_seller(s, LIVE, OUT / s)
        except Exception as e:   # 원래 주소에 아직 없으면 조직 주소에서
            print("원래 주소 복사 실패, 조직 주소에서:", s, e)
            mirror.copy_seller(s, mirror.NEW, OUT / s)
        copied.append(s)
    mirror.copy_admin(OUT / "admin")
    shutil.copytree("example", OUT / "example")   # 미팅용 '예시' 캘린더(지어낸 내용, 시트 연동 없음) — 원본 example_calendar_app/
    for f in ("index.html", "robots.txt"):
        shutil.copy(f, OUT / f)
    print("새로 만듦:", built)
    print("기존 유지:", copied)
    core = [OUT / s / "index.html" for s in mirror.SELLERS + ["admin"]]
    missing = [str(p) for p in core if not (p.exists() and p.stat().st_size > 1000)]
    assert not missing, f"핵심 파일 누락: {missing}"   # 빈 사이트로 덮어쓰지 않게


if __name__ == "__main__":
    sys.exit(main())
