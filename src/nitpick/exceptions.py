"""Nitpick exceptions."""


class StyleError(Exception):
    """An error in a style file."""

    def __init__(self, style_file_name: str, *args: object) -> None:
        self.style_file_name = style_file_name
        super().__init__(*args)
