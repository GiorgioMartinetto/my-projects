from sqlalchemy.orm import Session


class BaseRepository:
    """Base repository class that provides common database operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        return self._session