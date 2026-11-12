"""명령어 파싱 + 실행 + REPL (사용자와 대화하는 창구)

[실생활 비유] 식당 주문 접수대. 손님의 한 줄 주문(문장)을 단어로 쪼개고(tokenize),
  메뉴판에 있는지/재료 수가 맞는지 확인한 뒤(execute) 주방(Store)에 전달하고 결과를 알려 준다.

[구역] 1구역: 상수 / 2구역: tokenize(쪼개기) / 3구역: execute(실행) / 4구역: repl(반복 입출력)
"""
from .store import OOMError, Store

# ===== 1구역: 표준 에러 문구 =====
ERR_INT = "(error) ERR value is not an integer or out of range"
ERR_OOM = "(error) OOM command not allowed when used_memory > 'maxmemory'"


# ===== 2구역: 한 줄 -> 단어 목록 =====
def tokenize(line):
    """공백으로 단어를 나누되 "큰따옴표로 감싼 값"은 공백이 있어도 한 덩어리로 취급."""
    tokens, cur, in_q, has = [], "", False, False
    for ch in line:
        if ch == '"':
            in_q, has = not in_q, True      # 따옴표 안/밖 전환 (빈 문자열 "" 도 인정)
        elif ch.isspace() and not in_q:     # 따옴표 밖의 공백 = 단어 끝
            if has or cur:
                tokens.append(cur)
            cur, has = "", False
        else:
            cur += ch
    if has or cur:
        tokens.append(cur)
    return tokens


def _to_int(s):
    """정수로 바꾸기. 실패하면 None."""
    try:
        return int(s)
    except ValueError:
        return None


# ===== 3구역: 명령 실행 =====
def execute(store, line):
    """한 줄을 실행해 출력 문자열을 반환. 빈 줄은 None."""
    tokens = tokenize(line)
    if not tokens:
        return None
    cmd, args = tokens[0].upper(), tokens[1:]   # 명령어는 대소문자 구분 없음
    store.purge_expired()                       # 실행 전, 힙으로 만료 키 먼저 청소

    # 명령별 필요한 인자 개수 (표에 없으면 알 수 없는 명령)
    # (명령, 인자수) 쌍의 튜플 - dict 금지 규칙 때문에 표를 튜플로 만들어 순서대로 찾는다
    arity = (("SET", 2), ("GET", 1), ("DEL", 1), ("EXISTS", 1), ("DBSIZE", 0),
             ("KEYS", 0), ("EXPIRE", 2), ("TTL", 1), ("INFO", 1), ("CONFIG", 3))
    need = -1
    for name, count in arity:
        if name == cmd:
            need = count
    if need < 0:
        return "(error) ERR unknown command '%s'" % tokens[0]
    if len(args) != need:
        return "(error) ERR wrong number of arguments for '%s' command" % cmd

    if cmd == "SET":
        try:
            store.set(args[0], args[1])
        except OOMError:
            return ERR_OOM
        return "OK"
    if cmd == "GET":
        v = store.get(args[0])
        return "(nil)" if v is None else '"%s"' % v
    if cmd == "DEL":
        return "(integer) %d" % (1 if store.delete(args[0]) else 0)
    if cmd == "EXISTS":
        return "(integer) %d" % (1 if store.exists(args[0]) else 0)
    if cmd == "DBSIZE":
        return "(integer) %d" % store.dbsize()
    if cmd == "KEYS":
        ks = store.keys()
        if not ks:
            return "(empty array)"
        return "\n".join('%d. "%s"' % (i + 1, k) for i, k in enumerate(ks))
    if cmd == "EXPIRE":
        n = _to_int(args[1])
        return ERR_INT if n is None else "(integer) %d" % store.expire(args[0], n)
    if cmd == "TTL":
        return "(integer) %d" % store.ttl(args[0])
    if cmd == "INFO":
        if args[0].lower() != "memory":
            return "(error) ERR unknown section '%s'" % args[0]
        return "used_memory:%d\nmaxmemory:%d\nevicted_keys:%d" % (
            store.used_memory, store.maxmemory, store.evicted_keys)
    # 남은 경우: CONFIG SET maxmemory <바이트>
    if args[0].upper() != "SET" or args[1].lower() != "maxmemory":
        return "(error) ERR unsupported CONFIG subcommand"
    n = _to_int(args[2])
    if n is None or n < 0:
        return ERR_INT
    store.set_maxmemory(n)
    return "OK"


# ===== 4구역: REPL (입력 -> 실행 -> 출력 반복) =====
def repl():
    store = Store()
    while True:
        try:
            line = input("mini-redis> ")        # 프롬프트 출력 후 한 줄 입력
        except (EOFError, KeyboardInterrupt):   # Ctrl+Z / Ctrl+C 로도 안전 종료
            break
        if line.strip().lower() in ("exit", "quit"):
            break
        out = execute(store, line)
        if out is not None:
            print(out)
