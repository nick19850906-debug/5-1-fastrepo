"""저장소 핵심: 해시맵(데이터) + 이중 연결 리스트(LRU) + 힙(TTL)을 조합.
해시맵 값 = Entry. Entry가 LRU 노드를 직접 쥐고 있어 LRU 갱신이 O(1).
"""
import time

from .hashmap import HashMap
from .heap import MinHeap
from .linked_list import DoublyLinkedList


class OOMError(Exception):
    """단일 엔트리가 maxmemory 보다 클 때."""


class Entry:
    def __init__(self, value, node):
        self.value = value
        self.node = node          # LRU 리스트 안의 내 노드
        self.expire_at = None     # None = 만료 없음


def _size(key, value):
    return len(key.encode("utf-8")) + len(value.encode("utf-8"))


class Store:
    def __init__(self, clock=time.time):
        self._map = HashMap()
        self._lru = DoublyLinkedList()   # head = 최근, tail = 가장 오래됨
        self._heap = MinHeap()           # (expire_at, key), lazy deletion
        self._clock = clock
        self.used_memory = 0
        self.maxmemory = 0               # 0 = 무제한
        self.evicted_keys = 0

    # ---- 내부 도우미 ----
    def _delete(self, key):
        entry = self._map.get(key)
        if entry is None:
            return False
        self._lru.remove_node(entry.node)
        self._map.remove(key)
        self.used_memory -= _size(key, entry.value)
        return True

    def _expire_if_needed(self, key):
        """만료됐으면 삭제하고 True."""
        entry = self._map.get(key)
        if entry and entry.expire_at is not None and self._clock() >= entry.expire_at:
            self._delete(key)
            return True
        return False

    def purge_expired(self):
        """힙 맨 위부터 만료된 키를 제거. 낡은(덮어써진) 힙 항목은 버린다."""
        now = self._clock()
        while self._heap.peek() and self._heap.peek()[0] <= now:
            expire_at, key = self._heap.pop()
            entry = self._map.get(key)
            if entry and entry.expire_at == expire_at:
                self._delete(key)

    def _evict(self):
        while self.maxmemory > 0 and self.used_memory > self.maxmemory:
            key = self._lru.tail.data
            self._delete(key)
            self.evicted_keys += 1

    # ---- 명령 ----
    def set(self, key, value):
        self._expire_if_needed(key)
        size = _size(key, value)
        if self.maxmemory > 0 and size > self.maxmemory:
            raise OOMError()
        entry = self._map.get(key)
        if entry:
            self.used_memory += size - _size(key, entry.value)
            entry.value = value
            entry.expire_at = None  # 덮어쓰면 TTL 초기화
            self._lru.move_to_front(entry.node)
        else:
            node = self._lru.insert_front(key)
            self._map.put(key, Entry(value, node))
            self.used_memory += size
        self._evict()

    def get(self, key):
        if self._expire_if_needed(key):
            return None
        entry = self._map.get(key)
        if entry is None:
            return None
        self._lru.move_to_front(entry.node)
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
        self.maxmemory = n
        self._evict()

    def expire(self, key, seconds):
        self._expire_if_needed(key)
        entry = self._map.get(key)
        if entry is None:
            return 0
        if seconds <= 0:
            self._delete(key)
            return 1
        entry.expire_at = self._clock() + seconds
        self._heap.push((entry.expire_at, key))
        return 1

    def ttl(self, key):
        if self._expire_if_needed(key):
            return -2
        entry = self._map.get(key)
        if entry is None:
            return -2
        if entry.expire_at is None:
            return -1
        return int(entry.expire_at - self._clock())
