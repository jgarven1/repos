# Google Vault export → Google Drive (no laptop download)

This little tool copies a **Google Vault** export straight into a **Google
Drive** folder. The files travel from one Google service to another and never
land on your own computer.

## Why this needs a few setup steps

A quick bit of background so the steps make sense:

- **Google Vault** is Google's tool for saving and searching a company's old
  email and files. When you "export" from Vault, it does **not** drop the files
  in Drive. It puts them in **Google Cloud Storage**, a separate file-storage
  service that developers use.
- Drive and Cloud Storage are two different systems, so there is no single
  "copy to Drive" button. Our program reads the files out of Cloud Storage and
  writes them into Drive for you.
- To let a program do that on your behalf, Google makes you create a
  **credential** (a kind of ID badge for your script). That's most of the
  setup below. You only do it once.

**Jargon, once:**
- *API* = a way for programs (not humans clicking) to talk to a service.
- *Google Cloud project* = a container where you turn APIs on and make credentials.
- *OAuth credential / client_secret.json* = the ID badge your script uses to log in as you.
- *Scope* = a specific permission, like "read Vault" or "write to Drive".

---

## The easiest way to run it: Google Colab

**Colab** is a free Google website that runs Python code in your browser on a
Google machine. Because it runs on Google's computer, "not saving to your
laptop" happens automatically.

You'll do two things: (A) a one-time setup in the Google Cloud Console to get
your ID badge, then (B) run the notebook.

---

## Part A — one-time setup (about 10 minutes)

You need to be a **Vault admin** (someone allowed to use Vault) for this to
work. If you can open the matter in vault.google.com, you're probably fine.

### Step 1: Open the Google Cloud Console and pick/create a project
1. Go to **https://console.cloud.google.com**.
2. At the top, click the project dropdown, then **New Project**. Name it
   anything (e.g. `vault-to-drive`) and click **Create**.
3. Make sure that new project is selected in the top dropdown before moving on.

### Step 2: Turn on the three APIs you need
For each of these, go to the link, make sure your project is selected, and
click **Enable**:
1. **Google Vault API** → https://console.cloud.google.com/apis/library/vault.googleapis.com
2. **Cloud Storage API** → https://console.cloud.google.com/apis/library/storage.googleapis.com
3. **Google Drive API** → https://console.cloud.google.com/apis/library/drive.googleapis.com

### Step 3: Set up the consent screen (who is allowed to log in)
1. Go to **https://console.cloud.google.com/apis/credentials/consent**.
2. Choose **Internal** if it's offered (that's simplest for a Workspace
   account). If only **External** is available, pick that.
3. Fill in an app name (e.g. `Vault to Drive`) and your email where asked.
   Click through **Save and Continue** on each page.
4. If you picked **External**, find the **Test users** section and add your own
   Google email as a test user. (This lets *you* use it without a full review.)

### Step 4: Make your ID badge (OAuth client) and download it
1. Go to **https://console.cloud.google.com/apis/credentials**.
2. Click **Create Credentials** → **OAuth client ID**.
3. For **Application type**, choose **Desktop app**. Give it any name.
4. Click **Create**, then **Download JSON**.
5. Rename the downloaded file to exactly **`client_secret.json`**. Keep it
   somewhere safe. This file is your login badge, so don't share it or commit
   it to GitHub.

You're done with setup. 🎉

---

## Part B — run it in Colab (about 5 minutes)

### Step 5: Open a new Colab notebook
1. Go to **https://colab.research.google.com** and click **New notebook**.
   (Or upload the `vault_to_drive.ipynb` file from this folder: **File →
   Upload notebook**.)

### Step 6: Install the libraries
Paste this into the first cell and press the ▶ play button:
```python
!pip install -q google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
```

### Step 7: Upload your badge and the program
In a new cell, run this, then use the **Choose Files** button to upload BOTH
`client_secret.json` and `vault_to_drive.py`:
```python
from google.colab import files
files.upload()
```

