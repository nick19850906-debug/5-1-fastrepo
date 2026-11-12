# Mini Redis (5-1 fastrepo)

해시맵·이중 연결 리스트·힙을 직접 구현한 CLI 기반 Mini Redis. (`dict`/`set`/`collections` 미사용, Python 3.8+)

## 실행
```
cd C:\Users\domod\5-1-fastrepo
python main.py
python -m unittest discover -s tests -t .
```

## 구조
| 파일 | 역할 |
| --- | --- |
| `mini_redis/linked_list.py` | 이중 연결 리스트 (prev/next/data, 전 연산 O(1)) |
| `mini_redis/hashmap.py` | 체이닝 해시맵 (djb2 해시, 로드 팩터 0.75 초과 시 버킷 2배) |
| `mini_redis/heap.py` | 최소 힙 `(expire_at, key)` |
| `mini_redis/store.py` | 해시맵 + LRU 리스트 + TTL 힙 조합 |
| `mini_redis/cli.py` | 파싱·실행·REPL |

## 명령어
`SET GET DEL EXISTS DBSIZE KEYS` · `CONFIG SET maxmemory N` · `INFO memory` · `EXPIRE TTL` · `exit/quit`

## 체크리스트 설명 요약
- **O(1) LRU**: 해시맵으로 키→Entry를 찾고, Entry가 쥔 리스트 노드를 앞뒤 포인터만 바꿔 맨 앞으로 이동. 제거 대상은 `tail`.
- **해시 충돌**: 버킷마다 이중 연결 리스트(체이닝). 로드 팩터(항목수/버킷수) > 0.75면 버킷 2배 후 전부 rehash.
- **TTL 힙**: 가장 빨리 만료될 키가 항상 루트라 `peek` O(1), `pop` O(log n). 덮어쓰기/삭제로 낡은 힙 항목은 pop 시 `expire_at` 비교로 버리는 lazy deletion.
- **eviction 흐름**: SET → `used_memory += len(key)+len(value)` → maxmemory 초과 동안 LRU tail 제거(`used_memory` 감소, `evicted_keys` +1). 단일 엔트리가 maxmemory 초과면 저장 없이 OOM.
- **GET 흐름**: 만료 확인 → 만료면 삭제 후 `(nil)`(LRU 갱신 안 함) → 없으면 `(nil)` → 있으면 LRU 맨 앞으로 이동 후 값 반환.
- **LFU로 바꾼다면**: 키별 접근 횟수 + 빈도별 리스트(freq→리스트)로 교체, 최소 빈도 리스트 tail 제거.
- **10만 건 이상**: 병목은 리스트·해시 체인 길이 → 해시 품질/리사이즈로 완화. 메모리는 Entry/노드 오버헤드가 크다(문서상 used_memory는 이를 제외).
- **오버헤드 포함 모델**: 노드·버킷·포인터 크기를 합산해야 하며, 비교 시 동일 기준(키+값만 vs 전체)으로 맞춰야 공정.
