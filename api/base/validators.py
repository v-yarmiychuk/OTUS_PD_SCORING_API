import inspect
import logging
from typing import Any
from typing import List
from typing import Tuple

from api.base.fields import BaseField
from api.configurator import Conf


class BaseValidators:
    _declared_fields = {}

    def __new__(cls, conf: Conf):
        setattr(cls, '_declared_fields', cls._get_declared_fields())
        return super().__new__(cls)

    def __init__(self, conf: Conf) -> None:
        self.conf = conf
        self.is_valid = False
        self._errors = []
        self.logger = logging.getLogger(f'scoring_api.Validators')

    @classmethod
    def _get_declared_fields(cls) -> dict:
        logger = logging.getLogger(f'scoring_api.Validators')
        declared_fields = {}
        base_members = [name for name, _ in inspect.getmembers(BaseValidators)]

        for name, obj in inspect.getmembers(cls):
            if all([
                name not in base_members,
                isinstance(obj, BaseField)
            ]):
                declared_fields[name] = obj
                # delattr(cls, name)

        logger.info(f'collected {len(declared_fields)} fields in the class {cls.__name__}')

        return declared_fields

    def validate(self, data: Any) -> Tuple[bool, List[str]]:
        self.is_valid = False
        self._errors.clear()
        self.logger.info(f'start validate in class {self.__class__.__name__}')

        for field_name, field_class in self._declared_fields.items():
            status, errors = field_class.validate(field_name, data)
            self._errors.extend(errors)

        self.class_validate(data)

        if not self._errors:
            self.is_valid = True
        else:
            self.logger.info(f'found {len(self._errors)} errors:')
            for error in self._errors:
                self.logger.info(error)

        return self.is_valid, self._errors

    def class_validate(self, data: Any) -> None:
        ...
