"""미션 5-1 자동 검증 스크립트

[실생활 비유] 시험 채점기. 요구사항 항목마다 O/X 를 매겨서 한눈에 보여 준다.

[실행] cd C:/Users/domod/<프로젝트폴더>   (이 파일이 있는 저장소 루트)
       python scripts/evaluate-mission.py
[통과 조건] 마지막 줄이 'RESULT: n/n PASS' 이고 종료 코드(exit code)가 0.
"""
import ast
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mini_redis.cli import execute          # noqa: E402
from mini_redis.store import Store          # noqa: E402

results = []


def check(name, ok):
    """항목 한 줄 채점 후 기록."""
    results.append(ok)
    print("[%s] %s" % ("PASS" if ok else "FAIL", name))


class Clock:
    """가짜 시계: 3초를 기다리지 않고 시간을 흘려보내기 위함."""

    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def run(store, *lines):
    return [execute(store, ln) for ln in lines]


# ----- 1구역: 금지 항목(dict/set/collections) 사용 검사 -----
def no_forbidden():
    bad = []
    for fn in os.listdir(os.path.join(ROOT, "mini_redis")):
        if not fn.endswith(".py"):
            continue
        tree = ast.parse(open(os.path.join(ROOT, "mini_redis", fn), encoding="utf-8").read())
        for n in ast.walk(tree):
            if isinstance(n, (ast.Dict, ast.Set, ast.DictComp, ast.SetComp)):
                bad.append(fn)
            if isinstance(n, ast.Name) and n.id in ("dict", "set", "defaultdict", "OrderedDict"):
                bad.append(fn)
            if isinstance(n, ast.Import) and any(a.name.split(".")[0] == "collections" for a in n.names):
                bad.append(fn)
            if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "collections":
                bad.append(fn)
    return not bad


# ----- 2구역: 요구사항 점검 -----
check("dict/set/collections 미사용", no_forbidden())
check("자료구조 3종 독립 파일 분리",
      all(os.path.exists(os.path.join(ROOT, "mini_redis", f))
          for f in ("linked_list.py", "hashmap.py", "heap.py")))

s = Store()
r = run(s, 'SET a "x y"', "GET a", "EXISTS a", "DBSIZE", "KEYS", "DEL a", "DEL a", "GET a")
check("String 명령 6종", r == ["OK", '"x y"', "(integer) 1", "(integer) 1", '1. "a"',
                               "(integer) 1", "(integer) 0", "(nil)"])

s = Store()
r = run(s, "CONFIG SET maxmemory 30", 'SET user:1 "Alice"', 'SET user:2 "Bob"',
        'SET user:3 "Charlie"', "GET user:1", "INFO memory")
check("LRU 자동 제거 + INFO memory (예시 22/30/1)",
      r[4] == "(nil)" and r[5] == "used_memory:22\nmaxmemory:30\nevicted_keys:1")

s = Store()
run(s, "CONFIG SET maxmemory 20", "SET a 1234567", "SET b 1234567", "GET a", "SET c 1234567")
check("GET 시 LRU 갱신 (a 생존, b 제거)", run(s, "EXISTS a", "EXISTS b") == ["(integer) 1", "(integer) 0"])

s = Store()
run(s, "CONFIG SET maxmemory 5")
check("단일 엔트리 초과 시 OOM 에러", execute(s, "SET key value").startswith("(error) OOM"))

c = Clock()
s = Store(c)
run(s, "SET a 1")
r = run(s, "TTL a", "EXPIRE a 3", "TTL a", "EXPIRE nokey 3")
c.t += 3
r2 = run(s, "GET a", "TTL a")
check("TTL/EXPIRE 동작 (-1, 3, 만료 후 nil/-2, 없는 키 0)",
      r == ["(integer) -1", "(integer) 1", "(integer) 3", "(integer) 0"] and r2 == ["(nil)", "(integer) -2"])

s = Store(Clock())
run(s, "SET a 1", "EXPIRE a 5", "SET a 2")
check("SET 덮어쓰기 시 TTL 초기화", execute(s, "TTL a") == "(integer) -1")

s = Store()
r = run(s, "CONFIG SET maxmemory abc", "GET", "HELLO")
check("에러 3종 표준 형식", r == [
    "(error) ERR value is not an integer or out of range",
    "(error) ERR wrong number of arguments for 'GET' command",
    "(error) ERR unknown command 'HELLO'"])

# ----- 3구역: 실제 CLI 프로세스로 REPL / quit 종료 확인 -----
p = subprocess.run([sys.executable, os.path.join(ROOT, "main.py")], input="SET k v\nGET k\nquit\n",
                   capture_output=True, text=True, encoding="utf-8")
check("REPL: 프롬프트 출력 + quit 종료", "mini-redis>" in p.stdout and '"v"' in p.stdout and p.returncode == 0)

# ----- 4구역: 단위 테스트 전체 실행 -----
suite = unittest.defaultTestLoader.discover(os.path.join(ROOT, "tests"), top_level_dir=ROOT)
res = unittest.TextTestRunner(stream=open(os.devnull, "w")).run(suite)
check("단위 테스트 %d개" % res.testsRun, res.wasSuccessful())

print("RESULT: %d/%d PASS" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)

