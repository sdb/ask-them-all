import factory

from askthemall.core.persistence import ChatBotData, ChatData, InteractionData


class ChatBotDataFactory(factory.Factory):
    class Meta:
        model = ChatBotData

    id = factory.Faker("uuid4")
    name = factory.Faker("name")


class ChatDataFactory(factory.Factory):
    class Meta:
        model = ChatData

    id = factory.Faker("uuid4")
    chat_bot_id = factory.Faker("uuid4")
    slug = factory.Faker("slug")
    title = factory.Faker("sentence")
    created_at = factory.Faker("date_time")


class InteractionDataFactory(factory.Factory):
    class Meta:
        model = InteractionData

    id = factory.Faker("uuid4")
    chat_id = factory.Faker("uuid4")
    question = factory.Faker("sentence")
    answer = factory.Faker("sentence")
    asked_at = factory.Faker("date_time")
