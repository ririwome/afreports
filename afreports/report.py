from __future__ import annotations

import base64
import re
import unicodedata
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

@dataclass
class Block:
    type: str
    data: dict[str, Any]


@dataclass
class TableOfContentsEntry:
    text: str
    anchor: str
    level: int
    number: str


@dataclass
class AppendixEntry:
    caption: str
    anchor: str
    label: str


class Report:
    """Build and render a PINS HTML report."""

    TEMPLATE_MAP = {
        "heading1": "blocks/heading1.html",
        "heading2": "blocks/heading2.html",
        "paragraph": "blocks/paragraph.html",
        "table": "blocks/table.html",
        "figure": "blocks/figure.html",
        "table_of_contents": "blocks/table_of_contents.html",
        "appendix": "blocks/appendix.html",
    }

    def __init__(self, title: str = "PINS report", *,subtitle: str = "") -> None:
        self.title = title
        self.subtitle = subtitle
        self.blocks: list[Block] = []

        self.environment = Environment(
            loader=FileSystemLoader(
                Path(__file__).parent / "templates"
            ),
            autoescape=select_autoescape(
                enabled_extensions=("html", "xml"),
                default_for_string=True,
            ),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def table_of_contents(self) -> "Report":
        self.blocks.append(
            Block(
                type="table_of_contents",
                data={},
            )
        )
        return self

    def appendix(self) -> "Report":
        self.blocks.append(
            Block(
                type="appendix",
                data={},
            )
        )
        return self

    def heading1(self, text: str) -> "Report":
        self.blocks.append(
            Block(
                type="heading1",
                data={"text": str(text)},
            )
        )
        return self

    def heading2(self, text: str) -> "Report":
        self.blocks.append(
            Block(
                type="heading2",
                data={"text": str(text)},
            )
        )
        return self

    def p(self, text: str) -> "Report":
        self.blocks.append(
            Block(
                type="paragraph",
                data={"text": str(text)},
            )
        )
        return self

    def table(
        self,
        dataframe: pd.DataFrame,
        *,
        caption: str = "",
        index: bool = False,
        na_rep: str = "",
        float_format: str | None = None,
    ) -> "Report":
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError(
                "table() expects a pandas DataFrame."
            )

        table_html = dataframe.to_html(
            index=index,
            na_rep=na_rep,
            border=0,
            classes=["report-table"],
            justify="left",
            escape=True,
            float_format=float_format,
        )

        self.blocks.append(
            Block(
                type="table",
                data={
                    "table_html": Markup(table_html),
                    "caption": str(caption),
                },
            )
        )
        return self

    def figure(
        self,
        figure_or_path: Any,
        *,
        caption: str = "",
        alt_text: str = "",
        image_format: str = "png",
        dpi: int = 150,
    ) -> "Report":
        source = self._prepare_figure_source(
            figure_or_path=figure_or_path,
            image_format=image_format,
            dpi=dpi,
        )

        self.blocks.append(
            Block(
                type="figure",
                data={
                    "source": source,
                    "caption": str(caption),
                    "alt_text": str(alt_text),
                },
            )
        )
        return self

    def render(self, output_path: str | Path) -> Path:
        output_path = Path(output_path)

        if output_path.suffix.lower() != ".html":
            raise ValueError(
                "The output path must use the .html extension."
            )

        prepared_blocks, toc_entries, appendix_entries = self._prepare_blocks()

        rendered_blocks = [
            self._render_block(
                block=block,
                toc_entries=toc_entries,
                appendix_entries=appendix_entries,
            )
            for block in prepared_blocks
        ]

        stylesheet = self._load_stylesheet()
        logo_data_uri = self._load_logo()

        page_template = self.environment.get_template(
            "report.html"
        )

        final_html = page_template.render(
            title=self.title,
            subtitle=self.subtitle,
            stylesheet=Markup(stylesheet),
            logo_data_uri=logo_data_uri,
            rendered_blocks=rendered_blocks,
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            final_html,
            encoding="utf-8",
        )

        return output_path

    def _prepare_blocks(
        self,
    ) -> tuple[list[Block], list[TableOfContentsEntry], list[AppendixEntry]]:
        anchor_generator = AnchorGenerator()

        prepared_blocks: list[Block] = []
        toc_entries: list[TableOfContentsEntry] = []
        appendix_entries: list[AppendixEntry] = []
        appendix_blocks: list[Block] = []
        item_numbers = {"table": 0, "figure": 0}
        section_number = 0
        subsection_number = 0

        for block in self.blocks:
            prepared_data = dict(block.data)

            if block.type in {"heading1", "heading2"}:
                anchor = anchor_generator.create(
                    prepared_data["text"]
                )

                prepared_data["anchor"] = anchor

                level = {
                    "heading1": 1,
                    "heading2": 2,
                }[block.type]

                if level == 1:
                    section_number += 1
                    subsection_number = 0
                    number = f"{section_number}."
                else:
                    subsection_number += 1
                    number = (
                        f"{section_number}.{subsection_number}"
                    )

                toc_entries.append(
                    TableOfContentsEntry(
                        text=prepared_data["text"],
                        anchor=anchor,
                        level=level,
                        number=number,
                    )
                )

            elif block.type in item_numbers:
                item_numbers[block.type] += 1
                number = item_numbers[block.type]
                label = f"{block.type.title()} {number}"
                if block.type == "table":
                    label += "."
                anchor = anchor_generator.create(f"{block.type}-{number}")
                prepared_data["anchor"] = anchor
                prepared_data["label"] = label
                if prepared_data.get("caption"):
                    appendix_entries.append(
                        AppendixEntry(
                            caption=prepared_data["caption"],
                            anchor=anchor,
                            label=label,
                        )
                    )

            elif block.type == "appendix":
                prepared_data["anchor"] = anchor_generator.create("appendix")
                appendix_blocks.append(
                    Block(type=block.type, data=prepared_data)
                )
                continue

            prepared_blocks.append(
                Block(
                    type=block.type,
                    data=prepared_data,
                )
            )

        prepared_blocks.extend(appendix_blocks)
        return prepared_blocks, toc_entries, appendix_entries

    def _render_block(
        self,
        block: Block,
        toc_entries: list[TableOfContentsEntry],
        appendix_entries: list[AppendixEntry],
    ) -> Markup:
        try:
            template_name = self.TEMPLATE_MAP[block.type]
        except KeyError as error:
            raise ValueError(
                f"Unsupported block type: {block.type}"
            ) from error

        template = self.environment.get_template(
            template_name
        )

        template_context = {
            **block.data,
            "entries": toc_entries,
            "appendix_entries": appendix_entries,
        }

        rendered_html = template.render(
            **template_context
        )

        return Markup(rendered_html)

    @staticmethod
    def _prepare_figure_source(
        figure_or_path: Any,
        image_format: str,
        dpi: int,
    ) -> str:
        if isinstance(figure_or_path, (str, Path)):
            return Path(figure_or_path).as_posix()

        if hasattr(figure_or_path, "savefig"):
            image_buffer = BytesIO()

            figure_or_path.savefig(
                image_buffer,
                format=image_format,
                dpi=dpi,
                bbox_inches="tight",
            )

            image_buffer.seek(0)

            encoded_image = base64.b64encode(
                image_buffer.read()
            ).decode("ascii")

            return (
                f"data:image/{image_format};"
                f"base64,{encoded_image}"
            )

        raise TypeError(
            "figure() expects a file path or a Matplotlib Figure."
        )

    @staticmethod
    def _load_stylesheet() -> str:
        package_directory = Path(__file__).parent
        stylesheet_path = (
            package_directory
            / "static"
            / "report.css"
        )

        return stylesheet_path.read_text(
            encoding="utf-8"
        )

    @staticmethod
    def _load_logo() -> str:
        logo_path = (
            Path(__file__).parent
            / "Planning-Inspectorate-logo-stacked.png"
        )
        encoded_logo = base64.b64encode(
            logo_path.read_bytes()
        ).decode("ascii")
        return f"data:image/png;base64,{encoded_logo}"

class AnchorGenerator:
    """Generate unique, readable fragment identifiers for report headings."""

    def __init__(self) -> None:
        self.used_anchors: set[str] = set()

    def create(self, text: str) -> str:
        normalized_text = unicodedata.normalize(
            "NFKC",
            text,
        ).casefold()
        anchor = re.sub(
            r"[\W_]+",
            "-",
            normalized_text,
            flags=re.UNICODE,
        ).strip("-") or "section"

        unique_anchor = anchor
        suffix = 2
        while unique_anchor in self.used_anchors:
            unique_anchor = f"{anchor}-{suffix}"
            suffix += 1

        self.used_anchors.add(unique_anchor)
        return unique_anchor