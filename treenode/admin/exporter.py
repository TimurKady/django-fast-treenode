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
from asgiref.sync import sync_to_async
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

    def _get_sync_iterator_item(self, iterator):
        """Return next item from a sync iterator or None when exhausted."""
        return next(iterator, None)

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

    async def async_csv_stream_data(self, delimiter=","):
        """Stream CSV or TSV data asynchronously."""
        yield "\ufeff"
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

        iterator = self.get_obj()
        while True:
            obj = await sync_to_async(
                self._get_sync_iterator_item,
                thread_sensitive=True,
            )(iterator)
            if obj is None:
                break

            row = await sync_to_async(
                self.get_serializable_row,
                thread_sensitive=True,
            )(obj)
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

    async def async_json_stream_data(self):
        """Stream JSON data asynchronously."""
        yield "[\n"
        first = True
        iterator = self.get_obj()

        while True:
            obj = await sync_to_async(
                self._get_sync_iterator_item,
                thread_sensitive=True,
            )(iterator)
            if obj is None:
                break

            row = await sync_to_async(
                self.get_serializable_row,
                thread_sensitive=True,
            )(obj)
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

    async def async_yaml_stream_data(self):
        """Stream YAML data asynchronously."""
        yield "---\n"
        iterator = self.get_obj()

        while True:
            obj = await sync_to_async(
                self._get_sync_iterator_item,
                thread_sensitive=True,
            )(iterator)
            if obj is None:
                break

            row = await sync_to_async(
                self.get_serializable_row,
                thread_sensitive=True,
            )(obj)
            yield yaml.safe_dump([row], allow_unicode=True)

    def _build_xlsx_payload(self):
        """Build XLSX bytes synchronously in a thread-safe block."""
        wb = Workbook()
        ws = wb.active
        ws.append(self.fields)

        for obj in self.get_obj():
            row = self.get_serializable_row(obj)
            ws.append([row.get(f, "") for f in self.fields])

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    def xlsx_stream_data(self):
        """Stream XLSX data."""
        yield self._build_xlsx_payload()

    async def async_xlsx_stream_data(self):
        """Stream XLSX data asynchronously."""
        payload = await sync_to_async(
            self._build_xlsx_payload,
            thread_sensitive=True,
        )()
        yield payload

    def _resolve_stream_data(self, is_async=False):
        """Resolve stream iterator for sync or async request handler."""
        if self.format == 'xlsx':
            stream = (
                self.async_xlsx_stream_data()
                if is_async else self.xlsx_stream_data()
            )
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-8"  # noqa: D501
        elif self.format == 'tsv':
            stream = (
                self.async_csv_stream_data(delimiter="\t")
                if is_async else self.csv_stream_data(delimiter="\t")
            )
            content_type = "text/tab-separated-values; charset=utf-8"
        elif self.format == 'csv':
            stream = (
                self.async_csv_stream_data(delimiter=",")
                if is_async else self.csv_stream_data(delimiter=",")
            )
            content_type = "text/csv; charset=utf-8"
        elif self.format == 'yaml':
            stream = (
                self.async_yaml_stream_data()
                if is_async else self.yaml_stream_data()
            )
            content_type = f"application/{self.format}; charset=utf-8"
        else:
            stream = (
                self.async_json_stream_data()
                if is_async else self.json_stream_data()
            )
            content_type = f"application/{self.format}; charset=utf-8"

        return stream, content_type

    def process_record(self, request=None):
        """
        Create a StreamingHttpResponse based on selected format.

        :param chunk_size: Batch size for iteration.
        :return: StreamingHttpResponse object.
        """
        is_async = bool(request and hasattr(request, "scope"))
        stream_data, content_type = self._resolve_stream_data(is_async=is_async)
        response = StreamingHttpResponse(
            streaming_content=stream_data,
            content_type=content_type,
        )

        response['Content-Disposition'] = f'attachment; filename="{self.filename}"'  # noqa: D501
        return response


# The End
