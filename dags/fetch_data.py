import datetime
import pornhub
from pyspark.sql import SparkSession
from airflow.sdk import DAG

with DAG(dag_id="spark_init", schedule="@daily") as spark_dag:
    spark = SparkSession.builder.getOrCreate()

with DAG(dag_id="load", schedule="@daily") as load_dag:
    client = pornhub.PornHub()
    for star in client.getStars(11, sort_by="rank"):
        for vid in client.getStarsVideos(star["name"], type=star["type"]):
            vid_clean = client.getVideo(url=vid)
