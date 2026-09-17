"""
vault_to_drive.py
=================

Copy a Google Vault export straight into a Google Drive folder, WITHOUT
saving it to your own computer first.

How it works (plain English):
  1. Vault does not store exports in Drive. It stages them in Google
     "Cloud Storage" (a developer file-storage service). This script asks
     Vault where your export lives.
  2. It reads those files out of Cloud Storage and writes them into a
     Drive folder. The bytes travel Google-to-Google. When you run this in
     Google Colab or on a cloud machine, they never touch your laptop.

You can run this two ways:
  * In Google Colab (easiest, nothing to install). See README.md.
  * On any computer with Python 3.9+ and the packages in requirements.txt.

Nothing here is specific to one account. You provide your own Google Cloud
OAuth credentials (client_secret.json) the first time, and it remembers you
after that (token.json).
"""

import argparse
import os
import sys
import tempfile
from urllib.parse import urlparse, parse_qs

# Google auth + API client libraries. Installed via requirements.txt.
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# ---------------------------------------------------------------------------
# Settings you can change (or leave as-is and answer the prompts instead).
# ---------------------------------------------------------------------------

# The "permissions" we ask Google for. Read-only for Vault and Cloud Storage
# (we never change them); drive.file lets us create the folder and files we
# make, and nothing else in your Drive.
SCOPES = [
    "https://www.googleapis.com/auth/ediscovery.readonly",     # read Vault
    "https://www.googleapis.com/auth/devstorage.read_only",    # read Cloud Storage
    "https://www.googleapis.com/auth/drive.file",              # write to Drive
]

# Where we look for your downloaded OAuth credentials, and where we cache
# your login so you only sign in once.
CLIENT_SECRET_FILE = os.environ.get("CLIENT_SECRET_FILE", "client_secret.json")
TOKEN_FILE = os.environ.get("TOKEN_FILE", "token.json")

# How big a chunk we move at a time (8 MB). Bigger = fewer round trips but
# more memory. This default is a safe middle ground for large exports.
CHUNK_SIZE = 8 * 1024 * 1024


def _running_in_colab():
    """True when this is running inside a Google Colab notebook.

    We check several signals because when the notebook runs us with
    `!python vault_to_drive.py`, this is a separate process that can't see the
    Colab Python module directly. The environment variable and the /content
    folder are inherited by that process, so they're reliable.
    """
    return bool(
        "google.colab" in sys.modules
        or os.environ.get("COLAB_RELEASE_TAG")
        or os.environ.get("COLAB_GPU")
        or os.path.isdir("/content")
    )


def _sign_in_by_paste(flow):
    """Colab-friendly sign-in: show a link, you approve, you paste it back.

    Google turned off the old "copy this code" method in 2023, so instead we
    send you to a normal Google sign-in page. After you approve, your browser
    tries to open an address starting with http://localhost that WON'T load
    (that's expected and fine). Copy that whole address from the address bar
    and paste it here. It contains the one-time code we need.
    """
    # Loopback (http://localhost) is always allowed for a "Desktop app" OAuth
    # client, so this needs no extra setup in the Cloud Console.
    flow.redirect_uri = "http://localhost"
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")

    print("\n" + "=" * 70)
    print("STEP 1: Open this link in a new browser tab and sign in / approve:\n")
    print(auth_url)
    print(
        "\nSTEP 2: Your browser will then try to open a page starting with\n"
        "        http://localhost and show an error like 'can't be reached'.\n"
        "        THAT IS NORMAL. Copy the FULL address from the address bar."
    )
    print("=" * 70)
    pasted = input("\nPaste that full http://localhost... address here: ").strip()

    # Accept either the whole redirected URL or just the bare code.
    code = pasted
    if "code=" in pasted:
        code = parse_qs(urlparse(pasted).query).get("code", [pasted])[0]

    flow.fetch_token(code=code)
    return flow.credentials


