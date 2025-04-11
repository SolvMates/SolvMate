
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sqrt, sum as spark_sum, max as spark_max, when

# Initialize Spark session
spark = SparkSession.builder.appName("MarketSCRAggregation").getOrCreate()

def aggregate_tree(aggregation_tree_id):
    """
    Aggregates market SCR values based on the specified aggregation tree ID.

    Parameters:
    aggregation_tree_id (str): The ID of the aggregation tree to be used for aggregation.

    Steps:
    1. Reads in the aggregation tree and data ID updated tables using Spark SQL.
    2. Initializes the "VALUE" column in the aggregation tree DataFrame to 0.
    3. Reads in values for nodes with "_AGGREGATION_METHOD_CD" = "external" and updates the "VALUE" column.
    4. Aggregates values for other nodes based on their aggregation method.
        - Supported methods: 'sum', 'max', 'correlated', 'dnav', 'max_scen'.
    5. Saves the results in a new table "aggregation_tree_market_enriched" in the "default" schema.

    Example usage:
    aggregate_market_scr('MARKET_INT')
    """
    
    # Step 1: Read in the tables using Spark SQL
    aggregation_tree = spark.sql(f'SELECT * FROM default.aggregation_tree_market WHERE AGGREGATION_TREE_ID = "{aggregation_tree_id}"')
    data_id_updated = spark.sql('SELECT * FROM default.data_id_updated')

    # Step 2: Add the column "VALUE" to the data frame "aggregation_tree" and initialize to 0
    aggregation_tree = aggregation_tree.withColumn("VALUE", when(col("_NODE_ID").isNotNull(), 0).cast("double"))

    # Step 3: Read in all values for nodes with "_AGGREGATION_METHOD_CD" = "external"
    external_nodes = aggregation_tree.filter(col("_AGGREGATION_METHOD_CD") == "external")
    external_node_ids = [row["_NODE_ID"] for row in external_nodes.collect()]
    external_values = data_id_updated.filter(data_id_updated["DATA_ID"].isin(external_node_ids))

    for row in external_nodes.collect():
        value_row = external_values.filter(external_values["DATA_ID"] == row["_NODE_ID"]).first()
        if value_row:
            aggregation_tree = aggregation_tree.withColumn("VALUE", 
                when(col("_NODE_ID") == row["_NODE_ID"], value_row["VALUE"]).otherwise(col("VALUE")))

    # Step 4: Aggregate all other values using their aggregation method
    def aggregate_node(node_id):
        node = aggregation_tree.filter(col("_NODE_ID") == node_id).first()
        if not node:
            return None

        method = node["_AGGREGATION_METHOD_CD"]
        children = aggregation_tree.filter(col("_PARENT_NODE_ID") == node_id)

        if method == 'sum':
            return children.agg(spark_sum("VALUE")).first()[0]
        elif method == 'max':
            return children.agg(spark_max("VALUE")).first()[0]
        elif method == 'correlated':
            matrix_id = node["_MATRIX_ID"]
            correlation_matrix = spark.sql(f'SELECT * FROM default.correlation_matrix WHERE CORRELATION_MATRIX_ID = "{matrix_id}"')
            total = 0
            child_ids = [row["_NODE_ID"] for row in children.collect()]
            for i in range(len(child_ids)):
                for j in range(len(child_ids)):
                    if i != j:
                        corr_value = correlation_matrix.filter((correlation_matrix["VAR1_NM"] == child_ids[i]) & 
                                                               (correlation_matrix["VAR2_NM"] == child_ids[j])).first()
                        if corr_value:
                            total += corr_value["CORRELATION_VALUE_NO"] * (children.filter(col("_NODE_ID") == child_ids[i]).select("VALUE").first()[0] * 
                                                                            children.filter(col("_NODE_ID") == child_ids[j]).select("VALUE").first()[0])
            return sqrt(total)
        elif method == 'dnav':
            base_case_assets = children.filter((col("BS_TYPE") == 'asset') & (col("SCENARIO") == 'BC')).agg(spark_sum("VALUE")).first()[0]
            base_case_liabilities = children.filter((col("BS_TYPE") == 'liab') & (col("SCENARIO") == 'BC')).agg(spark_sum("VALUE")).first()[0]
            shocked_assets = children.filter((col("BS_TYPE") == 'asset') & (col("SCENARIO") == 'SH')).agg(spark_sum("VALUE")).first()[0]
            shocked_liabilities = children.filter((col("BS_TYPE") == 'liab') & (col("SCENARIO") == 'SH')).agg(spark_sum("VALUE")).first()[0]
            return (base_case_assets - base_case_liabilities) - (shocked_assets - shocked_liabilities)
        elif method == 'max_scen':
            return children.agg(spark_max("VALUE")).first()[0]
        else:
            return None

    # Apply aggregation recursively for all nodes
    node_ids = [row["_NODE_ID"] for row in aggregation_tree.collect()]
    for node_id in node_ids:
        if aggregation_tree.filter(col("_NODE_ID") == node_id).select("VALUE").first()[0] is None:
            value = aggregate_node(node_id)
            aggregation_tree = aggregation_tree.withColumn("VALUE", 
                when(col("_NODE_ID") == node_id, value).otherwise(col("VALUE")))

    # Step 5: Save the results in a new table in schema "default" with name "aggregation_tree_market_enriched"
    aggregation_tree.select("_NODE_ID", "VALUE").write.mode("overwrite").saveAsTable("default.aggregation_tree_market_enriched")

# Example usage
#aggregate_tree('MARKET_INT')



