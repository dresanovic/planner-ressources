# FS-020 Independent iCalendar Validator Toolchain

## Pinned validator

- Tool: iCal4j Command
- Distribution version: `0.1.1-develop-SNAPSHOT`
- Embedded iCal4j version: `4.0.0-rc6`
- Official distribution URL: `https://files.ical4j.org/releases/ical4j-0.1.1-develop-SNAPSHOT.zip`
- SHA-256: `45aee44d1bea6146b43eeb7c88411a430808d58d9a4731b98078206912a7e469`
- Verified JVM: OpenJDK Corretto `21.0.12`

The upstream download URL is mutable by name, so the checksum is mandatory. A different checksum is a different validator input and must not be used for FS-020 acceptance without updating this pin and regenerating validation evidence.

## Installation and checksum verification

```powershell
Invoke-WebRequest -Uri 'https://files.ical4j.org/releases/ical4j-0.1.1-develop-SNAPSHOT.zip' -OutFile 'ical4j-0.1.1-develop-SNAPSHOT.zip'
$actual = (Get-FileHash -LiteralPath 'ical4j-0.1.1-develop-SNAPSHOT.zip' -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne '45aee44d1bea6146b43eeb7c88411a430808d58d9a4731b98078206912a7e469') { throw 'iCal4j checksum mismatch' }
Expand-Archive -LiteralPath 'ical4j-0.1.1-develop-SNAPSHOT.zip' -DestinationPath 'ical4j-tool'
& 'ical4j-tool/ical4j-0.1.1-develop-SNAPSHOT/bin/ical4j.bat' --version
```

Expected version output:

```text
iCal4j Command 0.1.1-develop-SNAPSHOT (ical4j=4.0.0-rc6, jvm=21.0.12)
```

## Validation command

```powershell
& 'ical4j-tool/ical4j-0.1.1-develop-SNAPSHOT/bin/ical4j.bat' calendar validator -file='<fixture.ics>'
```

The packaged command is `calendar validator`. The upstream guide currently shows `calendar validate`, but that token is not a subcommand in this pinned distribution; its own `--help` output is authoritative for the retained command evidence.
