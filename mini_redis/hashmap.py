"""해시맵 (Hash Map, 체이닝 방식)

[실생활 비유]
  아파트 우편함. 해시 함수는 '이름 -> 몇 호'를 정해 주는 규칙이고,
  우연히 같은 호수가 나오면(충돌) 그 호 우편함 안에 편지를 줄(연결 리스트)로 세워 둔다.
  너무 꽉 차면(로드 팩터 > 0.75) 건물을 2배로 증축하고 전원 재배치한다.

[구역] 1구역: hash_key(해시 함수) / 2구역: 기본 동작 / 3구역: _resize(2배 확장)
"""
from .linked_list import DoublyLinkedList

LOAD_FACTOR_LIMIT = 0.75   # 로드 팩터(항목수 / 버킷수)가 이 값을 넘으면 확장


# ===== 1구역: 해시 함수 =====
def hash_key(key):
    """문자열을 큰 정수로 바꾼다 (djb2). h = h*33 + 글자값 반복.
    & 0xFFFFFFFF : 32비트 안으로 자르기(숫자가 끝없이 커지는 것 방지)."""
    h = 5381
    for b in key.encode("utf-8"):
        h = (h * 33 + b) & 0xFFFFFFFF
    return h


class HashMap:
    def __init__(self, capacity=8):
        # 버킷 = 우편함 칸. 칸마다 이중 연결 리스트(체이닝용)를 하나씩 둔다.
        # (파이썬 리스트 []는 '고정 길이 배열' 용도로만 사용, dict/set 은 쓰지 않음)
        self._buckets = [DoublyLinkedList() for _ in range(capacity)]
        self._size = 0

    # ===== 2구역: 기본 동작 =====
    def size(self):
        """저장된 항목 수."""
        return self._size

    def _find(self, key):
        """(키가 속한 버킷, 그 키의 노드 또는 None) 반환.
        % len(buckets) : 해시값을 '몇 번 칸'으로 바꾸는 나머지 연산."""
        bucket = self._buckets[hash_key(key) % len(self._buckets)]
        node = bucket.head
        while node:                      # 같은 칸의 줄을 앞에서부터 확인 (체이닝)
            if node.data[0] == key:      # data = [키, 값]
                return bucket, node
            node = node.next
        return bucket, None

    def put(self, key, value):
        """저장. 이미 있으면 값만 교체, 없으면 줄 끝에 추가."""
        bucket, node = self._find(key)
        if node:
            node.data[1] = value
            return
        bucket.insert_back([key, value])
        self._size += 1
        if self._size / len(self._buckets) > LOAD_FACTOR_LIMIT:
            self._resize()               # 너무 붐비면 증축

    def get(self, key):
        """조회. 없으면 None."""
        _, node = self._find(key)
        return node.data[1] if node else None

    def contains(self, key):
        """키 존재 여부."""
        return self._find(key)[1] is not None

    def remove(self, key):
        """삭제. 지웠으면 True, 원래 없었으면 False."""
        bucket, node = self._find(key)
        if not node:
            return False
        bucket.remove_node(node)
        self._size -= 1
        return True

    def keys(self):
        """모든 키 목록 (순서 보장 없음)."""
        result = []
        for bucket in self._buckets:     # 모든 칸을 돌며
            node = bucket.head
            while node:                  # 줄에 선 키를 모은다
                result.append(node.data[0])
                node = node.next
        return result

    # ===== 3구역: 버킷 2배 확장 =====
    def _resize(self):
        """칸 수가 바뀌면 '몇 호'도 바뀌므로 전원 rehash(재배치) 해야 한다."""
        old = self._buckets
        self._buckets = [DoublyLinkedList() for _ in range(len(old) * 2)]
        for bucket in old:
            node = bucket.head
            while node:
                k, v = node.data
                self._buckets[hash_key(k) % len(self._buckets)].insert_back([k, v])
                node = node.next
