from typing import Any

from api.base.fields import ArgumentsField
from api.base.fields import BirthDayField
from api.base.fields import CharField
from api.base.fields import ChoiceField
from api.base.fields import ClientIDsField
from api.base.fields import DateField
from api.base.fields import EmailField
from api.base.fields import PhoneField
from api.base.validators import BaseValidators


class MethodValidator(BaseValidators):
    account = CharField(required=False, null=True)
    login = CharField(required=True, null=True)
    token = CharField(required=True, null=True)
    method = CharField(required=True, null=False)
    arguments = ArgumentsField(required=True, null=True)


class ClientsInterestsValidator(BaseValidators):
    client_ids = ClientIDsField(required=True, null=False)
    date = DateField(required=False, null=True, date_format='%d.%m.%Y')


class OnlineScoreValidator(BaseValidators):
    UNKNOWN = 1
    MALE = 2
    FEMALE = 3
    GENDERS = {
        UNKNOWN: 'unknown',
        MALE: 'male',
        FEMALE: 'female',
    }

    first_name = CharField(required=False, null=True)
    last_name = CharField(required=False, null=True)
    email = EmailField(required=False, null=True)
    phone = PhoneField(required=False, null=True, max_len=11)
    birthday = BirthDayField(required=False, null=True, date_format='%d.%m.%Y', not_older_year=70)
    gender = ChoiceField(required=False, null=True, choice_items=GENDERS)

    def class_validate(self, data: Any) -> None:
        couples = [
            (data.get('phone', '') and data.get('email', '')),
            (data.get('last_name', '') and data.get('first_name', '')),
            (data.get('gender', '') and data.get('birthday', ''))
        ]

        if not any(couples):
            self._errors.append(
                'at least one pair of phone-email, first name-last name, '
                'gender-birthday with non-empty values is required '
            )
