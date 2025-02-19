import logging
from typing import List

from opensearchpy import OpenSearch

from askthemall.core.persistence import DatabaseClient, ChatData, InteractionData, DataListResult, ChatBotData

logger = logging.getLogger(__name__)


class OpenSearchDatabaseClient(DatabaseClient):

    def __init__(self, host, port, index_prefix=''):
        self.client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False
        )
        self.__index_prefix = index_prefix

    @property
    def __chats_index_name(self):
        return f"{self.__index_prefix}chats"

    @property
    def __interactions_index_name(self):
        return f"{self.__index_prefix}interactions"

    @property
    def __chat_bots_index_name(self):
        return f"{self.__index_prefix}chat_bots"

    def save_chat(self, chat: ChatData):
        self.client.index(
            index=self.__chats_index_name,
            body=chat.__dict__,
            id=chat.id,
            refresh=True,
            op_type='index'
        )

    def get_chat_by_id(self, chat_id) -> ChatData:
        response = self.client.get(index=self.__chats_index_name, id=chat_id)
        return ChatData(**response['_source'])

    def save_interaction(self, interaction: InteractionData):
        self.client.index(
            index=self.__interactions_index_name,
            body=interaction.__dict__,
            id=interaction.id,
            refresh=True,
            op_type='index'
        )

    def save_chat_bot(self, chat_bot: ChatBotData):
        self.client.index(
            index=self.__chat_bots_index_name,
            body=chat_bot.__dict__,
            id=chat_bot.id,
            refresh=True,
            op_type='index'
        )

    def delete_chat(self, chat_id):
        self.client.delete(index=self.__chats_index_name, id=chat_id, refresh=True)

    def delete_interactions(self, chat_id):
        self.client.delete_by_query(index=self.__interactions_index_name,
                                    body={"query": {"term": {"chat_id.keyword": chat_id}}})

    def list_all_chats(self, chat_bot_id, max_results=100) -> DataListResult[ChatData]:
        response = self.client.search(
            index=self.__chats_index_name,
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
        chats = [ChatData(**hit["_source"]) for hit in response["hits"]["hits"]]
        total_results = response["hits"]["total"]["value"]
        return DataListResult(data=chats, total_results=total_results)

    def filter_chats(self, search_filter: str, max_results=100) -> DataListResult[ChatData]:
        # TODO: currently only 1000 distinct chats are supported, should use pagination using composite aggregation to support unlimited results
        chat_ids_response = self.client.search(
            index=self.__interactions_index_name,
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
        chats_response = self.client.search(
            index=self.__chats_index_name,
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
        chats = [ChatData(**hit["_source"]) for hit in chats_response["hits"]["hits"]]
        total_results = chats_response["hits"]["total"]["value"]
        return DataListResult(data=chats, total_results=total_results)

    def list_all_interactions(self, chat_id) -> list[InteractionData]:
        response = self.client.search(
            index=self.__interactions_index_name,
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
        interactions = [InteractionData(**hit["_source"]) for hit in response["hits"]["hits"]]
        return interactions

    def list_all_chat_bots(self) -> List[ChatBotData]:
        response = self.client.search(
            index=self.__chat_bots_index_name,
            body={
                "query": {
                    "match_all": {}
                }
            }
        )
        chat_bots = [ChatBotData(**hit["_source"]) for hit in response["hits"]["hits"]]
        return chat_bots

    def __create_index_if_not_exists(self, name, body):
        index_name = f'{name}_v1'
        if not self.client.indices.exists(index=name):
            self.client.indices.create(index=index_name, body=body)
            self.client.indices.put_alias(index=index_name, name=name)
            logger.info(f"Index '{index_name}' and alias '{name}' created")
        else:
            logger.info(f"Index '{name}' already exists")

    def migrate(self):
        self.__create_index_if_not_exists(name=self.__chats_index_name, body={
            "mappings": {
                "properties": {
                    "created_at": {
                        "type": "date"
                    }
                }
            }
        })
        self.__create_index_if_not_exists(name=self.__interactions_index_name, body={
            "mappings": {
                "properties": {
                    "asked_at": {
                        "type": "date"
                    }
                }
            }
        })
        self.__create_index_if_not_exists(name=self.__chat_bots_index_name, body={})
