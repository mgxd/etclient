"""
Create queries and mutations to be sent to the graphql endpoint.
"""
from __future__ import annotations

import dataclasses
import enum
import json
import typing as ty
import warnings

from migas.config import Config, logger, telemetry_enabled
from migas.request import request

class TextType(enum.Enum):
    LITERAL = 1
    FREE = 2

ERROR = '[migas-py] An error occurred.'


@dataclasses.dataclass
class Operation:
    operation_type: str
    operation_name: str
    query_args: dict
    selections: tuple | None = None  # TODO: Add subfield selection support
    query: str = ''
    fingerprint: bool = False
    error_response: dict | None = None

    @classmethod
    def generate_query(cls, *args, **kwargs) -> str:
        parameters = _introspec(cls.generate_query, locals())
        params = Config.populate() if cls.fingerprint else {}
        params = {**params, **kwargs, **parameters}
        query = cls._construct_query(params)
        return query

    @classmethod
    def _construct_query(cls, params: dict) -> str:
        """Construct the graphql query."""
        query = _parse_format_params(params, cls.query_args)
        cls.query = f'{cls.operation_type}{{{cls.operation_name}({query})'
        if cls.selections:
            cls.query += f'{{{",".join(f for f in cls.selections)}}}'
        cls.query += '}'
        return cls.query


class AddBreadcrumb(Operation):
    operation_type = "mutation"
    operation_name = "add_breadcrumb"
    query_args = {
        "project": TextType.FREE,
        "project_version": TextType.FREE,
        "language": TextType.FREE,
        "language_version": TextType.FREE,
        "ctx": {
            "session_id": TextType.FREE,
            "user_id": TextType.FREE,
            "user_type": TextType.LITERAL,
            "platform": TextType.FREE,
            "container": TextType.LITERAL,
            "is_ci": TextType.LITERAL,
        },
        "proc": {
            "status": TextType.LITERAL,
            "status_desc": TextType.FREE,
            "error_type": TextType.FREE,
            "error_desc": TextType.FREE,
        },
    }
    fingerprint = True
    selections = ('success',)


@telemetry_enabled
def add_breadcrumb(project: str, project_version: str, **kwargs) -> dict:
    """
    Send a breadcrumb with usage information to the telemetry server.

    - `project` - application name
    - `project_version` - application version

    Optional keyword arguments
    - `language` (auto-detected)
    - `language_version` (auto-detected)
    - process-specific
        - `status`
        - `status_desc`
        - `error_type`
        - `error_desc`
    - context-specific
        - `user_id` (auto-generated)
        - `session_id`
        - `user_type`
        - `platform` (auto-detected)
        - `container` (auto-detected)
        - `is_ci` (auto-detected)

    Returns
    -------
    response: dict
        keys: success
    """
    query = AddBreadcrumb.generate_query(
        project=project, project_version=project_version, **kwargs
    )
    logger.debug(query)
    _, response = request(Config.endpoint, query=query)
    res = _filter_response(response, AddBreadcrumb.operation_name, AddBreadcrumb.error_response)
    return res


class AddProject(Operation):
    operation_type = "mutation"
    operation_name = "add_project"
    query_args = {
        "p": {
            "project": TextType.FREE,
            "project_version": TextType.FREE,
            "language": TextType.FREE,
            "language_version": TextType.FREE,
            "is_ci": TextType.LITERAL,
            "status": TextType.LITERAL,
            "status_desc": TextType.FREE,
            "error_type": TextType.FREE,
            "error_desc": TextType.FREE,
            "user_id": TextType.FREE,
            "session_id": TextType.FREE,
            "container": TextType.LITERAL,
            "user_type": TextType.LITERAL,
            "platform": TextType.FREE,
            "arguments": TextType.FREE,
        },
    }
    fingerprint = True
    error_response = {
        "success": False,
        "latest_version": None,
        "message": ERROR,
    }


