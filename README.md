# Prot

## Stack

|                               |                                      |
|-------------------------------|--------------------------------------|
| data workflows management     | [Prefect](https://docs.prefect.io/)  |
| graph database                | [neo4j](https://neo4j.com/)          |
| Python _neo4j_ client library | [py2neo](https://py2neo.org/2021.1/) |

### Prefect

[Prefect](https://docs.prefect.io/) has the same purposes as [Apache Airflow](https://airflow.apache.org/),
with some advantages:

- Frictionless local development and testing.
- Tasks accept arguments and use them exactly as the (decorated) functions that define
them. We can adapt Python functions into Prefect _flows_ and _tasks_ with minimal changes.
- Better scheduling.

The following articles discuss those aspects:

- [Airflow, Prefect, and Dagster: An Inside Look](https://towardsdatascience.com/airflow-prefect-and-dagster-an-inside-look-6074781c9b77)
- [Apache Airflow vs Prefect](https://understandingdata.com/posts/apache-airflow-vs-prefect/)

### py2neo

[py2neo](https://py2neo.org/2021.1/) extends the functionality of the official `neo4j`
library. It provides a full object-oriented representation for the _property graphs_.
By defining the corresponding classes, it makes _node_, _relationship_, and _subgraph_
first-class citizens. It accepts instances of these classes in the _create_ and
_merge_ operations.

This way, we can extract an entire _graph_ into an in-memory representation of it.

The mentioned model offers a straightforward interface between the _extract_ and _load_ operations.

Furthermore, the in-memory _graph_ representation permits optimizing the _neo4j_ lookups.
Consider the following _graph_:

```python
   n1 =  Node("N", {"p": 1})
   n2 = Node("N", {"p": 2})
   n3 =  Node("N", {"p": 3})
   r1 =  Relationship("R", n1, n2)
   r2 = Relationship("R", n2, n3)
   graph = n1 | n2 | n3 | r1 | r2
```

It allows for translation into a _Cypher_ transaction as follows:

```SQL
    CREATE [n1:N {p: 1}]-[r1:R]->[n2:N {p: 2}]
    MERGE [n2:N]-[r2:R]->[n3:N {n:3}]
```

As _n2_ is bound to the variable `n2` after the first clause, the next one doesn't imply
a lookup. In this case, no lookup would be necessary.

With a partial graph representation, it could be necessary to create one element at
a time:

```SQL
    CREATE [:N {p: 1}]
    CREATE [:N {p: 2}]
    CREATE [:N {p: 3}]
    MERGE [:N {p: 1}]-[:R]->[:N {p: 2}]
    MERGE [:N {p: 2}]-[:R]->[:N {p: 3}]
```

Such a transaction could imply 4 lookups - two per relationship.

Although I didn't investigate to what extent `py2neo` takes advantage of such
optimizations, its model is a good starting point.

`py2neo` may be slower than `neo4j` official library at transaction execution.
Yet, we could extend `neo4j` with a _properties graph_ interface matching `py2neo`'s.
Then taking advantage of the mentioned optimizations.

## Local usage

### Preparing the environment

1. Clone the repository.

   ```bash
   git clone git@github.com:91nunocosta/prot.git
   ```

2. Change to the project directory.

   ```bash
   cd prot
   ```

3. Install [_poetry_](https://python-poetry.org/) _package and dependency manager_.
Follow the [poetry installation guide](https://python-poetry.org/docs/#installation).
Choose the method that is more convenient to you, for example:

   ```bash
   pip install --user poetry
   ```

4. Create a new virtual environment (managed by _poetry_) with the project dependencies.

   ```bash
   poetry install
   ```

5. Enter the virtual environment.

   ```bash
   poetry shell
   ```

6. Set environment variables needed for _neo4j_, the neo4j URI
   and authentication (disabling it):

    ```bash
    source .env
    ```

7. Start _neo4j_:

    ```bash
    docker-compose up -d
    ```

8. Open _neo4j_ at http://localhost:7474/browser/, select `No authentication` as
   _Authentication type_, and press _connect_.

### Running the ingestion workflow

#### Invoking the workflow from the command line

1. Prepare the environment as described in
[**Preparing the environment**](#preparing-the-environment).

2. Invoke the workflow:

    ```bash
    python prot/flows.py
    ```

3. _(Optional)_ Open the [Prefect UI](https://docs.prefect.io/ui/overview/)
at the URL in the following command's output.

    ```bash
    prefect server start
    ```

4. Check _neo4j_ at http://localhost:7474/browser/.

#### Invoking the workflow from the Prefect UI

1. Prepare the environment as described in
[**Preparing the environment**](#preparing-the-environment).

2. Create and upload a [deployment](https://docs.prefect.io/concepts/deployments/)
   containing the workflow:

    ```bash
    prefect deployment build prot/flows.py:ingest_uniprot_into_neo4j_flow \
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
at the URL in the previous command's output.

6. Check _neo4j_ at http://localhost:7474/browser/.

## Next steps

This solution is a proof of concept scoped by the following assumptions:

1. the execution environment is a single local machine;

2. the provided UniProt XML file represents well the data to ingest.

We can consider the following steps to make this solution suitable for a real-world scenario.

1. Extract and load several XML files in parallel - if there are many. It is possible by
configuring [_Prefect Task Runners_](https://docs.prefect.io/concepts/task-runners/) for
the extract and load tasks.

2. Extract and load the XML files in chunks. That would allow handling XML files that
don't fit into memory.

3. Fine-tune the size of _neo4j_ transactions, buffering the extracted nodes and
   relationships if needed.

4. Develop bulk _create_ and _merge_ operations optimized for _tree-shaped graphs_.
Here we could use several heuristics:

   1. Assign univocal identifiers for every _node_ based on the corresponding XML
element position. We could translate those ids into _Cypher_ variables, thus avoiding
some node lookups. We could also assign those ids to _indexed properties_
to make node lookups faster.

   2. Group all _nodes_ and _relationships_ _merge_ by child _node_ type.
Given the _tree_ shape, there is a single parent _node_ type and parent
_relationship_ type for every _node_ type. It allows for patterns
for every _Child_ _node_ type:

    ```SQL
    {
        "relationships":[
            {
                "parent": {
                    "id": 1
                },
                "child": {
                    "id": 2,
                }
            },
            {
                "parent": {
                    "id": 1
                },
                "child": {
                    "id": 3,
                }
            }
        ]
    }
    UNWIND $relationships as r
    MERGE (:Parent {id: r.parent.id})-[R]->(:Child: {id: r.child.id})
    ```

5. Develop a slimmer representation of the graphs. `py2neo` stores _property_ names
and values along with the _nodes_ and _relationships_. Yet, the nodes of the same
type share the same properties. A collection of bi-dimensional arrays per _node_ type
can store all instances for each type. Rows would represent nodes. The columns would
represent the corresponding properties. This way, we would store each _property_ name once
per _node_ type.

6. Extend the [uniprot2graph](./prot/uniprot2graph_config.py) configuration to improve
the graph representation of _UniProt_ data. We could create a Python script to generate
part of the configuration (e.g., property types) from the _UniProt_ XML schema. Someone with
domain knowledge could fill in the details in the config.
We could add support to extra configuration parameters if needed.

7. Encapsulate the flow into a docker and configure Prefect with a
[Kubernetes infrastructure](https://docs.prefect.io/concepts/infrastructure/#kubernetesjob).

8. Develop a Kubernetes configuration for Prefect (server, agents, blocks, etc.).
It is also possible to use [Prefect managed cloud service](https://www.prefect.io/cloud/).
Yet, the effort of setting-up Prefect would pay off in the long run and avoid vendor lock-in.

## Development

### Linting

1. Prepare the environment as described in
[**Preparing the environment**](#preparing-the-environment).

2. Install linting dependencies:

   ```bash
   poetry install --with lint --with test
   ```

3. (Optional) Install linting pre-commit hooks:

   ```bash
   pre-commit install -t pre-commit -t pre-push -t commit-msg
   ```

4. Linting all files:

   ```bash
   pre-commit run --all-files
   ```

### Testing

1. Prepare the environment as described in
[**Preparing the environment**](#preparing-the-environment).

2. Install Continuous Delivery dependencies:

   ```bash
   poetry install --with cd
   ```

3. Run _tox_:

    ```bash
    tox
    ```
