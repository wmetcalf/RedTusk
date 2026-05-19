/*
  LNK_AnsiOnly_LolBin / LNK_AnsiOnly_Executable
  ============================================

  Detects Windows .lnk shortcut files whose IDList ShellItem targets an
  executable via an ANSI-only (cp1252) name AND the BEEF0004 Unicode LFN
  extension is absent from the file. Modern Windows always writes a
  BEEF0004 block alongside the ANSI shortname for every FileSystem item.
  Its complete absence on an LNK whose target is an executable indicates
  a hand-crafted shortcut — the dominant shape of 2023-2025 phishing
  campaigns (cmd.exe/powershell.exe payloads via .url/.lnk).

  Encoding rationale
  ------------------
  YARA literal "cmd.exe\x00" is 8 contiguous bytes. UTF-16-encoded "cmd.exe"
  in the file is "c\0m\0d\0.\0e\0x\0e\0\0\0" (NUL-interleaved), so an ANSI
  literal cannot match UTF-16 content. The rules inherently fire only
  when the executable name lives as pure ANSI bytes — exactly the
  malformed shape.

  False-positive scope
  --------------------
  Condition `not $beef0004` is whole-file. A benign LNK that has BEEF0004
  somewhere (e.g. for an intermediate Windows shell folder item) but is
  ANSI-only at the leaf executable will NOT match. That's safer at the
  cost of some recall. Empirically this is rare since Windows writes
  BEEF0004 for every file item too.

  Rule selectivity (highest first)
  --------------------------------
    LNK_AnsiOnly_LolBin       — name matches a known LoLBin (tightest)
    LNK_AnsiOnly_Executable   — any *.exe/*.dll/*.scr/etc. (broader)

  Use both together for retrohunting; the LoLBin variant has the higher
  prior of being malicious in any hit.
*/

rule LNK_AnsiOnly_LolBin
{
    meta:
        author      = "wmetcalf + redtusk"
        description = "LNK targeting an ANSI-only LoLBin in IDList with no BEEF0004 anywhere — hand-crafted shape"
        date        = "2026-05-18"
        ref         = "WinShortcutParser idlist:target_ansi_only metadata field"
        severity    = "high"

    strings:
        $lnk_magic = { 4C 00 00 00 01 14 02 00 }
        $beef0004  = { 04 00 EF BE }

        $a_cmd         = "cmd.exe\x00"          nocase ascii
        $a_powershell  = "powershell.exe\x00"   nocase ascii
        $a_pwsh        = "pwsh.exe\x00"         nocase ascii
        $a_wscript     = "wscript.exe\x00"      nocase ascii
        $a_cscript     = "cscript.exe\x00"      nocase ascii
        $a_mshta       = "mshta.exe\x00"        nocase ascii
        $a_rundll32    = "rundll32.exe\x00"     nocase ascii
        $a_conhost     = "conhost.exe\x00"      nocase ascii
        $a_regsvr32    = "regsvr32.exe\x00"     nocase ascii
        $a_hh          = "hh.exe\x00"           nocase ascii
        $a_forfiles    = "forfiles.exe\x00"     nocase ascii
        $a_certutil    = "certutil.exe\x00"     nocase ascii
        $a_bitsadmin   = "bitsadmin.exe\x00"    nocase ascii
        $a_wmic        = "wmic.exe\x00"         nocase ascii
        $a_msbuild     = "msbuild.exe\x00"      nocase ascii
        $a_msiexec     = "msiexec.exe\x00"      nocase ascii
        $a_ie4uinit    = "ie4uinit.exe\x00"     nocase ascii
        $a_syncavps    = "syncappvpublishingserver.vbs\x00" nocase ascii
        $a_diskshadow  = "diskshadow.exe\x00"   nocase ascii
        $a_installutil = "installutil.exe\x00"  nocase ascii
        $a_control     = "control.exe\x00"      nocase ascii
        $a_msxsl       = "msxsl.exe\x00"        nocase ascii
        $a_regsvcs     = "regsvcs.exe\x00"      nocase ascii
        $a_regasm      = "regasm.exe\x00"       nocase ascii
        $a_msdt        = "msdt.exe\x00"         nocase ascii

    condition:
        $lnk_magic at 0
        and any of ($a_*)
        and not $beef0004
        and filesize > 100
}

rule LNK_AnsiOnly_Executable
{
    meta:
        author      = "wmetcalf + redtusk"
        description = "LNK targeting ANY ANSI-only executable in IDList with no BEEF0004 — hand-crafted shape, broader catch"
        date        = "2026-05-18"
        severity    = "medium"

    strings:
        $lnk_magic = { 4C 00 00 00 01 14 02 00 }
        $beef0004  = { 04 00 EF BE }
        // Regex: contiguous ASCII filename chars followed by an executable
        // extension and a NUL terminator. ANSI-only by construction — UTF-16
        // content has \x00 between every char and won't match this.
        $ansi_exe = /[A-Za-z0-9_.\\\-]{1,260}\.(exe|dll|scr|com|bat|cmd|ps1|vbs|js|jse|hta|wsf|msi|msp)\x00/ ascii nocase

    condition:
        $lnk_magic at 0
        and $ansi_exe
        and not $beef0004
        and filesize > 100
}
