"""해시맵 (체이닝). 충돌 시 같은 버킷의 이중 연결 리스트에 이어 붙인다.
[실생활 비유] 아파트 동호수 - 해시 함수가 '몇 호'인지 정하고, 같은 호에 여럿이면 줄로 세운다.
"""
from .linked_list import DoublyLinkedList

LOAD_FACTOR_LIMIT = 0.75


def hash_key(key):
    """직접 설계한 해시 함수 (djb2): h = h*33 + 바이트."""
    h = 5381
    for b in key.encode("utf-8"):
        h = (h * 33 + b) & 0xFFFFFFFF
    return h


class HashMap:
    def __init__(self, capacity=8):
        self._buckets = [DoublyLinkedList() for _ in range(capacity)]
        self._size = 0

    def size(self):
        return self._size

    def _find(self, key):
        bucket = self._buckets[hash_key(key) % len(self._buckets)]
        node = bucket.head
        while node:
            if node.data[0] == key:
                return bucket, node
            node = node.next
        return bucket, None

    def put(self, key, value):
        bucket, node = self._find(key)
        if node:
            node.data[1] = value
            return
        bucket.insert_back([key, value])
        self._size += 1
        if self._size / len(self._buckets) > LOAD_FACTOR_LIMIT:
            self._resize()

    def get(self, key):
        _, node = self._find(key)
        return node.data[1] if node else None

    def contains(self, key):
        return self._find(key)[1] is not None

    def remove(self, key):
        bucket, node = self._find(key)
        if not node:
            return False
        bucket.remove_node(node)
        self._size -= 1
        return True

    def keys(self):
        result = []
        for bucket in self._buckets:
            node = bucket.head
            while node:
                result.append(node.data[0])
                node = node.next
        return result

    def _resize(self):
        """버킷 2배 확장 후 모든 항목 재배치(rehash)."""
        old = self._buckets
        self._buckets = [DoublyLinkedList() for _ in range(len(old) * 2)]
        for bucket in old:
            node = bucket.head
            while node:
                k, v = node.data
                self._buckets[hash_key(k) % len(self._buckets)].insert_back([k, v])
                node = node.next
