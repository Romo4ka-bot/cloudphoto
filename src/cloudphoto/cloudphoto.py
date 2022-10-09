import sys

from commands import upload_photo, download_photo, list_img, list_albums, delete_photo, delete_album, create_site
from service import init_session
from service import init


def upload(session):
    params = {"album": None, "path": None}

    try:
        params[sys.argv[2][2:]] = sys.argv[3]
    except Exception as e:
        raise Exception("Не хватает параметров")

    try:
        params[sys.argv[4][2:]] = sys.argv[5]
    except Exception as e:
        pass

    if not params.get("album"):
        raise Exception("Введите параметр album")

    if params.get("album").find("/") != -1:
        raise Exception("Параметр album не может содержать символ /")

    upload_photo(session, params.get("album"), (params.get("path") if params.get("path") else "."))


def download(session):
    params = {"album": None, "path": None}

    try:
        params[sys.argv[2][2:]] = sys.argv[3]
    except Exception as e:
        raise Exception("Не хватает параметров")

    try:
        params[sys.argv[4][2:]] = sys.argv[5]
    except Exception as e:
        pass

    if not params.get("album"):
        raise Exception("Введите параметр album")

    download_photo(session, params.get("album"), params.get("path"))


def list_command(session):
    params = {
        "album": None,
    }

    try:
        params[sys.argv[2][2:]] = sys.argv[3]
    except Exception as e:
        pass
    list_img(session, params.get("album")) if params.get("album") else list_albums(session)


def delete(session):
    params = {"album": None, "photo": None}

    try:
        params[sys.argv[2][2:]] = sys.argv[3]
    except Exception as e:
        raise Exception("Не хватает параметров")

    try:
        params[sys.argv[4][2:]] = sys.argv[5]
    except Exception as e:
        pass

    if not params.get("album"):
        raise Exception("Введите параметр album")

    delete_photo(session, params.get("album"), params.get("photo")) if params.get("photo") else delete_album(session, params.get("album"))


def mksite(session):
    create_site(session)


def init_com():
    init()


COMMANDS_NAME_AND_FUNCTIONS = {
    "upload": upload,
    "download": download,
    "list": list_command,
    "delete": delete,
    "mksite": mksite,
    "init": init_com,
}


def main():
    sys.tracebacklimit = -1

    try:
        command = sys.argv[1]
    except Exception as e:
        raise Exception("Введите команду")

    function = COMMANDS_NAME_AND_FUNCTIONS.get(command)

    if function != init_com:
        session = init_session()
        function(session)
    else:
        function()


if __name__ == "__main__":
    main()
