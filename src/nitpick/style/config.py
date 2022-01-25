"""Config validator."""
from dataclasses import dataclass
from typing import Dict, List, Tuple, Type

from marshmallow import Schema
from more_itertools import peekable

from nitpick.constants import PROJECT_NAME
from nitpick.exceptions import Deprecation
from nitpick.plugins.info import FileInfo
from nitpick.project import Project
from nitpick.schemas import BaseStyleSchema, NitpickSectionSchema
from nitpick.typedefs import JsonDict


@dataclass(repr=True)  # TODO: refactor: use attrs instead
class ConfigValidator:
    """Validate a nitpick configuration."""

    project: Project

    def validate(self, config_dict: Dict) -> Tuple[Dict, Dict]:
        """Validate an already parsed toml file."""
        validation_errors = {}
        toml_dict = {}
        for key, value_dict in config_dict.items():
            info = FileInfo.create(self.project, key)
            toml_dict[info.path_from_root] = value_dict
            validation_errors.update(self._validate_item(key, info, value_dict))
        return toml_dict, validation_errors

    def _validate_item(self, key, info, value_dict):
        validation_errors = {}
        if key == PROJECT_NAME:
            schemas = [NitpickSectionSchema]
        else:
            schemas = peekable(self._get_validation_schemas_for_file(info))
            if not schemas:
                validation_errors[key] = [BaseStyleSchema.error_messages["unknown"]]
        valid_schema, all_errors = self._validate_schemas(info, schemas, value_dict)
        if not valid_schema:
            Deprecation.jsonfile_section(all_errors)
            validation_errors.update(all_errors)

        return validation_errors

    def _get_validation_schemas_for_file(self, info):
        for plugin_class in self.project.plugin_manager.hook.can_handle(info=info):  # pylint: disable=no-member
            yield plugin_class.validation_schema

    def _validate_schemas(self, info, schemas, value_dict):
        all_errors = {}
        for schema in schemas:
            errors = self._validate_schema(schema, info.path_from_root, value_dict)
            if not errors:
                # When multiple schemas match a file type, exit when a valid schema is found
                return True, {}

            all_errors.update(errors)

        return False, all_errors

    @staticmethod
    def _validate_schema(schema: Type[Schema], path_from_root: str, original_data: JsonDict) -> Dict[str, List[str]]:
        """Validate the schema for the file."""
        if not schema:
            return {}

        inherited_schema = schema is not BaseStyleSchema
        data_to_validate = original_data if inherited_schema else {path_from_root: None}
        local_errors = schema().validate(data_to_validate)
        if local_errors and inherited_schema:
            local_errors = {path_from_root: local_errors}
        return local_errors
