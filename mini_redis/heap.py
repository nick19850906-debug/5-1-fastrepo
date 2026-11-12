"""최소 힙 (Min Heap)

[실생활 비유]
  유통기한 임박 순으로 쌓는 냉장고. 맨 위(peek)만 보면 '가장 급한 음식'을 바로 안다.
  TTL 에서는 (만료시각, 키) 중 만료시각이 가장 작은 것이 맨 위에 온다.

[배열로 만든 완전 이진 트리] i번 칸의 부모 = (i-1)//2, 왼쪽 자식 = 2i+1, 오른쪽 자식 = 2i+2
[복잡도] peek O(1), push/pop O(log n)
"""


class MinHeap:
    def __init__(self):
        self._a = []   # 힙 저장용 배열

    def size(self):
        """요소 개수."""
        return len(self._a)

    def peek(self):
        """가장 작은 요소를 꺼내지 않고 보기. 비었으면 None."""
        return self._a[0] if self._a else None

    def push(self, item):
        """맨 끝에 넣고 위로 올려 정렬 상태를 복구한다."""
        self._a.append(item)
        self._heapify_up(len(self._a) - 1)

    def pop(self):
        """가장 작은 요소를 꺼낸다. 마지막 요소를 루트로 옮기고 아래로 내린다."""
        if not self._a:
            return None
        top = self._a[0]
        last = self._a.pop()
        if self._a:
            self._a[0] = last
            self._heapify_down(0)
        return top

    def _heapify_up(self, i):
        """부모보다 작으면 자리를 바꾸며 위로 올라간다."""
        while i > 0:
            p = (i - 1) // 2
            if self._a[i] >= self._a[p]:
                break                                  # 부모가 더 작으면 끝
            self._a[i], self._a[p] = self._a[p], self._a[i]
            i = p

    def _heapify_down(self, i):
        """자식 중 더 작은 쪽과 바꾸며 아래로 내려간다."""
        n = len(self._a)
        while True:
            smallest, l, r = i, 2 * i + 1, 2 * i + 2   # 나/왼쪽/오른쪽 중 최솟값 찾기
            if l < n and self._a[l] < self._a[smallest]:
                smallest = l
            if r < n and self._a[r] < self._a[smallest]:
                smallest = r
            if smallest == i:
                return                                 # 내가 제일 작으면 끝
            self._a[i], self._a[smallest] = self._a[smallest], self._a[i]
            i = smallest
