"""2.7 Heap — the structure for "the k best" when you do not want the rest sorted.

Self-contained: loaded by file path, so no package-relative imports.

`heapq` is a min-heap over a plain list. Half of this unit is its API; the other half is
the judgement call about when it beats `sorted`, and the negation trick that turns it into
a max-heap.

The catalogue's build exercise -- a streaming median from two heaps -- is a class, so it
arrives as a `design` problem.
"""

from __future__ import annotations

from harness.constraints import Forbid, ForbidCall, RequireCall
from harness.units import split
from harness.model import KIND_DRILL, Level, Method, Problem, case, op

METHODS = (
    Method(
        display="K_SMALLEST",
        signature="(nums: list[int], k: int) -> list[int]",
        doc="The k smallest values, ascending. Fewer if the list is shorter.",
        constraint_note="use heapq.nsmallest; do not sort the whole list",
        constraints=(
            ForbidCall(("sorted", "sort"),
                       because="sorting is O(n log n) to answer a question about k items; "
                               "nsmallest is O(n log k), which matters when k is small and "
                               "n is not",
                       hint="heapq.nsmallest(k, nums)"),
        ),
    ),
    Method(
        display="K_LARGEST",
        signature="(nums: list[int], k: int) -> list[int]",
        doc="The k largest values, DESCENDING. Fewer if the list is shorter.",
        constraint_note="use heapq.nlargest; mind the order it returns",
        constraints=(
            ForbidCall(("sorted", "sort"),
                       because="the same argument as nsmallest, and nlargest already "
                               "returns them largest-first so no reversal is needed",
                       hint="heapq.nlargest(k, nums)"),
        ),
    ),
    Method(
        display="DRAIN_ORDER",
        signature="(nums: list[int]) -> list[int]",
        doc="Every value, popped from a min-heap one at a time, in the order they come out.",
        constraint_note="build a heap and pop it; no sorted()",
        constraints=(
            RequireCall(("heappop",),
                        because="popping a heap to exhaustion IS a sort -- that is heapsort, "
                                "and doing it once by hand is how the invariant sticks",
                        hint="heapify(nums), then heappop until it is empty"),
            ForbidCall(("sorted", "sort"),
                       because="the answer is sorted; arriving there via the heap is the drill",
                       hint="heapify then heappop"),
        ),
    ),
    Method(
        display="K_CLOSEST",
        signature="(points: list[tuple[int, int]], k: int) -> list[tuple[int, int]]",
        doc="The k points closest to the origin, nearest first. Ties are broken by x then "
            "y, both ascending. Distance is compared, never displayed.",
        constraint_note="use heapq.nsmallest with a key; no full sort",
        constraints=(
            ForbidCall(("sorted", "sort"),
                       because="nsmallest takes a key, so the whole list never has to be "
                               "ordered to answer a question about k of them",
                       hint="heapq.nsmallest(k, points, key=...) -- and squared distance "
                            "orders identically to distance, so no sqrt is needed"),
        ),
    ),
    Method(
        display="MAX_HEAP_ORDER",
        signature="(nums: list[int]) -> list[int]",
        doc="Every value, largest first, using a MAX-heap built from heapq.",
        constraint_note="negate on the way in and back out; heapq has no max-heap",
        constraints=(
            RequireCall(("heappush", "heappushpop", "heapify"),
                        because="heapq is a min-heap and there is no flag to reverse it; "
                                "pushing -value and negating again on the way out is the "
                                "standard trick, and it is worth having written it once",
                        hint="push -value, then pop and negate"),
            ForbidCall(("sorted", "sort", "nlargest"),
                       because="the drill is the negation trick, not the shortest route",
                       hint="heapify a list of negatives"),
        ),
    ),
    Method(
        display="MERGE_K",
        signature="(lists: list[list[int]]) -> list[int]",
        doc="One sorted list from k already-sorted lists. Keeps duplicates.",
        constraint_note="use heapq.merge, or a heap of one head per list",
        constraints=(
            ForbidCall(("sorted", "sort"),
                       because="concatenating and sorting throws away the fact that all k "
                               "inputs are already ordered",
                       hint="heapq.merge(*lists) does exactly this, lazily"),
        ),
    ),
    Method(
        display="TOP_K_FREQUENT",
        signature="(items: list[str], k: int) -> list[str]",
        doc="The k most frequent items, most frequent first, ties broken alphabetically.",
        checkpoint=True,
    ),
)

