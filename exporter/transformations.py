import logging


from exporter.scripts.context import DataSource, Config

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def preview() -> None:
    """Preview the changes that will be applied to the dataset"""
    data = DataSource.get()
    config = Config()

    if "include" not in config.content:
        logging.info("No columns to include in the dataset.")
        return

    columns = config.content["include"]
    validate_columns(data, columns)

    logging.info("Included columns: %s", columns)
    preview_dataset(data, columns)


def include(columns: list[str]) -> None:
    """Columns to include in the final dataset"""
    data = DataSource.get()
    validate_columns(data, columns)
    add_columns(columns)

    logging.info("Included columns: %s", columns)


def validate_columns(data: DataSource, columns: list[str]) -> None:
    """Validates that the columns exist in the dataset."""
    entry = list(data.source.load())[0]

    for column in columns:
        if column not in entry:
            logging.error("Column '%s' does not exist in the dataset.", column)
            raise ValueError(f"Column '{column}' does not exist in the dataset.")


def add_columns(columns: list[str]) -> None:
    """Updates the config file with the columns to include."""
    config = Config()
    config.content["include"] = columns
    config.write()


def preview_dataset(data, columns):
    """Prints the first 10 rows of the dataset."""
    print("Preview of the dataset:")
    for row in list(data.source.load())[0:10]:
        print({column: row[column] for column in columns})