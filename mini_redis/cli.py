"""명령어 파싱 + 실행 + REPL."""
from .store import OOMError, Store

ERR_INT = "(error) ERR value is not an integer or out of range"
ERR_OOM = "(error) OOM command not allowed when used_memory > 'maxmemory'"


def tokenize(line):
    """공백으로 분리하되 "큰따옴표로 감싼 값"은 하나로 취급."""
    tokens, cur, in_q, has = [], "", False, False
    for ch in line:
        if ch == '"':
            in_q, has = not in_q, True
        elif ch.isspace() and not in_q:
            if has or cur:
                tokens.append(cur)
            cur, has = "", False
        else:
            cur += ch
    if has or cur:
        tokens.append(cur)
    return tokens


def _to_int(s):
    try:
        return int(s)
    except ValueError:
        return None


def execute(store, line):
    """한 줄을 실행해 출력 문자열을 반환. 빈 줄은 None."""
    tokens = tokenize(line)
    if not tokens:
        return None
    cmd, args = tokens[0].upper(), tokens[1:]
    store.purge_expired()

    arity = {"SET": 2, "GET": 1, "DEL": 1, "EXISTS": 1, "DBSIZE": 0,
             "KEYS": 0, "EXPIRE": 2, "TTL": 1, "INFO": 1, "CONFIG": 3}
    if cmd not in arity:
        return "(error) ERR unknown command '%s'" % tokens[0]
    if len(args) != arity[cmd]:
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
    # CONFIG SET maxmemory N
    if args[0].upper() != "SET" or args[1].lower() != "maxmemory":
        return "(error) ERR unsupported CONFIG subcommand"
    n = _to_int(args[2])
    if n is None or n < 0:
        return ERR_INT
    store.set_maxmemory(n)
    return "OK"


def repl():
    store = Store()
    while True:
        try:
            line = input("mini-redis> ")
        except (EOFError, KeyboardInterrupt):
            break
        if line.strip().lower() in ("exit", "quit"):
            break
        out = execute(store, line)
        if out is not None:
            print(out)
