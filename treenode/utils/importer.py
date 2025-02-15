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
import math
import pandas as pd
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
        """Возвращает содержимое файла в виде строки."""
        if isinstance(self.file_content, bytes):
            return self.file_content.decode("utf-8")
        return self.file_content

    def import_data(self):
        """Импортирует данные и возвращает список словарей."""
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
        # Обработка: фильтрация полей, упаковка сложных значений и приведение типов
        processed_data = self.process_records(raw_data)
        return processed_data

    def from_csv(self):
        """Импорт из CSV."""
        text = self.get_text_content()
        return list(csv.DictReader(StringIO(text)))

    def from_json(self):
        """Импорт из JSON."""
        return json.loads(self.get_text_content())

    def from_xlsx(self):
        """Импорт из XLSX (Excel)."""
        df = pd.read_excel(BytesIO(self.file_content))
        return df.to_dict(orient="records")

    def from_yaml(self):
        """Импорт из YAML."""
        return yaml.safe_load(self.get_text_content())

    def from_tsv(self):
        """Импорт из TSV."""
        text = self.get_text_content()
        return list(csv.DictReader(StringIO(text), delimiter="\t"))

    def filter_fields(self, record):
        """
        Фильтрует запись согласно маппингу.
        Остаются только нужные ключи, при этом имена переименовываются.
        """
        new_record = {}
        for file_key, model_field in self.mapping.items():
            new_record[model_field] = record.get(file_key)
        return new_record

    def process_complex_fields(self, record):
        """
        Если значение поля — словарь или список, упаковывает его в JSON-строку.
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
        Приводит значения полей записи к типам, определённым в модели.

        Для каждого поля вызывается его метод to_python(). Если значение равно nan,
        оно заменяется на None.

        Для ForeignKey-полей (many-to-one) значение записывается в атрибут <field>_id,
        а исходный ключ удаляется.
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
        Обрабатывает список записей:
          1. Фильтрует поля по маппингу.
          2. Упаковывает сложные (вложенные) данные в JSON.
          3. Приводит значения каждого поля к типам, определённым в модели.
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
        Валидирует и подготавливает данные для массового сохранения объектов.

        Для каждой записи:
         - Проверяется наличие уникального поля 'id'.
         - Значение родительской связи (tn_parent или tn_parent_id) сохраняется отдельно и удаляется из данных.
         - Приводит данные к типам модели.
         - Пытается создать экземпляр модели с валидацией через full_clean().

        Возвращает словарь со следующими ключами:
          'create'         - список объектов для создания,
          'update'         - список объектов для обновления (в данном случае оставим пустым),
          'update_fields'  - список полей, подлежащих обновлению (например, ['tn_parent']),
          'fk_mappings'    - словарь {id_объекта: значение родительского ключа из исходных данных},
          'errors'         - список ошибок валидации.
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

            # Сохраняем значение родительской связи и удаляем его из данных
            fk_value = None
            if 'tn_parent' in data:
                fk_value = data['tn_parent']
                del data['tn_parent']
            elif 'tn_parent_id' in data:
                fk_value = data['tn_parent_id']
                del data['tn_parent_id']

            # Приводим значения к типам модели
            data = self.cast_record_types(data)

            try:
                instance = self.model(**data)
                instance.full_clean()
                result["create"].append(instance)
                # Сохраняем значение родительского ключа для последующего обновления
                result["fk_mappings"][instance.id] = fk_value
            except Exception as e:
                error_message = f"Validation error creating {data}: {e}"
                result["errors"].append(error_message)
                logger.warning(error_message)
                continue

        # В данном сценарии обновление происходит только для родительской связи
        result["update_fields"] = ['tn_parent']
        return result

    def save_data(self, create, update, fields):
        """
        Сохраняет объекты в базу в рамках атомарной транзакции.
        :param create: список объектов для создания.
        :param update: список объектов для обновления.
        :param fields: список полей, которые обновляются (для bulk_update).
        """
        with transaction.atomic():
            if update:
                self.model.objects.bulk_update(update, fields, batch_size=1000)
            if create:
                self.model.objects.bulk_create(create, batch_size=1000)

    def update_parent_relations(self, fk_mappings):
        """
        Обновляет поле tn_parent для объектов, используя сохранённые fk_mappings.
        :param fk_mappings: словарь {id_объекта: значение родительского ключа из исходных данных}
        """
        instances_to_update = []
        for obj_id, parent_id in fk_mappings.items():
            # Если родитель не указан, пропускаем
            if not parent_id:
                continue
            try:
                instance = self.model.objects.get(pk=obj_id)
                parent_instance = self.model.objects.get(pk=parent_id)
                instance.tn_parent = parent_instance
                instances_to_update.append(instance)
            except self.model.DoesNotExist:
                logger.warning(
                    "Parent with id %s not found for instance %s", parent_id, obj_id)
        if instances_to_update:
            update_fields = ['tn_parent']
            self.model.objects.bulk_update(
                instances_to_update, update_fields, batch_size=1000)

    # Если захочешь объединить операции сохранения и обновления родителей,
    # можно добавить метод, который вызовет save_data и update_parent_relations последовательно.
    def finalize_import(self, clean_result):
        """
        Финализирует импорт: сохраняет новые объекты и обновляет родительские связи.
        :param clean_result: словарь, возвращённый методом clean.
        """
        # Если есть ошибки – можно прервать импорт или вернуть их для обработки
        if clean_result["errors"]:
            return clean_result["errors"]

        # Сначала выполняем массовое создание
        self.save_data(
            clean_result["create"], clean_result["update"], clean_result["update_fields"])
        # Затем обновляем родительские связи
        self.update_parent_relations(clean_result["fk_mappings"])
        return None  # Или вернуть успешное сообщение

# The End
