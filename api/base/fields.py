import inspect
import logging
import re
from collections import OrderedDict
from datetime import datetime
from typing import Any
from typing import List
from typing import Tuple


class BaseField(object):
    logger = logging.getLogger(f'scoring_api.Field')

    def __init__(self, required=False, null=True) -> None:
        self.required = required
        self.null = null

        self._validate_handlers = dict()
        self._is_valid = False
        self._errors = []

    def validate(self, name: str, data: dict) -> Tuple[bool, List[str]]:
        self._is_valid = False
        self._errors.clear()
        self.logger.info(f'validate field "{name}": started')

        if data.get(name, None) is None:
            if self.required:
                self._errors.append(f'The "{name}" field is required')
            else:
                self.logger.info(f'optional field "{name}" is missing, processing is not performed')

        elif not (self.null or data[name]):
            self._errors.append(f'The "{name}" field cannot be empty')

        else:
            self._get_validate_handlers()

            for func_name, func in OrderedDict(sorted(self._validate_handlers.items())).items():
                self.logger.info(f'validate field "{name}": started method {func_name}')

                try:
                    func(name, data[name])
                except self.ValidateError as e:
                    self._errors.append(e)

        if not self._errors:
            self._is_valid = True
            self.logger.info(f'validate field "{name}": completed successful')
        else:
            self.logger.info(f'validate field "{name}": completed unsuccessful')

        return self._is_valid, self._errors

    def _get_validate_handlers(self) -> None:
        for name, func in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith('_validate_'):
                self._validate_handlers[name] = func

    class ValidateError(Exception):
        ...


class ValidateMixinsMaxLen:
    def __init__(self, max_len: int = 256, *args, **kwargs) -> None:
        self._max_len = max_len
        super().__init__(*args, **kwargs)

    def _validate_max_len(self, name: str, data: Any) -> None:
        if not len(str(data)) <= self._max_len:
            raise BaseField.ValidateError(
                f'The "{name}" field is too long, the maximum number of characters is {self._max_len}'
            )


class CharField(ValidateMixinsMaxLen, BaseField):
    def _validate_type(self, name: str, data: Any) -> None:
        if not isinstance(data, str):
            raise BaseField.ValidateError(f'The "{name}" field is not instance of str')


class ArgumentsField(BaseField):
    def _validate_type(self, name: str, data: Any) -> None:
        if not isinstance(data, dict):
            raise BaseField.ValidateError(f'The "{name}" field is not instance of dict')


class EmailField(CharField):
    EMAIL_REGEX = re.compile(r"^[A-Za-z0-9.+_-]+@[A-Za-z0-9._-]+\.[a-zA-Z]*$")

    def _validate_mask(self, name: str, data: Any) -> None:
        if not self.EMAIL_REGEX.match(data):
            raise BaseField.ValidateError(f'The "{name}" field does not match the mail mask')


class PhoneField(ValidateMixinsMaxLen, BaseField):
    PHONE_REGEX = re.compile(r"^7[0-9- ()]*$")

    def _validate_type(self, name: str, data: Any) -> None:
        if not (isinstance(data, str) or isinstance(data, int)):
            raise BaseField.ValidateError(f'The "{name}" field is not instance of str')

    def _validate_mask(self, name: str, data: Any) -> None:
        if not self.PHONE_REGEX.match(str(data)):
            raise BaseField.ValidateError(f'The "{name}" field does not match the phone mask')


class DateField(BaseField):
    def __init__(self, date_format: str = '%Y-%m-%d', *args, **kwargs) -> None:
        self._format = date_format
        super().__init__(*args, **kwargs)

    def _validate_type(self, name: str, data: Any) -> None:
        try:
            datetime.strptime(data, self._format)
        except ValueError:
            raise BaseField.ValidateError(f'The "{name}" field has incorrect data format, should be {self._format}')


class BirthDayField(DateField):
    def __init__(self, not_older_year: int = 18, *args, **kwargs) -> None:
        self._not_older_year = not_older_year
        super().__init__(*args, **kwargs)

    def _validate_not_older_year(self, name: str, data: Any) -> None:
        try:
            time_between_insertion = datetime.now() - datetime.strptime(data, self._format)
            if time_between_insertion.days > self._not_older_year * 365:
                raise ValueError()
        except ValueError:
            raise BaseField.ValidateError(f'The "{name}" date is older than {self._not_older_year} years"')


class ChoiceField(BaseField):
    def __init__(self, choice_items: dict, *args, **kwargs) -> None:
        self._choices = choice_items
        super().__init__(*args, **kwargs)

    def _validate_choice(self, name: str, data: Any) -> None:
        if data not in self._choices.keys():
            raise BaseField.ValidateError(
                f'The "{name}" field does not match any of the options values {self._choices.keys()}'
            )


class ClientIDsField(BaseField):
    def _validate_type(self, name: str, data: Any) -> None:
        if not isinstance(data, list):
            raise BaseField.ValidateError(f'The "{name}" field is not instance of list')
        if not all([isinstance(item, int) for item in data]):
            raise BaseField.ValidateError(f'The "{name}" field does not contain only int')