def sign_in(force_paste=False):
    """Log in to Google and return credentials we can reuse.

    The first run needs one sign-in step. After that we reuse the saved token
    so you are not asked again (until it expires, when we refresh it).
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_FILE):
                raise SystemExit(
                    f"\nI can't find '{CLIENT_SECRET_FILE}'.\n"
                    "Follow steps 1-4 in README.md to download it from the "
                    "Google Cloud Console, then put it next to this script.\n"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            if force_paste or _running_in_colab():
                # In Colab there is no local browser we can hand off to, so we
                # use the copy-the-address method.
                creds = _sign_in_by_paste(flow)
            else:
                # On a normal computer this pops open your browser and captures
                # the response automatically.
                creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print("Signed in and saved your login to", TOKEN_FILE)

    return creds


def pick_export(vault, matter_id):
    """Show the exports inside a matter and let the user choose one."""
    print(f"\nLooking up exports in matter {matter_id} ...")
    exports = []
    page_token = None
    while True:
        resp = (
            vault.matters()
            .exports()
            .list(matterId=matter_id, pageToken=page_token)
            .execute()
        )
        exports.extend(resp.get("exports", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    if not exports:
        raise SystemExit(
            "\nThis matter has no exports yet.\n"
            "Create one in the Vault website first: open your matter, run a "
            "search, click Export, and wait for it to finish. Then run this "
            "script again.\n"
        )

    print("\nExports found:")
    for i, ex in enumerate(exports, start=1):
        status = ex.get("status", "UNKNOWN")
        print(f"  [{i}] {ex.get('name')}   (status: {status})")

    while True:
        choice = input("\nType the number of the export you want: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(exports):
            chosen = exports[int(choice) - 1]
            break
        print("Please type one of the numbers shown above.")

    if chosen.get("status") != "COMPLETED":
        print(
            f"\nHeads up: this export's status is '{chosen.get('status')}', not "
            "COMPLETED. If it isn't finished, wait and try again."
        )
    return chosen


def get_or_create_drive_folder(drive, folder_name):
    """Find a Drive folder by name, or make one, and return its ID."""
    safe_name = folder_name.replace("'", "\\'")
    query = (
        "mimeType='application/vnd.google-apps.folder' "
        f"and name='{safe_name}' and trashed=false"
    )
    hits = (
        drive.files()
        .list(q=query, fields="files(id,name)", pageSize=1)
        .execute()
        .get("files", [])
    )
    if hits:
        print(f"Using existing Drive folder '{folder_name}'.")
        return hits[0]["id"]

    folder = (
        drive.files()
        .create(
            body={
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            },
            fields="id",
        )
        .execute()
    )
    print(f"Created a new Drive folder '{folder_name}'.")
    return folder["id"]


def transfer_one_file(storage, drive, sink_file, drive_folder_id):
    """Move a single export file: Cloud Storage -> temp -> Drive.

    We download to a temporary file on THIS machine (the Colab/cloud VM, not
    your laptop), then upload it to Drive, then delete the temporary file. For
    big exports this is the most reliable approach and uses only scratch space
    on the cloud machine.
    """
    bucket = sink_file["bucketName"]
    object_name = sink_file["objectName"]
    # The object name looks like a path; the file's real name is the last part.
    file_name = object_name.split("/")[-1]

    print(f"\n-> {file_name}")

    # Step 1: download from Cloud Storage in chunks.
    request = storage.objects().get_media(bucket=bucket, object=object_name)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
        downloader = MediaIoBaseDownload(tmp, request, chunksize=CHUNK_SIZE)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"   downloading... {int(status.progress() * 100)}%", end="\r")
    print("   downloaded 100%          ")

    # Step 2: upload the temp file into the Drive folder (resumable = safe for
    # large files; it can pick up after a hiccup).
    try:
        media = MediaFileUpload(tmp_path, chunksize=CHUNK_SIZE, resumable=True)
        upload = drive.files().create(
            body={"name": file_name, "parents": [drive_folder_id]},
            media_body=media,
            fields="id,name",
        )
        response = None
        while response is None:
            status, response = upload.next_chunk()
            if status:
                print(f"   uploading to Drive... {int(status.progress() * 100)}%", end="\r")
        print("   uploaded to Drive 100%   ")
    finally:
        # Step 3: always clean up the scratch file.
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def main():
    parser = argparse.ArgumentParser(
        description="Copy a Google Vault export into a Google Drive folder."
    )
    parser.add_argument(
        "--matter-id",
        help="The Vault matter ID (the long code in the vault.google.com URL).",
    )
    parser.add_argument(
        "--drive-folder",
        help="Name of the Drive folder to put the files in (created if missing).",
    )
    parser.add_argument(
        "--paste-auth",
        action="store_true",
        help="Force the copy-the-address sign-in method (use if auto-detect fails).",
    )
    args = parser.parse_args()

    matter_id = args.matter_id or input("Paste your Vault matter ID: ").strip()
    drive_folder = (
        args.drive_folder
        or input("Name for the Drive folder [Vault Export]: ").strip()
        or "Vault Export"
    )

    creds = sign_in(force_paste=args.paste_auth)

    # Build the three service "clients" we talk to.
    vault = build("vault", "v1", credentials=creds)
    storage = build("storage", "v1", credentials=creds)
    drive = build("drive", "v3", credentials=creds)

    chosen = pick_export(vault, matter_id)
    sink = chosen.get("cloudStorageSink", {})
    files = sink.get("files", [])
    if not files:
        raise SystemExit(
            "That export has no files listed yet. If it just finished, wait a "
            "moment and run again."
        )

    folder_id = get_or_create_drive_folder(drive, drive_folder)

    print(f"\nTransferring {len(files)} file(s) into Drive folder '{drive_folder}'...")
    for sink_file in files:
        transfer_one_file(storage, drive, sink_file, folder_id)

    print(
        f"\nAll done! {len(files)} file(s) are now in your Drive folder "
        f"'{drive_folder}'. Nothing was saved to your own computer."
    )


if __name__ == "__main__":
    main()
