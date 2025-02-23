import logging
from abc import ABC, abstractmethod
from typing import List

from opensearchpy import OpenSearch

from askthemall.core.persistence import DatabaseMigration, ChatData, InteractionData, DataListResult, ChatBotData, \
    Repository, Data, InteractionRepository, ChatRepository

logger = logging.getLogger(__name__)


class IndexNames:
    CHAT_BOTS = 'chat_bots'
    CHATS = 'chats'
    INTERACTIONS = 'interactions'

    def __init__(self, prefix):
        self.__prefix = prefix

    @property
    def chat_bots(self):
        return f'{self.__prefix}{self.CHAT_BOTS}'

    @property
    def chats(self):
        return f'{self.__prefix}{self.CHATS}'

    @property
    def interactions(self):
        return f'{self.__prefix}{self.INTERACTIONS}'


class OpenSearchRepository(Repository[Data], ABC):

    def __init__(self, client: OpenSearch, alias):
        self._client = client
        self._alias = alias

    @abstractmethod
    def _to_data(self, hit):
        pass

    def _get_index_creation_body(self) -> dict:
        return {}

    def create_index_if_not_exists(self):
        index_name = f'{self._alias}_v1'
        if not self._client.indices.exists(index=self._alias):
            self._client.indices.create(index=index_name, body=self._get_index_creation_body())
            self._client.indices.put_alias(index=index_name, name=self._alias)
            logger.info(f"Index '{index_name}' and alias '{self._alias}' created")
        else:
            logger.info(f"Index '{index_name}' already exists")

    def save(self, data: Data):
        self._client.index(
            index=self._alias,
            body=data.__dict__,
            id=data.id,
            refresh=True,
            op_type='index'
        )

    def get_by_id(self, data_id) -> Data:
        response = self._client.get(index=self._alias, id=data_id)
        return self._to_data(response['_source'])

    def find_all(self) -> List[Data]:
        response = self._client.search(
            index=self._alias,
            body={
                "query": {
                    "match_all": {}
                }
            }
        )
        all_data = [self._to_data(hit["_source"]) for hit in response["hits"]["hits"]]
        return all_data

    def delete_by_id(self, data_id):
        self._client.delete(index=self._alias, id=data_id, refresh=True)


class OpenSearchChatBotRepository(OpenSearchRepository[ChatBotData]):

    def __init__(self, client: OpenSearch, index_names: IndexNames):
        super().__init__(client, index_names.chat_bots)

    def _to_data(self, hit):
        return ChatBotData(**hit)


class OpenSearchChatRepository(OpenSearchRepository[ChatData], ChatRepository):

    def __init__(self, client: OpenSearch, index_names: IndexNames):
        super().__init__(client, index_names.chats)
        self.__index_names = index_names

    def _to_data(self, hit):
        return ChatData(**hit)

    def _get_index_creation_body(self) -> dict:
        return {
            "mappings": {
                "properties": {
                    "created_at": {
                        "type": "date"
                    }
                }
            }
        }

    def find_all_by_chat_bot_id(self, chat_bot_id, max_results) -> DataListResult[ChatData]:
        response = self._client.search(
            index=self._alias,
            body={
                "query": {
                    "term": {
                        "chat_bot_id.keyword": chat_bot_id
                    }
                },
                "sort": [
                    {
                        "created_at": {
                            "order": "desc"
                        }
                    }
                ],
                "size": max_results
            }
        )
        chats = [self._to_data(hit["_source"]) for hit in response["hits"]["hits"]]
        total_results = response["hits"]["total"]["value"]
        return DataListResult(data=chats, total_results=total_results)

    def search_chats(self, search_filter: str, max_results=100) -> DataListResult[ChatData]:
        # TODO: currently only 1000 distinct chats are supported, should use pagination using composite aggregation to support unlimited results
        chat_ids_response = self._client.search(
            index=self.__index_names.interactions,
            body={
                "query": {
                    "bool": {
                        "should": [
                            {
                                "wildcard": {
                                    "question": search_filter
                                }
                            },
                            {
                                "wildcard": {
                                    "answer": search_filter
                                }
                            }
                        ]
                    }
                },
                "size": 0,
                "aggs": {
                    "distinct_values": {
                        "terms": {
                            "field": "chat_id.keyword",
                            "size": 1000
                        }
                    }
                }
            },
            _source=['chat_id']
        )
        chat_ids = list(
            set([bucket["key"] for bucket in chat_ids_response["aggregations"]["distinct_values"]["buckets"]]))
        chats_response = self._client.search(
            index=self.__index_names.chats,
            body={
                "query": {
                    "terms": {
                        "id.keyword": chat_ids
                    }
                },
                "sort": [
                    {
                        "created_at": {
                            "order": "desc"
                        }
                    }
                ],
                "size": max_results
            }
        )
        chats = [self._to_data(hit["_source"]) for hit in chats_response["hits"]["hits"]]
        total_results = chats_response["hits"]["total"]["value"]
        return DataListResult(data=chats, total_results=total_results)


class OpenSearchInteractionRepository(OpenSearchRepository[InteractionData], InteractionRepository):

    def __init__(self, client: OpenSearch, index_names: IndexNames):
        super().__init__(client, index_names.interactions)

    def _to_data(self, hit):
        return InteractionData(**hit)

    def _get_index_creation_body(self) -> dict:
        return {
            "mappings": {
                "properties": {
                    "asked_at": {
                        "type": "date"
                    }
                }
            }
        }

    def find_all_by_chat_id(self, chat_id: str) -> list[InteractionData]:
        response = self._client.search(
            index=self._alias,
            body={
                "query": {
                    "term": {
                        "chat_id.keyword": chat_id
                    }
                },
                "sort": [
                    {
                        "asked_at": {
                            "order": "asc"
                        }
                    }
                ]
            }
        )
        return [self._to_data(hit["_source"]) for hit in response["hits"]["hits"]]

    def delete_all_by_chat_id(self, chat_id):
        self._client.delete_by_query(index=self._alias,
                                     body={"query": {"term": {"chat_id.keyword": chat_id}}})


class OpenSearchDatabaseMigration(DatabaseMigration):

    def __init__(self,
                 chat_bot_repository: OpenSearchChatBotRepository,
                 chat_repository: OpenSearchChatRepository,
                 interaction_repository: OpenSearchInteractionRepository):
        self.__chat_bot_repository = chat_bot_repository
        self.__chat_repository = chat_repository
        self.__interaction_repository = interaction_repository

    def migrate(self):
        self.__chat_bot_repository.create_index_if_not_exists()
        self.__chat_repository.create_index_if_not_exists()
        self.__interaction_repository.create_index_if_not_exists()
