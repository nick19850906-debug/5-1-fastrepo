"""저장소 핵심 (Store): 해시맵 + 이중 연결 리스트(LRU) + 힙(TTL) 조합

[실생활 비유]
  도서관 사서 한 명이 세 가지 도구를 쓴다.
   - 해시맵      = 도서 검색대 (제목 -> 책 위치를 바로 찾음)
   - 연결 리스트 = 대출 순서 줄 (최근에 읽은 책이 맨 앞, 오래 안 읽은 책이 맨 뒤)
   - 힙          = 반납 기한 알림판 (가장 먼저 만료되는 책이 맨 위)
  서가(maxmemory)가 꽉 차면 맨 뒤(가장 오래 안 읽은) 책부터 치운다 = LRU.

[구역] 1구역: Entry / 크기 계산 / 2구역: 내부 도우미 / 3구역: 명령(SET~TTL)
"""
import time

from .hashmap import HashMap
from .heap import MinHeap
from .linked_list import DoublyLinkedList


class OOMError(Exception):
    """키+값 한 건만으로도 maxmemory 를 넘을 때 발생 (저장 불가)."""


# ===== 1구역: 데이터 상자 =====
class Entry:
    """해시맵에 저장되는 값. LRU 노드를 직접 쥐고 있어서 LRU 갱신이 O(1)."""

    def __init__(self, value, node):
        self.value = value
        self.node = node          # LRU 리스트 안의 내 노드
        self.expire_at = None     # 만료 시각(초). None = 만료 없음


def _size(key, value):
    """used_memory 공식: len(utf8(key)) + len(utf8(value)). 노드/포인터 오버헤드는 제외."""
    return len(key.encode("utf-8")) + len(value.encode("utf-8"))


class Store:
    def __init__(self, clock=time.time):
        self._map = HashMap()            # 데이터 본체
        self._lru = DoublyLinkedList()   # head = 최근 사용, tail = 가장 오래됨
        self._heap = MinHeap()           # (expire_at, key) - lazy deletion 방식
        self._clock = clock              # 시계 (테스트에서 가짜 시계로 교체 가능)
        self.used_memory = 0             # 현재 사용량(바이트)
        self.maxmemory = 0               # 한도. 0 = 무제한
        self.evicted_keys = 0            # LRU 로 쫓겨난 키 누적 수

    # ===== 2구역: 내부 도우미 =====
    def _delete(self, key):
        """데이터/LRU/사용량에서 한꺼번에 제거 (힙 항목은 lazy deletion 으로 나중에 버림)."""
        entry = self._map.get(key)
        if entry is None:
            return False
        self._lru.remove_node(entry.node)
        self._map.remove(key)
        self.used_memory -= _size(key, entry.value)
        return True

    def _expire_if_needed(self, key):
        """키 기반 명령 실행 전 만료 검사. 만료됐으면 삭제하고 True."""
        entry = self._map.get(key)
        if entry and entry.expire_at is not None and self._clock() >= entry.expire_at:
            self._delete(key)
            return True
        return False

    def purge_expired(self):
        """힙 맨 위부터 만료된 키를 정리. 덮어쓰기로 낡아진 힙 항목은 그냥 버린다."""
        now = self._clock()
        while self._heap.peek() and self._heap.peek()[0] <= now:
            expire_at, key = self._heap.pop()
            entry = self._map.get(key)
            if entry and entry.expire_at == expire_at:   # 최신 만료시각과 같을 때만 진짜 만료
                self._delete(key)

    def _evict(self):
        """한도 초과인 동안 가장 오래 안 쓴 키(리스트 tail)부터 제거."""
        while self.maxmemory > 0 and self.used_memory > self.maxmemory:
            key = self._lru.tail.data
            self._delete(key)
            self.evicted_keys += 1

    # ===== 3구역: 명령 =====
    def set(self, key, value):
        self._expire_if_needed(key)
        size = _size(key, value)
        if self.maxmemory > 0 and size > self.maxmemory:
            raise OOMError()                             # 혼자서도 못 들어가면 저장 거부
        entry = self._map.get(key)
        if entry:                                        # 덮어쓰기
            self.used_memory += size - _size(key, entry.value)
            entry.value = value
            entry.expire_at = None                       # 덮어쓰면 TTL 초기화
            self._lru.move_to_front(entry.node)
        else:                                            # 새 키
            node = self._lru.insert_front(key)
            self._map.put(key, Entry(value, node))
            self.used_memory += size
        self._evict()                                    # 초과 시 LRU 제거

    def get(self, key):
        if self._expire_if_needed(key):
            return None                                  # 만료 삭제 시 LRU 갱신 안 함
        entry = self._map.get(key)
        if entry is None:
            return None
        self._lru.move_to_front(entry.node)              # 성공했을 때만 LRU 갱신
        return entry.value

    def delete(self, key):
        self._expire_if_needed(key)
        return self._delete(key)

    def exists(self, key):
        self._expire_if_needed(key)
        return self._map.contains(key)

    def dbsize(self):
        return self._map.size()

    def keys(self):
        return self._map.keys()

    def set_maxmemory(self, n):
        """한도 변경. 줄였을 때 이미 초과면 즉시 LRU 제거."""
        self.maxmemory = n
        self._evict()

    def expire(self, key, seconds):
        """1 = 설정 성공, 0 = 없는 키. seconds <= 0 이면 즉시 삭제."""
        self._expire_if_needed(key)
        entry = self._map.get(key)
        if entry is None:
            return 0
        if seconds <= 0:
            self._delete(key)
            return 1
        entry.expire_at = self._clock() + seconds
        self._heap.push((entry.expire_at, key))          # 힙에 (만료시각, 키) 등록
        return 1

    def ttl(self, key):
        """없는 키 -2, 만료 없음 -1, 그 외 남은 초."""
        if self._expire_if_needed(key):
            return -2
        entry = self._map.get(key)
        if entry is None:
            return -2
        if entry.expire_at is None:
            return -1
        return int(entry.expire_at - self._clock())
