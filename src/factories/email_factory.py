# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
# SPDX-FileCopyrightText: 2026 Kevin Ottens <kevin.ottens@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from dataclasses import dataclass, field
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

import factory
from AkonadiCore import Akonadi  # type: ignore
from faker import Faker
from imap_tools import BaseMailBox

from src.akonadi.imap_resource import ImapResource
from src.akonadi.utils import AkonadiUtils

fake = Faker()

_clients: dict[str, BaseMailBox | ImapResource] = {}


def set_clients(imap: BaseMailBox, akonadi: ImapResource):
    _clients["imap"] = imap
    _clients["akonadi"] = akonadi


@dataclass
class Email:
    message: EmailMessage
    folder: str
    flags: list[str] = field(default_factory=list)

    def as_bytes(self) -> bytes:
        return self.message.as_bytes()

    def save_to_imap_server(self):
        _clients["imap"].append(self.as_bytes(), folder=self.folder, flag_set=self.flags)

    def save_to_akonadi(self, collection: Akonadi.Collection | None):
        collection = collection or _clients["akonadi"].resolve_collection(self.folder)
        _clients["akonadi"].akonadi_client.add_item(collection.id(), self.as_bytes(), "message/rfc822")


@dataclass
class Folder:
    name: str
    messages: list[Email] = field(default_factory=list)


class BaseEmailFactory(factory.Factory):
    class Meta:
        model = Email
        abstract = True

    subject = factory.Faker("sentence", nb_words=5)
    content = factory.Faker("paragraphs", nb=5)
    from_name = factory.Faker("name")
    from_email = factory.Faker("email")
    to_name = factory.Faker("name")
    to_email = factory.Faker("email")
    date = factory.Faker("date_time_this_decade")
    message_id = factory.LazyFunction(make_msgid)

    @classmethod
    def _build(cls, model_class, **kwargs):
        assert "folder" in kwargs, "Email requires folder parameter"
        msg = EmailMessage()
        msg.set_content("\r\n".join(kwargs.get("content")))
        msg["Subject"] = kwargs.get("subject")
        msg["From"] = f"{kwargs.get('from_name')} <{kwargs.get('from_email')}>"
        msg["To"] = f"{kwargs.get('to_name')} <{kwargs.get('to_email')}>"
        msg["Date"] = formatdate(timeval=kwargs.get("date").timestamp(), localtime=True)
        msg["Message-ID"] = kwargs.get("message_id")
        return model_class(message=msg, folder=kwargs["folder"], flags=kwargs.get("flags", []))


class ImapEmailFactory(BaseEmailFactory):
    class Meta:
        model = Email

    @classmethod
    def _create(cls, model_class, **kwargs):
        email = cls._build(model_class, **kwargs)
        email.save_to_imap_server()
        return email


class AkonadiEmailFactory(BaseEmailFactory):
    class Meta:
        model = Email

    @classmethod
    def _create(cls, model_class, **kwargs):
        email = cls._build(model_class, **kwargs)
        email.save_to_akonadi(kwargs.get("collection"))
        return email


class BaseFolderFactory(factory.Factory):
    class Meta:
        model = Folder
        abstract = True

    folder_depth = 1
    nb_items = factory.Faker("random_int", min=1, max=8)
    email_factory: type[BaseEmailFactory] | None = None

    @factory.lazy_attribute
    def name(obj):
        depth = obj.folder_depth
        return "/".join(fake.word() for _ in range(depth)) if depth > 1 else fake.word()

    @classmethod
    def _build(cls, model_class, **kwargs):
        folder = model_class(name=kwargs["name"])
        folder.messages = cls.email_factory.build_batch(kwargs.get("nb_items"), folder=folder.name)
        return folder


class ImapFolderFactory(BaseFolderFactory):
    class Meta:
        model = Folder

    email_factory = ImapEmailFactory

    @classmethod
    def _create(cls, model_class, **kwargs):
        folder = cls._build(model_class, **kwargs)
        client = _clients["imap"]
        client.folder.create(folder.name)
        for email in folder.messages:
            client.append(email.as_bytes(), folder=folder.name, flag_set=email.flags)
        return folder


class AkonadiFolderFactory(BaseFolderFactory):
    class Meta:
        model = Folder

    email_factory = AkonadiEmailFactory

    @classmethod
    def _create(cls, model_class, **kwargs):
        folder = cls._build(model_class, **kwargs)
        client = _clients["akonadi"]

        root = client.get_root_collection()
        collection = Akonadi.Collection()
        collection.setName(folder.name)
        collection.setContentMimeTypes(["inode/directory", "message/rfc822"])
        collection.setParentCollection(root)
        job = Akonadi.CollectionCreateJob(collection)
        AkonadiUtils.wait_for_job(job)
        collection = job.collection()
        for email in folder.messages:
            email.save_to_akonadi(collection)
        return folder