@telemetry_enabled
def add_project(project: str, project_version: str, **kwargs) -> dict:
    """
    Send project usage information to the telemetry server.

    This function requires a `project`, which is a string in the format of the GitHub
    `{owner}/{repository}`, and the current version being used.

    Additionally, the follow information is collected:
    - language (python is assumed by default)
    - language version
    - platform
    - containerized (docker, apptainer/singularity)

    Returns
    -------
    A dictionary containing the latest released version of the project,
    as well as any messages sent by the developers.
    """
    warnings.warn(
        "This method has been separated into `add_breadcrumb` and `check_project` methods.",
        DeprecationWarning,
        stacklevel=2,
    )
    query = AddProject.generate_query(project=project, project_version=project_version, **kwargs)
    logger.debug(query)
    _, response = request(Config.endpoint, query=query)
    res = _filter_response(response, AddProject.operation_name, AddProject.error_response)
    return res


class CheckProject(Operation):
    operation_type = "query"
    operation_name = "check_project"
    query_args = {
        "project": TextType.FREE,
        "project_version": TextType.FREE,
        "language": TextType.FREE,
        "language_version": TextType.FREE,
        "is_ci": TextType.LITERAL,
        "status": TextType.LITERAL,
        "status_desc": TextType.FREE,
        "error_type": TextType.FREE,
        "error_desc": TextType.FREE,
        "user_id": TextType.FREE,
        "session_id": TextType.FREE,
        "container": TextType.LITERAL,
        "platform": TextType.FREE,
        "arguments": TextType.FREE,
    }
    selections = ('success', 'flagged', 'latest', 'message')


@telemetry_enabled
def check_project(project: str, project_version: str, **kwargs) -> dict:
    """
    Check a project version with the latest available.

    This can be used to check for the most recent version, as well as if
    the `project_version` has been flagged by developers.

    Returns
    -------
    response: dict
        keys: success, flagged, latest, message
    """
    query = CheckProject.generate_query(project=project, project_version=project_version, **kwargs)
    logger.debug(query)
    _, response = request(Config.endpoint, query=query)
    res = _filter_response(response, CheckProject.operation_name)
    return res


class GetUsage(Operation):
    operation_type = 'query'
    operation_name = 'get_usage'
    query_args = {
        "project": TextType.FREE,
        "start": TextType.FREE,
        "end": TextType.FREE,
        "unique": TextType.LITERAL,
    }


@telemetry_enabled
def get_usage(project: str, start: str, **kwargs) -> dict:
    query = GetUsage.generate_query(project=project, start=start, **kwargs)
    logger.debug(query)
    _, response = request(Config.endpoint, query=query)
    res = _filter_response(response, GetUsage.operation_name)
    return res


def _introspec(func: ty.Callable, func_locals: dict) -> dict:
    """Inspect a function and return all parameters (not defaults)."""
    import inspect

    sig = inspect.signature(func)
    return {
        param: func_locals[param]
        for param, val in sig.parameters.items()
        if func_locals[param] != val.default and param != "kwargs"
    }


def _filter_response(response: dict | str, operation: str, fallback: dict | None = None):
    if not fallback:
        fallback = {
            'success': False,
            'message': ERROR,
        }

    if isinstance(response, dict):
        res = response.get("data")
        # success
        if isinstance(res, dict):
            return res.get(operation, fallback)

    # Otherwise data is None, return fallback response with error reported
    try:
        fallback['message'] = response.get('errors')[0]['message']
    finally:
        return fallback


def _parse_format_params(params: dict, query_args: dict) -> str:
    query_inputs = []
    vals = None

    for qarg, qval in query_args.items():
        if qarg in params:
            val = params[qarg]
            if isinstance(val, bool):
                val = str(val).lower()

            if qval.name == 'FREE':
                fval = json.dumps(val)
            elif qval.name == 'LITERAL':
                fval = val
            else:
                logger.error('Do not know how to handle type %s', qarg.name)
                fval = ''
            query_inputs.append(f'{qarg}:{fval}')

        elif isinstance(qval, dict):
            vals = _parse_format_params(params, qval)
            query_inputs.append(f'{qarg}:{{{vals}}}')

    return ','.join(query_inputs)
