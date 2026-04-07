from pydantic import BaseModel, ConfigDict, Field, model_validator


class CardPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    details: str


class ColumnPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    cardIds: list[str]


class BoardPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    columns: list[ColumnPayload]
    cards: dict[str, CardPayload]

    @model_validator(mode="after")
    def validate_board_references(self) -> "BoardPayload":
        column_ids = [column.id for column in self.columns]
        if len(column_ids) != len(set(column_ids)):
            raise ValueError("column ids must be unique")

        card_ids = set(self.cards.keys())
        referenced_ids: set[str] = set()
        for column in self.columns:
            for card_id in column.cardIds:
                if card_id not in card_ids:
                    raise ValueError(f"card id '{card_id}' is missing from cards map")
                referenced_ids.add(card_id)

        orphans = card_ids - referenced_ids
        if orphans:
            raise ValueError(f"cards not referenced by any column: {sorted(orphans)}")

        return self
