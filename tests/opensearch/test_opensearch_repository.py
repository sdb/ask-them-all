from dataclasses import dataclass

import factory
import pytest
from _pytest.fixtures import fixture
from opensearchpy import NotFoundError

from askthemall.opensearch import OpenSearchRepository


@dataclass
class DummyData:
    id: str
    name: str


class DummyRepository(OpenSearchRepository[DummyData]):

    def __init__(self, client):
        super().__init__(client, 'test')

    def _to_data(self, hit):
        return DummyData(**hit)

    def _get_index_creation_body(self) -> dict:
        return {}


class DummyDataFactory(factory.Factory):
    class Meta:
        model = DummyData

    id = factory.Faker("uuid4")
    name = factory.Faker("name")


@fixture
def dummy_repository(client):
    test_repository = DummyRepository(client)
    client.indices.create(index='test', body={})
    yield test_repository
    client.indices.delete(index='test')


def test_save(client, dummy_repository):
    test_data = DummyDataFactory.create()
    dummy_repository.save(test_data)
    doc = client.get(index='test', id=test_data.id)
    assert doc['_source']['id'] == test_data.id
    assert doc['_source']['name'] == test_data.name


def test_get_by_id(client, dummy_repository):
    test_data = DummyDataFactory.create()
    client.index(index='test', body=test_data.__dict__, id=test_data.id, refresh=True)
    assert dummy_repository.get_by_id(test_data.id) == test_data


def test_find_all(client, dummy_repository):
    test_data = DummyDataFactory.create_batch(5)
    for test in test_data:
        client.index(index='test', body=test.__dict__, id=test.id, refresh=True)
    assert len(dummy_repository.find_all()) == 5


def test_delete_by_id(client, dummy_repository):
    test_data = DummyDataFactory.create()
    client.index(index='test', body=test_data.__dict__, id=test_data.id, refresh=True)
    assert client.get(index='test', id=test_data.id) is not None
    dummy_repository.delete_by_id(test_data.id)
    with pytest.raises(NotFoundError):
        client.get(index='test', id=test_data.id)
