#region Import Section
from pyspark import SparkConf, SparkContext
from pyspark.sql import SQLContext, Row, SparkSession
#endregion
#TEMPLATE CHANGED KEY VALUE 
#TEMPLATE CHANGED AGAIN COMMENT ADDED

#region CONSTANTS
AWS_ACCESS_KEY = "AKIAJGPUYM53BFC34GRA"
AWS_SECRET_KEY = "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"
TEMP_BUCKET ="s3n://haider-ali-invesco-assignment/temp_babar/" 
DATA_FILE_PATH ="s3n://haider-ali-invesco-assignment/1800.csv"
jdbcUsername = "redshiftuser"
jdbcPassword = "Redshift1234"
jdbcHostname = "babar-rs-invesco-traning.cfzi7ijp9ypg.us-east-1.redshift.amazonaws.com"
jdbcPort = 5439
jdbcDatabase = "redshiftdb"
jdbcUrl = "jdbc:redshift://wmi-lite-redshift-cluster.cfzi7ijp9ypg.us-east-1.redshift.amazonaws.com:5439/redshiftdb?user=redshiftuser&password=Redshift1234"
DB_TABLE ="Temperature"
#endregion

#region Helper Functions
def parseLine(line):
    fields = line.split(',')
    stationID = fields[0]
    entryType = fields[2]
    temperature = float(fields[3]) * 0.1 * (9.0 / 5.0) + 32.0
    return (stationID, entryType, temperature)

def getMinTempsRDD(parsedLines):
    minTemps = parsedLines.filter(lambda x: "TMIN" in x[1])
    stationMinTemps = minTemps.map(lambda x: (x[0], x[2]))
    minTemps = stationMinTemps.reduceByKey(lambda x, y: min(x,y))
    return minTemps

def getMaxTempsRDD(parsedLines):
    maxTemps = parsedLines.filter(lambda x: "TMAX" in x[1])
    stationMaxTemps = maxTemps.map(lambda x: (x[0], x[2]))
    maxTemps = stationMaxTemps.reduceByKey(lambda x, y: max(x,y))
    return maxTemps
#endregion



#region Spark Configuration local
# conf = SparkConf().setMaster("local").setAppName("Temeprature")
# sc = SparkContext(conf = conf)
# sqlContext = SQLContext(sc)
# DATA_FILE_PATH = "1800.csv"
#endregion
#region Spark Configuration
conf = SparkConf().setAppName("MinMaxTemperatures")
sc = SparkContext(conf = conf)
sc._jsc.hadoopConfiguration().set('fs.s3n.awsAccessKeyId',AWS_ACCESS_KEY)
sc._jsc.hadoopConfiguration().set('fs.s3n.awsSecretAccessKey',AWS_SECRET_KEY)
sqlContext = SQLContext(sc)
#endregion
#region Processing of Data
lines = sc.textFile(DATA_FILE_PATH)
parsedLines = lines.map(parseLine)
minTemps = getMinTempsRDD(parsedLines)
maxTemps = getMaxTempsRDD(parsedLines)
results = minTemps.join(maxTemps)
#endregion



#region Create Data Frame
df = results.map(lambda x: Row(StationId =x[0], MinimumTemperature = x[1][0], MaximumTemperature = x[1][1]))
dataFrame= sqlContext.createDataFrame(df)
dataFrame.show()
#endregion

#region Write data to RedShift
dataFrame.write \
  .format("com.databricks.spark.redshift") \
  .option("url", jdbcUrl) \
  .option("dbtable", DB_TABLE) \
  .option("tempdir", TEMP_BUCKET) \
  .option("tempformat","CSV") \
  .option("aws_iam_role", "arn:aws:iam::585091576682:role/redshift-admin") \
  .mode("overwrite") \
  .save()
#endregion