LEVELS = (Level(1, "Heap", theme="the k best, without sorting the rest"),)

TAG_GLOSSARY = {
    "top-n": "the k best of n, without ordering the rest",
    "heap-order": "the push/pop invariant itself",
    "negation": "turning a min-heap into a max-heap",
    "key": "ordering by a computed value rather than the item",
    "merge": "combining several already-sorted inputs",
    "edge-values": "empty inputs, k of 0, k larger than n, ties",
    "checkpoint": "the unit's checkpoint: no constraints, several ideas at once",
}


def _c(name, opname, *args, ret, tags, visible=False, doc="", why=""):
    return case(name, 1, [op(opname, *args, ret=ret, why=why)], tags=tags,
                visible=visible, doc=doc)


CASES = [
    _c("k_smallest_basic", "K_SMALLEST", [5, 1, 3], 2, ret=[1, 3],
       tags=["top-n"], visible=True, doc="Ascending."),
    _c("k_smallest_k_bigger", "K_SMALLEST", [2], 5, ret=[2],
       tags=["top-n", "edge-values"], visible=True,
       doc="k larger than the list returns everything, not an error."),
    _c("k_smallest_k_zero", "K_SMALLEST", [1, 2], 0, ret=[], tags=["top-n", "edge-values"]),
    _c("k_smallest_duplicates", "K_SMALLEST", [2, 2, 1], 2, ret=[1, 2],
       tags=["top-n", "edge-values"], why="duplicates are values, not one value"),
    _c("k_smallest_empty", "K_SMALLEST", [], 3, ret=[], tags=["top-n", "edge-values"]),

    _c("k_largest_basic", "K_LARGEST", [5, 1, 3], 2, ret=[5, 3],
       tags=["top-n"], visible=True,
       doc="DESCENDING -- the largest first, which is the order nlargest gives."),
    _c("k_largest_k_bigger", "K_LARGEST", [2], 5, ret=[2], tags=["top-n", "edge-values"]),
    _c("k_largest_k_zero", "K_LARGEST", [1, 2], 0, ret=[], tags=["top-n", "edge-values"]),
    _c("k_largest_negative", "K_LARGEST", [-5, -1, -3], 2, ret=[-1, -3],
       tags=["top-n", "edge-values"]),
    _c("k_largest_empty", "K_LARGEST", [], 3, ret=[], tags=["top-n", "edge-values"]),

    _c("drain_basic", "DRAIN_ORDER", [3, 1, 2], ret=[1, 2, 3],
       tags=["heap-order"], visible=True, doc="A min-heap drains ascending."),
    _c("drain_duplicates", "DRAIN_ORDER", [2, 1, 2], ret=[1, 2, 2], tags=["heap-order"]),
    _c("drain_single", "DRAIN_ORDER", [7], ret=[7], tags=["heap-order", "edge-values"]),
    _c("drain_empty", "DRAIN_ORDER", [], ret=[], tags=["heap-order", "edge-values"]),

    _c("closest_basic", "K_CLOSEST", [(1, 0), (3, 0)], 1, ret=[(1, 0)],
       tags=["key"], visible=True, doc="Nearest the origin first."),
    _c("closest_tie", "K_CLOSEST", [(0, 1), (1, 0)], 2, ret=[(0, 1), (1, 0)],
       tags=["key", "edge-values"], visible=True,
       doc="Both are at distance 1. The tie-break is x ascending, and (0,1) has x=0, "
           "so it comes first regardless of the order they were given in."),
    _c("closest_negative", "K_CLOSEST", [(-1, 0), (2, 0)], 1, ret=[(-1, 0)],
       tags=["key"], visible=True,
       doc="Distance ignores sign: (-1,0) is nearer than (2,0)."),
    _c("closest_k_bigger", "K_CLOSEST", [(1, 1)], 4, ret=[(1, 1)],
       tags=["key", "edge-values"]),
    _c("closest_k_zero", "K_CLOSEST", [(1, 1)], 0, ret=[], tags=["key", "edge-values"]),
    # From `drill_mutation.py --triage`: with only one or two points, a key that reads
    # the wrong coordinate still happens to order them correctly. Three points do not.
    _c("closest_three", "K_CLOSEST", [(2, 3), (-1, 4), (2, 1)], 4,
       ret=[(2, 1), (2, 3), (-1, 4)], tags=["key"], visible=True,
       doc="Squared distances 5, 13 and 17, so no tie-break is needed here -- only a "
           "correct distance."),
    _c("closest_three_way_tie", "K_CLOSEST", [(1, 2), (2, 1), (2, -1), (-1, 1)], 3,
       ret=[(-1, 1), (1, 2), (2, -1)], tags=["key", "edge-values"], visible=True,
       doc="(-1,1) is nearest at 2. The other three are all at 5, so x then y decides: "
           "(1,2), then (2,-1) before (2,1) because -1 < 1. Only three are asked for, so "
           "(2,1) is dropped."),
    _c("closest_empty", "K_CLOSEST", [], 2, ret=[], tags=["key", "edge-values"]),

    _c("max_heap_basic", "MAX_HEAP_ORDER", [1, 3, 2], ret=[3, 2, 1],
       tags=["negation"], visible=True, doc="Largest first."),
    _c("max_heap_negatives", "MAX_HEAP_ORDER", [-1, -3], ret=[-1, -3],
       tags=["negation", "edge-values"], visible=True,
       doc="Negating negatives works the same way; -1 is the larger."),
    _c("max_heap_duplicates", "MAX_HEAP_ORDER", [2, 2], ret=[2, 2], tags=["negation"]),
    _c("max_heap_empty", "MAX_HEAP_ORDER", [], ret=[], tags=["negation", "edge-values"]),

    _c("merge_k_basic", "MERGE_K", [[1, 4], [2, 3]], ret=[1, 2, 3, 4],
       tags=["merge"], visible=True, doc="Two sorted lists interleaved."),
    _c("merge_k_three", "MERGE_K", [[1], [2], [0]], ret=[0, 1, 2], tags=["merge"],
       visible=True, doc="Three inputs need no more code than two."),
    _c("merge_k_with_empty", "MERGE_K", [[], [1]], ret=[1],
       tags=["merge", "edge-values"], visible=True, doc="An empty input contributes nothing."),
    _c("merge_k_duplicates", "MERGE_K", [[2], [2]], ret=[2, 2], tags=["merge"],
       why="duplicates are kept, not collapsed"),
    _c("merge_k_none", "MERGE_K", [], ret=[], tags=["merge", "edge-values"]),
    _c("merge_k_all_empty", "MERGE_K", [[], []], ret=[], tags=["merge", "edge-values"]),

    _c("top_k_freq_basic", "TOP_K_FREQUENT", ["a", "b", "a"], 1, ret=["a"],
       tags=["checkpoint"], visible=True, doc="Most frequent first."),
    _c("top_k_freq_tie", "TOP_K_FREQUENT", ["b", "a"], 2, ret=["a", "b"],
       tags=["checkpoint", "edge-values"], visible=True,
       doc="Equal counts break alphabetically, which nlargest on the counts alone will "
           "not do -- it keeps insertion order."),
    _c("top_k_freq_k_bigger", "TOP_K_FREQUENT", ["a"], 5, ret=["a"],
       tags=["checkpoint", "edge-values"]),
    _c("top_k_freq_k_zero", "TOP_K_FREQUENT", ["a"], 0, ret=[],
       tags=["checkpoint", "edge-values"]),
    _c("top_k_freq_empty", "TOP_K_FREQUENT", [], 2, ret=[],
       tags=["checkpoint", "edge-values"]),
    _c("top_k_freq_mixed", "TOP_K_FREQUENT", ["c", "b", "b", "a", "a"], 2,
       ret=["a", "b"], tags=["checkpoint"],
       why="a and b both appear twice, so alphabetical order decides which comes first"),
]

ALL_CASES = tuple(CASES)

UNIT = Problem(
    key="heaps",
    title="2.7 Heap / priority queue",
    blurb="nsmallest and nlargest, the heap invariant, the negation trick and merging k.",
    class_name="",
    kind=KIND_DRILL,
    total_points=100,
    category="data-structures",
    difficulty="medium",
    topics=("top-n", "negation", "merge"),
    levels=LEVELS,
    methods=METHODS,
    cases=ALL_CASES,
    tag_glossary=TAG_GLOSSARY,
    source="Curriculum unit 2.7 — see docs/CATALOGUE.md",
)

PROBLEMS = split(UNIT)
