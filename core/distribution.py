"""Ядро Fleet Manager: справедливое распределение персонажей по флоту.

Чистая логика без Qt — легко тестируется.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set

FLEET_LIMIT = 60


@dataclass
class Member:
    """Участник флота."""
    id: str
    name: str
    max_chars: int          # максимум персонажей, которых может поднять
    created_at: float       # время добавления (для сортировки)
    current_chars: int = 0  # сколько персонажей поднято ПРЯМО СЕЙЧАС (факт)


@dataclass
class DistributionResult:
    assigned: Dict[str, int] = field(default_factory=dict)  # id -> сколько поднять
    target: int = 0                                         # = min(FLEET_LIMIT, Σmax)
    total_assigned: int = 0
    is_full: bool = False
    shortfall: int = 0                                      # сколько не хватает до лимита
    capped_ids: Set[str] = field(default_factory=set)       # кто упёрся в свой максимум


def compute_distribution(queue: List[Member],
                         fleet_limit: int = FLEET_LIMIT) -> DistributionResult:
    """Water-filling с учётом потолков: наливаем поровну, кто упёрся в свой
    максимум — выбывает, излишек перетекает остальным. Остаток (когда target не
    делится нацело) раздаётся по одной единице в порядке очереди ``queue``,
    пропуская тех, кто уже на капе.

    :param queue: участники В ПОРЯДКЕ ОЧЕРЕДИ (= текущая сортировка). Порядок
                  определяет, кому достанется остаток.
    """
    assigned: Dict[str, int] = {m.id: 0 for m in queue}
    # Нормализуем потолки: целые, не отрицательные.
    cap: Dict[str, int] = {m.id: max(0, int(m.max_chars or 0)) for m in queue}

    sum_max = sum(cap.values())
    target = min(fleet_limit, sum_max)

    remaining = target
    # active = те, кто ещё может принять персонажей (assigned < cap), в порядке очереди.
    active = [m for m in queue if cap[m.id] > 0]

    while remaining > 0 and active:
        share = remaining // len(active)

        if share == 0:
            # Остаток меньше числа активных — раздаём по одной в порядке очереди.
            for m in active:
                if remaining == 0:
                    break
                if assigned[m.id] < cap[m.id]:
                    assigned[m.id] += 1
                    remaining -= 1
            break

        for m in active:
            give = min(share, cap[m.id] - assigned[m.id])
            assigned[m.id] += give
            remaining -= give

        active = [m for m in active if assigned[m.id] < cap[m.id]]

    capped_ids = {m.id for m in queue if cap[m.id] > 0 and assigned[m.id] == cap[m.id]}
    total_assigned = target - remaining

    return DistributionResult(
        assigned=assigned,
        target=target,
        total_assigned=total_assigned,
        is_full=total_assigned >= fleet_limit,
        shortfall=max(0, fleet_limit - total_assigned),
        capped_ids=capped_ids,
    )
