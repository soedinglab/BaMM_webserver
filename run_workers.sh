# hack to make sure that the init system sends sigterm signals directly to celery, but not to the forked subprocesses.

# TODO - still not perfect: once celery in exec is finished the docker container will exec independently of the status of the other workers

(celery\
	-A webserver.celery:app worker\
	--loglevel=${BAMM_LOG_LEVEL}\
	-Q priority\
&)

(celery -A webserver.celery:app beat -s /logs/celerybeat-schedule &)

exec celery \
	--loglevel=${BAMM_LOG_LEVEL}\
	--app=webserver.celery:app worker\
	--soft-time-limit ${JOB_TIME_LIMIT}\
	--concurrency $N_PARALLEL_JOBS