### Step 8: Run the transfer
In a new cell, paste this. Replace the matter ID with yours if it's different,
then press ▶:
```python
!python vault_to_drive.py \
    --matter-id 3cf11af8-e562-40a7-af21-0de0dd0db91a \
    --drive-folder "Vault Export"
```

### Step 9: Sign in (the copy-the-address method)
The first time you run it, it prints a **sign-in link**. Here's exactly what to do:
1. **Copy the link** it prints and open it in a **new browser tab**.
2. Choose your Google account and click **Allow** to approve the permissions.
   - If you see a warning that the app "isn't verified," click **Advanced**,
     then **Go to (your app name)**. This is safe: it's your own app that you
     created in Part A.
3. Your browser will then try to open a page that starts with
   **`http://localhost`** and show an error like **"This site can't be
   reached."** *This is normal and expected.* Nothing is broken.
4. **Copy the entire address** from your browser's address bar (it looks like
   `http://localhost/?code=4/0Ab...&scope=...`).
5. Go back to the Colab cell and **paste that whole address** where it asks,
   then press Enter.

### Step 10: Pick your export(s) and wait
- It lists the exports in your matter, each with a number.
- You can pick **one or many**:
  - a single one: `2`
  - several: `1,3,4`
  - a range: `2-5`
  - everything: type `all`
- If you pick more than one, each export gets its **own subfolder** inside your
  Drive folder, so nothing gets mixed up or overwritten.
- Watch the download/upload progress. When it says **All done!**, open Drive
  and look for the **Vault Export** folder.

That's it. The files went from Vault's storage into your Drive without ever
being saved on your computer.

---

## Important: create the export in Vault first

This tool copies an export that **already exists**. If your matter has none
yet, make one first:
1. Open your matter at **vault.google.com**.
2. Run a search (pick the accounts / date range you want).
3. Click **Export**, then wait. Big exports can take minutes to hours.
4. Once it shows as finished, run this tool and it will appear in the list.

---

## Running it on your own computer instead (optional)

If you'd rather not use Colab, you can run it locally. The download still
streams through Google's libraries, and if you'd like to avoid your disk
entirely, run it on a cheap cloud VM instead of your laptop.

```bash
cd vault_to_drive
pip install -r requirements.txt
# Put client_secret.json in this folder, then:
python vault_to_drive.py --matter-id 3cf11af8-e562-40a7-af21-0de0dd0db91a --drive-folder "Vault Export"
```

---

## If something goes wrong

- **"I can't find client_secret.json"** → You didn't upload it (Step 7) or it's
  named differently. It must be exactly `client_secret.json`.
- **"Access blocked: Authorization Error ... response_type is missing"** →
  This is the old sign-in method that Google turned off. The current version of
  the tool uses the copy-the-address method in Step 9 instead, so make sure
  you're running the latest `vault_to_drive.py`. If it still tries the wrong
  way, add `--paste-auth` to the command in Step 8 to force the new method.
- **"Access blocked" / "app not verified"** → Add your email as a **Test user**
  in Step 3, or use the **Internal** consent option. On the warning page, click
  **Advanced → Go to (your app)**; it's your own app, so it's safe.
- **The `http://localhost` page won't load** → That's expected. You don't need
  it to load. Just copy the address from the address bar and paste it back.
- **"insufficient permission" or 403** → The account you signed in with isn't a
  Vault admin, or one of the three APIs in Step 2 isn't enabled.
- **The export list is empty** → Create and finish an export in Vault first
  (see the section above).
- **Colab disconnected on a huge export** → Colab sessions time out when idle.
  Keep the tab active, or run it on a cloud VM for very large exports.

## A note on safety

- `client_secret.json` and `token.json` are like keys to your account. Never
  commit them to GitHub or share them. They are already covered by the
  `.gitignore` in this folder.
- This tool only ever **reads** Vault and Cloud Storage, and only **creates**
  new files in Drive. It cannot change or delete your Vault data.
