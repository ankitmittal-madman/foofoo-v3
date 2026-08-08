from ops.recommendation.catalogue_publish_targets import (
    publish_to_aux,
    publish_to_all_targets,
    publish_to_ghar,
    publish_to_qdrant,
)

ROWS = [{"id": "1", "name": "Poha"}, {"id": "2", "name": "Idli"}]
VERSION = "sha256:" + "a" * 64


class FakeQdrant:
    def __init__(self, accepted=None):
        self.accepted = accepted
        self.calls = []

    def upsert_collection(self, collection, points):
        self.calls.append((collection, points))
        return self.accepted if self.accepted is not None else len(points)


class FakeGhar:
    def __init__(self, ok=True):
        self.ok = ok
        self.calls = []

    def deploy_published_catalogue(self, publication_version, rows):
        self.calls.append((publication_version, rows))
        return self.ok


class FakeAux:
    def __init__(self, ok=True):
        self.ok = ok
        self.calls = []

    def register_catalogue_version(self, publication_version, dish_count):
        self.calls.append((publication_version, dish_count))
        return self.ok


def test_qdrant_adapter_uses_content_hash_derived_collection_name():
    qdrant = FakeQdrant()
    result = publish_to_qdrant(qdrant, publication_version=VERSION, rows=ROWS)
    assert result.target == "qdrant"
    assert result.publication_version == VERSION
    assert result.accepted is True
    assert qdrant.calls[0][0] == f"foofoo_recipes__{'a' * 12}"


def test_qdrant_adapter_reports_not_accepted_on_count_mismatch():
    qdrant = FakeQdrant(accepted=1)
    result = publish_to_qdrant(qdrant, publication_version=VERSION, rows=ROWS)
    assert result.accepted is False


def test_ghar_adapter_stamps_version_and_passes_rows_through():
    ghar = FakeGhar()
    result = publish_to_ghar(ghar, publication_version=VERSION, rows=ROWS)
    assert result.target == "ghar"
    assert result.publication_version == VERSION
    assert result.accepted is True
    assert ghar.calls == [(VERSION, ROWS)]


def test_aux_adapter_registers_dish_count_and_stamps_version():
    aux = FakeAux()
    result = publish_to_aux(aux, publication_version=VERSION, rows=ROWS)
    assert result.target == "aux"
    assert result.accepted is True
    assert aux.calls == [(VERSION, len(ROWS))]


def test_publish_to_all_targets_stamps_every_target_with_the_same_version():
    qdrant, ghar, aux = FakeQdrant(), FakeGhar(), FakeAux()
    results = publish_to_all_targets(
        publication_version=VERSION, rows=ROWS, qdrant=qdrant, ghar=ghar, aux=aux
    )
    assert {r.target for r in results} == {"qdrant", "ghar", "aux"}
    assert {r.publication_version for r in results} == {VERSION}
    assert all(r.accepted for r in results)


def test_publish_to_all_targets_surfaces_a_failing_target_without_masking_the_others():
    qdrant, ghar, aux = FakeQdrant(), FakeGhar(ok=False), FakeAux()
    results = publish_to_all_targets(
        publication_version=VERSION, rows=ROWS, qdrant=qdrant, ghar=ghar, aux=aux
    )
    by_target = {r.target: r for r in results}
    assert by_target["ghar"].accepted is False
    assert by_target["qdrant"].accepted is True
    assert by_target["aux"].accepted is True
    # Version id stays consistent across targets even when one target rejects the publish.
    assert {r.publication_version for r in results} == {VERSION}
