# -*- coding: utf-8 -*-
"""
TreeNode Importer Module

This module provides functionality for importing tree-structured data
from various formats, including CSV, JSON, XLSX, YAML, and TSV.

Features:
- Supports field mapping and data type conversion for model compatibility.
- Handles ForeignKey relationships and ManyToMany fields.
- Validates and processes raw data before saving to the database.
- Uses bulk operations for efficient data insertion and updates.
- Supports transactional imports to maintain data integrity.

Version: 2.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


import csv
import json
import yaml
import openpyxl
import math
from io import BytesIO, StringIO
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class TreeNodeImporter:
    """Импортер древовидных данных из различных форматов."""

    def __init__(self, model, file, format, fields=None, mapping=None):
        """
        Init method.

        :param model: Django model where the data will be imported.
        :param file: File object.
        :param format: File format ('csv', 'json', 'xlsx', 'yaml', 'tsv').
        :param fields: List of model fields to import.
        :param mapping: Dictionary for mapping keys from file to model
        field names.
        For example: {"Name": "title", "Description": "desc"}
        """
        self.model = model
        self.format = format
        # Если поля не заданы, используем все поля модели
        self.fields = fields or [field.name for field in model._meta.fields]
        # По умолчанию маппинг идентичен: ключи совпадают с именами полей
        self.mapping = mapping or {field: field for field in self.fields}
        # Считываем содержимое файла один раз, чтобы избежать проблем с курсором
        self.file_content = file.read()

    def get_text_content(self):
        """Return the contents of a file as a string."""
        if isinstance(self.file_content, bytes):
            return self.file_content.decode("utf-8")
        return self.file_content

    def import_data(self):
        """Import data and returns a list of dictionaries."""
        importers = {
            "csv": self.from_csv,
            "json": self.from_json,
            "xlsx": self.from_xlsx,
            "yaml": self.from_yaml,
            "tsv": self.from_tsv,
        }
        if self.format not in importers:
            raise ValueError("Unsupported import format")

        raw_data = importers[self.format]()
        # Processing: field filtering, complex value packing and type casting
        processed_data = self.process_records(raw_data)
        return processed_data

    def from_csv(self):
        """Import from CSV."""
        text = self.get_text_content()
        return list(csv.DictReader(StringIO(text)))

    def from_json(self):
        """Import from JSON."""
        return json.loads(self.get_text_content())

    def from_xlsx(self):
        """Import from XLSX (Excel)."""
        file_stream = BytesIO(self.file_content)
        rows = []
        wb = openpyxl.load_workbook(file_stream, read_only=True)
        ws = wb.active
        headers = [
            cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))
        ]
        for row in ws.iter_rows(min_row=2, values_only=True):
            rows.append(dict(zip(headers, row)))
        return rows

    def from_yaml(self):
        """Import from YAML."""
        return yaml.safe_load(self.get_text_content())

    def from_tsv(self):
        """Import from TSV."""
        text = self.get_text_content()
        return list(csv.DictReader(StringIO(text), delimiter="\t"))

    def filter_fields(self, record):
        """
        Filter the record according to the mapping.

        Only the necessary keys remain, while the names are renamed.
        """
        new_record = {}
        for file_key, model_field in self.mapping.items():
            new_record[model_field] = record.get(file_key)
        return new_record

    def process_complex_fields(self, record):
        """
        Pack it into a JSON string.

        If the field value is a dictionary or list.
        """
        for key, value in record.items():
            if isinstance(value, (list, dict)):
                try:
                    record[key] = json.dumps(value, ensure_ascii=False)
                except Exception as e:
                    logger.warning("Error serializing field %s: %s", key, e)
                    record[key] = None
        return record

    def cast_record_types(self, record):
        """
        Casts the values ​​of the record fields to the types defined in the model.

        For each field, its to_python() method is called. If the value is nan,
        it is replaced with None.
        For ForeignKey fields (many-to-one), the value is written to 
        the <field>_id attribute, and the original key is removed.
        """
        for field in self.model._meta.fields:
            field_name = field.name
            if field.is_relation and field.many_to_one:
                if field_name in record:
                    value = record[field_name]
                    if isinstance(value, float) and math.isnan(value):
                        value = None
                    try:
                        converted = None if value is None else int(value)
                        # Записываем в атрибут, например, tn_parent_id
                        record[field.attname] = converted
                    except Exception as e:
                        logger.warning("Error converting FK field %s with value %r: %s",
                                       field_name, value, e)
                        record[field.attname] = None
                    # Удаляем оригинальное значение, чтобы Django не пыталась его обработать
                    del record[field_name]
            else:
                if field_name in record:
                    value = record[field_name]
                    if isinstance(value, float) and math.isnan(value):
                        record[field_name] = None
                    else:
                        try:
                            record[field_name] = field.to_python(value)
                        except Exception as e:
                            logger.warning("Error converting field %s with value %r: %s",
                                           field_name, value, e)
                            record[field_name] = None
        return record

    def process_records(self, records):
        """
        Process a list of records.

        1. Filters fields by mapping.
        2. Packs complex (nested) data into JSON.
        3. Converts the values ​​of each field to the types defined in the model.
        """
        processed = []
        for record in records:
            filtered = self.filter_fields(record)
            filtered = self.process_complex_fields(filtered)
            filtered = self.cast_record_types(filtered)
            processed.append(filtered)
        return processed

    def clean(self, raw_data):
        """
        Validat and prepare data for bulk saving of objects.

        For each record:
        - The presence of a unique field 'id' is checked.
        - The value of the parent relationship (tn_parent or tn_parent_id)
          is saved separately and removed from the data.
        - Casts the data to model types.
        - Attempts to create a model instance with validation via full_clean().

        Returns a dictionary with the following keys:
        'create' - a list of objects to create,
        'update' - a list of objects to update (in this case, we leave 
        it empty),
        'update_fields' - a list of fields to update (for example, 
        ['tn_parent']),
        'fk_mappings' - a dictionary of {object_id: parent key value from 
        the source data},
        'errors' - a list of validation errors.
        """
        result = {
            "create": [],
            "update": [],
            "update_fields": [],
            "fk_mappings": {},
            "errors": []
        }

        for data in raw_data:
            if 'id' not in data:
                error_message = f"Missing unique field 'id' in record: {data}"
                result["errors"].append(error_message)
                logger.warning(error_message)
                continue

            # Save the parent relationship value and remove it from the data
            fk_value = None
            if 'tn_parent' in data:
                fk_value = data['tn_parent']
                del data['tn_parent']
            elif 'tn_parent_id' in data:
                fk_value = data['tn_parent_id']
                del data['tn_parent_id']

            # Convert values ​​to model types
            data = self.cast_record_types(data)

            try:
                instance = self.model(**data)
                instance.full_clean()
                result["create"].append(instance)
                # Save the parent key value for future update
                result["fk_mappings"][instance.id] = fk_value
            except Exception as e:
                error_message = f"Validation error creating {data}: {e}"
                result["errors"].append(error_message)
                logger.warning(error_message)
                continue

        # In this scenario, the update occurs only for the parent relationship
        result["update_fields"] = ['tn_parent']
        return result

    def save_data(self, create, update, fields):
        """
        Save objects to the database as part of an atomic transaction.

        :param create: list of objects to create.
        :param update: list of objects to update.
        :param fields: list of fields to update (for bulk_update).
        """
        with transaction.atomic():
            if update:
                self.model.objects.bulk_update(update, fields, batch_size=1000)
            if create:
                self.model.objects.bulk_create(create, batch_size=1000)

    def update_parent_relations(self, fk_mappings):
        """
        Update the tn_parent field for objects using the saved fk_mappings.

        :param fk_mappings: dictionary {object_id: parent key value from 
        the source data}
        """
        instances_to_update = []
        for obj_id, parent_id in fk_mappings.items():
            # If parent is not specified, skip
            if not parent_id:
                continue
            try:
                instance = self.model.objects.get(pk=obj_id)
                parent_instance = self.model.objects.get(pk=parent_id)
                instance.tn_parent = parent_instance
                instances_to_update.append(instance)
            except self.model.DoesNotExist:
                logger.warning(
                    "Parent with id %s not found for instance %s",
                    parent_id,
                    obj_id
                )
        if instances_to_update:
            update_fields = ['tn_parent']
            self.model.objects.bulk_update(
                instances_to_update, update_fields, batch_size=1000)

        # If you want to combine the save and update parent operations,
        # you can add a method that calls save_data and update_parent_relations
        # sequentially.

    def finalize_import(self, clean_result):
        """
        Finalize the import: saves new objects and updates parent links.

        :param clean_result: dictionary returned by the clean method.
        """
        # If there are errors, you can interrupt the import or return them
        # for processing
        if clean_result["errors"]:
            return clean_result["errors"]

        # First we do a bulk creation
        self.save_data(
            clean_result["create"], clean_result["update"], clean_result["update_fields"])
        # Then we update the parent links
        self.update_parent_relations(clean_result["fk_mappings"])
        return None  # Or return a success message

# The End
