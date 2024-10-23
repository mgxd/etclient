# Migas Client

A Python package to communicate with a migas server.

## About

`migas` (*mee-gahs*) is a Python client to facilitate communication with a [`migas` server](https://github.com/nipreps/migas-server).


## Usage

To start communicating with a `migas` server, the client must first be setup.

```python
import migas; migas.setup()
```

By default, `migas-py` will communicate with the official hosted `migas` server.
However it can easily be configured to communicate with any hosted `migas` server.

```python
import migas; migas.setup(endpoint='your-endpoint')
```

`setup()` will populate the [interal configuration](#configuration), which is done at the process level.

## API

`migas` includes the following functions to communicate with the telemetry server:

### [migas.add_breadcrumb] (#add-breadcrumb)
---
Send a breadcrumb with usage information to the server.

##### Mandatory
- `project` - application name
- `project_version` - application version

##### Optional
- `language` (auto-detected)
- `language_version` (auto-detected)
- process:
  - `status`
  - `status_desc`
  - `error_type`
  - `error_desc`
- context:
  - `user_id` (auto-generated)
  - `session_id`
  - `user_type`
  - `platform` (auto-detected)
  - `container` (auto-detected)
  - `is_ci` (auto-detected)

<details>
<summary>add_breadcrumb example</summary>

```python
>>> add_breadcrumb('nipreps/migas-py', '0.0.1', status='R', status_desc='Finished long step')
>>>
```

</details>

### [migas.check_project] (#check-project)
---
Check a project version against later developments.

##### Mandatory
- `project`
- `project_version`


<details>
<summary>check_project example</summary>

```python
>>> check_project('nipreps/migas-py', '0.0.1')
{'success': True, 'flagged': False, 'latest': '0.4.0', 'message': ''}
```

</details>

### [migas.get_usage] (#get-usage)
---
Check number of uses a `project` has received from a start date, and optionally an end date.
If no end date is specified, the current datetime is used.

<details>
<summary>get_usage example</summary>

```python
>>> get_usage('nipreps/migas-py', '2022-07-01')
{'hits': 7, 'message': '', 'unique': False, 'success': True}
```

</details>


### [migas.track_exit] (#track-exit)
---
Register an exit function to send a final ping upon termination of the Python interpretter.
Useful when monitoring a process that may preemptively error.
The inputs are equivalent to [`add_breadcrumb()`](#add-breadcrumb)

## User Control

`migas` can controlled by the following environmental variables:

| Envvar | Description | Value | Default |
| ---- | ---- | ---- | ---- |
| `MIGAS_OPTOUT` | Disable telemetry collection | Any | None
| `MIGAS_TIMEOUT` | Seconds to wait for server response | Number >= 0 | 5
| `MIGAS_LOG_LEVEL` | Logger level | [Logging levels](https://docs.python.org/3/library/logging.html#levels) | WARNING


## Configuration

The internal configuration stores the following telemetry information:

- language and language version
- operating system
- run within a container
- run from continuous integration
