Benign regression archives from libarchive/libarchive, commit 686c6ac3142e16fb095d5f8aa8951f63cbe49b5e

Source: https://github.com/libarchive/libarchive/tree/686c6ac3142e16fb095d5f8aa8951f63cbe49b5e/libarchive/test
Names: test_read_format_rar5_{stored,unicode,encrypted,multiple_files}.rar.uu (uudecoded).
Upstream license: https://github.com/libarchive/libarchive/blob/686c6ac3142e16fb095d5f8aa8951f63cbe49b5e/COPYING

altstream_decoy_regular.rar, altstream_decoy_symlink.rar: hand-built RAR5 (2026-11-18 review of
RedTusk#67). Each holds an unlisted NTFS alternate stream (decoy bytes "harmless") ahead of
payload.exe ("MALWARE!", benign text) and a data-less symlink whose header claims payload.exe's
size, so a whole-archive `7zz x -so` stream matches the listing's total while shifting
payload.exe's bytes. Benign: no executable content.

truncated_member_{shuffle,swap,stored}.rar: hand-built stored RAR5 (2026-11-18 review of
RedTusk#67). A member stores fewer bytes than its listed Size, and later members' header CRCs
are chosen to match the windows they shift into, so a whole-archive `7zz x -so` stream that is
split by listed sizes publishes bytes under the wrong names. `7zz t` exits 2 on each. Benign.

emptylink_*.rar: hand-built RAR5 (2026-11-18 final review of RedTusk#67). An entry listed as a
regular file (empty link values) that is really a data-less hard link / file copy / symlink
(redirect record with an empty target, redirect type 0, or Unix symlink mode) passes `7zz t`
but writes 0 bytes under `x -so`; with CRC32-forged later members the stream shifts. Benign.
