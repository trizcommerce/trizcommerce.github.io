"""배포된 캘린더 사이트를 그대로 복사하는 도구 (assemble.py 가 씀).
파일 목록: 각 캘린더의 files.txt(빌드가 만듦). 없으면 data.json 의 이미지 + 저장소의 downloads/ + 고정 파일로 대신 만든다.
python mirror.py 로 직접 실행하면 조직 주소 전체를 _site/ 로 복사한다(점검용)."""
import json
import os
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


def get(url, ok404=False, tries=4):
    for i in range(tries):
        try:
            h = {"User-Agent": "mirror"}
            if url.startswith("https://api.github.com/") and os.environ.get("GH_TOKEN"):   # 익명 API 한도(60회/시간) 회피
                h["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
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


def files_of(s, base):
    lst = get(f"{base}/{s}/files.txt", ok404=True)
    if lst:
        return [l for l in lst.decode("utf-8").splitlines() if l.strip()]
    data = get(f"{base}/{s}/data.json", ok404=True)
    if data is None:
        raise RuntimeError(f"{base}/{s} 에 캘린더가 없음")
    media = sorted(set(re.findall(rb"media/([0-9a-f]{16}\.jpg)", data)))
    dl = [p for p in tree(s) if p.startswith("downloads/")]
    extra = ["downloads/app.apk", "downloads/app.mobileconfig"] if dl else []
    return FIXED + [f"media/{m.decode()}" for m in media] + dl + extra


def _download(jobs):
    def fetch(job):
        url, dest = job
        b = get(url, ok404=True)
        if b is None:
            return url
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b)
        return None
    with ThreadPoolExecutor(12) as ex:
        return [m for m in ex.map(fetch, jobs) if m]


def copy_seller(s, base, dest):
    missing = _download([(f"{base}/{s}/{p}", dest / p) for p in files_of(s, base)])
    if not (dest / "index.html").exists():
        raise RuntimeError(f"{s} index.html 없음")
    return missing


def copy_admin(dest):
    return _download([(f"{NEW}/admin/{p}", dest / p) for p in tree("admin") if not p.startswith((".github/", "master/"))])


if __name__ == "__main__":
    out = Path("_site")
    for s in SELLERS:
        print(s, "빠짐", copy_seller(s, NEW, out / s))
    print("admin 빠짐", len(copy_admin(out / "admin")))
    sys.exit(0)
