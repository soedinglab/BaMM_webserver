#!/bin/bash

celery\
	--app=webserver.celery:app worker\
	--soft-time-limit $JOB_TIME_LIMIT\
	--concurrency $N_PARALLEL_JOBS

