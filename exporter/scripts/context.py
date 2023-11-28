import os
from pathlib import Path

import pandas as pd
import yaml

# TODO: move over to separate .py

CONFIG_HOME = ".exporter"
CONFIG_NAME = os.environ.get("EXPORTER_CONFIG_NAME") or "config.yml"


class Data(object):
    """Base class for data sources."""

    def __init__(self, path: str) -> None:
        self.path = Path.cwd() / Path(CONFIG_HOME) / Path(path)
        # Check if the file exists
        if not self.path.exists():
            raise FileNotFoundError(f"File '{self.path}' not found.")

    def load(self):
        pass

    def save(self):
        pass

    @property
    def get(self):
        pass


class CSV(Data):
    def __init__(self, path: str = None) -> None:
        super().__init__(path)

        self.df = self.load()

    def load(self):
        csv_file = open(self.path, "r")
        csv_reader = pd.read_csv(csv_file)
        return csv_reader


class DataSource(object):
    def __init__(self) -> None:
        self.config = Config()
        self.source = self.load()
        self._loaded = None
        self.join_sources = None

    @classmethod
    def get(cls):
        return cls()

    def load(self) -> Data:
        """Loads the data source."""
        source_path = self.config.content.get("data", None).get("src", None)
        join_sources = self.config.content.get("join", None)
        if not source_path and not join_sources:
            raise ValueError("No data source found in the config file.")
        if source_path and join_sources:
            raise ValueError(
                "You cannot specify both a data source and join sources in the config file."
            )
        if join_sources:
            self.join_sources = [
                JoinSource(
                    DataSource(join_source),
                    join_sources["on"],
                    join_sources.get("how", "left"),
                )
                for join_source in join_sources["src"]
            ]
        # TODO: auto-determine the data source type
        csv = CSV(source_path)
        self._loaded = list(csv.load())
        return csv

    @classmethod
    def save_to_file(cls, df, config) -> None:
        """Saves the data source."""
        dest_name = config.content.get("data", None).get("dest", None)
        dest_path = Path.cwd() / Path(CONFIG_HOME) / Path(dest_name)

        if not dest_path:
            raise ValueError("No data destination found in the config file.")
        try:
            df.to_csv(dest_path, index=False)
        except Exception as e:
            print(f"Error while saving the data source: {e}")
            raise


class Config(object):
    def __init__(self) -> None:
        self.config_path = Path.cwd() / Path(CONFIG_HOME) / CONFIG_NAME
        self._content = self._read_config() or {}

    def _create_config(self):
        pass

    def _read_config(self):
        try:
            # Open and load the YAML file
            with open(self.config_path, "r") as yaml_file:
                return yaml.safe_load(yaml_file)
        except FileNotFoundError:
            print(f"File '{self.yaml_file_path}' not found.")
            raise
        except yaml.YAMLError as e:
            print(f"Error while loading YAML file: {e}")
            raise

    @classmethod
    def init(cls, dataset: str, dest: str) -> None:
        """Stores the dataset name in the config file."""
        config = cls()

        if config.content is None:
            config.content = {"data": {"src": dataset, "dest": dest}}
        else:
            config.content["data"]["src"] = dataset
            config.content["data"]["dest"] = dest
        with open(config.config_path, "w") as yaml_file:
            yaml.safe_dump(config.content, yaml_file, default_flow_style=False)

    @property
    def dest_name(self) -> str:
        return self.content.get("data", None).get("dest", None)

    @property
    def destination_path(self) -> Path:
        dest_name = self.dest_name
        return Path.cwd() / Path(CONFIG_HOME) / Path(dest_name)

    @property
    def content(self):
        if not self._content:
            self._content = self._read_config()
        return self._content

    @content.setter
    def content(self, value):
        self._content = value

    def write(self):
        with open(self.config_path, "w") as yaml_file:
            yaml.safe_dump(self.content, yaml_file, default_flow_style=False)


class JoinSource(object):
    def __init__(self, source: DataSource, on: str, how: str = "left") -> None:
        self.source = source
        self.on = on
        self.how = how
