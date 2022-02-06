# Mail-Backup

Mail-Backup stores your emails locally as eml files (as delivered by the server).
Eml-Files can be viewed at least with Thunderbird, even extracting attachments.


## Features

- Download emails via IMAP as eml files.
- Configure local storage paths and file names based on email attributes (like date).
- Handles duplicated backups.
- Limit/filter by "last days" number.

Tipp: You may search your emails with a desktop search app, like [Recoll](https://www.lesbonscomptes.com/recoll/).


## Disclaimer

- Tested only on Linux. There is no plan to support Windows, even though there should be only minor issues with path handling.
- Some (minimal) experience with the Linux command line and YAML files required!


## Start up

### Prepare python environment

```bash
git clone https://github.com/rosenloecher-it/mail-backup

cd mail-backup
virtualenv -p /usr/bin/python3 venv

# activate venv
source ./venv/bin/activate

# check python version >= 3.8
python --version

# install required packages
pip install -r requirements.txt
```

### Configuration

Prepare your own config file based on `./mail-backup.yaml.sample`.

```bash
# cd ... goto project dir
cp ./mail-backup.yaml.sample ./mail-backup.yaml
```

Edit your `mail-backup.yaml`. See comments there. Make sure your IMAP credentials are configured. The password may be set alternatively via command line. 

You may configure the storage path per email attributes. Available replacement tokens:
- Email time settings (not the download time): YEAR, MONTH, DAY, HOUR, MINUTE
- Common email settings: UID (IDs are only unique per folder), SUBJECT, TO1 (first receiver email), FROM (email, no name)

Example:
```
./downloaded/{YEAR}-{MONTH}/{YEAR}{MONTH}{DAY}-{HOUR}{MINUTE}-IN-{FROM}-{SUBJECT}-{UID}.eml
```
Gets to:
```
./downloaded/2021-04/20210401-1604-IN-no-reply.company.com-The.subject-123.eml
```
Not existing paths get created automatically. 

All attribute strings get preprocessed in a quite opinionated manner, e.g. UTF-8 characters and white space gets removed. "Fwd:", "Re:" in subjects are removed too.

The handling of already existing mails files can be configured. Just set `when_exists` in `imap_folders` (see [mail-backup.yaml.sample](./mail-backup.yaml.sample)). Available options: 
- `skip`: Skip the email backup if a file with the proposed name already exists. 
- `overwrite`: Overwrite the email backup if a file with the proposed name already exists.
- `compare`: Even by using the `UID`, there is no guarantee that different emails get different file names, so emails could get overwritten. 
  In `compare` mode existing files gets compared with downloaded email content and written with a postfixed path ("mail.eml" => "mail.2.eml"). 

With `last_days` in `imap_folders` you can limit the backup to the most recent emails (see [mail-backup.yaml.sample](./mail-backup.yaml.sample)).


### Run

```bash
# see command line options
./mail-backup.sh --help

./mail-backup.sh -c ./mail-backup.yaml
```

## Maintainer & License

MIT © [Raul Rosenlöcher](https://github.com/rosenloecher-it)

The code is available at [GitHub][home].

[home]: https://github.com/rosenloecher-it/mail-backup
