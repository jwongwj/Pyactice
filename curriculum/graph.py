"""The ladder: four categories, their subtopics, and what comes before what.

One file on purpose. Ordering scattered across two hundred problem files is ordering
nobody can read or check; here the whole shape is visible at once and `validate()` can
prove it is acyclic and that every problem it names actually exists.

Two things this file is careful about:

  * `requires` **advises**. Nothing in the platform refuses to start a subtopic because
    of it -- the UI says "usually done after" and offers the button anyway. A claim about
    the usual order is not a claim about capability.
  * A subtopic can be planned. `problems=()` with `planned=6` means six exercises are
    designed but not yet authored, and the UI shows the real shape of the ladder rather
    than pretending the unwritten half does not exist.

The catalogue that this encodes, with the reasoning for each rung, is docs/CATALOGUE.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Subtopic:
    id: str                              # "2.3" -- stable, used in URLs and session logs
    slug: str                            # "dict"
    title: str
    requires: tuple[str, ...] = ()       # subtopic ids, advisory
    problems: tuple[str, ...] = ()       # authored problem keys
    planned: int = 0                     # designed, not yet authored
    minutes: tuple[int, int] = (10, 20)
    # Concept tags this subtopic teaches. `./pfs stats` reports failing tags across
    # sessions, so this is what turns "you keep failing tie-breaks" into a next step.
    tags: tuple[str, ...] = ()

    @property
    def total(self) -> int:
        return len(self.problems) + self.planned

    @property
    def authored(self) -> bool:
        return bool(self.problems)


@dataclass(frozen=True)
class Category:
    number: int
    slug: str
    title: str
    blurb: str
    subtopics: tuple[Subtopic, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# 1. Basic Python

BASIC_PYTHON = Category(
    1, "basic-python", "Basic Python",
    "The language does more than you are using. Short drills, one idiom each.",
    (
        # `split()` turns each authored unit into one problem per drill, so `problems`
        # lists the drill keys, not the unit's. The unit key is not in the bank at all.
        Subtopic("1.1", "for-loops", "For loops and comprehensions",
                 problems=(
                           "for_loops.shout",
                           "for_loops.py_files",
                           "for_loops.numbered",
                           "for_loops.pair_up",
                           "for_loops.backwards",
                           "for_loops.every_other",
                           "for_loops.first_admin",
                           "for_loops.rising",
                           "for_loops.flatten",
                           "for_loops.lookup",
                           "for_loops.running_max",
                           "for_loops.report",
                       ), minutes=(10, 20),
                 tags=("iteration", "comprehension")),
        Subtopic("1.2", "strings", "String manipulation", requires=("1.1",),
                 problems=(
                           "strings.trimmed",
                           "strings.unwrap",
                           "strings.sentence",
                           "strings.fields",
                           "strings.extension",
                           "strings.basename",
                           "strings.key_value",
                           "strings.redact",
                           "strings.same_word",
                           "strings.is_image",
                           "strings.ticket",
                           "strings.aligned",
                           "strings.letters_only",
                           "strings.find_at",
                           "strings.parse_log",
                       ), minutes=(20, 35), tags=("paths", "strings")),
        Subtopic("1.3", "ints", "Int and number manipulation",
                 problems=(
                           "ints.split_total",
                           "ints.hms",
                           "ints.floor_pair",
                           "ints.wrap",
                           "ints.towards_zero",
                           "ints.digits",
                           "ints.money",
                           "ints.exact_cents",
                           "ints.clamp",
                           "ints.as_binary",
                           "ints.from_hex",
                           "ints.is_power_of_two",
                           "ints.bits_set",
                           "ints.root",
                           "ints.totals",
                           "ints.human_bytes",
                       ), minutes=(20, 35), tags=("edge-values", "boundaries")),
        Subtopic("1.4", "functions-lambda", "Functions, lambda and key=", requires=("1.1",),
                 problems=(
                           "functions_lambda.greet",
                           "functions_lambda.collect",
                           "functions_lambda.tally",
                           "functions_lambda.settings",
                           "functions_lambda.by_length",
                           "functions_lambda.by_score",
                           "functions_lambda.field_sort",
                           "functions_lambda.doubled",
                           "functions_lambda.positives",
                           "functions_lambda.shout_long",
                           "functions_lambda.rounded",
                           "functions_lambda.join_all",
                           "functions_lambda.leaderboard",
                       ), minutes=(20, 35), tags=("ordering",)),
        Subtopic("1.5", "unpacking", "Unpacking and assignment", requires=("1.1",),
                 problems=(
                           "unpacking.swapped",
                           "unpacking.full_names",
                           "unpacking.head_tail",
                           "unpacking.last_two",
                           "unpacking.middle",
                           "unpacking.coords",
                           "unpacking.columns",
                           "unpacking.reshape",
                           "unpacking.regroup",
                       ), minutes=(15, 25)),
        Subtopic("1.6", "truthiness", "Truthiness, None and conditionals",
                 problems=(
                           "truthiness.has_items",
                           "truthiness.label",
                           "truthiness.port",
                           "truthiness.first_set",
                           "truthiness.in_range",
                           "truthiness.grade",
                           "truthiness.all_passed",
                           "truthiness.any_failed",
                           "truthiness.safe_length",
                           "truthiness.validate",
                       ), minutes=(15, 25),
                 tags=("edge-values", "rejection")),
        Subtopic("1.7", "sorting", "Sorting", requires=("1.1", "1.4"),
                 problems=(
                           "sorting.alphabetical",
                           "sorting.biggest_first",
                           "sorting.ranked",
                           "sorting.by_last_name",
                           "sorting.case_blind",
                           "sorting.stable_groups",
                           "sorting.top_two",
                           "sorting.standings",
                       ), minutes=(20, 30),
                 tags=("ordering", "tie-break", "top-n")),
        Subtopic("1.8", "errors", "Errors and context managers",
                 problems=(
                           "errors.as_int",
                           "errors.divide",
                           "errors.pick",
                           "errors.first_number",
                           "errors.total_or_zero",
                           "errors.require_positive",
                           "errors.cleanup_order",
                           "errors.read_lines",
                           "errors.load_config",
                       ), minutes=(20, 30), tags=("errors",)),
    ),
)

# ---------------------------------------------------------------------------
# 2. Data Structures

DATA_STRUCTURES = Category(
    2, "data-structures", "Data Structures",
    "One per structure. Use it, then build it -- using a stack teaches nothing about stacks.",
    (
        # `planned` counts what is DESIGNED but not written. The catalogue's build
        # exercises -- a dynamic array, a hash map with chaining -- are classes rather
        # than one-function drills, so they stay planned here and will arrive as their
        # own `design` problems, not inside these units.
        Subtopic("2.1", "list", "List", requires=("1.1",), minutes=(20, 30),
                 tags=("two-pointer", "slicing"),
                 problems=("lists.insert_at", "lists.drop_at", "lists.drop_value",
                           "lists.flipped", "lists.deduped", "lists.rotated",
                           "lists.merge_sorted", "lists.chunked", "lists.top_scores",
                           "dynamic_array")),
        Subtopic("2.2", "tuple", "Tuple", requires=("1.1",), minutes=(10, 15),
                 tags=("as-key", "ordering"),
                 problems=("tuples.min_max", "tuples.visits", "tuples.by_dept_then_pay",
                           "tuples.peak", "tuples.unique_pairs", "tuples.leaderboard")),
        Subtopic("2.3", "dict", "Dict", requires=("1.1", "1.6"), minutes=(25, 40),
                 tags=("basics", "counting", "grouping"),
                 problems=("dicts.lookup_or", "dicts.append_to", "dicts.grouped",
                           "dicts.tally", "dicts.top_items", "dicts.merged",
                           "dicts.inverted", "dicts.first_unique",
                           "dicts.subarray_sum_count", "hash_map")),
        Subtopic("2.4", "set", "Set", requires=("1.1", "1.6"), minutes=(12, 20),
                 tags=("algebra", "membership"),
                 problems=("sets.unique_sorted", "sets.unique_stable", "sets.common",
                           "sets.only_in_first", "sets.in_all_three", "sets.tag_groups",
                           "sets.overlap_report")),
        Subtopic("2.5", "stack", "Stack", requires=("2.1",), minutes=(25, 40),
                 tags=("monotonic", "matching"),
                 problems=("stacks.balanced", "stacks.eval_rpn", "stacks.apply_undo",
                           "stacks.next_greater", "stacks.daily_wait",
                           "stacks.largest_rectangle", "min_stack")),
        Subtopic("2.6", "queue-deque", "Queue and deque", requires=("2.1",),
                 minutes=(20, 30), tags=("fifo", "bfs"),
                 problems=("queues.served_order", "queues.last_n", "queues.rotated_queue",
                           "queues.bfs_steps", "queues.window_max", "queues.task_rounds",
                           "two_stack_queue", "circular_buffer")),
        Subtopic("2.7", "heap", "Heap / priority queue", requires=("1.7", "2.3"),
                 minutes=(30, 45), tags=("top-n",),
                 problems=("heaps.k_smallest", "heaps.k_largest", "heaps.drain_order",
                           "heaps.k_closest", "heaps.max_heap_order", "heaps.merge_k",
                           "heaps.top_k_frequent", "streaming_median")),
        Subtopic("2.8", "linked-list", "Linked list", requires=("2.1",),
                 minutes=(30, 45), tags=("two-pointer",),
                 problems=("linked_lists.length", "linked_lists.to_list",
                           "linked_lists.reversed_chain", "linked_lists.has_cycle",
                           "linked_lists.merge_chains",
                           "linked_lists.drop_nth_from_end",
                           "doubly_linked_list", "lru_cache")),
        # 3.6 (backtracking) was listed as a prerequisite and is not one: nothing in this
        # unit needs it, and requiring an unwritten algorithms subtopic before a core data
        # structure had the ladder leaning on a rung above it.
        Subtopic("2.9", "tree", "Tree", requires=("2.6",), minutes=(35, 50),
                 tags=("bfs",),
                 problems=("trees.in_order", "trees.pre_order", "trees.post_order",
                           "trees.max_depth", "trees.level_order", "trees.is_bst",
                           "trees.diameter", "bst", "tree_codec")),
        Subtopic("2.10", "trie", "Trie", requires=("2.3", "2.9"), minutes=(25, 40),
                 tags=("prefix",),
                 problems=("tries.with_prefix", "tries.count_prefixes",
                           "tries.longest_common_prefix", "tries.autocomplete",
                           "trie_structure")),
        Subtopic("2.11", "graph", "Graph", requires=("2.3", "2.6"), minutes=(30, 45),
                 tags=("traverse", "cycle"),
                 problems=("graphs.adjacency", "graphs.degrees", "graphs.components",
                           "graphs.has_cycle_directed", "graphs.is_bipartite",
                           "graphs.reachable_within")),
        Subtopic("2.12", "union-find", "Union-Find", requires=("2.3", "2.6"),
                 minutes=(25, 40), tags=("join",),
                 problems=("union_find.group_count", "union_find.same_group",
                           "union_find.redundant_edge", "union_find.islands",
                           "union_find.accounts_merge", "union_find_structure")),
    ),
)

# ---------------------------------------------------------------------------
# 3. Algorithms

ALGORITHMS = Category(
    3, "algorithms", "Algorithms",
    "By name, with the cue that should make you reach for each one.",
    (
        Subtopic("3.1", "binary-search", "Binary search", requires=("1.7",),
                 minutes=(30, 45), tags=("classic", "boundary"),
                 problems=("binary_search.find_index", "binary_search.insert_position",
                           "binary_search.first_occurrence",
                           "binary_search.last_occurrence", "binary_search.rotated_min",
                           "binary_search.min_capacity")),
        Subtopic("3.2", "two-pointers", "Two pointers", requires=("2.1", "2.3"),
                 minutes=(25, 40), tags=("ordering", "duplicates"),
                 problems=("two_sum_pairs", "two_pointers.pair_sum",
                           "two_pointers.sorted_squares", "two_pointers.most_water",
                           "two_pointers.three_sum", "two_pointers.sort_colors")),
        Subtopic("3.3", "sliding-window", "Sliding window", requires=("2.1", "2.3"),
                 minutes=(30, 50), tags=("counts",),
                 problems=("sliding_window.max_sum_k", "sliding_window.longest_unique",
                           "sliding_window.longest_ones",
                           "sliding_window.anagram_starts",
                           "sliding_window.min_window")),
        Subtopic("3.4", "dfs", "DFS", requires=("2.11",), minutes=(30, 45),
                 tags=("traverse",),
                 problems=("dfs.flood_fill", "dfs.island_sizes", "dfs.all_paths",
                           "dfs.has_path", "dfs.longest_region")),
        Subtopic("3.5", "bfs", "BFS", requires=("2.11", "2.6"), minutes=(30, 45),
                 tags=("bfs",),
                 problems=("bfs.distances_from", "bfs.rot_time", "bfs.ladder_length",
                           "bfs.nearest_exit", "bfs.min_multiply")),
        Subtopic("3.6", "backtracking", "Backtracking", requires=("1.1",),
                 minutes=(35, 55), tags=("recursion",),
                 problems=("backtracking.subsets", "backtracking.permutations",
                           "backtracking.combination_sum",
                           "backtracking.partition_equal", "backtracking.n_queens")),
        Subtopic("3.7", "dijkstra", "Dijkstra", requires=("3.5", "2.7"),
                 minutes=(40, 60), tags=("top-n", "bfs"),
                 problems=("dijkstra.shortest_costs", "dijkstra.shortest_to",
                           "dijkstra.slowest_arrival", "dijkstra.max_probability",
                           "dijkstra.cheapest_with_stops")),
        Subtopic("3.8", "a-star", "A*", requires=("3.7",), minutes=(40, 60),
                 tags=("bfs",),
                 problems=("a_star.manhattan", "a_star.grid_path_cost",
                           "a_star.expanded_count", "a_star.is_admissible",
                           "a_star.path_with_heuristic")),
        Subtopic("3.9", "topological-sort", "Topological sort", requires=("3.4", "2.6"),
                 minutes=(30, 45), tags=("cycle",),
                 problems=("topological.in_degrees", "topological.topo_order",
                           "topological.can_finish", "topological.depth_levels",
                           "topological.alien_order")),
        Subtopic("3.10", "dynamic-programming", "Dynamic programming", requires=("3.6",),
                 minutes=(45, 70), tags=("recursion",),
                 problems=("dynamic_programming.climb_ways",
                           "dynamic_programming.house_robber",
                           "dynamic_programming.coin_change",
                           "dynamic_programming.longest_increasing",
                           "dynamic_programming.edit_distance")),
        Subtopic("3.11", "greedy", "Greedy", requires=("1.7",), minutes=(30, 45),
                 tags=("greedy",),
                 problems=("greedy.can_jump", "greedy.min_jumps", "greedy.gas_station",
                           "greedy.max_meetings", "greedy.min_platforms")),
        Subtopic("3.12", "sorting-algorithms", "Sorting algorithms", requires=("1.7",),
                 minutes=(35, 50), tags=("ordering",),
                 problems=("sorting_algorithms.merge_sort",
                           "sorting_algorithms.partition",
                           "sorting_algorithms.quickselect",
                           "sorting_algorithms.counting_sort",
                           "sorting_algorithms.stable_by_key")),
        Subtopic("3.13", "prefix-sums", "Prefix sums", requires=("2.1",),
                 minutes=(25, 40), tags=("running",),
                 problems=("prefix_sums.running_sum", "prefix_sums.range_sums",
                           "prefix_sums.pivot_index",
                           "prefix_sums.product_except_self",
                           "prefix_sums.region_sum")),
        Subtopic("3.14", "kadane", "Kadane", requires=("2.1",), minutes=(20, 35),
                 tags=("running",),
                 problems=("kadane.max_subarray", "kadane.min_subarray",
                           "kadane.max_subarray_range", "kadane.max_product",
                           "kadane.max_circular")),
        Subtopic("3.15", "monotonic-stack", "Monotonic stack", requires=("2.5",),
                 minutes=(35, 50), tags=("monotonic",),
                 problems=("monotonic_stack.previous_smaller",
                           "monotonic_stack.next_smaller_index",
                           "monotonic_stack.trapped_water",
                           "monotonic_stack.stock_span",
                           "monotonic_stack.max_of_mins")),
        Subtopic("3.16", "bit-manipulation", "Bit manipulation", requires=("1.3",),
                 minutes=(25, 40), tags=("bitwise",),
                 problems=("bits.lonely_value", "bits.count_bits",
                           "bits.is_power_of_four", "bits.subset_at",
                           "bits.single_of_three")),
        Subtopic("3.17", "floyd-cycle", "Floyd cycle detection", requires=("2.8",),
                 minutes=(20, 30), tags=("two-pointer",),
                 problems=("floyd.cycle_length", "floyd.cycle_start",
                           "floyd.find_duplicate", "floyd.meeting_point",
                           "floyd.happy_number")),
        Subtopic("3.18", "intervals", "Intervals", requires=("1.7",), minutes=(25, 40),
                 tags=("ordering", "greedy"),
                 problems=("intervals.merge_intervals", "intervals.insert_interval",
                           "intervals.min_rooms", "intervals.erase_overlaps",
                           "intervals.free_slots")),
    ),
)

# ---------------------------------------------------------------------------
# 4. Industry practices

INDUSTRY = Category(
    4, "industry", "Industry practices",
    "Ninety minutes, four progressive levels, a class you keep refactoring as "
    "requirements arrive. Everything above, at once, under a clock.",
    (
        Subtopic("4.1", "file-hosting", "In-Memory File Hosting Service",
                 requires=("2.3", "1.7"), problems=("file_hosting",), minutes=(90, 90),
                 tags=("ttl", "rollback")),
        Subtopic("4.2", "cloud-storage", "Cloud File Storage",
                 requires=("2.3", "1.7"), problems=("cloud_storage",), minutes=(90, 90),
                 tags=("capacity", "restore")),
        Subtopic("4.3", "in-memory-db", "In-Memory Key-Value Database",
                 requires=("2.3", "1.7"), problems=("in_memory_db",), minutes=(90, 90),
                 tags=("ttl", "backup")),
        Subtopic("4.4", "banking", "Banking System",
                 requires=("2.3", "2.7"), problems=("banking",), minutes=(90, 90),
                 tags=("cashback", "history")),
        Subtopic("4.5", "file-system", "Hierarchical File System",
                 requires=("2.9", "2.3"), problems=("file_system",), minutes=(90, 90),
                 tags=("paths", "permissions", "symlinks")),
    ),
)

CATEGORIES: tuple[Category, ...] = (BASIC_PYTHON, DATA_STRUCTURES, ALGORITHMS, INDUSTRY)


# ---------------------------------------------------------------------------
# lookups


def all_subtopics() -> tuple[Subtopic, ...]:
    return tuple(s for category in CATEGORIES for s in category.subtopics)


def by_id(subtopic_id: str) -> Subtopic | None:
    for subtopic in all_subtopics():
        if subtopic.id == subtopic_id:
            return subtopic
    return None


def by_slug(slug: str) -> Subtopic | None:
    for subtopic in all_subtopics():
        if subtopic.slug == slug:
            return subtopic
    return None


def category_of(subtopic_id: str) -> Category | None:
    for category in CATEGORIES:
        if any(s.id == subtopic_id for s in category.subtopics):
            return category
    return None


def subtopic_for_problem(key: str) -> Subtopic | None:
    for subtopic in all_subtopics():
        if key in subtopic.problems:
            return subtopic
    return None


def frontier(cleared: set[str]) -> tuple[Subtopic, ...]:
    """Subtopics worth doing next: every prerequisite cleared, not itself cleared.

    A frontier rather than a single next step. One forced next is a rail, and the whole
    point is that the path is steppable-off.
    """
    return tuple(
        s for s in all_subtopics()
        if s.id not in cleared and all(r in cleared for r in s.requires)
    )


def missing_requirements(subtopic: Subtopic, cleared: set[str]) -> tuple[Subtopic, ...]:
    return tuple(
        r for r in (by_id(i) for i in subtopic.requires)
        if r is not None and r.id not in cleared
    )


def subtopics_for_tag(tag: str) -> tuple[Subtopic, ...]:
    return tuple(s for s in all_subtopics() if tag in s.tags)


# ---------------------------------------------------------------------------
# self-check


def validate(known_problem_keys: set[str] | None = None) -> list[str]:
    """Structural check. Returns a list of problems found; empty means healthy."""
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_slugs: set[str] = set()

    for subtopic in all_subtopics():
        if subtopic.id in seen_ids:
            errors.append(f"duplicate subtopic id {subtopic.id}")
        seen_ids.add(subtopic.id)
        if subtopic.slug in seen_slugs:
            errors.append(f"duplicate slug {subtopic.slug!r}")
        seen_slugs.add(subtopic.slug)
        if subtopic.total == 0:
            errors.append(f"{subtopic.id} has no exercises, authored or planned")

    for subtopic in all_subtopics():
        for required in subtopic.requires:
            if required not in seen_ids:
                errors.append(f"{subtopic.id} requires unknown subtopic {required}")

    # Prerequisites must be acyclic, or the frontier is empty forever and nothing is
    # ever reachable -- a failure mode with no visible symptom except an empty screen.
    order: dict[str, int] = {}

    def depth(node_id: str, seen: tuple[str, ...] = ()) -> int:
        if node_id in order:
            return order[node_id]
        if node_id in seen:
            errors.append("prerequisite cycle: " + " -> ".join(seen + (node_id,)))
            return 0
        node = by_id(node_id)
        if node is None:
            return 0
        value = 1 + max((depth(r, seen + (node_id,)) for r in node.requires), default=0)
        order[node_id] = value
        return value

    for subtopic in all_subtopics():
        depth(subtopic.id)

    if known_problem_keys is not None:
        for subtopic in all_subtopics():
            for key in subtopic.problems:
                if key not in known_problem_keys:
                    errors.append(f"{subtopic.id} names unknown problem {key!r}")
        placed = {k for s in all_subtopics() for k in s.problems}
        for key in sorted(known_problem_keys - placed):
            errors.append(f"problem {key!r} is in the bank but not placed in the ladder")

    return errors
