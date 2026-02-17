from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, explode, lit, current_timestamp, year, month, dayofmonth
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, ArrayType, IntegerType
)
# ---------------------------------------------------
# Create Spark Session
# ---------------------------------------------------
spark = SparkSession.builder \
    .appName("OrderStreamingJob") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# ---------------------------------------------------
# Define Schema for Current API Payload
# ---------------------------------------------------
item_schema = StructType([
    StructField("product_id", StringType(), True),
    StructField("product_name", StringType(), True),
    StructField("quantity", DoubleType(), True),
    StructField("price", DoubleType(), True)
])

order_schema = StructType([
    StructField("event_type", StringType(), True),
    StructField("order_id", StringType(), True),
    StructField("user_id", StringType(), True),
    StructField("total_amount", DoubleType(), True),
    StructField("items", ArrayType(item_schema), True)
])

# ---------------------------------------------------
# Read From Kafka
# ---------------------------------------------------
raw_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "order_created") \
    .option("startingOffsets", "latest") \
    .load()

# Convert binary to string
string_df = raw_df.selectExpr("CAST(value AS STRING) as json_value")

# ---------------------------------------------------
# Parse JSON
# ---------------------------------------------------
parsed_df = string_df.select(
    from_json(col("json_value"), order_schema).alias("data")
)

# Filter out bad records
valid_orders_df = parsed_df.filter(col("data").isNotNull()).select("data.*")

# ---------------------------------------------------
# Explode Items Array (1 order → multiple rows)
# ---------------------------------------------------
exploded_df = valid_orders_df.withColumn("item", explode(col("items")))

# ---------------------------------------------------
# Flatten Structure + Compute Metrics
# ---------------------------------------------------
final_df = exploded_df.select(
    col("order_id"),
    col("user_id"),
    lit("PENDING").alias("status"),           # default status
    current_timestamp().alias("created_at"),  # current timestamp
    col("total_amount").alias("order_total_amount"),
    col("item.product_id"),
    col("item.quantity").cast("int").alias("quantity"),
    col("item.price").alias("price_at_purchase"),
    (col("item.quantity") * col("item.price")).alias("item_total")
)

# ---------------------------------------------------
# Add Partition Columns (Good Data Lake Practice)
# ---------------------------------------------------

final_df_with_partitions = final_df \
    .withColumn("year", year(col("created_at"))) \
    .withColumn("month", month(col("created_at"))) \
    .withColumn("day", dayofmonth(col("created_at")))

# ---------------------------------------------------
# Write Stream to S3 (Raw Layer - Bronze)
# ---------------------------------------------------
query = final_df_with_partitions.writeStream \
    .outputMode("append") \
    .format("parquet") \
    .option("path", "s3a://ecommerce-data-lake-prathmesh-2026/raw/orders/") \
    .option("checkpointLocation", "s3a://ecommerce-data-lake-prathmesh-2026/raw/checkpoints/orders/") \
    .partitionBy("year", "month", "day") \
    .start()

query.awaitTermination()    