from pyspark.sql.functions import col , when , to_timestamp , coalesce

def normalize_dates(df):
    date_columns = [
        "date_actualisation",
        "date_ingestion",
        "date_publication"
    ]
    for co in date_columns:
        df = df.withColumn(
            co,
            when(col(co) == "", None)
            .otherwise(
                coalesce(
                    to_timestamp(col(co)),                    
                    to_timestamp(col(co), "dd/MM/yyyy")        
                )
            )
        )
    return df