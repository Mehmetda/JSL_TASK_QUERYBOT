import os, tempfile, traceback
os.environ.pop('HADOOP_HOME', None)
os.environ['PATH'] = ';'.join(p for p in os.environ.get('PATH','').split(';') if 'hadoop' not in p.lower() and 'winutils' not in p.lower())
os.environ.setdefault('SPARK_LOCAL_DIRS', tempfile.gettempdir())
try:
    from sparknlp_jsl import start
    start(os.getenv('JSL_LICENSE_FILE') or os.getenv('SPARK_NLP_LICENSE'),
          os.getenv('JSL_SECRET'))
    from sparknlp.pretrained import PretrainedPipeline
    PretrainedPipeline('ner_profiling_clinical','en','clinical/models')
    print('OK: pipeline loaded')
except Exception:
    traceback.print_exc()
