from food_ontology_service.cache_invalidator import CacheInvalidator


class Repository:
    def cache_invalidation_events(self, after_id, limit):
        assert after_id == 0
        assert limit == 500
        return [
            {"id": 1, "namespace": "dish"},
            {"id": 2, "namespace": "dish"},
            {"id": 3, "namespace": "classes"},
        ]


class Redis:
    def __init__(self):
        self.commands = []

    def command(self, *parts):
        self.commands.append(parts)
        if parts == ("GET", "foofoo:ontology:invalidation_cursor"):
            return None
        return "OK"


def test_invalidator_bumps_each_namespace_once_then_advances_cursor():
    redis = Redis()
    assert CacheInvalidator(Repository(), redis).run_once() == 3
    assert redis.commands == [
        ("GET", "foofoo:ontology:invalidation_cursor"),
        ("INCR", "foofoo:ontology:v:classes"),
        ("INCR", "foofoo:ontology:v:dish"),
        ("SET", "foofoo:ontology:invalidation_cursor", 3),
    ]
