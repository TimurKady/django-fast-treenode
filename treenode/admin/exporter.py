# -*- coding: utf-8 -*-
"""
TreeNode Exporter Module

This module provides functionality for stream exporting tree-structured data
to various formats, including CSV, JSON, TSV, XLSX, YAML.

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

import csv
import json
import yaml
from django.core.serializers.json import DjangoJSONEncoder
from django.http import StreamingHttpResponse
from io import BytesIO, StringIO
from openpyxl import Workbook


class TreeNodeExporter:
    """Exporter for tree-structured data to various formats."""

    def __init__(self, model, filename="tree_nodes", fileformat="csv"):
        """
        Initialize exporter.

        :param queryset: Django QuerySet to export.
        :param filename: Base name for the output file.
        :param fileformat: Export format (csv, json, xlsx, yaml, tvs).
        """
        self.filename = filename
        self.format = fileformat
        self.model = model
        self.queryset = model.objects.get_queryset()
        self.fields = self.get_ordered_fields()

    def get_ordered_fields(self):
        """
        Define and return the ordered list of fields for export.

        Required fields come first, blocked fields are omitted.
        """
        fields = sorted([field.name for field in self.model._meta.fields])
        required_fields = ["id", "parent", "priority"]
        blocked_fields = ["_path", "_depth"]

        other_fields = [
            field for field in fields
            if field not in required_fields and field not in blocked_fields
        ]
        return required_fields + other_fields

    def get_obj(self):
        """Yield rows from queryset as row data dict."""
        queryset = self.queryset.order_by('_path').only(*self.fields)
        for obj in queryset.iterator():
            yield obj

    def get_serializable_row(self, obj):
        """Get serialized object."""
        fields = self.fields
        raw_data = {}
        for field in fields:
            if field == "parent":
                raw_data["parent"] = getattr(obj, "parent_id", None)
            else:
                raw_data[field] = getattr(obj, field, None)
        serialized = json.loads(json.dumps(raw_data, cls=DjangoJSONEncoder))
        return serialized

    def csv_stream_data(self, delimiter=","):
        """Stream CSV or TSV data."""
        yield "\ufeff"  # BOM for Excel
        buffer = StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=self.fields,
            delimiter=delimiter
        )
        writer.writeheader()
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        for obj in self.get_obj():
            row = self.get_serializable_row(obj)
            writer.writerow(row)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    def json_stream_data(self):
        """Stream JSON data."""
        yield "[\n"
        first = True
        for obj in self.get_obj():
            row = self.get_serializable_row(obj)
            if not first:
                yield ",\n"
            else:
                first = False
            yield json.dumps(row, ensure_ascii=False)
        yield "\n]"

    def tsv_stream_data(self, chunk_size=1000):
        """Stream TSV (tab-separated values) data."""
        yield from self.csv_stream_data(delimiter="\t")

    def yaml_stream_data(self):
        """Stream YAML data."""
        yield "---\n"
        for obj in self.get_obj():
            row = self.get_serializable_row(obj)
            yield yaml.safe_dump([row], allow_unicode=True)

    def xlsx_stream_data(self):
        """Stream XLSX data."""
        wb = Workbook()
        ws = wb.active
        ws.append(self.fields)

        for obj in self.get_obj():
            row = self.get_serializable_row(obj)
            ws.append([row.get(f, "") for f in self.fields])

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        yield output.getvalue()

    def process_record(self):
        """
        Create a StreamingHttpResponse based on selected format.

        :param chunk_size: Batch size for iteration.
        :return: StreamingHttpResponse object.
        """
        if self.format == 'xlsx':
            response = StreamingHttpResponse(
                streaming_content=self.xlsx_stream_data(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-8"  # noqa: D501
            )
        elif self.format == 'tsv':
            response = StreamingHttpResponse(
                streaming_content=self.csv_stream_data(delimiter="\t"),
                content_type="text/tab-separated-values; charset=utf-8"
            )
        elif self.format == 'csv':
            response = StreamingHttpResponse(
                streaming_content=self.csv_stream_data(delimiter=","),
                content_type="text/csv; charset=utf-8"
            )
        elif self.format == 'yaml':
            response = StreamingHttpResponse(
                streaming_content=self.yaml_stream_data(),
                content_type=f"application/{self.format}; charset=utf-8"
            )
        else:
            response = StreamingHttpResponse(
                streaming_content=self.json_stream_data(),
                content_type=f"application/{self.format}; charset=utf-8"
            )

        response['Content-Disposition'] = f'attachment; filename="{self.filename}"'  # noqa: D501
        return response


# The End
