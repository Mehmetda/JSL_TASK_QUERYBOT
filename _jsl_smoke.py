import os, tempfile
os.environ.pop("HADOOP_HOME", None)
os.environ.setdefault("SPARK_LOCAL_DIRS", tempfile.gettempdir())

from sparknlp_jsl import start
start(r"F:\spark_nlp_for_healthcare_spark_ocr_10494.json",
      "6.1.0-aed05ae6b3d6b6cfb4bcd896ff00c85919413cd2")

from sparknlp.pretrained import PretrainedPipeline
PretrainedPipeline("ner_profiling_clinical","en","clinical/models")
print("OK: pipeline loaded")
