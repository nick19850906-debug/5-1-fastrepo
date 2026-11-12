import unittest

from mini_redis.cli import execute
from mini_redis.hashmap import HashMap
from mini_redis.heap import MinHeap
from mini_redis.linked_list import DoublyLinkedList
from mini_redis.store import Store


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def run(s, *lines):
    return [execute(s, l) for l in lines]


class StructTests(unittest.TestCase):
    def test_list(self):
        l = DoublyLinkedList()
        a, b, c = l.insert_back(1), l.insert_back(2), l.insert_back(3)
        l.move_to_front(c)
        self.assertEqual((l.head.data, l.tail.data), (3, 2))
        l.remove_node(a)
        self.assertEqual((l.remove_front(), l.remove_back(), len(l)), (3, 2, 0))

    def test_hashmap_resize(self):
        m = HashMap(2)
        for i in range(100):
            m.put("k%d" % i, i)
        self.assertEqual(m.size(), 100)
        self.assertEqual(m.get("k57"), 57)
        self.assertTrue(m.remove("k57"))
        self.assertFalse(m.contains("k57"))
        self.assertTrue(len(m._buckets) >= 128)

    def test_heap(self):
        h = MinHeap()
        for x in [5, 3, 8, 1, 9, 2]:
            h.push((x, "k"))
        self.assertEqual([h.pop()[0] for _ in range(6)], [1, 2, 3, 5, 8, 9])


class CommandTests(unittest.TestCase):
    def test_spec_example(self):
        s = Store()
        r = run(s, "CONFIG SET maxmemory 30", 'SET user:1 "Alice"', 'SET user:2 "Bob"',
                'SET user:3 "Charlie"', "GET user:1", "INFO memory")
        self.assertEqual(r[:5], ["OK"] * 4 + ["(nil)"])
        self.assertEqual(r[5], "used_memory:22\nmaxmemory:30\nevicted_keys:1")

    def test_lru_get_refresh(self):
        s = Store()
        run(s, "CONFIG SET maxmemory 20", "SET a 1234567", "SET b 1234567", "GET a", "SET c 1234567")
        self.assertEqual(run(s, "EXISTS a", "EXISTS b"), ["(integer) 1", "(integer) 0"])

    def test_oom(self):
        s = Store()
        run(s, "CONFIG SET maxmemory 5")
        self.assertTrue(execute(s, "SET key value").startswith("(error) OOM"))

    def test_ttl(self):
        c = Clock()
        s = Store(c)
        run(s, "SET a 1", "SET b 2")
        self.assertEqual(run(s, "TTL a", "EXPIRE a 3", "TTL a", "EXPIRE x 3"),
                         ["(integer) -1", "(integer) 1", "(integer) 3", "(integer) 0"])
        c.t += 3
        self.assertEqual(run(s, "GET a", "TTL a", "DBSIZE"), ["(nil)", "(integer) -2", "(integer) 1"])

    def test_set_resets_ttl(self):
        s = Store(Clock())
        run(s, "SET a 1", "EXPIRE a 5", "SET a 2")
        self.assertEqual(execute(s, "TTL a"), "(integer) -1")

    def test_errors(self):
        s = Store()
        self.assertEqual(run(s, "CONFIG SET maxmemory abc", "GET", "HELLO"), [
            "(error) ERR value is not an integer or out of range",
            "(error) ERR wrong number of arguments for 'GET' command",
            "(error) ERR unknown command 'HELLO'"])

    def test_basic(self):
        s = Store()
        self.assertEqual(run(s, "KEYS", 'SET k "a b"', "GET k", "DEL k", "DEL k", "DBSIZE"),
                         ["(empty array)", "OK", '"a b"', "(integer) 1", "(integer) 0", "(integer) 0"])


if __name__ == "__main__":
    unittest.main()

