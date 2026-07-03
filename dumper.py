import argparse
import base64
import html
from pathlib import Path
import re
import unicodedata
import urllib.request


SOURCE_URL = "https://circulate.neuma.studio/"
SOURCE_HTML = Path("source.html")
DUMP_FOLDER = Path("dumps")

PATCH_CALL_RE = re.compile(
    r"(?:sendPatchToCircuit|savePatchToCircuit)"
    r"\('(?P<title>.*?)',\s*atob\('(?P<patch>[A-Za-z0-9+/=]+)'\)"
)
INVALID_FILENAME_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def download_source(url, destination):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "circulate-dump/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        source = response.read()
    destination.write_bytes(source)
    return source.decode("utf-8")


def read_source(path):
    return path.read_text(encoding="utf-8")


def find_patches_in_html(html_source):
    patches = {}
    for match in PATCH_CALL_RE.finditer(html_source):
        title = html.unescape(match.group("title")).strip()
        encoded_patch = match.group("patch")
        patches.setdefault((title, encoded_patch), None)
    return [title_patch for title_patch in patches]


def decode_patch(encoded_patch):
    decoded_patch = base64.b64decode(encoded_patch, validate=True).decode("ascii")
    return bytes(int(byte_string) for byte_string in decoded_patch.split(","))


def filename_for_title(title):
    filename = unicodedata.normalize("NFKD", title)
    filename = filename.encode("ascii", "ignore").decode("ascii")
    filename = INVALID_FILENAME_CHARS_RE.sub("_", filename)
    filename = re.sub(r"\s+", "_", filename).strip(" ._")
    if not filename:
        filename = "patch"
    if filename.upper() in WINDOWS_RESERVED_NAMES:
        filename = f"{filename}_patch"
    return filename


def unique_output_path(folder, title, used_filenames):
    base_name = filename_for_title(title)
    candidate = f"{base_name}.syx"
    suffix = 2
    while candidate.lower() in used_filenames:
        candidate = f"{base_name}_{suffix}.syx"
        suffix += 1
    used_filenames.add(candidate.lower())
    return folder / candidate


def dump_patches(patches, folder):
    folder.mkdir(exist_ok=True)
    used_filenames = set()
    for title, encoded_patch in patches:
        patch_bytes = decode_patch(encoded_patch)
        output_path = unique_output_path(folder, title, used_filenames)
        output_path.write_bytes(patch_bytes)
        print(f"  {output_path.name}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Dump Novation Circuit patches from circulate.neuma.studio."
    )
    parser.add_argument("--url", default=SOURCE_URL)
    parser.add_argument("--source", type=Path, default=SOURCE_HTML)
    parser.add_argument("--output-dir", type=Path, default=DUMP_FOLDER)
    parser.add_argument(
        "--use-existing-source",
        action="store_true",
        help="Do not download the page again; parse the existing source file.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.use_existing_source:
        html_source = read_source(args.source)
    else:
        html_source = download_source(args.url, args.source)

    patches = find_patches_in_html(html_source)
    dump_patches(patches, args.output_dir)
    print(f"DUMPING FINISHED - {len(patches)} patches dumped")


if __name__ == "__main__":
    main()
