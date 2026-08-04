"""
ghar_re_core.similarity — IDF-weighted ingredient cosine similarity (Core Spine SP-F6),
implementing the frozen spine's own formula `delta_ING = 1 - cosine(v(a), v(b))` for real, rather
than the `pairing.same_base()` set-intersection proxy the spine itself flagged as a stand-in
(pairing.py:39, "Proxy for the §1 ING base-cosine gate, using MAIN ingredients").

Founder-directed backlog closeout (2026-08-04, item 7): builds the cosine machinery and a
cross-cuisine discovery function on top of it — finding dishes with similar ingredient profiles
across DIFFERENT cuisines, the discovery use case SP-F6 names ("Learned ingredient embeddings
replacing IDF" is the deferred v2 upgrade; this is the v1 IDF-overlap version the spine's own
formula already specifies, not a learned embedding). Does not touch `pairing.same_base()` itself —
that stays the reviewed hard-gate proxy it already is; this is a new, separate discovery feature,
not a scoring-path change (no golden-master impact).
"""
import math
from collections import Counter


def build_idf(catalogue):
    """ingredient_name -> IDF weight (log(N / (1 + doc_freq))), computed over every dish in
    `catalogue` (an iterable of Dish objects, or anything with .ingredient_names). Rarer
    ingredients across the catalogue get a higher weight, exactly as the spine's IDF-weighted
    formula intends — a shared 'salt'/'onion' contributes little to similarity, a shared
    'kokum'/'bamboo shoot' contributes a lot."""
    doc_freq = Counter()
    n = 0
    for dish in catalogue:
        n += 1
        for ing in set(dish.ingredient_names):
            doc_freq[ing] += 1
    return {ing: math.log(n / (1 + df)) for ing, df in doc_freq.items()}


def dish_vector(dish, idf):
    """Sparse IDF-weighted ingredient vector for one dish: {ingredient_name: idf_weight}. Missing
    ingredients (not seen when `idf` was built) are simply absent, not zero-padded — cosine() below
    only sums over the intersection, which is mathematically equivalent to zero-padding a full
    vocabulary vector, without needing one."""
    return {ing: idf[ing] for ing in set(dish.ingredient_names) if ing in idf}


def cosine(vec_a, vec_b):
    """Cosine similarity between two sparse {ingredient: weight} vectors, in [0, 1] since all
    weights are non-negative. Returns 0.0 for an empty vector rather than dividing by zero —
    a dish with no resolved ingredients is simply dissimilar to everything, not an error."""
    shared = set(vec_a) & set(vec_b)
    numerator = sum(vec_a[k] * vec_b[k] for k in shared)
    norm_a = math.sqrt(sum(w * w for w in vec_a.values()))
    norm_b = math.sqrt(sum(w * w for w in vec_b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return numerator / (norm_a * norm_b)


def cross_cuisine_similar(dish, catalogue, idf=None, top_n=5):
    """The `n` dishes from a DIFFERENT cuisine to `dish` with the highest ingredient-vector cosine
    similarity to it — the cross-cuisine discovery feature SP-F6 names ("cosine similarity on
    genome vectors" for cross-cuisine discovery). `idf` can be precomputed via build_idf() and
    reused across many calls (recommended for a real catalogue — rebuilding IDF per call is
    wasteful); if not given, it's built fresh from `catalogue` each call.

    Returns a list of (other_dish, similarity) tuples, sorted by similarity descending, length
    <= top_n. Ties broken by catalogue iteration order (stable, not randomized)."""
    if idf is None:
        idf = build_idf(catalogue)
    dish_vec = dish_vector(dish, idf)
    scored = []
    for other in catalogue:
        if other.cuisine == dish.cuisine or other.name == dish.name:
            continue
        sim = cosine(dish_vec, dish_vector(other, idf))
        if sim > 0.0:
            scored.append((other, sim))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_n]
