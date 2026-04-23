# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
# SPDX-FileCopyrightText: 2026 Kevin Ottens <kevin.ottens@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from __future__ import annotations

from dataclasses import dataclass, field
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from typing import TypedDict

import factory
from AkonadiCore import Akonadi  # type: ignore
from faker import Faker
from imap_tools import BaseMailBox

from src.akonadi.imap_resource import ImapResource
from src.akonadi.utils import AkonadiUtils

fake = Faker()


class _Clients(TypedDict):
    imap: BaseMailBox
    akonadi: ImapResource


_clients: _Clients = {}  #  type: ignore[typeddict-item]


def set_clients(imap: BaseMailBox, akonadi: ImapResource):
    _clients["imap"] = imap
    _clients["akonadi"] = akonadi


@dataclass
class Email:
    """
    Note: folder must be a Folder object or the folder path with correct delimiters
    """

    message: EmailMessage
    folder: Folder | str
    flags: list[str] = field(default_factory=list)

    def as_bytes(self) -> bytes:
        return self.message.as_bytes()

    def _folder_path(self) -> str:
        return self.folder.imap_path if isinstance(self.folder, Folder) else self.folder

    def save_to_imap_server(self):
        _clients["imap"].append(self.as_bytes(), folder=self._folder_path(), flag_set=self.flags)

    def save_to_akonadi(self, collection: Akonadi.Collection | None):
        collection = collection or _clients["akonadi"].resolve_collection(self._folder_path())
        item = _clients["akonadi"].akonadi_client.add_item(
            collection.id(), self.as_bytes(), "message/rfc822"
        )
        for flag in self.flags:
            _clients["akonadi"].add_flag(item.id(), flag)


@dataclass
class Folder:
    name: str
    messages: list[Email] = field(default_factory=list)
    parent: Folder | None = None

    @property
    def imap_path(self, delim: str | None = None) -> str:
        if delim is None:
            delim = _clients["imap"].delimiter  # type: ignore[attr-defined]
        if self.parent:
            return f"{self.parent.imap_path}{delim}{self.name}"
        return self.name

    def get_collection(self) -> Akonadi.Collection:
        return _clients["akonadi"].resolve_collection(self.imap_path)

    def save_to_imap_server(self):
        _clients["imap"].folder.create(self.imap_path)
        for email in self.messages:
            email.save_to_imap_server()

    def save_to_akonadi(self):
        client = _clients["akonadi"]
        if self.parent:
            parent = client.resolve_collection(self.parent.imap_path)
        else:
            parent = client.get_root_collection()
        assert parent

        collection = Akonadi.Collection()
        collection.setName(self.name)
        collection.setContentMimeTypes(["inode/directory", "message/rfc822"])
        collection.setParentCollection(parent)
        job = Akonadi.CollectionCreateJob(collection)
        AkonadiUtils.wait_for_job(job)
        collection = job.collection()
        for email in self.messages:
            email.save_to_akonadi(collection)


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
    flags = fake.random_elements(
        elements=["\\Answered", "\\Flagged", "\\Draft", "\\Seen"], unique=True
    )

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
        return model_class(message=msg, folder=kwargs["folder"], flags=kwargs.get("flags"))


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

    name = factory.Faker("word")
    nb_items = factory.Faker("random_int", min=1, max=8)
    email_factory: type[BaseEmailFactory] | None = None
    parent: Folder | None = None

    @classmethod
    def _build(cls, model_class, **kwargs):
        folder = model_class(name=kwargs["name"], parent=kwargs.get("parent"))
        folder.messages = cls.email_factory.build_batch(
            kwargs.get("nb_items"), folder=folder.imap_path
        )
        return folder


class ImapFolderFactory(BaseFolderFactory):
    class Meta:
        model = Folder

    email_factory = ImapEmailFactory

    @classmethod
    def _create(cls, model_class, **kwargs):
        folder = cls._build(model_class, **kwargs)
        folder.save_to_imap_server()
        return folder


class AkonadiFolderFactory(BaseFolderFactory):
    class Meta:
        model = Folder

    email_factory = AkonadiEmailFactory

    @classmethod
    def _create(cls, model_class, **kwargs):
        folder = cls._build(model_class, **kwargs)
        folder.save_to_akonadi()
        return folder
