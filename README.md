# Weave Challenge

Weave challenge data engineering coding challenge.

## Stack

- **data workflows management**: [Prefect](https://docs.prefect.io/).

## Local usage

### Preparing the environment

1. Clone the repository.

   ```bash
   git clone git@github.com:91nunocosta/weave-challenge.git
   ```

2. Change to the project directory.

   ```bash
   cd weave-challenge
   ```

3. Install [_poetry_](https://python-poetry.org/) _package and dependency manager_.
Follow the [poetry installation guide](https://python-poetry.org/docs/#installation).
Chose the method that is more convenient to you, for example:

   ```bash
   pip install --user poetry
   ```

   or

   ```bash
   curl -sSL\
        https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py \
      | python -
   ```

4. Create a new virtual environment (managed by _poetry_) with the project dependencies.

   ```bash
   poetry install
   ```

5. Enter the virtual environment.

   ```bash
   poetry shell
   ```

6. Set environment variables, needed for _neo4j_:

    ```bash
    source .env
    ```

7. Start _neo4j_:

    ```bash
    docker-compose up -d
    ```

### Running the ingestion workflow

#### Invoking the workflow from the command line

1. Prepare the environment, as described in
[**Preparing the environment**](#preparing-the-environment).

2. Start _prefect_ server:

    ```bash
    prefect server start
    ```

3. _(Optional)_ Open the [Prefect UI](https://docs.prefect.io/ui/overview/)
at the URL displayed in previous command's output,
in order to monitor workflow execution.

4. Invoke the workflow:

    ```bash
    python weave_challenge/flows.py
    ```

#### Invoking the workflow from the Prefect UI

1. Prepare the environment, as described in
[**Preparing the environment**](#preparing-the-environment).

2. Create and upload an [deployment](https://docs.prefect.io/concepts/deployments/),
   containing the workflow:

    ```bash
    prefect deployment build weave_challenge/flows.py:ingest_uniprot_into_neo4j_flow \
        --name ingest_uniprot_into_neo4j \
        --apply
    ```

3. Start a [Prefect agent](https://docs.prefect.io/concepts/work-pools/)

    ```bash
    prefect agent start -q 'default'
    ```

4. Start _prefect_ server:

    ```bash
    prefect server start
    ```

5. Open the [Prefect UI](https://docs.prefect.io/ui/overview/)
at the URL displayed in previous command's output.

## Development

### Linting

1. Prepare the environment, as described in
[**Preparing the environment**](#preparing-the-environment).

2. Install linting dependencies:

   ```bash
   poetry install --with lint
   ```

3. (Optional) Install linting pre commit hooks:

   ```bash
   pre-commit install -t pre-commit -t pre-push -t commit-msg
   ```

4. Linting all files:

   ```bash
   pre-commit run --all-files
   ```

### Testing

1. Prepare the environment, as described in
[**Preparing the environment**](#preparing-the-environment).

2. Install Continuous Delivery dependencies:

   ```bash
   poetry install --with cd
   ```

3. Run _tox_:

    ```bash
    tox
    ```
