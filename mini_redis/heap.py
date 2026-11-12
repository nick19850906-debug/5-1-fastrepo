"""최소 힙. 맨 위(peek)가 항상 가장 작은 (expire_at, key) = 가장 빨리 만료될 키.
[실생활 비유] 유통기한 임박 순으로 쌓는 냉장고 - 맨 위만 보면 가장 급한 음식을 안다.
"""


class MinHeap:
    def __init__(self):
        self._a = []  # 완전 이진 트리를 배열로 표현: 부모 (i-1)//2, 자식 2i+1, 2i+2

    def size(self):
        return len(self._a)

    def peek(self):
        return self._a[0] if self._a else None

    def push(self, item):
        self._a.append(item)
        self._heapify_up(len(self._a) - 1)

    def pop(self):
        if not self._a:
            return None
        top = self._a[0]
        last = self._a.pop()
        if self._a:
            self._a[0] = last
            self._heapify_down(0)
        return top

    def _heapify_up(self, i):
        while i > 0:
            p = (i - 1) // 2
            if self._a[i] >= self._a[p]:
                break
            self._a[i], self._a[p] = self._a[p], self._a[i]
            i = p

    def _heapify_down(self, i):
        n = len(self._a)
        while True:
            smallest, l, r = i, 2 * i + 1, 2 * i + 2
            if l < n and self._a[l] < self._a[smallest]:
                smallest = l
            if r < n and self._a[r] < self._a[smallest]:
                smallest = r
            if smallest == i:
                return
            self._a[i], self._a[smallest] = self._a[smallest], self._a[i]
            i = smallest
