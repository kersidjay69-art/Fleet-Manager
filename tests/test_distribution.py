"""Тесты алгоритма справедливого распределения. Запуск: python -m unittest -v"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.distribution import Member, compute_distribution, FLEET_LIMIT

_seq = [0]


def mk(name, max_chars):
    _seq[0] += 1
    return Member(id=f"{name}-{_seq[0]}", name=name, max_chars=max_chars, created_at=_seq[0])


def total(result):
    return sum(result.assigned.values())


class TestDistribution(unittest.TestCase):
    def test_even_split(self):
        users = [mk("A", 30), mk("B", 30), mk("C", 30)]
        r = compute_distribution(users)
        self.assertEqual(r.target, 60)
        self.assertEqual(total(r), 60)
        for u in users:
            self.assertEqual(r.assigned[u.id], 20)
        self.assertTrue(r.is_full)
        self.assertEqual(r.shortfall, 0)

    def test_low_cap_overflow(self):
        users = [mk("A", 2), mk("B", 50), mk("C", 50)]
        r = compute_distribution(users)
        self.assertEqual(total(r), 60)
        self.assertEqual(r.assigned[users[0].id], 2)
        self.assertIn(users[0].id, r.capped_ids)
        self.assertEqual(r.assigned[users[1].id], 29)
        self.assertEqual(r.assigned[users[2].id], 29)

    def test_never_exceeds_cap(self):
        users = [mk("A", 5), mk("B", 1), mk("C", 100), mk("D", 7)]
        r = compute_distribution(users)
        for u in users:
            self.assertLessEqual(r.assigned[u.id], u.max_chars)
        self.assertEqual(total(r), r.target)

    def test_shortfall(self):
        users = [mk("A", 10), mk("B", 10), mk("C", 10)]
        r = compute_distribution(users)
        self.assertEqual(r.target, 30)
        self.assertEqual(total(r), 30)
        for u in users:
            self.assertEqual(r.assigned[u.id], 10)
        self.assertFalse(r.is_full)
        self.assertEqual(r.shortfall, 30)

    def test_diff_at_most_one(self):
        users = [mk(c, 100) for c in "ABCDEFG"]
        r = compute_distribution(users)  # 60 / 7 = 8 ост. 4
        vals = [r.assigned[u.id] for u in users]
        self.assertLessEqual(max(vals) - min(vals), 1)
        self.assertEqual(total(r), 60)

    def test_remainder_follows_queue_order(self):
        users = [mk(c, 100) for c in "ABCDEFG"]
        r = compute_distribution(users)  # base 8, остаток 4 → первым четырём
        self.assertEqual(r.assigned[users[0].id], 9)
        self.assertEqual(r.assigned[users[3].id], 9)
        self.assertEqual(r.assigned[users[4].id], 8)
        self.assertEqual(r.assigned[users[6].id], 8)

        r2 = compute_distribution(list(reversed(users)))
        self.assertEqual(r2.assigned[users[6].id], 9)
        self.assertEqual(r2.assigned[users[0].id], 8)

    def test_ignores_zero_negative_caps(self):
        users = [mk("A", 0), mk("B", -5), mk("C", 30)]
        r = compute_distribution(users)
        self.assertEqual(r.assigned[users[0].id], 0)
        self.assertEqual(r.assigned[users[1].id], 0)
        self.assertEqual(r.assigned[users[2].id], 30)
        self.assertEqual(total(r), 30)

    def test_empty(self):
        r = compute_distribution([])
        self.assertEqual(r.target, 0)
        self.assertEqual(total(r), 0)
        self.assertEqual(r.shortfall, FLEET_LIMIT)

    def test_overflow_clamped_to_limit(self):
        users = [mk("A", 40), mk("B", 40), mk("C", 40)]
        r = compute_distribution(users)
        self.assertEqual(total(r), 60)
        self.assertEqual(r.assigned[users[0].id], 20)


if __name__ == "__main__":
    unittest.main()
