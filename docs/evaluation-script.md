# 퍼실리테이터 1:1 평가 발표 대본 (미션 5-1 Mini Redis)

> 그대로 읽으면 약 5분. `[시연]`은 터미널에서 직접 실행하는 부분.
> 사전 준비: `cd C:\Users\domod\5-1-fastrepo` (클론한 폴더) → `python scripts/evaluate-mission.py` 로 11/11 PASS 확인.

## 1. 한 줄 소개 (20초)
"Redis가 왜 빠른지를 직접 확인하려고, 해시맵·이중 연결 리스트·힙을 밑바닥부터 구현해서 LRU와 TTL이 동작하는 CLI Mini Redis를 만들었습니다. dict, set, collections는 쓰지 않았습니다."

## 2. 구조 (30초)
"자료구조 3개는 각각 독립 파일입니다. `linked_list.py`, `hashmap.py`, `heap.py`, 이를 조합한 `store.py`, 명령어 처리 `cli.py`입니다."

## 3. 핵심 설명 (2분)
- **해시맵**: "djb2 해시 함수로 키를 숫자로 바꾸고 버킷 수로 나눈 나머지가 칸 번호입니다. 충돌은 체이닝, 즉 칸마다 이중 연결 리스트로 해결합니다. 항목 수 나누기 버킷 수인 로드 팩터가 0.75를 넘으면 버킷을 2배로 늘리고 전부 다시 배치합니다. 칸 수가 바뀌면 나머지 값도 바뀌기 때문입니다."
- **O(1) LRU**: "해시맵의 값(Entry)이 리스트 노드를 직접 들고 있습니다. 키로 노드를 O(1)에 찾고, 노드를 맨 앞으로 옮기는 것도 앞뒤 포인터만 바꾸니 O(1)입니다. 제거 대상은 맨 뒤 tail입니다."
- **TTL 힙**: "필요한 건 '가장 빨리 만료될 키' 하나라서 최소 힙의 루트를 O(1)로 보면 됩니다. 덮어쓰기로 낡아진 힙 항목은 pop할 때 현재 만료시각과 비교해 버리는 lazy deletion을 썼습니다."
- **eviction 흐름**: "SET하면 used_memory에 키+값 바이트를 더하고, maxmemory를 넘는 동안 tail부터 제거하며 evicted_keys를 올립니다. 한 건만으로 한도를 넘으면 저장하지 않고 OOM 에러를 냅니다."
- **GET 흐름**: "만료 확인 → 만료면 삭제 후 (nil), LRU 갱신 안 함 → 없으면 (nil) → 있으면 맨 앞으로 이동 후 값 반환."

## 4. 시연 (1분 30초) — `python main.py`
```
CONFIG SET maxmemory 30
SET user:1 "Alice"
SET user:2 "Bob"
SET user:3 "Charlie"
GET user:1            -> (nil)   # LRU로 제거됨
INFO memory           -> used_memory:22 / maxmemory:30 / evicted_keys:1
KEYS
EXPIRE user:2 3       -> (integer) 1
TTL user:2            -> (integer) 2 또는 3
(3초 후) GET user:2   -> (nil)
CONFIG SET maxmemory abc -> (error) ERR value is not an integer or out of range
GET                   -> (error) ERR wrong number of arguments for 'GET' command
HELLO                 -> (error) ERR unknown command 'HELLO'
quit
```

## 5. 자동 검증 (30초)
"`python scripts/evaluate-mission.py`를 실행하면 금지 자료형 미사용, 명령어, LRU, TTL, 에러 형식, 단위 테스트 10개까지 11개 항목이 PASS로 나옵니다."

## 6. 예상 질문 & 답
| 질문 | 답 |
| --- | --- |
| LFU로 바꾼다면? | 키별 접근 횟수를 저장하고, 빈도별 리스트(빈도→리스트)와 최소 빈도를 관리. 제거는 최소 빈도 리스트의 tail. |
| 데이터 10만 건이면 병목은? | 체인 길이(해시 품질·리사이즈), 노드/Entry 객체의 메모리 오버헤드. |
| 오버헤드를 포함하면? | 노드·버킷·포인터 크기까지 합산해야 하고, 비교 시 '키+값만' vs '전체' 기준을 맞춰야 공정. |
| 왜 해시맵 하나로 LRU 안 하나? | 해시맵은 순서를 모름. 사용 순서를 O(1)로 갱신하려면 리스트가 필요. |
| 왜 TTL에 정렬 대신 힙? | 가장 이른 것 하나만 필요 → push/pop O(log n), peek O(1). |
