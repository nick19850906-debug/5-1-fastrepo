"""이중 연결 리스트 (Doubly Linked List)

[실생활 비유]
  줄 서 있는 사람들이 '앞사람(prev)'과 '뒷사람(next)'의 손을 모두 잡고 있는 모습입니다.
  중간 사람이 빠져도 앞사람과 뒷사람이 손만 다시 잡으면 끝 -> 전체를 뒤질 필요가 없어 O(1).

[구역]  1구역: Node (사람 한 명) / 2구역: DoublyLinkedList (줄 전체)
"""


# ===== 1구역: 노드 (사람 한 명) =====
class Node:
    """노드 = 데이터 상자 + 앞뒤 손(포인터)."""

    def __init__(self, data):
        self.prev = None   # 앞사람 (None = 내가 맨 앞)
        self.next = None   # 뒷사람 (None = 내가 맨 뒤)
        self.data = data   # 내가 들고 있는 값


# ===== 2구역: 이중 연결 리스트 (줄 전체) =====
class DoublyLinkedList:
    """head(맨 앞)와 tail(맨 뒤)만 기억하면 양 끝 작업이 O(1).
    LRU 에서는 head = 방금 쓴 키, tail = 가장 오래 안 쓴 키."""

    def __init__(self):
        self.head = None   # 맨 앞 노드 (가장 최근 사용)
        self.tail = None   # 맨 뒤 노드 (가장 오래 사용 안 함)
        self._size = 0     # 현재 노드 개수

    def __len__(self):
        """len(리스트)로 개수를 물을 때 호출된다."""
        return self._size

    def insert_front(self, data):
        """맨 앞에 새 노드 삽입. O(1)"""
        node = Node(data)
        node.next = self.head          # 새 노드의 뒷사람 = 기존 맨 앞
        if self.head:
            self.head.prev = node      # 기존 맨 앞의 앞사람 = 새 노드
        else:
            self.tail = node           # 비어 있었다면 꼬리도 새 노드
        self.head = node
        self._size += 1
        return node                    # 노드를 돌려줘야 나중에 O(1)로 지울 수 있다

    def insert_back(self, data):
        """맨 뒤에 새 노드 삽입. O(1)"""
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
        """노드 주소만 알면 앞뒤 이웃끼리 손을 다시 잡게 해 O(1) 제거."""
        if node.prev:
            node.prev.next = node.next   # 앞사람의 뒷사람 = 내 뒷사람
        else:
            self.head = node.next        # 내가 맨 앞이었다면 head 교체
        if node.next:
            node.next.prev = node.prev   # 뒷사람의 앞사람 = 내 앞사람
        else:
            self.tail = node.prev        # 내가 맨 뒤였다면 tail 교체
        node.prev = node.next = None     # 내 손은 놓는다
        self._size -= 1
        return node.data

    def remove_front(self):
        """맨 앞 노드 제거 후 값 반환. 비었으면 None."""
        return self.remove_node(self.head) if self.head else None

    def remove_back(self):
        """맨 뒤 노드 제거 후 값 반환 (LRU 제거 대상). 비었으면 None."""
        return self.remove_node(self.tail) if self.tail else None

    def move_to_front(self, node):
        """기존 노드를 맨 앞으로 이동 = '방금 사용했다' 표시. O(1)"""
        if node is self.head:
            return                       # 이미 맨 앞이면 할 일 없음
        self.remove_node(node)           # 1) 지금 자리에서 빼고
        node.next = self.head            # 2) 맨 앞에 다시 끼운다
        if self.head:
            self.head.prev = node
        else:
            self.tail = node
        self.head = node
        self._size += 1                  # remove_node 가 줄인 개수를 되돌림
