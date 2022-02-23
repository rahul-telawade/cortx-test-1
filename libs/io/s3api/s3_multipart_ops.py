#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#
#

"""Python Library to perform multipart operations using boto3 module."""

import logging
import os

from commons.utils.system_utils import cal_percent
from libs.io.s3api.s3_restapi import S3RestApi

logger = logging.getLogger(__name__)


class S3MultiParts(S3RestApi):
    """Class for Multipart operations."""

    def create_multipart_upload(self, bucket_name: str, obj_name: str) -> dict:
        """
        Request to initiate a multipart upload.

        :param bucket_name: Name of the bucket.
        :param obj_name: Name of the object.
        :return: Response of create multipart upload.
        """
        response = self.s3_client.create_multipart_upload(Bucket=bucket_name, Key=obj_name)
        logger.debug("Response: %s", response)

        return response

    def upload_part(self, body: bytes, bucket_name: str, object_name: str, **kwargs) -> dict:
        """
        Upload parts of a specific multipart upload.

        :param body: content of the object.
        :param bucket_name: Name of the bucket.
        :param object_name: Name of the object.
        :upload_id: upload id of the multipart upload.
        :part_number: part number to be uploaded.
        :return: response of upload part.
        """
        upload_id = kwargs.get("upload_id")
        part_number = kwargs.get("part_number")
        response = self.s3_client.upload_part(
            Body=body, Bucket=bucket_name, Key=object_name,
            UploadId=upload_id, PartNumber=part_number)
        logging.debug(response)

        return response

    def list_parts(self, mpu_id: str, bucket: str, object_name: str) -> dict:
        """
        list parts of a specific multipart upload.

        :param mpu_id: Multipart upload ID.
        :param bucket: Name of the bucket.
        :param object_name: Name of the object.
        :return: Response of list parts.
        """
        response = self.s3_client.list_parts(Bucket=bucket, Key=object_name, UploadId=mpu_id)
        logger.debug(response)

        return response

    def complete_multipart_upload(
            self,
            mpu_id: str,
            parts: list,
            bucket: str,
            object_name: str) -> dict:
        """
        Complete a multipart upload, s3 creates an object by concatenating the parts.

        :param mpu_id: Multipart upload ID.
        :param parts: Uploaded parts in sorted ordered.
        :param bucket: Name of the bucket.
        :param object_name: Name of the object.
        :return: response of complete multipart upload.
        """
        logger.debug("initiated complete multipart upload")
        response = self.s3_client.complete_multipart_upload(
            Bucket=bucket,
            Key=object_name,
            UploadId=mpu_id,
            MultipartUpload={"Parts": parts})
        logger.debug(response)

        return response

    def list_multipart_uploads(self, bucket: str) -> dict:
        """
        List all initiated multipart uploads.

        :param bucket: Name of the bucket.
        :return: response of list multipart uploads.
        """
        response = self.s3_client.list_multipart_uploads(Bucket=bucket)
        logger.debug(response)

        return response

    def abort_multipart_upload(self, bucket: str, object_name: str, upload_id: str) -> dict:
        """
        Abort multipart upload for given upload_id.

        :param bucket: Name of the bucket.
        :param object_name: Name of the object.
        :param upload_id: Name of the object.
        :return: Response of abort multipart upload.
        """
        response = self.s3_client.abort_multipart_upload(
            Bucket=bucket, Key=object_name, UploadId=upload_id)
        logger.debug(response)

        return response

    def upload_part_copy(self, copy_source: str, bucket_name: str,
                         object_name: str, **kwargs) -> dict:
        """
        Upload parts of a specific multipart upload from existing object.

        :param copy_source: source of part copy.
        :param bucket_name: Name of the bucket.
        :param object_name: Name of the object.
        :upload_id: upload id of the multipart upload.
        :part_number: part number to be uploaded.
        :return: response of the upload part copy.
        """
        upload_id = kwargs.get("upload_id")
        part_number = kwargs.get("part_number")
        response = self.s3_client.upload_part_copy(
            Bucket=bucket_name, Key=object_name,
            UploadId=upload_id, PartNumber=part_number,
            CopySource=copy_source)
        logging.debug(response)

        return response

    def upload_parts(self,
                     mpu_id: int,
                     bucket_name: str,
                     object_name: str,
                     multipart_obj_path: str,
                     total_parts: int) -> list:
        """
        Upload parts for a specific multipart upload ID.

        :param mpu_id: Multipart Upload ID.
        :param bucket_name: Name of the bucket.
        :param object_name: Name of the object.
        :param total_parts: No. of parts to be uploaded.
        :param multipart_obj_path: Path of object file.
        :return: (Boolean, List of uploaded parts).
        """
        parts = list()
        uploaded_bytes = 0
        if not os.path.exists(multipart_obj_path):
            raise IOError("File path '%s' does not exists.", multipart_obj_path)
        multipart_obj_size = os.stat(multipart_obj_path).st_size
        single_part_size = multipart_obj_size // int(total_parts)
        with open(multipart_obj_path, "rb") as file_pointer:
            i = 1
            while True:
                data = file_pointer.read(single_part_size)
                logger.info("data_len %s", str(len(data)))
                if not data:
                    break
                part = self.upload_part(
                    data, bucket_name, object_name, upload_id=mpu_id, part_number=i)
                logger.debug("Part : %s", str(part))
                parts.append({"PartNumber": i, "ETag": part["ETag"]})
                uploaded_bytes += len(data)
                logger.debug(
                    "{0} of {1} uploaded ({2:.2f}%)".format(
                        uploaded_bytes,
                        multipart_obj_size *
                        1048576,
                        cal_percent(
                            uploaded_bytes,
                            multipart_obj_size *
                            1048576)))
                i += 1
        logger.info(parts)

        return parts