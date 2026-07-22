#!/bin/sh
sleep 5
mc alias set myminio ${MINIO_ENDPOINT} ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}
mc mb myminio/raw-files || true
mc anonymous set public myminio/raw-files || true
