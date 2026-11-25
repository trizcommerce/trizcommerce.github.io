"""예전 주소(trizcommerce.github.io) 거울 사이트.
2026-11-25 저장소를 조직 trizcommerce-team 으로 옮기면서 캘린더 주소가 바뀌었다.
셀러 휴대폰에 깔린 예전 바로가기·앱이 그대로 열리도록, 새 주소의 배포 파일을 그대로 복사해 _site/ 에 만든다.
파일 목록: 각 캘린더의 files.txt(빌드가 만듦). 아직 없으면 data.json 의 이미지 + 저장소의 downloads/ + 고정 파일로 대신 만든다."""
import json
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

NEW = "https://trizcommerce-team.github.io"
API = "https://api.github.com/repos/trizcommerce-team"
SELLERS = ["imxux9", "duckduck0613", "minjinchoa", "paorang73", "___solvely___", "berberlog",
           "mija_uni", "smitruti1010", "shinyoung_h", "hae.seoyoung"]
FIXED = ["index.html", "manifest.webmanifest", "sw.js", "version.txt", "data.json", "config.json", "ideas.json",
         "opinion.json", "icon-180.png", "icon-192.png", "icon-512.png", "calendar.ics", "calendar-1d.ics", "calendar-3d.ics"]
OUT = Path("_site")


def get(url, ok404=False, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "mirror"}), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if ok404 and e.code == 404:
                return None
            if e.code < 500 or i == tries - 1:
                raise RuntimeError(f"{e.code} {url}") from e
        except urllib.error.URLError:
            if i == tries - 1:
                raise
        time.sleep(3 * (i + 1))


def tree(repo):
    t = json.loads(get(f"{API}/{repo}/git/trees/HEAD?recursive=1"))
    return [x["path"] for x in t["tree"] if x["type"] == "blob"]


def seller_files(s):
    lst = get(f"{NEW}/{s}/files.txt", ok404=True)
    if lst:
        return [l for l in lst.decode("utf-8").splitlines() if l.strip()]
    data = get(f"{NEW}/{s}/data.json", ok404=True) or b""
    media = sorted(set(re.findall(rb"media/([0-9a-f]{16}\.jpg)", data)))
    dl = [p for p in tree(s) if p.startswith("downloads/")]
    extra = ["downloads/app.apk", "downloads/app.mobileconfig"] if dl else []
    return FIXED + [f"media/{m.decode()}" for m in media] + dl + extra


def main():
    jobs = []
    for s in SELLERS:
        jobs += [(f"{NEW}/{s}/{p}", OUT / s / p) for p in seller_files(s)]
    # admin 은 저장소 그대로 배포됨(브랜치 배포) → 저장소 파일 전부
    jobs += [(f"{NEW}/admin/{p}", OUT / "admin" / p) for p in tree("admin") if not p.startswith((".github/", "master/"))]

    def fetch(job):
        url, dest = job
        b = get(url, ok404=True)
        if b is None:
            return url
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b)
        return None

    with ThreadPoolExecutor(12) as ex:
        missing = [m for m in ex.map(fetch, jobs) if m]
    for f in ("index.html", "robots.txt"):
        (OUT / f).write_bytes(Path(f).read_bytes())
    print("copied", len(jobs) - len(missing), "missing", len(missing))
    for m in missing[:30]:
        print(" -", m)
    # 핵심 파일(각 캘린더 index.html)이 빠지면 배포하지 않음 — 빈 사이트로 덮어쓰지 않게
    core = [OUT / s / "index.html" for s in SELLERS + ["admin"]]
    assert all(p.exists() and p.stat().st_size > 1000 for p in core), "핵심 파일 누락"


if __name__ == "__main__":
    sys.exit(main())
