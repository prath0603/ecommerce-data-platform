import os
import json
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import time

def get_producer():
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

    # Retry logic (important in distributed systems)
    for i in range(5):
        try:
            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(
                    v,
                    default=str
                ).encode("utf-8"),
                acks="all",
                retries=3
            )
            print("✅ Connected to Kafka")
            return producer
        except NoBrokersAvailable:
            print("⏳ Kafka not ready, retrying...")
            time.sleep(3)

    raise Exception("❌ Could not connect to Kafka after retries")


def send_order_event(order_data: dict):
    producer = get_producer()

    try:
        future = producer.send("order_created", order_data)
        record_metadata = future.get(timeout=10)

        print("✅ Order event sent to Kafka")
        print(f"   Topic: {record_metadata.topic}")
        print(f"   Partition: {record_metadata.partition}")
        print(f"   Offset: {record_metadata.offset}")

    except Exception as e:
        print("❌ Failed to send order event:", str(e))

    finally:
        producer.flush()
