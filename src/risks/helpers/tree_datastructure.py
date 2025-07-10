from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Any, List
from dependency_injector import containers, providers
from dependency_injector.wiring import inject, Provide

import pandas as pd

from src.risks.containers import Container
from src.risks.helpers.input_file_reader_interface import FilePathReader


@dataclass
class AggregationTreeNode:
    risk_name: str
    # Think if the parent should be aggregation tree node, or just parent risk_name
    parent: Optional["AggregationTreeNode"] = None
    # Added children, as they are easily computable based on the parents
    children: Optional[List["AggregationTreeNode"]] = field(default_factory=list)
    value: Optional[float] = None

    input_data: Optional[Any] = None
    # Below define any addional fields you want to include


@dataclass
class AggregationTree:
    nodes: List[AggregationTreeNode] = field(default_factory=list)
    nodes_not_yet_computed: Optional[List[AggregationTreeNode]] = field(
        default_factory=list
    )

    def __init__(self, input_dataframe: pd.DataFrame):
        self.nodes = []
        self.nodes_not_yet_computed = []

        # First pass to define all of the nodes
        for index, row in input_dataframe.iterrows():
            row_dict = row.to_dict()
            new_aggregation_tree_node = AggregationTreeNode(
                risk_name=row_dict["NODE_ID"], parent=None, value=None, input_data=None
            )
            self.add_node(new_aggregation_tree_node)

        # Second pass to properly assign all of the parents
        for index, row in input_dataframe.iterrows():
            row_dict = row.to_dict()
            parent_id = row_dict.get("PARENT_NODE_ID")
            current_node = next(
                node for node in self.nodes if node.risk_name == row_dict["NODE_ID"]
            )
            if pd.notna(parent_id):
                parent_node = next(
                    (node for node in self.nodes if node.risk_name == parent_id), None
                )
                current_node.parent = parent_node
                if parent_node:
                    parent_node.children.append(current_node)

    def add_node(self, node: AggregationTreeNode):
        self.nodes.append(node)
        if not node.value:
            self.nodes_not_yet_computed.append(node)


@inject
def main(filePathReader: FilePathReader = Provide[Container.filePathReader]):
    current_file = Path(__file__).resolve()
    aggregation_tree_input_path = current_file.parent / "aggregation_tree.xlsx"
    tree_input_dataframe = filePathReader.read_file_path(
        str(aggregation_tree_input_path)
    )
    tree_input_dataframe.columns = [
        col.strip().upper() for col in tree_input_dataframe.columns
    ]
    aggregation_tree = AggregationTree(tree_input_dataframe)
    node_names_list = [elem.risk_name for elem in aggregation_tree.nodes]
    print(node_names_list)
    print(len(node_names_list))


if __name__ == "__main__":
    container = Container()
    container.wire(modules=[__name__])
    main()
