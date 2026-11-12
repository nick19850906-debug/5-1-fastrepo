"""이중 연결 리스트 (prev / next / data). 모든 삽입·삭제·이동은 O(1).
[실생활 비유] 줄 서 있는 사람들이 앞뒤 사람 손을 잡고 있는 모습 - 중간에서 빠져도 앞뒤만 다시 손잡으면 끝.
"""


class Node:
    """노드: 앞(prev)·뒤(next) 이웃과 담긴 값(data)."""

    def __init__(self, data):
        self.prev = None
        self.next = None
        self.data = data


class DoublyLinkedList:
    def __init__(self):
        self.head = None  # 맨 앞 (가장 최근 사용)
        self.tail = None  # 맨 뒤 (가장 오래 사용 안 함)
        self._size = 0

    def __len__(self):
        return self._size

    def insert_front(self, data):
        node = Node(data)
        node.next = self.head
        if self.head:
            self.head.prev = node
        else:
            self.tail = node
        self.head = node
        self._size += 1
        return node

    def insert_back(self, data):
        node = Node(data)
        node.prev = self.tail
        if self.tail:
            self.tail.next = node
        else:
            self.head = node
        self.tail = node
        self._size += 1
        return node

    def remove_node(self, node):
        """노드 참조만 있으면 앞뒤를 이어 붙여 O(1) 제거."""
        if node.prev:
            node.prev.next = node.next
        else:
            self.head = node.next
        if node.next:
            node.next.prev = node.prev
        else:
            self.tail = node.prev
        node.prev = node.next = None
        self._size -= 1
        return node.data

    def remove_front(self):
        return self.remove_node(self.head) if self.head else None

    def remove_back(self):
        return self.remove_node(self.tail) if self.tail else None

    def move_to_front(self, node):
        if node is self.head:
            return
        self.remove_node(node)
        node.next = self.head
        if self.head:
            self.head.prev = node
        else:
            self.tail = node
        self.head = node
        self._size += 1
