import configparser
import pathlib
from os import path

import boto3 as boto3
from botocore.exceptions import ClientError

DELIMITER = '/'

DEFAULT_URL = "https://storage.yandexcloud.net"
DEFAULT_REGION = "ru-central1"
ROOT_PATH_DIRECTORY = path.dirname(pathlib.Path(__file__).parent)
CONFIG_PATH_DIRECTORY = pathlib.Path.home() / ".config" / "cloudphoto"
CONFIG_FILENAME = "cloudphotorc"
CONFIG_PATH_FILE = str(CONFIG_PATH_DIRECTORY / CONFIG_FILENAME)


def create_session(access_key, secret_access_key, endpoint_url, region_name) -> boto3.session:
    session = boto3.session.Session()
    return session.client(
        service_name="s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_access_key,
        region_name=region_name
    )


def init_session() -> boto3.session:
    if is_configured():
        config = read_config_file()
        config = {
            "endpoint_url": config.get("DEFAULT", "endpoint_url"),
            "access_key": config.get("DEFAULT", "aws_access_key_id"),
            "secret_access_key": config.get("DEFAULT", "aws_secret_access_key"),
            "region_name": config.get("DEFAULT", "region")
        }

        return create_session(**config)


def read_config_file() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH_FILE)

    return config


def create_config_file(access_key, secret_key, bucket_name):
    CONFIG_PATH_DIRECTORY.mkdir(parents=True, exist_ok=True)

    config = configparser.ConfigParser()
    config["DEFAULT"] = {
        "bucket": bucket_name,
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "region": "ru-central-1",
        "endpoint_url": "https://storage.yandexcloud.net"
    }

    with open(CONFIG_PATH_FILE, "w") as file:
        config.write(file)


def is_configured():
    if path.exists(CONFIG_PATH_FILE):
        config = read_config_file()
        if config["DEFAULT"]:
            return True

    raise Exception("Запустите init")


def get_bucket() -> str:
    is_configured()
    return read_config_file().get("DEFAULT", "bucket")


def init():
    access_key = input("access key: ")
    secret_access_key = input("secret access key: ")
    bucket_name = input("bucket name: ")
    try:
        s3 = create_session(access_key, secret_access_key, DEFAULT_URL, DEFAULT_REGION)
        s3.create_bucket(Bucket=bucket_name, ACL='public-read-write')
    except ClientError as clientError:
        if clientError.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
            raise clientError

    create_config_file(access_key=access_key, secret_key=secret_access_key, bucket_name=bucket_name)


def verification_album(album: str):
    if album.count("/"):
        raise Exception("album cannot contain '/'")


def get_photo_path(album, image):
    return album + DELIMITER + image


def is_album_existed(session, bucket, album):
    list_objects = session.list_objects(
        Bucket=bucket,
        Prefix=album + DELIMITER,
        Delimiter=DELIMITER,
    )
    if "Contents" in list_objects:
        for _ in list_objects["Contents"]:
            return True
    return False


def is_photo_existed(session, bucket, album, photo):
    try:
        session.get_object(Bucket=bucket, Key=get_photo_path(album, photo))
    except ClientError as error:
        if error.response["Error"]["Code"] != "NoSuchKey":
            raise error
        return False
    return True
