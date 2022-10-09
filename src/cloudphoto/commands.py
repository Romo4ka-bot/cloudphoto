import logging
import os
import random
import shutil
import string
from pathlib import Path

from jinja2 import Template

import templates
from service import DELIMITER, is_album_existed
from service import ROOT_PATH_DIRECTORY
from service import verification_album
from service import get_bucket
from service import is_photo_existed, get_photo_path

IMG_EXT = [".jpg", ".jpeg", ".png", ".gif"]
CONFIG = {
    "ErrorDocument": {"Key": "error.html"},
    "IndexDocument": {"Suffix": "index.html"},
}

def delete_photo(session, album: str, photo: str):
    photo_path = get_photo_path(album, photo)
    bucket = get_bucket()

    if not is_album_existed(session, bucket, album):
        raise Exception("Альбом не существует")

    if not is_photo_existed(session, bucket, album, photo):
        raise Exception("Фотографии не существует")

    session.delete_objects(
        Bucket=bucket, Delete={"Objects": [{"Key": photo_path}]}
    )


def get_all_photo_paths(session, bucket: str, album: str):
    list_objects = session.list_objects(
        Bucket=bucket,
        Prefix=album + DELIMITER,
        Delimiter=DELIMITER,
    )["Contents"]
    return [{"Key": photo_path.get('Key')} for photo_path in list_objects]


def delete_album(session, album: str):
    bucket = get_bucket()

    if not is_album_existed(session, bucket, album):
        raise Exception("Альбом не существует")

    photo_paths = get_all_photo_paths(session, bucket, album)

    session.delete_objects(Bucket=bucket, Delete={"Objects": photo_paths})


def download_photo(session, album: str, path: str):
    path = Path(path)
    bucket = get_bucket()
    if not is_album_existed(session, bucket, album):
        raise Exception("Альбом не существует")

    if not path.is_dir():
        raise Exception(f"{str(path)} не папка")

    list_object = session.list_objects(Bucket=bucket, Prefix=album + DELIMITER, Delimiter=DELIMITER)
    for key in list_object["Contents"]:
        obj = session.get_object(Bucket=bucket, Key=key["Key"])
        filename = Path(key['Key']).name

        filepath = path / filename
        with filepath.open("wb") as file:
            file.write(obj["Body"].read())


def list_img(session, album):
    bucket = get_bucket()

    if not is_album_existed(session, bucket, album):
        raise Exception(f"Альбом '{album}' не существует")

    list_objects = session.list_objects(
        Bucket=bucket,
        Prefix=album + DELIMITER,
        Delimiter=DELIMITER
    )
    photos = []
    for key in list_objects["Contents"]:
        photos.append(Path(key["Key"]).name)

    if not len(photos):
        raise Exception("Нет картинок")

    print(f"Фотографии в альбоме {album}:")
    for photo_name in photos:
        print(f"# {photo_name}")


def list_albums(session):
    bucket = get_bucket()
    list_objects = session.list_objects(Bucket=bucket)
    albums = set()
    if "Contents" in list_objects:
        for key in list_objects["Contents"]:
            albums.add(Path(key["Key"]).parent)

    if not len(albums):
        raise Exception(f"В {bucket} нет альбомов")

    print(f"Albums in bucket {bucket}:")
    for album in albums:
        print(f"# {album}")


def get_albums_data(session, bucket: str):
    albums = {}
    list_objects = session.list_objects(Bucket=bucket)
    for key in list_objects["Contents"]:
        album_img = key["Key"].split("/")
        if len(album_img) != 2:
            continue
        album, img = album_img
        if album in albums:
            albums[album].append(img)
        else:
            albums[album] = [img]

    return albums


def save_template(template) -> str:
    filename = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) + ".html"
    path = Path(ROOT_PATH_DIRECTORY) / "temp" / filename
    if not path.parent.exists():
        os.mkdir(path.parent)

    with open(path, "w") as file:
        file.write(template)

    return str(path)


def remove_directory():
    path = Path(ROOT_PATH_DIRECTORY) / "temp"
    shutil.rmtree(path)


def create_site(session):
    bucket = get_bucket()
    url = f"https://{bucket}.website.yandexcloud.net"
    albums = get_albums_data(session, bucket)

    template = templates.album

    albums_rendered = []
    i = 1
    for album, photos in albums.items():
        template_name = f"album{i}.html"
        rendered_album = Template(template).render(album=album, images=photos, url=url)
        path = save_template(rendered_album)

        session.upload_file(path, bucket, template_name)
        albums_rendered.append({"name": template_name, "album": album})
        i += 1

    template = templates.index
    rendered_index = Template(template).render(template_objects=albums_rendered)
    path = save_template(rendered_index)
    session.upload_file(path, bucket, "index.html")

    template = templates.error
    path = save_template(template)
    session.upload_file(path, bucket, "error.html")

    session.put_bucket_website(Bucket=bucket, WebsiteConfiguration=CONFIG)

    remove_directory()

    print(url)


def is_photo(file):
    return file.is_file() and file.suffix in IMG_EXT


def upload_photo(session, album: str, path: str):
    path = Path(path)
    verification_album(album)
    count = 0

    if not path.is_dir():
        raise Exception(f"{str(path)} папка не существует")

    for file in path.iterdir():
        if is_photo(file):
            try:
                print(f"{file.name} картинка загружается...")
                key = f"{album}/{file.name}"
                session.upload_file(str(file), get_bucket(), key)
                count += 1
            except Exception as ex:
                logging.warning(ex)

    if not count:
        raise Exception(f"В указанной папке нет изображений с расширениями, разрешенных: {IMG_EXT}")
