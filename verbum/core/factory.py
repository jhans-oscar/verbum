"""Shared helpers for constructing Verbum services."""

from importlib.resources import files
from typing import Tuple

from verbum.core.bible_service import BibleService
from verbum.infrastructure.repositories.json_bible_repository import JsonBibleRepository

DEFAULT_DATASET = "KJV.json"


def build_service(dataset_name: str = DEFAULT_DATASET) -> Tuple[JsonBibleRepository, BibleService]:
    """Instantiate a repository + service pair using bundled JSON data."""
    data_path = files("verbum.data").joinpath(dataset_name)
    repository = JsonBibleRepository(data_path)
    return repository, BibleService(repository)
