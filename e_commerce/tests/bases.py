import datetime
import random
import typing
from typing import Any, Dict, List, Type

import factory
from pydantic_factories import AsyncPersistenceProtocol, ModelFactory, PostGenerated
from pytz import utc
from django.db import models


class BaseModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        abstract = True

    @staticmethod
    def check_factory(
        factory_class: typing.Type["BaseModelFactory"], model: typing.Type[models.Model]
    ) -> None:
        """Test that factory creates successfully."""
        obj = factory_class()
        size = random.randint(2, 3)
        objs = factory_class.create_batch(size=size)

        assert isinstance(obj, model)
        assert size == len(objs)
        for i in objs:
            assert isinstance(i, model)

