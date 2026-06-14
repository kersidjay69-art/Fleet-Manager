"""Сортировка участников. Порядок задаёт И отображение, И очередь раздачи остатка."""
from typing import List
from core.distribution import Member

# id режима -> человекочитаемое название (порядок = порядок в выпадающем списке)
SORT_MODES = {
    "name-asc": "Имя A→Z",
    "name-desc": "Имя Z→A",
    "time-asc": "Сначала старые",
    "time-desc": "Сначала новые",
}


def sort_members(members: List[Member], mode: str) -> List[Member]:
    """Возвращает НОВЫЙ отсортированный список (исходный не мутируется)."""
    if mode == "name-asc":
        return sorted(members, key=lambda m: m.name.casefold())
    if mode == "name-desc":
        return sorted(members, key=lambda m: m.name.casefold(), reverse=True)
    if mode == "time-asc":
        return sorted(members, key=lambda m: m.created_at)
    if mode == "time-desc":
        return sorted(members, key=lambda m: m.created_at, reverse=True)
    return list(members)
