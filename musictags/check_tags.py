import argparse
from functools import partial, reduce
import os
import os.path
import sys

import mutagen
from termcolor import colored, cprint


# Silently skip files ending with these strings
IGNORE_EXT = ["m3u", "jpg", "jpeg", "png", "nfo", "txt"]

# ID3 Frames
# as per id3 documentation, all checked frames must be unique
# (no multiple frames with same id)

# at least these frames, one in each cathegory, must be present
ID3_MANDATORY = [
    # title
    "TIT2",
    # artists
    ("TPE1", "TPE2", "TPE4"),
    # date
    ("TDOR", "TDRC", "TDRL"),
]

# if part of an album:
ID3_ALBUM = [
    ("TALB",),
    ("TRCK",),
]

# optional, but useful
ID3_USEFUL = ["TCON", "TSOP", "TSOT", "TOFN"]


def _info(message, color=None):
    cprint(message, color=color)


_detail = partial(_info, color="white")
_warn = partial(_info, color="yellow")
_error = partial(_info, color="red")
_debug = partial(_info, color="cyan")


def _list_get_first(l):
    return l[0] if len(l) > 0 else None


def id3_tags_presence(spec, tag):
    if tag is None:
        return 0
    score = 0
    for frames in spec:
        # need at least one from many
        if isinstance(frames, str):
            frames = (frames,)
        alternatives = [_list_get_first(tag.getall(frame)) for frame in frames]
        if any(alternatives):
            score += 1
    return score


def check_tags(filepath, verbose=False):
    """Checks music tags in given file. If file is not a known music format,
    exit silently."""
    audio = mutagen.File(filepath)
    if audio is None:
        _warn("[FILE] {} ... skipping (not recognized)".format(filepath))
        return
    if isinstance(audio.tags, mutagen.id3.ID3):
        if verbose:
            _info("[FILE] {}".format(filepath))
            _detail("\t" + audio.info.pprint())
            _detail("\t" + "id3 v{}".format(
                ".".join([str(i) for i in audio.tags.version])))
        # check for existing tag frames
        mandatory = id3_tags_presence(ID3_MANDATORY, audio.tags)
        album = id3_tags_presence(ID3_ALBUM, audio.tags)
        useful = id3_tags_presence(ID3_USEFUL, audio.tags)
        if verbose:
            _detail(
                "\tMandatory fields: {} of {}".format(
                    mandatory,
                    len(ID3_MANDATORY)))
            _detail(
                "\tAlbum fields: {} of {}".format(
                    album,
                    len(ID3_ALBUM)))
            _detail(
                "\tUseful fields: {} of {}".format(
                    useful,
                    len(ID3_USEFUL)))
        return (
            mandatory/len(ID3_MANDATORY),
            album/len(ID3_ALBUM),
            useful/len(ID3_USEFUL))
    else:
        _warn("[FILE] {} ... skipping (unsupported tag type)".format(filepath))


def _canonical_relpath(path):
    """Get a canonical path that is absolute if original path is also absolute, or
    a relative path if the original is relative"""
    return os.path.relpath(os.path.realpath(path), os.path.dirname(path))


def _split_path(path):
    if path == "":
        return ""
    init, last = os.path.split(path)
    return [c for c in _split_path(init)] + [last]


def _is_ignored_dir(dirpath):
    split_path = _split_path(dirpath)
    components = filter(
        lambda c: c not in (".", "..", "/", ""),
        split_path)
    return any(map(lambda s: s.startswith("."), components))


def _is_ignored_file(filepath):
    return os.path.basename(filepath).startswith(".") or any(
        map(filepath.lower().endswith, IGNORE_EXT))


def dir_expand(file_or_dir):
    """Generates paths to the file or the files in the provided directory,
    recursively"""
    path = _canonical_relpath(file_or_dir)
    if os.path.isfile(path):
        yield file_or_dir
    elif os.path.isdir(file_or_dir):
        for dirpath, dirs, files in os.walk(file_or_dir):
            if _is_ignored_dir(dirpath):
                continue
            yield (
                dirpath,
                [os.path.join(dirpath, f) for f in files
                 if not _is_ignored_file(f)])


def add_arrays(xs, ys):
    return [x+y for x, y in zip(xs, ys)]


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Given a music file or directory, recurisively check file names "
            "and tags for presennce and consistency."))
    parser.add_argument(
        "files_or_dirs", nargs="*", default=".",
        help="File/directory to check. Use current directory if not provided.")
    parser.add_argument(
        "--verbose", default=False, action="store_true",
        help="Be verbose")
    args = parser.parse_args()

    for file_or_dir in args.files_or_dirs:
        for dirpath, files in dir_expand(file_or_dir):
            _info("[DIR] {}".format(dirpath))
            file_scores = list(filter(None, [
                check_tags(filepath, verbose=args.verbose)
                for filepath in files]))
            n = len(file_scores)
            if n > 0:
                m, a, u = reduce(add_arrays, file_scores)
                mandatory = m/n
                album = a/n
                useful = u/n
                pretty = ", ".join(
                    colored("{:.2f}".format(x),
                            color="green" if x == 1.0 else "red")
                    for x in (mandatory, album, useful))
                _info("\tscore: " + pretty)
            elif len(files) == 0:
                if args.verbose:
                    _detail("\t<no music files>")
            else:
                _info("\tNo tags found.")


if __name__ == "__main__":
    sys.exit(main())
