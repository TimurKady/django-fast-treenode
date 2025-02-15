# -*- coding: utf-8 -*-
"""
TreeNode Exporter Module

This module provides functionality for exporting tree-structured data
to various formats, including CSV, JSON, XLSX, YAML, and TSV.

Features:
- Supports exporting ForeignKey fields as IDs and ManyToMany fields as JSON
  lists.
- Handles complex field types (lists, dictionaries) with proper serialization.
- Provides optimized data extraction for QuerySets.
- Generates downloadable files with appropriate HTTP responses.

Version: 2.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


import csv
import json
import yaml
import pandas as pd
from io import BytesIO
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)


class TreeNodeExporter:
    """Exporter for tree-structured data to various formats."""

    def __init__(self, queryset, filename="tree_nodes"):
        """
        Init.

        :param queryset: QuerySet of objects to export.
        :param filename: Filename without extension.
        """
        self.queryset = queryset
        self.filename = filename
        self.fields = [field.name for field in queryset.model._meta.fields]

    def export(self, format):
        """Determine the export format and calls the corresponding method."""
        exporters = {
            "csv": self.to_csv,
            "json": self.to_json,
            "xlsx": self.to_xlsx,
            "yaml": self.to_yaml,
            "tsv": self.to_tsv,
        }
        if format not in exporters:
            raise ValueError("Unsupported export format")
        return exporters[format]()

    def process_complex_fields(self, record):
        """Convert complex fields (lists, dictionaries) into JSON strings."""
        for key, value in record.items():
            if isinstance(value, (list, dict)):
                try:
                    record[key] = json.dumps(value, ensure_ascii=False)
                except Exception as e:
                    logger.warning("Error serializing field %s: %s", key, e)
                    record[key] = None
        return record

    def get_data(self):
        """Return a list of data from QuerySet as dictionaries."""
        data = []
        for obj in self.queryset:
            record = {}
            for field in self.fields:
                value = getattr(obj, field, None)
                field_object = obj._meta.get_field(field)
                if field_object.is_relation:
                    if field_object.many_to_many:
                        # ManyToMany - save as a JSON string
                        record[field] = json.dumps(
                            list(value.values_list('id', flat=True)),
                            ensure_ascii=False)
                    elif field_object.many_to_one:
                        # ForeignKey - save as ID
                        record[field] = value.id if value else None
                    else:
                        record[field] = value
                else:
                    record[field] = value
            record = self.process_complex_fields(record)
            data.append(record)
        return data

    def to_csv(self):
        """Export to CSV with proper attachment handling."""
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{self.filename}.csv"'
        writer = csv.DictWriter(response, fieldnames=self.fields)
        writer.writeheader()
        writer.writerows(self.get_data())
        return response

    def to_json(self):
        """Export to JSON with UUID serialization handling."""
        response = HttpResponse(content_type="application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename="{self.filename}.json"'
        json.dump(self.get_data(), response,
                  ensure_ascii=False, indent=4, default=str)
        return response

    def to_xlsx(self):
        """Export to XLSX."""
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="{self.filename}.xlsx"'
        df = pd.DataFrame(self.get_data())
        with BytesIO() as buffer:
            writer = pd.ExcelWriter(buffer, engine="xlsxwriter")
            df.to_excel(writer, index=False)
            writer.close()
            response.write(buffer.getvalue())
        return response

    def to_yaml(self):
        """Export to YAML with proper attachment handling."""
        response = HttpResponse(content_type="application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename="{self.filename}.yaml"'
        yaml_str = yaml.dump(self.get_data(), allow_unicode=True)
        response.write(yaml_str)
        return response

    def to_tsv(self):
        """Export to TSV with proper attachment handling."""
        response = HttpResponse(content_type="application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename="{self.filename}.tsv"'
        writer = csv.DictWriter(
            response, fieldnames=self.fields, delimiter="	")
        writer.writeheader()
        writer.writerows(self.get_data())
        return response
