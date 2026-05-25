# RedTusk Metadata Field Registry

Combined static + runtime inventory. Generated 2026-05-25T07:31:00.785503+00:00.

- **4674** total fields seen across sources
- **276** declared + observed (the healthy core)
- **488** declared but not observed (rare formats / unwalked code paths)
- **79** observed undeclared string literals (migration targets)
- **0** observed but no source trace (investigation queue)

## Field index

| Field | Status | Type | Declared in | Observed in (top 3 MIMEs) |
|---|---|---|---|---|
| `(?i:.*APPLICABLE\sDOCUMENTS|REFERENCE|STANDARD|REQUIREMENT|GUIDELINE|COMPLIANCE.*)` | declared,not-observed | `String` | `StandardsText` | _-_ |
| `([A-Za-z][A-Za-z0-9+.-]{1,120}:[A-Za-z0-9/](([A-Za-z0-9$_.+!*,;/?:@&~=-])|%[A-Fa-f0-9]{2}){1,333}(#([a-zA-Z0-9][a-zA-Z0-9$_.+!*,;/?:@&~=%-]{0,1000}))?)` | declared,not-observed | `String` | `RegexUtils` | _-_ |
| `([^\c\(\)<>@,;:\\"/\[\]\?=\s]+)` | declared,not-observed | `String` | `MediaType` | _-_ |
| `(\s(?i:Publication|Standard))` | declared,not-observed | `String` | `StandardsText` | _-_ |
| `Abstract` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `AccessContraints ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Address` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Affiliation` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Authors` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `AvgCharacterWidth` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `CharacterSet` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `CitationDate ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `CitedResponsiblePartyEMail ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `CitedResponsiblePartyName ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `CitedResponsiblePartyOrganizationName ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `CitedResponsiblePartyPositionName ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `CitedResponsiblePartyRole ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Class` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ContactPartyName-` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ContactRole` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Content-Disposition` | declared,observed | `String` | `HttpHeaders` | `application/gzip`, `application/msword`, `application/pdf` |
| `Content-Encoding` | declared,observed | `String` | `HttpHeaders` | `application/json`, `application/mbox`, `application/pdf` |
| `Content-Language` | declared,observed | `String` | `HttpHeaders` | `application/xhtml+xml`, `text/html` |
| `Content-Length` | declared,observed | `String` | `HttpHeaders` | `application/msword`, `application/octet-stream`, `application/pdf` |
| `Content-Location` | declared,observed | `String` | `HttpHeaders` | `text/html` |
| `Content-Type` | declared,not-observed | `String` | `HttpHeaders` | _-_ |
| `Content-Type-Hint` | declared,observed | `internalText` | `TikaCoreProperties` | `application/xhtml+xml`, `text/html` |
| `Content-Type-Magic-Detected` | declared,observed | `internalText` | `TikaCoreProperties` | `application/gzip`, `application/illustrator`, `application/java-archive` |
| `Content-Type-Override` | declared,not-observed | `internalText` | `TikaCoreProperties` | _-_ |
| `Content-Type-Parser-Override` | declared,observed | `internalText` | `TikaCoreProperties` | `message/rfc822` |
| `Copyright` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `DATE` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `DateInfo ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `DistributionFormatSpecificationAlternativeTitle ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Distributor Contact ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Distributor Organization Name ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `DocVersion` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Error` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ExploitClass` | undeclared-literal,observed | `-` | `-` | `application/x-msc`, `application/x-mswinurl`, `application/x-rdp` |
| `File-Parsed` | declared,not-observed | `String` | `TSDParser` | _-_ |
| `File-Parsed-DateTime` | declared,not-observed | `String` | `TSDParser` | _-_ |
| `File-Type-Description` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FileOwner` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FileOwnerGroup` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FilePermissions` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FileSize` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Filename` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FontFamilyName` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FontFullName` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FontName` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FontNotice` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FontSubFamilyName` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FontUnderlineThickness` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FontVersion` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FontWeight` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FullAffiliations` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `GeographicIdentifierAuthorityAlternativeTitle ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `GeographicIdentifierAuthorityDate ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `GeographicIdentifierAuthorityTitle ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `GeographicIdentifierCode ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Geographic_LATITUDE` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Geographic_LONGITUDE` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Geographic_NAME` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `HP-UX` | declared,not-observed | `String` | `MachineMetadata` | _-_ |
| `ICBM` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ICC:AToB 0` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:AToB 1` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:AToB 2` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Apple Multi-language Profile Name` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:BToA 0` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:BToA 1` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:BToA 2` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Blue Colorant` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Blue TRC` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:CMM Type` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Char Target` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Chromatic Adaptation` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Chromaticity` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Class` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Color space` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Device Mfg Description` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Device Model Description` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Device manufacturer` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Device model` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Gamut` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Gray TRC` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Green Colorant` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Green TRC` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Luminance` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Measurement` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Media Black Point` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Media White Point` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Primary Platform` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Profile Connection Space` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Profile Copyright` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Profile Date/Time` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Profile Description` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Profile Size` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Red Colorant` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Red TRC` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Rendering Intent` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Signature` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Tag Count` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Technology` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Unknown tag (0x61617079)` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Unknown tag (0x63696370)` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Version` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Viewing Conditions` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Viewing Conditions Description` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:XYZ values` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `Icon count` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Icon details` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `IdentificationInfoAbstract ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `IdentificationInfoCitationTitle ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `IdentificationInfoLanguage-->` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `IdentificationInfoStatus ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `IdentificationInfoTopicCategory-->` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Iptc4xmpCore:CiAdrCity` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpCore:CiAdrCtry` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpCore:CiAdrExtadr` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpCore:CiAdrPcode` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpCore:CiAdrRegion` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpCore:CiEmailWork` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpCore:CiTelWork` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpCore:CiUrlWork` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpCore:CountryCode` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpCore:CreatorContactInfo` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpCore:IntellectualGenre` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpCore:Location` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpCore:Scene` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpCore:SubjectCode` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:AOCopyrightNotice` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:AOCreator` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:AODateCreated` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:AOSource` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:AOSourceInvNo` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:AOTitle` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:AddlModelInfo` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpExt:ArtworkOrObject` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:CVterm` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:DigImageGUID` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpExt:DigitalSourceType` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpExt:DigitalSourcefileType` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpExt:Event` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpExt:IptcLastEdited` | declared,not-observed | `internalDate` | `IPTC` | _-_ |
| `Iptc4xmpExt:LocationCreated` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:LocationCreatedCity` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpExt:LocationCreatedCountryCode` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpExt:LocationCreatedCountryName` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpExt:LocationCreatedProvinceState` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpExt:LocationCreatedSublocation` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpExt:LocationCreatedWorldRegion` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `Iptc4xmpExt:LocationShown` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:LocationShownCity` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:LocationShownCountryCode` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:LocationShownCountryName` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:LocationShownProvinceState` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:LocationShownSublocation` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:LocationShownWorldRegion` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:MaxAvailHeight` | declared,not-observed | `internalInteger` | `IPTC` | _-_ |
| `Iptc4xmpExt:MaxAvailWidth` | declared,not-observed | `internalInteger` | `IPTC` | _-_ |
| `Iptc4xmpExt:ModelAge` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:OrganisationInImageCode` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:OrganisationInImageName` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:PersonInImage` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:RegItemId` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:RegOrgId` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Iptc4xmpExt:RegistryId` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `Keyword` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Language` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `LastModifiedDate` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `License-Location` | declared,not-observed | `String` | `CreativeCommons` | _-_ |
| `License-Url` | declared,not-observed | `String` | `CreativeCommons` | _-_ |
| `LoC` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Masked icon count` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Masked icon details` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `MasterPageCount` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `MasterSpreadPageCount` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `MboxParser-accept-language` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-authentication-results` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-authentication-results-original` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-content-language` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-content-transfer-encoding` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-delivered-to` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-dkim-filter` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-dkim-signature` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-dmarc-filter` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-from` | undeclared-literal,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-mime-version` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-organization` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-original-recipient` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-received` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-received-spf` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-references` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-reply-to` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-resent-from` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-return-path` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-spamdiagnosticmetadata` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-spamdiagnosticoutput` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-thread-index` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-thread-topic` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-account-key` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-antiabuse` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-authority-reason` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-auto-response-suppress` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-bwhitelist` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-crosspremisesheadersfiltered` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-crosspremisesheaderspromoted` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-email-count` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-eopattributedmessage` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-exchange-antispam-report-cfa-test` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-exchange-antispam-report-test` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-exim-id` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-forefront-antispam-report` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-forefront-antispam-report-untrusted` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-forefront-prvs` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ipas-result` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ironport-anti-spam-filtered` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ironport-anti-spam-result` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ironport-av` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-local-domain` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-microsoft-antispam` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-microsoft-antispam-mailbox-delivery` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-microsoft-antispam-message-info` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-microsoft-antispam-prvs` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-microsoft-antispam-untrusted` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-microsoft-exchange-diagnostics` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-microsoft-exchange-diagnostics-untrusted` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-mimeole` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-mozilla-keys` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-mozilla-status` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-mozilla-status2` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-crosstenant-fromentityheader` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-crosstenant-id` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-crosstenant-network-message-id` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-crosstenant-originalarrivaltime` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-crosstenant-originalattributedtenantconnectingip` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-organization-authas` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-organization-authmechanism` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-organization-authsource` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-organization-avstamp-mailbox` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-organization-expirationinterval` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-organization-expirationintervalreason` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-organization-expirationstarttime` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-organization-expirationstarttimereason` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-organization-messagedirectionality` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-organization-network-message-id` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-organization-scl` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-processed-by-bccfoldering` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-transport-crosstenantheadersstamped` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-transport-crosstenantheadersstripped` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-transport-endtoendlatency` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-office365-filtering-correlation-id` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-publictraffictype` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-traffictypediagnostic` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-msmail-priority` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-organizationheaderspreserved` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-original-to` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-originating-ip` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-originatororg` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-priority` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-received` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-sbrs` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-source` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-source-args` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-source-auth` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-source-cap` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-source-dir` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-source-ip` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-source-l` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-source-sender` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-tm-as-gconf` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-tm-as-product-ver` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-tm-as-url-rewrite` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-tm-deliver-signature` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-tm-received-spf` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-tmase-matchedrid` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-tmase-result` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-tmase-snap-result` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-tmase-version` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-uidl` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-virus-scanned` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-wi-port` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message-Bcc` | declared,observed | `String` | `Message` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message-Cc` | declared,observed | `String` | `Message` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message-From` | declared,observed | `String` | `Message` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message-Recipient-Address` | declared,observed | `String` | `Message` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message-To` | declared,observed | `String` | `Message` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:BCC-Display-Name` | declared,not-observed | `internalTextBag` | `Message` | _-_ |
| `Message:BCC-Email` | declared,not-observed | `internalTextBag` | `Message` | _-_ |
| `Message:BCC-Name` | declared,not-observed | `internalTextBag` | `Message` | _-_ |
| `Message:CC-Display-Name` | declared,observed | `internalTextBag` | `Message` | `application/vnd.ms-outlook` |
| `Message:CC-Email` | declared,observed | `internalTextBag` | `Message` | `application/vnd.ms-outlook` |
| `Message:CC-Name` | declared,observed | `internalTextBag` | `Message` | `application/vnd.ms-outlook` |
| `Message:From-Email` | declared,observed | `internalTextBag` | `Message` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:From-Name` | declared,observed | `internalTextBag` | `Message` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:--0-1107789460-1150005065=` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:070700018);DIR` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:146.namprd18.prod.outlook.com;PTR` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:2025-04-30T04` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:2025-06-14T21` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:2025-08-23T15` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:2025-10-04T22` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:2025-12-05T07` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:</s` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:<faultcode>s` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:<geso@dd7.jp>` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:<mailto` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:<s` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:<sarra.rassaa@ctaa.com.tn>` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:>>6;;>111;73<52@77C856865=8CD9@<;9><4>C;D@BA>96AC55>8C5R487@@>>7<75689<BB@>6535>B;8q9I=A?@-95@@?6<;A@73B7B37@?2CF>@@<=7=<6>AB` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:@9=*)738<463;=?.27?>>?0,,9CECE@,#,5?20` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:A<'1]-@22-@@OVD0B6;?FC` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:A?C>7?>DBA>?CB@?>2DBAC@??BKNLBF>4@BM>CCJDAH?DHA>E;@UB@@?G?@@JJ@5CCH>DF?K2BA@!>>2LBOC@C@D?FBDD?@A@?>A>>'A>B9?H<CIA?BEDA?6E?N?BE` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:A?F13>@ADC?@@CA5>AC?BD?8A@MEIGE;%?>U?=FA>` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:ABIs` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:AMQ-Delivery-Message-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:ARC-Authentication-Results` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:ARC-Message-Signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:ARC-Seal` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Accept-Language` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Action` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Arc-Authentication-Results` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Arc-Message-Signature` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Arc-Seal` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Archiver-Version` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Arrival-Date` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Atlassian-Build-Date` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Authentication-Results` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Authentication-Results-Original` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Authentication-results` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Author` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Author-email` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Auto-Submitted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Autocrypt` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:BIMI-Selector` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Barcode.........` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Bcc` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Bnd-LastModified` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Board` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Body` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Brand` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Build-Jdk` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Built-By` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Bundle-Description` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Bundle-DocURL` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Bundle-ManifestVersion` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Bundle-Name` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Bundle-SymbolicName` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Bundle-Vendor` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Bundle-Version` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:BypassFocusedInbox` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:CC` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:CallID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Cc` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Class-Path` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Classifier` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Code` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Comment` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Connection` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Content-Class` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Content-Description` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Content-Disposition` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Content-ID` | templated,observed | `-` | `-` | `application/pdf`, `application/vnd.ms-excel`, `application/vnd.ms-htmlhelp` |
| `Message:Raw-Header:Content-Language` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Content-Length` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Content-Location` | templated,observed | `-` | `-` | `application/x-msdownload`, `application/xhtml+xml`, `application/xml` |
| `Message:Raw-Header:Content-Transfer-Encoding` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Content-Type` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Content-disposition` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Content-language` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Content-transfer-encoding` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Content-type` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Contents........` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Created-By` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Custom-Header-ClaycoIT` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:DEADLINE` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:DKIM-Filter` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:DKIM-RESULT` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:DKIM-Signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:DKIMCheck` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:DMARC-Filter` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Date` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Delivered-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Delivery-date` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Description-Content-Type` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Device` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Diagnostic-Code` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Disposition-Notification-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Dkim-Signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:DomainKey-Signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Duration` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Dynamic` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:DynamicImport-Package` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Edition.........` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Encoding` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Envelope-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Envelope-to` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Errors-To` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:ExtraHeaders00001` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:FMLAT` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:FMLCorePlugin` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:FMLCorePluginContainsFMLMod` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Feedback-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Feedback-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Final-Recipient` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:ForceLoadAsMod` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Forward-Confirmed-ReverseDNS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:From` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Genre...........` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:HEADER` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Hardware` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Headers` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Home-page` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Hostname` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Import-Package` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Importance` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:In-Reply-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:In-reply-to` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:IronPort-Data` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:IronPort-HdrOrdr` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:IronPort-PHdr` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:IronPort-SDR` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Ironport-Data` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Ironport-Hdrordr` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Ironport-Phdr` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Ironport-Sdr` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Keywords` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Language........` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Last-Modified` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:License` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:License-Expression` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:License-File` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:List-Archive` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:List-Help` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:List-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:List-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:List-Post` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:List-Subscribe` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:List-Unsubscribe` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:List-Unsubscribe-Post` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:MIME-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822`, `multipart/related` |
| `Message:Raw-Header:MIME-version` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Mail-Reply-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Mailing-list` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Manifest-Version` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Message` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Message-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Message-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Message-id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:MessageID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Metadata-Version` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Method` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Microsoft.exchange.rmsapaagent.protectiontemplateid` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Mime-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:MixinConfigs` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Name` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Organization` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Original-recipient` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:P?Return-Path` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:PP-Correlation-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Platform` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Platform........` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Precedence` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Priority` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Project-URL` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Protection......` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Protocol` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Provides-Extra` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Queue-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Received` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Received-SPF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Received-Spf` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:References` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Reply-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Reply-to` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Reporting-MTA` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Require-Capability` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Require-Recipient-Valid-Since` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Requires-Dist` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Requires-Python` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Resent-From` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Return-Path` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Return-Receipt-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Return-path` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:ReverseDNS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:SHA-256-Digest-Manifest` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:SHA1-Digest-Manifest` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:SPFCheck` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Sensitivity` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Sent` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Signature-Version` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Snapshot-Content-Location` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:SpamDiagnosticMetadata` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:SpamDiagnosticOutput` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:SpamTally` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Subject` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Summary` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Sun-Java-System-SMTP-Warning` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Thread-Index` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Thread-Topic` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Thread-index` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Thread-topic` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Title...........` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Tool` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:TweakClass` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:UI-InboundReport` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:UI-Loop` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:UI-OutboundReport` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:URL` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:User-Agent` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Version` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-1and1-Spam-Level` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-250ok-CID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-4EC0790` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-7564579A` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-77F55803` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-7FA49CB5` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ACC-Host` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ACF` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-ACFC-SN` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-ACFC-V` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-ACL-Warn` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ASG-Debug-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-ASG-Orig-Subj` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-ASG-Quarantine` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ASG-Whitelist` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-ASSP-DKIMidentity` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-AUTH-Result` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Accept-Language` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Account-Key` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Accounttype` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Alimail-AntiSpam` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Amavis-Alert` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Amavis-Hold` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Amavis-Modified` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Amp-File-Uploaded` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Amp-Original-Verdict` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Amp-Result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Android-APK-Signed` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-AntiAbuse` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Antivirus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Antivirus-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Apparently-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Archive-Queue` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Area1Security-Processed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Assp-Client-TLS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Assp-DKIM` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Assp-Delay` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Assp-Detected-RIP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Assp-Envelope-From` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Assp-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Assp-IP-Score` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Assp-Intended-For` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Assp-Message-Score` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Assp-Original-Subject` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Assp-Received-RWL` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Assp-Server-TLS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Assp-Session` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Assp-Source-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Assp-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Assp-Whitelisted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-AttachExt` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Attachment-filename` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-AttachmentOrder` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-AuditID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Auth-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Authenticated-Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Authenticated-User` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Authentication-Warning` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Authenticator` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Authority-Analysis` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Authority-Reason` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Auto-Response-Suppress` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-AutoForwarded-By` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-AzureVoicemail-CallId` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-AzureVoicemail-FirehoseActivityId` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-AzureVoicemail-TranscriptionRequestId` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-BANNER-OFF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-BASF-SMTPOUT` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-BESS-Apparent-Source-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-BESS-BRTS-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-BESS-DMARC` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-BESS-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-BESS-Info` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-BESS-Outbound-Spam-Score` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-BESS-Parts` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-BESS-Spam-Report` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-BESS-Spam-Score` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-BESS-Spam-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-BESS-VER` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-BWhitelist` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Apparent-Source-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-BRTS-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Connect` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Effective-Source-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Encrypted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Envelope-From` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-RBL-Trusted-Forwarder` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Scan-Msg-Size` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Spam-Flag` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Spam-Report` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Spam-Score` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Spam-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Start-Time` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-URL` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-BeenThere` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Binding` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-BitDefender-CF-Stamp` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-BitDefender-Scanner` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-BitDefender-Spam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-BitDefender-SpamStamp` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Bluewin-Bp` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Bluewin-Spam-Analysis` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Bluewin-Spam-Score` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Brightmail-Tracker` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-BypassBranding` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-C1DE0DAB` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-C2AutoRespond` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-C2ProcessedOrg` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-C8649E89` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CCM` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-CFEmailSecurity-Processed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CFilter-Loop` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-CGO-SPAM` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-CI-MailPolicy-Key` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CKN-Banner` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CLIENT-HOSTNAME` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CLIENT-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CLOUD-SEC-AV-INT-Relay` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CLOUD-SEC-AV-Info` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CLOUD-SEC-AV-UUID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CLX-Response` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-CLX-Shades` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-CM-Analysis` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CM-Envelope` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CM-HeaderCharset` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-CM-TRANSID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-CMAE-Analysis` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-CMAE-Envelope` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-CMAE-Score` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-CP-PEC-Spam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-CP-To-Confirm` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-CSA-Complaints` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-CSE-ConnectionGUID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-CSE-MsgGUID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-CTCH-IPCLASS` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-CTCH-RefID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-CTCH-Spam` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-CTCH-VOD` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-CTCT-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CallingTelephoneNumber` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Campaign` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Campaign-Activity-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Campaign-ID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Campaignid` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Channel-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Classification-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Client-Addr` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Client-Proto` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-ClientProxiedBy` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Cloudmark-SP-Filtered` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Cloudmark-SP-Result` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Cloudmilter-Processed` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-CodeTwo-MessageID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CodeTwoProcessed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Company-Header` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Complaints-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Complaints-to` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Coremail-Antispam` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Country-Code` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Country-Path` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Crid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CrossPremisesHeadersFiltered` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-CrossPremisesHeadersFilteredByDsnGenerator` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CrossPremisesHeadersFilteredBySendConnector` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CrossPremisesHeadersPromoted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Csa-Complaints` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Cse-Connectionguid` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Cse-Msgguid` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Custom-Campaign` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Custom-Campaign-Type` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Custom-Header` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Custom-Recipient` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Cyrus-Session-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-D57D3AED` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-DCC--Metrics` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-DDEI-TLS-USAGE` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-DKIM` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-DKIM-Results` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-DKIM-Verification` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-DMARC-Verification` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-DNSRBL` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-DOORAY-SPAM` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-DSNContext` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-DSPAM-Confidence` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-DSPAM-Factors` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-DSPAM-Probability` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-DSPAM-Processed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-DSPAM-Result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-DSPAM-Signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Date` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-David-Flags` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-David-Sym` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Dedup-Identifier` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Default-Received-SPF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Delivery-Time` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Destination-ID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Dewaweb-Class` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Dewaweb-Evidence` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Disclaimed` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Dmarc-Test` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Document-Type` | templated,observed | `-` | `-` | `multipart/related` |
| `Message:Raw-Header:X-Durian-MailFrom` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Durian-RcptTo` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EBS` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-EEMSG-Attachment-filename` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EEMSG-Attachment-filesize` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EEMSG-ORIG-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EEMSG-SBRS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EEMSG-check-002` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EEMSG-check-004` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EEMSG-check-008` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EEMSG-check-009` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EEMSG-check-019` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EEMSG-check-021` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EN-AuthUser` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-EN-IMPSID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EN-OrigHost` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-EN-OrigIP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-EN-UserInfo` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-ENVELOPE-TO` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-EOPAttributedMessage` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-EOPTenantAttributedMessage` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-ESA-HAT` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ESA-Listener` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ESA-SBRS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ESET-AS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ESET-Antispam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ETP-Message-Attributes` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-ETP-TRAFFIC-TYPE` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-ETR` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-EXCLAIMER-MD-CONFIG` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Email-Count` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Email-Type-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Encryption` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EndpointSecurity-0xde81-EV` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EndpointSecurity-Spam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EndpointSecurity-SpamStamp` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Entity-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Env-Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Envelope-From` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Envelope-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Envelope-To-Blocked` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Envelope-to` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EopAttribution-RoutedToQuarantineCount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Eopattributedmessage` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Eoptenantattributedmessage` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-EsetId` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EsetResult` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Evolution-Source` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ExSBR-Direction` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ExSBR-HeaderCheck` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Exchange-Antispam-Report-CFA-Test` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Exchange-Antispam-Report-Test` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-ExclaimerHostedSignatures-MessageProcessed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ExclaimerImprintAction` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ExclaimerImprintLatency` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ExclaimerProxyLatency` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Exim-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-ExtLoop1` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ExtScanner` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ExternalRecipientOutboundConnectors` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-F-Verdict` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-FACEBOOK-PRIORITY` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FB-Internal-MID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FB-Internal-NotifID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FB-Internal-Notiftype` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FB-Internal-RecipID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FE-Attachment-Name` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-FE-ETP-CONNECTING-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-FE-ETP-METADATA` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-FE-ETP-SENDER-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-FE-Envelope-From` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-FE-Last-Public-Client-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-FE-Macro` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FE-Orig-Env-From` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FE-Orig-Env-Rcpt` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FE-Policy-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-FEAS-AntiVirus` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FEAS-Attachment-Filter` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FEAS-BEC-Info` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-FEAS-BannedWord` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FEAS-Client-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-FEAS-DKIM` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-FEAS-DLP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-FEAS-Deferred` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-FEAS-Dictionary` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FEAS-FortiSandbox` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FEAS-HASH` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FEAS-Relationship` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FEAS-SBL` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FEAS-SPF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-FEAS-SURL` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FM-Pack-Time` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Facebook` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Facebook-Notify` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Failed-Recipients` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FangMail-Spam-Reason` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FangMail-SpamHead` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Feedback-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Feedback-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Filter-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-FireEye` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Footer` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Forefront-Antispam-Report` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Forefront-Antispam-Report-Untrusted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Forefront-PRVS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Forwarded-Encrypted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Forwarded-Message-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-From-Rewrite` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-GBUdb-Analysis` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-GFI-SMTP-HelloDomain` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-GFI-SMTP-RemoteIP` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-GFI-SMTP-Submission` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Get-Message-Sender-Via` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-GitHub-Assignees` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-GitHub-Labels` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-GitHub-Notify-Platform` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-GitHub-PullRequestStatus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-GitHub-Reason` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-GitHub-Recipient` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-GitHub-Recipient-Address` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-GitHub-Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Gm-Features` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Gm-Gg` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Gm-Message-State` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Google-DKIM-Signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Google-Dkim-Signature` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Google-Group-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Google-Smtp-Source` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Greylist` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Group` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-HE-SMSGID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-HS-Cid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-HS-Fax-Cid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Ham-Report` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Harmony-Turn` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Helo-Args` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-HopCount` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Hox-Email-Type` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Hox-Organization-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Hox-Quest-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Hox-Quest-Tag` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Hox-User-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Hoxid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IMSS-DKIM-White-List` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-IP-stats` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IPAS-Result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-IS-SYNAQ-MX` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-IceWarp-AntiSpam-Result` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-IncomingHeaderCount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-IncomingTopHeaderMarker` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Info` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IntLoop1` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IntLoopCount2` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Intloopheader` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ipas-Result` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-IronPort-AV` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-IronPort-Anti-Spam-Filtered` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-IronPort-Anti-Spam-Result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-IronPort-Anti-Spam-Scanned` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-IronPort-DK-Sig` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-IronPort-Listener` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-MID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-MailFlowPolicy` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-Outbreak-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-RemoteIP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-Reputation` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-SPF-pass` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-SenderGroup` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-operated` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Ironport-Anti-Spam-Filtered` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ironport-Av` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ironport-Dmarc-Check-Result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-IsFriend` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IsPstnCall` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-JMailer` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-JNJ` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Jid` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Junkmail` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-K` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-KSMG-AntiPhishing` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KSMG-AntiSpam-Auth` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KSMG-AntiSpam-Envelope-From` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KSMG-AntiSpam-Info` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KSMG-AntiSpam-Interceptor-Info` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KSMG-AntiSpam-Lua-Profiles` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KSMG-AntiSpam-Method` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KSMG-AntiSpam-Rate` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KSMG-AntiSpam-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KSMG-AntiSpam-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KSMG-AntiVirus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KSMG-AntiVirus-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KSMG-KATA-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KSMG-LinksScanning` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KSMG-Message-Action` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KSMG-Rule-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KasLoop` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KasSpamfilter` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Kaspersky` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-KommONE` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-LASED-Hits` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-LASED-Impersonation` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-LASED-MailType` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-LASED-Spam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-LASED-SpamProbability` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-LD-Processed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-LOGIX-ANTISPAM` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Last-TLS-Session-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Lms-Client-Ip` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Local-Domain` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Logix-Listener` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Logix-MID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Logix-MailFlowPolicy` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Logix-RemoteIP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Logix-Reputation` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Logix-SenderGroup` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Logix-Time` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-M2K-DINF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MAIL` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MC-Copy` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MC-Ingress-Time` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MC-Loop-Signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MC-Relay` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MC-Unique` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MC-User` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MD-FROM` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MD-TO` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MDAV-Processed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MDArrival-Date` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MDID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MDID-I` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MDRcpt-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MDaemon-Deliver-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ME-Auth` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-ME-Bayesian` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ME-Date` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-ME-Helo` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-ME-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-ME-Spam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MG` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MG-SentBy-BASF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MGA-submission` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MGBASF-SpamOverruled` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MGBASF-authorized` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MIMEOLE` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MIMETrack` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MJ-Mid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MJ-SMTPGUID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MLModelPrediction` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-ATPSafeLinks-BitVector` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-AntiSpam-ExternalHop-MessageData-0` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-AntiSpam-ExternalHop-MessageData-ChunkCount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-AntiSpam-MessageData` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-AntiSpam-MessageData-0` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-AntiSpam-MessageData-ChunkCount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-AntiSpam-MessageData-Original-0` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-AntiSpam-MessageData-Original-ChunkCount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-AntiSpam-Relay` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-AtpMessageProperties` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Authentication-Results` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Calendar-Series-Instance-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-AuthAs` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-AuthSource` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-FromEntityHeader` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-MailboxType` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-Network-Message-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-OriginalArrivalTime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-OriginalAttributedTenantConnectingIp` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-RMS-PersistedConsumerOrg` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-UserPrincipalName` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-fromentityheader` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-mailboxtype` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-originalarrivaltime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-rms-persistedconsumerorg` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-userprincipalname` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-EOPDirect` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-ExternalInOutlookResult` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-ExternalOriginalInternetSender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Forest-ArrivalHubServer` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Forest-EmailMessageHash` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Forest-IndexAgent` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Forest-IndexAgent-0` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Forest-Language` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Forest-MessageScope` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Forest-RulesExecuted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-ForwardingLoop` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Generated-Message-Source` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Inbox-Rules-Loop` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-MeetingForward-Message` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Message-Is-Ndr` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-MessageSentRepresentingType` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ACSExecutionContext` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AS-LastExternalIp` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ASDirectionalityType` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ATPCustomPipelineScanCompleteAction` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ATPDetonation-SonarData-0` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ATPDetonation-SonarData-1` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ATPDetonation-SonarData-ChunkCount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ATPDetonationContext` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ATPDetonationLatency` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ATPExecutionContext` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ATPSafeLinks-UrlSideline` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ATPScanUrlInfo-0` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ATPScanUrlInfo-ChunkCount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ATPScanUrls` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ATPService-SubmissionContext` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AVScanComplete` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AVScannedByV2` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AVStamp-Enterprise` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AVStamp-Mailbox` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AVStamp-MalwareDetected` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AcceptedDomain` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AntiPhishPolicy` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AntiSpam-ArcTrustedDomains` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AntiSpam-RefreshSpfDnsRecordInCache` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AntiSpam-SpfDnsTimeoutError` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antiphish-V2` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antispam-AnalystFeatureFilter-ScanContext` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antispam-AnalystRuleHits` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antispam-AuthResults` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antispam-ContentFilter-ScanContext` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antispam-PreContentFilter-PolicyLoadTime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antispam-PreContentFilter-ScanContext` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antispam-ProtocolFilterHub-ScanContext` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antispam-Report` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antispam-ScanContext` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antispam-SpamFilter-ScanContext` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AtpDetonationPriority` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AttachmentDetails` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AttachmentDetailsHeaderStamp-Success` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AttachmentDetailsInfo-0` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AttachmentDetailsInfo-ChunkCount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Auth-DmarcStatus` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Auth-ExtendedDmarcStatus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AuthAs` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AuthMechanism` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AuthSource` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AutoForwarded` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-BCL` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-BCL-Source` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Base64-MessageInboundConnectorData` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Boomerang-Verdict` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-BypassClutter` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-BypassFocusedInbox` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-CFA-UserOption` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-CommunicationStateSummary` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-CompAuthReason` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-CompAuthRes` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ComplianceLabelId` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ConnectingEHLO` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ConnectingIP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ContainsAttachments` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Cross-Premises-Headers-Processed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Cross-Session-Cache` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-DMARC-Enforcement` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Disclaimer-Hash` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-EhloAndPtrDomain` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-EmailFingerprintsDetailsInfo-0` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-EmailFingerprintsDetailsInfo-ChunkCount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExpirationInterval` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExpirationIntervalReason` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExpirationStartTime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExpirationStartTimeReason` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExternalRecipientCount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExternalRoutingTopologyAnalysis` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExtractedBarcode` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExtractionTags` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExtractionTagsFrom` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExtractionTagsSubject` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExtractionTagsSubjectNormalized` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExtractionTagsURLFound` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-FFO-ServiceTag` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Feature-Long` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-FeatureTable` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-FeatureTableV2` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-FirstContactSummary` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-FromEntityHeader` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-HDRFeatureV2` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-HMATPModel-DkimAuthStatus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-HMATPModel-DmarcAuthStatus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-HMATPModel-Recipient` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-HMATPModel-Spf` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-HVERecipientsForked` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-HostedContentFilterPolicy` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-HybridAttributionCategory` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-HygienePolicy` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-IP-Bulk-Level` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-InboundConnector-Attributes` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-IncludeInSla` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-InternalOrgSender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-IntraOrgOverride-CompAuthReason` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-IntraOrgOverride-CompAuthRes` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-IsAnyAttachmentAtpSupported` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-IsAtpTenant` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-IsBipIncludedAtpTenant` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-IsKnownDomain` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-IsS2500Tenant` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-IsS500Tenant` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-IsSingleRepresentative` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-IsTrialAtpTenant` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-KnownHighVolumeSender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Malware-OriginalScanContext` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MalwareFilterPolicy` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Manual-IP-List-Hi-Confidence` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MessageDirectionality` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MessageFingerprint` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MessageHighPrecisionLatencyInProgress` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MessageInboundConnectorData` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MessageInboundConnectorName` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MessageInboundConnectorType` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MessageLatency` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MessageScope` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MetadataFeatureTable` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ModifySensitivityLabel` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MxPointsToUs` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Network-Message-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-NonRfcFrom-V2` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OffboxClassificationInfo` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OrderedPrecisionLatencyInProgress` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OrgEopForest` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalArrivalTime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalAttributedTenantConnectingIp` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalClientIPAddress` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalEnvelopeRecipients` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalServerIPAddress` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalSize` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalTenant-AuthAs` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalTenant-AuthSource` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalTenant-FromEntityHeader` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalTenant-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalTenant-Network-Message-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalTenant-OriginalArrivalTime` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Originating-Country` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginatorOrganization` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-P2SenderDisplayNamePII` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-P2SenderPII` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-PCL` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-PFAHub-Total-Message-Size` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-PRD` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-PassLevelSpfRecord` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Persisted-Urls-0` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Persisted-Urls-1` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Persisted-Urls-ChunkCount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-PersistedUrlCount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-PersistedUrlInfoCount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-PhishSim-Rules-Execution-History` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Prioritization` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-PriorityRequest` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-PtrDomains` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Recipient-Limit-Verified` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Recipient-P2-Type` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-RecipientDomainMxInfo` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-RecipientDomainMxRecord-PFAFD` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-RecordReviewCfmType` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ReplicationInfo` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-RuleName-Execution-Log` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Rules-Execution-History` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Rules-Execution-Log` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-RulesExecuted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-RunDetonationScan` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SCL` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SafeAttachmentPolicy` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SafeAttachmentPolicy-BIP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SafeAttachmentPolicy-Enable` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SafeAttachmentProcessing` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SafeLinksPolicy` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SafeLinksPolicy-BIP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SafeLinksPolicy-EnableSafeLinksForEmail` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SafeLinksPolicy-EnableSafeLinksForInternalSenders` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SecOpsMailboxOverride` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SecOpsOverride-Rules-Execution-History` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SenderIdResult` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SenderIntelligence-P2Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SenderIntelligence-P2SenderOrgDomainTenantId` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SenderRecipientCommunicationState` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SenderRep-Data` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SenderRep-Score` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SkipDynamicAttachments` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SkipListedRecipientPilot` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SkipSafeAttachmentProcessing` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SonarDetectionsInAttachmentDetails` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SpoofDetection-Frontdoor-DisplayDomainName` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-TargetResourceForest` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-TenantServiceProvider` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-TopLevelSpfRecord` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-TotalRecipientCount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-TrafficSelection-PSE` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Transport-Properties` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-TransportTrafficSubType` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-TransportTrafficType` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-URLFeatureReduction` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-UriInBody` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-UrlLogged` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-UrlMinimumDomainAge` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-UrlSelected` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-VBR-Class` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-VerifiedDkimDomainsList` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-XMSExchangeOrganizationATPComponentLatencies` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-XMSExchangeOrganizationATPPendingLatencyItems` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Parent-Message-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Processed-By-BccFoldering` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-QuarantineResubmitTime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-SenderADCheck` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-SharedMailbox-RoutingAgent-Processed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-SkipListedInternetSender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Transport-CrossTenantHeadersPromoted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Transport-CrossTenantHeadersStamped` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Transport-CrossTenantHeadersStripped` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Transport-EndToEndLatency` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Transport-Forked` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Transport-Rules-Loop` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-UnifiedGroup-Address` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-UnifiedGroup-DisplayName` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-UnifiedGroup-MailboxGuid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Has-Attach` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Office365-Filtering-Correlation-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Office365-Filtering-Correlation-Id-Prvs` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Oob-TLC-OOBClassifiers` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-PublicTrafficType` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-TNEF-Correlator` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-TrafficTypeDiagnostic` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-UserLastLogonTime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MSFBL` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MSH` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MSMail-Priority` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MSW-Message-Direction` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MSW-SpamLogic` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MSYS-API` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MSmail-Priority` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MTA-CheckPoint` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1670613585159` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1727850061922` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1755436301993` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1755614014568` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1756501596107` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933347` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933376` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933475` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933507` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933533` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933559` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933589` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933611` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933633` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933652` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933677` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933699` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933721` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933740` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933771` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933792` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933824` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933849` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933947` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758116933968` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758482008562` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1758570774735` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1759222917513` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1761084423005` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1761672243279` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1761710752858` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1761853276621` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1763596485766` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1763596485927` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1763596486163` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1765336011334` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1765336011397` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1765336011556` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MW-Processed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Ma4-Node` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MagicMail-Authenticated` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MagicMail-EnvelopeFrom` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MagicMail-OS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MagicMail-RegexMatch` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MagicMail-SourceIP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MagicMail-UUID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Mail-Args` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MailChannels-Auth-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MailChannels-SenderId` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MailGates` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Mailer` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Mailer-ID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mailer-Info` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mailfrom` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mailgun-Dkim` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mailgun-Native-Send` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mailgun-Sending-Ip` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Mailgun-Sending-Ip-Pool` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Mailgun-Sending-Ip-Pool-Name` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Mailgun-Sid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Mailgun-Tag` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Mailgun-Track-Clicks` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mailgun-Track-Opens` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mailgun-Variables` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Mailin-Campaign` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Mailin-Client` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MailingID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mailru-MI` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Mailru-Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Mailru-Src` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Mandrill-User` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MarketoID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Matching-Connectors` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MaxCode-Template` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mc-User` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mdid` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mdid-I` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Message-Delivery` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Message-Flag` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Message-Flag-Colorid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Message-ID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Message-Info` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Message-Status` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MessageID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MessageType` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mga-Submission` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Microsoft-Antispam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Microsoft-Antispam-Mailbox-Delivery` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Microsoft-Antispam-Message-Info` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Microsoft-Antispam-Message-Info-Original` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Microsoft-Antispam-PRVS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Microsoft-Antispam-Untrusted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Microsoft-Exchange-Diagnostics` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Microsoft-Exchange-Diagnostics-untrusted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MimeOLE` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Mimecast-Impersonation-Protect` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Mimecast-MFC-AGG-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Mimecast-MFC-PROC-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Mimecast-Spam-Score` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MktArchive` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MktMailDKIM` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mozilla-Keys` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mozilla-Status` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mozilla-Status2` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mras` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Ms-Exchange-Antispam-Messagedata-Original-0` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Antispam-Messagedata-Original-Chunkcount` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Antispam-Relay` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Atpmessageproperties` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Authentication-Results` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Crosstenant-Authas` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Crosstenant-Authsource` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Crosstenant-Fromentityheader` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Crosstenant-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Crosstenant-Network-Message-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Crosstenant-Originalarrivaltime` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Crosstenant-Originalattributedtenantconnectingip` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Externalinoutlookresult` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Externaloriginalinternetsender` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Authas` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Authmechanism` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Authsource` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Expirationinterval` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Expirationintervalreason` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Expirationstarttime` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Expirationstarttimereason` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Messagedirectionality` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Network-Message-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Network-Message-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Scl` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Transportdecryption-Action` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Processed-By-Bccfoldering` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Senderadcheck` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Skiplistedinternetsender` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Transport-Crosstenantheaadersstamped` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Transport-Crosstenantheaderspromoted` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Transport-Crosstenantheadersstamped` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Transport-Crosstenantheadersstripped` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Transport-Endtoendlatency` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Has-Attach` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Office365-Filtering-Correlation-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Office365-Filtering-Correlation-Id-Prvs` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Publictraffictype` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Tnef-Correlator` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Traffictypediagnostic` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Msfbl` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Msg-EID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Msg-Ref` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Msmail-Priority` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-NA-AI-Is-Spam` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-NA-AI-Spam-Probability` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-NAI-ID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Native-Encoded` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Naver-ESV` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Neo-Attach` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Neo-Rcpt` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Neo-Sender` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Neo-Subj` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Neo-Version-Info` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-NetatworkMailGateway-Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-NetpionMsgID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-No-Auth` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-NoSpamProxy-AttachmentID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-NoSpamProxy-Gateway` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-NoSpamProxy-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-NoSpamProxy-Rating` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-NoSpamProxy-Rule` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-NoSpamProxy-Scl` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-NoSpamProxy-Tests` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-NoSpamProxy-TrustedMail` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Note` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Note-419` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Note-AR-Scan` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Note-AR-ScanTimeLocal` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Note-Return-Path` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Note-Reverse-DNS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Note-Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Note-Sending-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Note-SnifferID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Notes-Item` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-OLX-Disclaimer` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ONET_PL-MDA-From` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ONET_PL-MDA-Info` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ONET_PL-MDA-Spam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ONET_PL-MDA-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ORIGINAL-IP` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-ORIGINAL-TIME` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-OVh-ClientIp` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-OlkEid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Org` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Organization` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-OrganizationHeadersPreserved` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Orig` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Origin-Country` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Origin-IP` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Origin-Time` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Original-Authentication-Results` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Original-From` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Original-MAILFROM` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Original-Message-ID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Original-Message-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Original-RCPTTO` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Original-Rcpt` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Original-Recipient` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Original-SENDERCOUNTRY` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Original-SENDERIP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Original-SPF` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Original-Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Original-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Original-X-Forefront-Antispam-Report` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Original-X-MS-Exchange-Organization-Network-Message-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Original-X-Microsoft-Antispam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-OriginalArrivalTime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Originating-Client` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Originating-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Originating-Ip` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-OriginatorOrg` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Our-Spam-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Outside` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Ovh-Tracer-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PEI-MailScanner` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PEI-MailScanner-From` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PEI-MailScanner-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PEI-MailScanner-Information` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PEI-MailScanner-SpamCheck` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PHISH-CRID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PHISHTEST` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PHP-Originating-Script` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-PHP-Script` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PMX-Spam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PMX-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-POPCON-SPAMCHECK` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-POPCON-TARGETADDRESS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PP-Email-transmission-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-PPE-STACK` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-PPE-TRUSTED` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-PPP-Message-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-PPP-Vhost` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-PT-TOKEN` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Payment-Notification` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-PaymentKey` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Perizia-MailScanner` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Perizia-MailScanner-From` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Perizia-MailScanner-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Perizia-MailScanner-Information` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Perizia-MailScanner-SpamCheck` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Perizia-MailScanner-SpamScore` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PhishAlarm-Format` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Pm-Message-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Policy` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Ppe-Stack` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ppe-Trusted` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Primary` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Priority` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Proofpoint-Banner-Trigger` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Proofpoint-GUID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Proofpoint-ID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Proofpoint-ORIG-GUID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Proofpoint-Reinject` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Proofpoint-Sentinel` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Proofpoint-Spam-Details` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Proofpoint-Spam-Details-Enc` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Proofpoint-Spam-Reason` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Proofpoint-Virus-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Provags-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Proxmox-VInfo` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-QQ-BUSINESS-ORIGIN` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-Bgrelay` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-FEAT` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-GoodBg` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-MIME` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-Mailer` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-SENDSIZE` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-SSF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-STYLE` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-XMAILINFO` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-XMRINFO` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-mid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Qmail-Scanner-Diagnostics` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Qnum` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Quarantine-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-REDF-ATP` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-REDF-HOPS` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-REDF-SHIELD` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-REDIFF-SENDER-VERIFY` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-RELAYMAIL` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-REPORT-ABUSE-TO` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-RTDREDIFF-Delivered-Remotely-To` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-RZG-AUTH` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-RZG-CLASS-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-RZG-Expurgate` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-RZG-Expurgate-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Rcpt-Args` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Rcpt-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Received` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Received-SPF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Recommended-Action` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Rejection-Reason` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Relaying-Domain` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Remote-IP` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Report-Abuse` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Report-Abuse-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Report-BASF-Outbound` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ReportingKey` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Request-ID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Return-Path` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Return-Path-Hint` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Riferimento-Message-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Roving-Campaignid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Roving-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Rozee` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Rspamd-Queue-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Rules-SCL-Zero` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SASI-Hits` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SASI-Probability` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SASI-RCODE` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SASI-SpamProbability` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SASI-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SBRS` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SEA-Spam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SECURESERVER-ACCT` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SES-Outgoing` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SF-HELO-Domain` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SF-Originating-IP` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SF-RX-Return-Path` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SF-WhiteListedReason` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SFMC-Stack` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SG-EID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SG-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SGG-5a5f2ea1c9c0921f2bc0bc3c8426700d-CYREN-AS-RESULT` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SGG-5a5f2ea1c9c0921f2bc0bc3c8426700d-SOPHOS-ASRESULT` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SGG-5a5f2ea1c9c0921f2bc0bc3c8426700d-SOPHOSAS-DATA` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SGG-5a5f2ea1c9c0921f2bc0bc3c8426700d-STATE-CONN` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SGG-5a5f2ea1c9c0921f2bc0bc3c8426700d-STATE-DATA` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SGG-DKIM-Signing` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SGG-MF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SGG-Platform` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SGG-RESULT` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SGG-UMAMSID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SID-PRA` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SID-Result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SM-incoming` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SM-outgoing` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SMFBL` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SMHeaderMap` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SMMKEYID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SMTP36-MailScanner` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SMTP36-MailScanner-From` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SMTP36-MailScanner-ID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SMTP36-MailScanner-Information` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SNCR-env-sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SONIC-DKIM-SIGN` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SPAM-LEVEL` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SPAM-SOURCE-CHECK` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SPF-Fail` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SPF-Received` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SPF-Result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SPF-Verification` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SRS-Domain` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Scanned-By` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ScotiaRedirect` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Sender-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Sender-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SenderField-ReMsg` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SenderField-Remind` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SenderName-ClientID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Senderauth-Result` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Session-IP` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-ShareDataEnabled` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Sieve` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Sieve-Redirected-From` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Signature-Violations` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SmartFilter` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SmarterMail-Authenticated-As` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SmarterMail-Spam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SmarterMail-SpamAction` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SmarterMail-TotalSpamWeight` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Smtp-Server` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Sonic-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Sonic-MF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Sophos-DomainHistory` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Sophos-ESA` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Sophos-Email` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Sophos-Email-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Sophos-Email-Scan-Details` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Sophos-Email-Transport-Route` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Sophos-Firewall` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Sophos-IBS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Sophos-MH-Mail-Info-Key` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Sophos-OBS` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Sophos-Product-Type` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Sophos-SenderHistory` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Sosafedkim` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Source` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Source-Args` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Source-Auth` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Source-Cap` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Source-Dir` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Source-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Source-L` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Source-Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Spam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Spam-Bar` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Spam-CMAECATEGORY` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Spam-CMAESUBCATEGORY` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Spam-CMAETAG` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Spam-Checked-In-Group` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Spam-Checker-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Spam-Filter` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Spam-Flag` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Spam-Level` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Spam-Processed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Spam-Report` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Spam-Score` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Spam-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Spam-Tests` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SpamExperts-Domain` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SpamExperts-Outgoing-Class` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SpamExperts-Outgoing-Evidence` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SpamExperts-Username` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SpamFilter-By` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SpamReason` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Spamd-Bar` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Spamd-Result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Spamina-ClassifiedBy` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Spamina-Destination` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Spamina-History` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Spamina-Host` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Spamina-MessageID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Spamina-Service-Type` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Spampanel-Class` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Spampanel-Evidence` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-StarScan-Received` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-StarScan-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Suspicious-Sender` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-System-Trace-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-TERRACE-CLASSID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TERRACE-DUMMYSUBJECT` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TERRACE-SID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TERRACE-SPAMMARK` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-AS-ERS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TM-AS-GCONF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TM-AS-MML` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-TM-AS-Product-Ver` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TM-AS-Result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TM-AS-SMTP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TM-AS-URL-Rewrite` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-AS-User-Approved-Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TM-AS-User-Blocked-Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-TM-Addin-Auth` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-Addin-ProductCode` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-Authentication-Results` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TM-DDEI-Authentication-Results` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-Deliver-Signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TM-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-TM-IMSS-BATV-Data` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-IMSS-Message-ID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-MAIL-RECEIVED-TIME` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-RISKAI-MATCHEDFID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-RISKAI-PTN-VERSION` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-Received-SPF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TM-SNTS-SMTP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TM4.5-S-ID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TMASE-MatchedRID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TMASE-Result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TMASE-SNAP-Result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TMASE-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TMASE-XGENCLOUD` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TNEFEvaluated` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TOI-EXPURGATEID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TOI-MSGID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TOI-VIRUSSCAN` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TSO-Authenticated` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Talos-CUID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Talos-Cuid` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Talos-MUID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Talos-Muid` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Task-Complete` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Task-Due-Date` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Task-Start-Date` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ThreatScanner-Verdict` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Threatscanner-Verdict` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Titan-Src-Out` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Tnid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Trasporto` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-UI-Filterresults` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-UI-Out-Filterresults` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-UI-Sender-Class` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-UID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-UIDL` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Universally-Unique-Identifier` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Unsubscribe-Web` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Usid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-VADE-SPAMCAUSE` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-VADE-SPAMSTATE` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-VR-SPAMCAUSE` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-VR-SPAMSCORE` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-VR-SPAMSTATE` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-VRC-POLICY-STATUS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-VRC-SPAM-STATE` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-VRC-SPAM-STATUS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Vade-Cause` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Vade-Score` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Vade-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Vipre-Scanned` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-VirtualServer` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-VirtualServerGroup` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Virus-Header` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Virus-Scan` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Virus-Scanned` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Virus-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-VirusChecked` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-VoiceMessageDuration` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-VoiceMessageLanguage` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-VoiceMessageSenderIsAnonymous` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-VoiceMessageSenderName` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-WB-MSG-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-WB-RES` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-WB-TRACE-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-WM-Dns-Ptr` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-WM-Tid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-WSS-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Warn` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Wi-Port` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Workday-Security` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Workday-Static-BP-Address` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Workday-System` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-XPT-XSL-Name` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-YMail-OSG` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-YMailISG` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Yahoo-Group-Post` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Yahoo-Profile` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-ZM-MESSAGEID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Zoho-AV-Stamp` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Zoho-Rid` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Zoho-Virus-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ZohoMail-DKIM` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ZohoMail-Owner` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-antispameurope` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-Connect` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-DKIM` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-Digest` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-antispameurope-LES` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-MSGID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-Mailarchiv` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-antispameurope-Mailarchivtype` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-antispameurope-RBLWL` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-antispameurope-REASON` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-SPFRESULT` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-Spamstatus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-Virusscan` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-WC` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-body-digest` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-date` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-disclaimer` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-orig` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-orig-host` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-orig-ip` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-recipient` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-sc` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-antispameurope-sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-bmsbeierlein-MailScanner-EFA` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-bmsbeierlein-MailScanner-EFA-From` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-bmsbeierlein-MailScanner-EFA-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-bmsbeierlein-MailScanner-EFA-Information` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-bmsbeierlein-MailScanner-EFA-SpamScore` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-bmsbeierlein-MailScanner-EFA-Watermark` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-bounce-key` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-campaignid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-cid` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-cloud-security` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-cloud-security-Digest` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-cloud-security-Mailarchiv` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-cloud-security-Mailarchivtype` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-cloud-security-Virusscan` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-cloud-security-connect` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-cloud-security-crypt` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-cloud-security-disclaimer` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-cloud-security-recipient` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-cloud-security-sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-eGroups-Moderators` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-eGroups-Msg-Info` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-elqPod` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-elqSiteID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-enQsig-EncryptionAlgorithm` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-enQsig-SignatureAlgorithm` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-enQsig-SignatureStatus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-fn` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-fs` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ft` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-hMailServer-ExternalAccount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-hMailServer-LoopCount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-hMailServer-Reason-1` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-hMailServer-Reason-2` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-hMailServer-Reason-3` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-hMailServer-Reason-4` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-hMailServer-Reason-5` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-hMailServer-Reason-Score` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-hMailServer-Spam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-hornetsecurity-identifier` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-imss-reprocess-rules` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-imss-reprocess-type` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-imss-scan-details` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-mailer` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-policyd-weight` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-purgate` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-purgate-Ad` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-purgate-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-purgate-size` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-purgate-type` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-rext` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-rpcampaign` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-sgxh1` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-sib-id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-smtpcorp-track` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X_Sophos_TLS_Connection` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X_Sophos_TLS_Delivery` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:[0606/153358.915` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153358.930` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153358.977` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.024` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.071` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.086` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.102` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.118` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.133` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.149` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.165` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.180` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.196` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.211` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.227` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.243` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.258` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.274` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.290` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.305` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.321` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.337` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.352` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.368` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.383` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.399` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.415` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.430` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.446` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.461` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.477` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.508` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.524` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.540` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.556` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.575` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.618` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.633` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.649` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.665` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.680` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.696` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.711` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.727` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.824` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.837` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.852` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.868` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.899` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.930` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.946` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.961` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.977` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153359.993` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153400.024` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153400.133` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153400.149` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153400.165` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153400.212` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153400.227` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153400.461` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.196` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.211` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.352` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.415` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.430` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.446` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.461` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.477` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.493` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.508` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.524` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.540` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.555` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.571` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.586` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.602` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.618` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.633` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.649` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.696` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.743` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.821` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.837` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.899` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.916` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153403.978` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153404.227` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153416.307` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153416.338` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153416.620` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153419.745` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153425.338` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153426.307` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153426.967` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153426.995` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/153427.104` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223130.576` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223130.591` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223130.607` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223130.638` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223130.654` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223132.842` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223132.857` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223135.076` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223135.091` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223135.248` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223135.263` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223135.310` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223135.373` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223135.388` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223135.779` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223135.795` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223136.107` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223136.123` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223138.435` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223138.467` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223144.263` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223144.279` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223147.982` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223216.920` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223241.383` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223241.555` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223241.899` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223254.106` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223254.122` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223254.334` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223254.403` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223254.450` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223254.591` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223254.606` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223254.747` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223254.763` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.028` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.059` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.091` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.138` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.169` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.231` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.263` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.309` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.341` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.372` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.403` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.434` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.481` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.528` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.559` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.591` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.622` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.700` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.731` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.778` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223317.887` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223318.403` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223318.466` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223318.528` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223318.559` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223318.622` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223318.700` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223318.919` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.122` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.153` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.184` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.325` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.356` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.403` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.419` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.434` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.450` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.466` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.497` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.513` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.528` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.544` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.575` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.591` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.606` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.622` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.653` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.684` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.700` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.780` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.794` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.809` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.841` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.856` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.872` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.888` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.903` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.919` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.934` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.966` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.981` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223319.997` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.013` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.059` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.075` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.091` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.106` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.122` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.153` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.184` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.216` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.231` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.247` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.278` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.294` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.309` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.325` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.341` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.372` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223320.419` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223321.606` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223321.622` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223321.653` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223321.684` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223321.731` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223321.809` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223321.872` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223321.981` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[0606/223321.997` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[2264` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[2408` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[2560` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[2764` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[3324` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[3336` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[3376` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[3392` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[3660` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[3688` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[3696` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:[3724` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:acceptlanguage` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:arc-authentication-results` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:arc-message-signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:arc-seal` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:authentication-results` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:authentication-results-original` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:client-request-id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:config` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:destinations` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:dkim-signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:feedback-id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:ironport-hdrordr` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:ironport-sdr` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:list-unsubscribe-post` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:msip_labels` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:ntiSpam-MessageData-ChunkCount` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:o` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:received-spf` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:request-id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:spam-stopper-id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:spam-stopper-v2` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:spamdiagnosticmetadata` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:spamdiagnosticoutput` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:thread-index` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-$rbp-opinion` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-$switch` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-aes-category` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-agari-authentication-results` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-aliyun-im-through` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-aliyun-mail-creator` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-amp-file-uploaded` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-amp-result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-bromium-msgid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-c2processedorg` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-cloud-sec-av-info` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-cmae-analysis` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-cmae-score` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-crosspremisesheadersfiltered` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-crosspremisesheaderspromoted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-envelope-mail-from` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-eopattributedmessage` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-eoptenantattributedmessage` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-esaext` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-esetid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-esetresult` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-exchange-antispam-report-cfa-test` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-exchange-antispam-report-test` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-ext-notification-enabled` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-forefront-antispam-report` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-forefront-antispam-report-untrusted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-forefront-prvs` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-gm-message-state` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-google-dkim-signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-google-smtp-source` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-gt-tenant` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-helo-string` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-incomingheadercount` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-incomingtopheadermarker` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-ipas-result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ironport-anti-spam-filtered` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ironport-av` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ironport-listener` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ironport-mailflowpolicy` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ironport-mid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ironport-remoteip` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ironport-reputation` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ironport-sendergroup` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-job` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ld-processed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-lsi-addin-version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-lsi-version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ma4-node` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-mailwall-from` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-mailwall-procid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-mailwall-template-id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-mde-internalonly` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-mdid` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-mga-submission` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-microsoft-antispam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-microsoft-antispam-mailbox-delivery` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-microsoft-antispam-message-info` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-microsoft-antispam-message-info-original` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-microsoft-antispam-prvs` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-microsoft-antispam-untrusted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-microsoft-exchange-diagnostics` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-mid` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-antispam-messagedata-0` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-antispam-messagedata-chunkcount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-antispam-messagedata-original-0` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-antispam-messagedata-original-chunkcount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-antispam-relay` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-atpmessageproperties` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-authentication-results` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-calendar-series-instance-id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-crosstenant-authas` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-crosstenant-authsource` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-crosstenant-fromentityheader` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-crosstenant-id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-crosstenant-mailboxtype` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-crosstenant-network-message-id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-crosstenant-originalarrivaltime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-crosstenant-originalattributedtenantconnectingip` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-crosstenant-userprincipalname` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-forest-arrivalhubserver` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-forest-emailmessagehash` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-forest-indexagent` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-forest-indexagent-0` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-forest-language` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-forest-messagescope` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-messagesentrepresentingtype` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-organization-antispam-precontentfilter-policyloadtime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-antispam-precontentfilter-scancontext` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-antispam-protocolfilterhub-scancontext` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-as-lastexternalip` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-asdirectionalitytype` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-auth-dmarcstatus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-auth-extendeddmarcstatus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-authas` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-organization-authsource` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-organization-avscancomplete` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-avscannedbyv2` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-boomerang-verdict` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-compauthreason` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-compauthres` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-connectingehlo` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-connectingip` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-cross-premises-headers-processed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-cross-session-cache` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-ehloandptrdomain` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-expirationinterval` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-organization-expirationintervalreason` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-organization-expirationstarttime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-organization-expirationstarttimereason` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-organization-externalroutingtopologyanalysis` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-featuretable` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-ffo-servicetag` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-fromentityheader` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-hmatpmodel-recipient` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-hmatpmodel-spf` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-hverecipientsforked` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-hygienepolicy` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-internalorgsender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-isatptenant` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-iss500tenant` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-messagedirectionality` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-organization-messagefingerprint` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-messagelatency` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-messagescope` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-mxpointstous` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-network-message-id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-organization-orderedprecisionlatencyinprogress` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-orgeopforest` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-originalarrivaltime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-originalclientipaddress` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-organization-originalenveloperecipients` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-originalserveripaddress` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-organization-originalsize` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-p2senderdisplaynamepii` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-p2senderpii` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-phishsim-rules-execution-history` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-ptrdomains` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-recipient-limit-verified` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-replicationinfo` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-rules-execution-history` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-safeattachmentpolicy` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-safelinkspolicy` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-senderintelligence-p2senderorgdomaintenantid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-spoofdetection-frontdoor-displaydomainname` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-targetresourceforest` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-totalrecipientcount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-transporttraffictype` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-verifieddkimdomainslist` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-processed-by-bccfoldering` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-senderadcheck` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-sharedmailbox-routingagent-processed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-skiplistedinternetsender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-slblob-mailprops` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-transport-crosstenantheaderspromoted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-transport-crosstenantheadersstamped` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-transport-crosstenantheadersstripped` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-transport-endtoendlatency` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-transport-fromentityheader` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-has-attach` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-ms-office365-filtering-correlation-id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-office365-filtering-correlation-id-prvs` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-oob-tlc-oobclassifiers` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-publictraffictype` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-reactions` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-traffictypediagnostic` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-msw-connecting-hostname` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-msw-connecting-ip` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-msw-jemd-lastmta` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-msw-jemd-malware` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-msw-jemd-newsletter` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-msw-jemd-refid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-msw-jemd-scanning-scores` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-msw-message-direction` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-msw-original-dkim-signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-msw-queue-id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-mxthunder-approved-sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-mxthunder-group` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-mxthunder-identifier` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-mxthunder-ip-rating` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-mxthunder-rf` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-mxthunder-rf-authresults` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-mxthunder-rf-level` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-mxthunder-rules` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-mxthunder-scan-result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-mxthunder-spam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-orgId` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-organizationheaderspreserved` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-originating-ip` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-originatororg` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-pps-dkim-result` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-priority` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-proofpoint-id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-rcpt-to` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-rdns-status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-received` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-rpcampaign` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-scoring-category` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-sdh-usedemail` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-sosafe-report-reference` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-source-ip` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-source-routing-agent` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-spam-category` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-spam-reasons` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-spam-score` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-spf-from-status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-spf-status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-tm-as-product-ver` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-tm-as-result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-tm-as-user-approved-sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-tm-as-user-blocked-sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-tm-deliver-signature` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-tm-mail-uuid` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-tm-snts-smtp` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-tmase-matchedrid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-tmase-result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-tmase-version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-tmn` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-vipre-scanned` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-virus-scanned` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:To-Display-Name` | declared,observed | `internalTextBag` | `Message` | `application/vnd.ms-outlook` |
| `Message:To-Email` | declared,observed | `internalTextBag` | `Message` | `application/vnd.ms-outlook` |
| `Message:To-Name` | declared,observed | `internalTextBag` | `Message` | `application/vnd.ms-outlook` |
| `MetaDataIdentifierCode` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `MetaDataResourceScope ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `MetaDataStandardEdition ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `MetaDataStandardTitle ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Multipart-Boundary` | declared,observed | `String` | `Message` | `application/gzip`, `application/msword`, `application/pdf` |
| `Multipart-Subtype` | declared,observed | `String` | `Message` | `application/gzip`, `application/msword`, `application/pdf` |
| `NumExecutables` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `NumHardLinks` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `OtherConstraints ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `PDF-SLICE-FAILED` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `PDF-SLICED-ERROR` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `PSName` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `PageCount` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ParentMetaDataTitle` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Password` | declared,not-observed | `externalText` | `JackcessParser` | _-_ |
| `Policy-Id` | declared,not-observed | `String` | `TSDParser` | _-_ |
| `ReferencePageCount` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ResourceFormatSpecificationAlternativeTitle ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Serial-Number` | declared,not-observed | `String` | `TSDParser` | _-_ |
| `SpreadPageCount` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TEIJSONSource` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TEIXMLSource` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ThesaurusNameDate ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Time-Stamp-DateTime` | declared,not-observed | `String` | `TSDParser` | _-_ |
| `Title` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TotalPageCount` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Trademark` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TransferOptionsOnlineDescription ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TransferOptionsOnlineFunction ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TransferOptionsOnlineLinkage ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TransferOptionsOnlineName ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TransferOptionsOnlineProfile ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TransferOptionsOnlineProtocol ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `User-Agent` | declared,not-observed | `String` | `AtlassianJwtFetcher` | _-_ |
| `UserConstraints ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Work-Type` | declared,not-observed | `String` | `CreativeCommons` | _-_ |
| `X-TIKA:EXCEPTION:container_exception` | declared,not-observed | `internalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:EXCEPTION:embedded_bytes_exception` | declared,not-observed | `internalTextBag` | `TikaCoreProperties` | _-_ |
| `X-TIKA:EXCEPTION:embedded_depth_limit_reached` | declared,not-observed | `internalBoolean` | `TikaCoreProperties` | _-_ |
| `X-TIKA:EXCEPTION:embedded_exception` | declared,not-observed | `internalTextBag` | `TikaCoreProperties` | _-_ |
| `X-TIKA:EXCEPTION:embedded_parser` | declared,not-observed | `internalText` | `ParserUtils` | _-_ |
| `X-TIKA:EXCEPTION:embedded_resource_limit_reached` | declared,not-observed | `internalBoolean` | `TikaCoreProperties` | _-_ |
| `X-TIKA:EXCEPTION:embedded_stream_exception` | declared,not-observed | `internalTextBag` | `TikaCoreProperties` | _-_ |
| `X-TIKA:EXCEPTION:embedded_warning` | declared,not-observed | `internalTextBag` | `TikaCoreProperties` | _-_ |
| `X-TIKA:EXCEPTION:runtime` | declared,not-observed | `externalText` | `ProfilerBase` | _-_ |
| `X-TIKA:EXCEPTION:warn` | declared,not-observed | `internalTextBag` | `TikaCoreProperties` | _-_ |
| `X-TIKA:EXCEPTION:write_limit_reached` | declared,not-observed | `internalBoolean` | `TikaCoreProperties` | _-_ |
| `X-TIKA:Parsed-By` | declared,not-observed | `internalTextBag` | `TikaCoreProperties` | _-_ |
| `X-TIKA:Parsed-By-Full-Set` | declared,not-observed | `internalTextBag` | `TikaCoreProperties` | _-_ |
| `X-TIKA:WARN:truncated_metadata` | declared,not-observed | `internalBoolean` | `TikaCoreProperties` | _-_ |
| `X-TIKA:content` | declared,not-observed | `internalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:content_handler` | declared,not-observed | `internalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:content_handler_type` | declared,not-observed | `internalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:decodedCharset` | declared,not-observed | `externalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:detectedEncoding` | declared,not-observed | `externalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:detected_language` | declared,not-observed | `externalTextBag` | `TikaCoreProperties` | _-_ |
| `X-TIKA:detected_language_confidence` | declared,not-observed | `externalTextBag` | `TikaCoreProperties` | _-_ |
| `X-TIKA:detected_language_confidence_raw` | declared,not-observed | `externalRealSeq` | `TikaCoreProperties` | _-_ |
| `X-TIKA:detection_content_length` | declared,not-observed | `internalInteger` | `TikaCoreProperties` | _-_ |
| `X-TIKA:digest:MD5` | declared,not-observed | `String` | `ProfilerBase` | _-_ |
| `X-TIKA:embeddedRelationshipId` | declared,not-observed | `internalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:embedded_depth` | declared,not-observed | `internalInteger` | `TikaCoreProperties` | _-_ |
| `X-TIKA:embedded_id` | declared,not-observed | `internalInteger` | `TikaCoreProperties` | _-_ |
| `X-TIKA:embedded_id_path` | declared,not-observed | `internalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:embedded_resource_path` | declared,not-observed | `internalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:encodingDetectionTrace` | declared,not-observed | `externalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:encodingDetector` | declared,not-observed | `externalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:encrypted` | declared,not-observed | `internalBoolean` | `TikaCoreProperties` | _-_ |
| `X-TIKA:final_embedded_resource_path` | declared,not-observed | `internalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:internalPath` | declared,not-observed | `internalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:origResourceName` | declared,not-observed | `internalTextBag` | `TikaCoreProperties` | _-_ |
| `X-TIKA:parse_time_millis` | declared,not-observed | `internalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:pdf:metadata-xmp-parse-failed` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `X-TIKA:pipes_result` | declared,not-observed | `externalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:resourceName` | declared,not-observed | `internalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:resourceNameExtensionInferred` | declared,not-observed | `externalBoolean` | `TikaCoreProperties` | _-_ |
| `X-TIKA:sourcePath` | declared,not-observed | `internalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:truncated_content_for_detection` | declared,not-observed | `internalBoolean` | `TikaCoreProperties` | _-_ |
| `X-TIKA:versionCount` | declared,not-observed | `externalInteger` | `TikaCoreProperties` | _-_ |
| `X-TIKA:versionNumber` | declared,not-observed | `externalInteger` | `TikaCoreProperties` | _-_ |
| `X-Tika-Handler` | declared,not-observed | `String` | `TikaResource` | _-_ |
| `X-Tika-OCR-Duration-Ms` | undeclared-literal,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/jpeg` |
| `X-Tika-OCR-Skipped-Reason` | undeclared-literal,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/jpeg` |
| `\(?(?<mainOrganization>[A-Z]\w{1,64}+)\)?((\s?(?<separator>\/)\s?)(\w{1,64}+\s)*\(?(?<secondOrganization>[A-Z]\w{1,64}+)\)?)?(\s(?i:Publication|Standard))?(-|\s)?(?<identifier>([0-9]{3,64}+|([A-Z]{1,64}+(-|_|\.)?[0-9]{2,64}+))((-|_|\.)?[A-Z0-9]{1,64}+){0,64}+)` | declared,not-observed | `String` | `StandardsText` | _-_ |
| `access_permission:assemble_document` | declared,observed | `externalText` | `AccessPermissions` | `application/illustrator`, `application/pdf` |
| `access_permission:can_modify` | declared,observed | `externalTextBag` | `AccessPermissions` | `application/illustrator`, `application/pdf` |
| `access_permission:can_print` | declared,observed | `externalText` | `AccessPermissions` | `application/illustrator`, `application/pdf` |
| `access_permission:can_print_faithful` | declared,observed | `externalText` | `AccessPermissions` | `application/illustrator`, `application/pdf` |
| `access_permission:extract_content` | declared,observed | `externalText` | `AccessPermissions` | `application/illustrator`, `application/pdf` |
| `access_permission:extract_for_accessibility` | declared,observed | `externalText` | `AccessPermissions` | `application/illustrator`, `application/pdf` |
| `access_permission:fill_in_form` | declared,observed | `externalText` | `AccessPermissions` | `application/illustrator`, `application/pdf` |
| `access_permission:modify_annotations` | declared,observed | `externalText` | `AccessPermissions` | `application/illustrator`, `application/pdf` |
| `admin-language` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `application` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `barcode:error-correction-level` | declared,observed | `internalTextBag` | `Barcode` | `image/gif`, `image/jpeg`, `image/png` |
| `barcode:format` | declared,observed | `internalTextBag` | `Barcode` | `image/gif`, `image/jpeg`, `image/png` |
| `barcode:is-mirrored` | declared,observed | `internalTextBag` | `Barcode` | `image/gif`, `image/jpeg`, `image/png` |
| `barcode:position` | declared,observed | `internalTextBag` | `Barcode` | `image/gif`, `image/jpeg`, `image/png` |
| `barcode:raw-bytes` | declared,observed | `internalTextBag` | `Barcode` | `image/gif`, `image/jpeg`, `image/png` |
| `barcode:value` | declared,observed | `internalTextBag` | `Barcode` | `image/gif`, `image/jpeg`, `image/png` |
| `bits` | undeclared-literal,observed | `-` | `-` | `audio/vnd.wave` |
| `channels` | undeclared-literal,observed | `-` | `-` | `audio/mpeg`, `audio/vnd.wave` |
| `cp:category` | declared,observed | `externalText` | `OfficeOpenXMLCore` | `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `cp:contentStatus` | declared,observed | `externalText` | `OfficeOpenXMLCore` | `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-word.template.macroenabled.12` |
| `cp:lastModifiedBy` | declared,not-observed | `externalText` | `OfficeOpenXMLCore` | _-_ |
| `cp:lastPrinted` | declared,not-observed | `externalDate` | `OfficeOpenXMLCore` | _-_ |
| `cp:revision` | declared,observed | `externalText` | `OfficeOpenXMLCore` | `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `cp:subject` | declared,not-observed | `externalText` | `OfficeOpenXMLCore` | _-_ |
| `cp:version` | declared,not-observed | `externalText` | `OfficeOpenXMLCore` | _-_ |
| `createdOn` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `creation-tool` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `creation-tool-version` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `csv:delimiter` | declared,observed | `externalText` | `TextAndCSVParser` | `text/csv` |
| `csv:num_columns` | declared,observed | `externalInteger` | `TextAndCSVParser` | `text/csv` |
| `csv:num_rows` | declared,observed | `externalInteger` | `TextAndCSVParser` | `text/csv` |
| `ctakes:schema` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `custom:ARMSEM` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:AVIWkjEfj` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:AWO` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:AppVersion` | templated,observed | `-` | `-` | `application/vnd.ms-powerpoint`, `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.oasis.opendocument.spreadsheet` |
| `custom:AsjGx0` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:AutosafePathAndName` | templated,observed | `-` | `-` | `application/vnd.ms-excel.addin.macroenabled.12` |
| `custom:BNHSvUxA` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:BRpv9ujLs` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:Base Target` | templated,observed | `-` | `-` | `application/msword` |
| `custom:Business Objects Context Information` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:Business Objects Context Information1` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:Business Objects Context Information2` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:Business Objects Context Information3` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:Business Objects Context Information4` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:Business Objects Context Information5` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:Business Objects Context Information6` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:BzR5V1sq45` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:CTPClassification` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:CTP_BU` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:CTP_IDSID` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:CTP_TimeStamp` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:CTP_WWID` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:Case` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:CaseDescription` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:CaseId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:Category` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:CheckOutDate` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:Classification` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:ClassificationContentMarkingFooterFontProps` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:ClassificationContentMarkingFooterShapeIds` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:ClassificationContentMarkingFooterText` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:Client` | templated,observed | `-` | `-` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:Company` | templated,observed | `-` | `-` | `application/vnd.ms-powerpoint`, `application/vnd.oasis.opendocument.text`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:ComplianceAssetId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:ContentType` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:ContentTypeId` | templated,observed | `-` | `-` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:Created` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:Creator` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:CurrentVersion` | templated,observed | `-` | `-` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:DSBuild` | templated,observed | `-` | `-` | `application/vnd.ms-powerpoint` |
| `custom:DXIdJRFTay` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:DXVersion` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:DateTimeReceived` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `custom:DocSecurity` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.oasis.opendocument.text`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:DocumentID` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:DocumentId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:DocumentenNr` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:E-mail` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:EMAIL_OWNER_ADDRESS` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:EditTemplate` | templated,observed | `-` | `-` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:FHGsprache` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:FHGvorlage` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:FIvNEP` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:FSObjType` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:FileDirRef` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:FileLeafRef` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:From` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `custom:FullFileName` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:GrammarlyDocumentId` | templated,observed | `-` | `-` | `application/msword`, `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:Here_index` | templated,observed | `-` | `-` | `application/msword` |
| `custom:HiddenSlides` | templated,observed | `-` | `-` | `application/vnd.ms-powerpoint` |
| `custom:HistoryId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:HtmlTempFilePath` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:HyperlinksChanged` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.oasis.opendocument.text`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:ICQ` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:ICV` | templated,observed | `-` | `-` | `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:IJmaSdV2` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:IbpWorkbookKeyString_GUID` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:Id` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:IsATDocument` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:IsMyDocuments` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:ItemClass` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `custom:ItemId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:JWnM6Bg` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:JyMVYox` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:KSOProductBuildVer` | templated,observed | `-` | `-` | `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:KdQ6sS8P` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:LastSaved` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:LinksUpToDate` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.oasis.opendocument.text`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:LockGuid` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MAIL_MSG_ID1` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MAIL_MSG_ID2` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MDIzLZpMG` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:MMClips` | templated,observed | `-` | `-` | `application/vnd.ms-powerpoint` |
| `custom:MP_InheritedTags` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:MPbroK3PDqE` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:MSIP_Label_00b5fe95-8f20-4bf1-a4bc-7cba4c4dcd39_ActionId` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_00b5fe95-8f20-4bf1-a4bc-7cba4c4dcd39_ContentBits` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_00b5fe95-8f20-4bf1-a4bc-7cba4c4dcd39_Enabled` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_00b5fe95-8f20-4bf1-a4bc-7cba4c4dcd39_Method` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_00b5fe95-8f20-4bf1-a4bc-7cba4c4dcd39_Name` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_00b5fe95-8f20-4bf1-a4bc-7cba4c4dcd39_SetDate` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_00b5fe95-8f20-4bf1-a4bc-7cba4c4dcd39_SiteId` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_09e9a456-2778-4ca9-be06-1190b1e1118a_ActionId` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_09e9a456-2778-4ca9-be06-1190b1e1118a_ContentBits` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_09e9a456-2778-4ca9-be06-1190b1e1118a_Enabled` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_09e9a456-2778-4ca9-be06-1190b1e1118a_Method` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_09e9a456-2778-4ca9-be06-1190b1e1118a_Name` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_09e9a456-2778-4ca9-be06-1190b1e1118a_SetDate` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_09e9a456-2778-4ca9-be06-1190b1e1118a_SiteId` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_15eba05f-5928-437b-aac0-a57b2de74a26_ActionId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_15eba05f-5928-437b-aac0-a57b2de74a26_ContentBits` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_15eba05f-5928-437b-aac0-a57b2de74a26_Enabled` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_15eba05f-5928-437b-aac0-a57b2de74a26_Method` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_15eba05f-5928-437b-aac0-a57b2de74a26_Name` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_15eba05f-5928-437b-aac0-a57b2de74a26_SetDate` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_15eba05f-5928-437b-aac0-a57b2de74a26_SiteId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_32905e9b-f125-48f4-ac14-e6cdbe91ddbf_ActionId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_32905e9b-f125-48f4-ac14-e6cdbe91ddbf_ContentBits` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_32905e9b-f125-48f4-ac14-e6cdbe91ddbf_Enabled` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_32905e9b-f125-48f4-ac14-e6cdbe91ddbf_Method` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_32905e9b-f125-48f4-ac14-e6cdbe91ddbf_Name` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_32905e9b-f125-48f4-ac14-e6cdbe91ddbf_SetDate` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_32905e9b-f125-48f4-ac14-e6cdbe91ddbf_SiteId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_340ed6a7-0f03-43d9-901d-02d4a7e408aa_ActionId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_340ed6a7-0f03-43d9-901d-02d4a7e408aa_ContentBits` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_340ed6a7-0f03-43d9-901d-02d4a7e408aa_Enabled` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_340ed6a7-0f03-43d9-901d-02d4a7e408aa_Method` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_340ed6a7-0f03-43d9-901d-02d4a7e408aa_Name` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_340ed6a7-0f03-43d9-901d-02d4a7e408aa_SetDate` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_340ed6a7-0f03-43d9-901d-02d4a7e408aa_SiteId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_36791f77-3d39-4d72-9277-ac879ec799ed_ActionId` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:MSIP_Label_36791f77-3d39-4d72-9277-ac879ec799ed_ContentBits` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:MSIP_Label_36791f77-3d39-4d72-9277-ac879ec799ed_Enabled` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:MSIP_Label_36791f77-3d39-4d72-9277-ac879ec799ed_Method` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:MSIP_Label_36791f77-3d39-4d72-9277-ac879ec799ed_Name` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:MSIP_Label_36791f77-3d39-4d72-9277-ac879ec799ed_SetDate` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:MSIP_Label_36791f77-3d39-4d72-9277-ac879ec799ed_SiteId` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:MSIP_Label_38c50358-8241-4bd4-82ad-acbc3e7e1546_ActionId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_38c50358-8241-4bd4-82ad-acbc3e7e1546_ContentBits` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_38c50358-8241-4bd4-82ad-acbc3e7e1546_Enabled` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_38c50358-8241-4bd4-82ad-acbc3e7e1546_Method` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_38c50358-8241-4bd4-82ad-acbc3e7e1546_Name` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_38c50358-8241-4bd4-82ad-acbc3e7e1546_SetDate` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_38c50358-8241-4bd4-82ad-acbc3e7e1546_SiteId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_5895c9ec-d095-4de7-bc86-cb1dea48d221_ActionId` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:MSIP_Label_5895c9ec-d095-4de7-bc86-cb1dea48d221_ContentBits` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:MSIP_Label_5895c9ec-d095-4de7-bc86-cb1dea48d221_Enabled` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:MSIP_Label_5895c9ec-d095-4de7-bc86-cb1dea48d221_Method` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:MSIP_Label_5895c9ec-d095-4de7-bc86-cb1dea48d221_Name` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:MSIP_Label_5895c9ec-d095-4de7-bc86-cb1dea48d221_SetDate` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:MSIP_Label_5895c9ec-d095-4de7-bc86-cb1dea48d221_SiteId` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:MSIP_Label_9238af61-cfb1-43e3-a724-fe68a71eee05_ActionId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_9238af61-cfb1-43e3-a724-fe68a71eee05_ContentBits` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_9238af61-cfb1-43e3-a724-fe68a71eee05_Enabled` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_9238af61-cfb1-43e3-a724-fe68a71eee05_Method` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_9238af61-cfb1-43e3-a724-fe68a71eee05_Name` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_9238af61-cfb1-43e3-a724-fe68a71eee05_SetDate` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_9238af61-cfb1-43e3-a724-fe68a71eee05_SiteId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_9238af61-cfb1-43e3-a724-fe68a71eee05_Tag` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_a245aec4-c4dc-4701-9d28-79032dd82e3b_Application` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_a245aec4-c4dc-4701-9d28-79032dd82e3b_Enabled` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_a245aec4-c4dc-4701-9d28-79032dd82e3b_Extended_MSFT_Method` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_a245aec4-c4dc-4701-9d28-79032dd82e3b_Name` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_a245aec4-c4dc-4701-9d28-79032dd82e3b_Owner` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_a245aec4-c4dc-4701-9d28-79032dd82e3b_SetDate` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_a245aec4-c4dc-4701-9d28-79032dd82e3b_SiteId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_b4afcec3-1c3f-46cc-9170-fdf0815f76db_ActionId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_b4afcec3-1c3f-46cc-9170-fdf0815f76db_ContentBits` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_b4afcec3-1c3f-46cc-9170-fdf0815f76db_Enabled` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_b4afcec3-1c3f-46cc-9170-fdf0815f76db_Method` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_b4afcec3-1c3f-46cc-9170-fdf0815f76db_Name` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_b4afcec3-1c3f-46cc-9170-fdf0815f76db_SetDate` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_b4afcec3-1c3f-46cc-9170-fdf0815f76db_SiteId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_c680b812-6168-496e-9a41-9d7bd71f8c3d_ActionId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_c680b812-6168-496e-9a41-9d7bd71f8c3d_ContentBits` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_c680b812-6168-496e-9a41-9d7bd71f8c3d_Enabled` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_c680b812-6168-496e-9a41-9d7bd71f8c3d_Method` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_c680b812-6168-496e-9a41-9d7bd71f8c3d_Name` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_c680b812-6168-496e-9a41-9d7bd71f8c3d_SetDate` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_c680b812-6168-496e-9a41-9d7bd71f8c3d_SiteId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_d5b8f4d7-14bc-4a30-8a91-299e587fa409_ActionId` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_d5b8f4d7-14bc-4a30-8a91-299e587fa409_ContentBits` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_d5b8f4d7-14bc-4a30-8a91-299e587fa409_Enabled` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_d5b8f4d7-14bc-4a30-8a91-299e587fa409_Method` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_d5b8f4d7-14bc-4a30-8a91-299e587fa409_Name` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_d5b8f4d7-14bc-4a30-8a91-299e587fa409_SetDate` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_d5b8f4d7-14bc-4a30-8a91-299e587fa409_SiteId` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_defa4170-0d19-0005-0004-bc88714345d2_ActionId` | templated,observed | `-` | `-` | `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_defa4170-0d19-0005-0004-bc88714345d2_ContentBits` | templated,observed | `-` | `-` | `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_defa4170-0d19-0005-0004-bc88714345d2_Enabled` | templated,observed | `-` | `-` | `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_defa4170-0d19-0005-0004-bc88714345d2_Method` | templated,observed | `-` | `-` | `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_defa4170-0d19-0005-0004-bc88714345d2_Name` | templated,observed | `-` | `-` | `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_defa4170-0d19-0005-0004-bc88714345d2_SetDate` | templated,observed | `-` | `-` | `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_defa4170-0d19-0005-0004-bc88714345d2_SiteId` | templated,observed | `-` | `-` | `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MSIP_Label_e463cba9-5f6c-478d-9329-7b2295e4e8ed_ActionId` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_e463cba9-5f6c-478d-9329-7b2295e4e8ed_ContentBits` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_e463cba9-5f6c-478d-9329-7b2295e4e8ed_Enabled` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_e463cba9-5f6c-478d-9329-7b2295e4e8ed_Method` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_e463cba9-5f6c-478d-9329-7b2295e4e8ed_Name` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_e463cba9-5f6c-478d-9329-7b2295e4e8ed_SetDate` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_e463cba9-5f6c-478d-9329-7b2295e4e8ed_SiteId` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:MSIP_Label_fe213162-8742-4817-ab6f-53da7c79e427_ActionId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_fe213162-8742-4817-ab6f-53da7c79e427_ContentBits` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_fe213162-8742-4817-ab6f-53da7c79e427_Enabled` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_fe213162-8742-4817-ab6f-53da7c79e427_Method` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_fe213162-8742-4817-ab6f-53da7c79e427_Name` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_fe213162-8742-4817-ab6f-53da7c79e427_SetDate` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_fe213162-8742-4817-ab6f-53da7c79e427_SiteId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MTWinEqns` | templated,observed | `-` | `-` | `application/msword` |
| `custom:MediaServiceImageTags` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:NSCPROP` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:NSCPROP_SA` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:Name` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:Notes` | templated,observed | `-` | `-` | `application/vnd.ms-powerpoint`, `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:Office` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:Order` | templated,observed | `-` | `-` | `application/msword`, `application/vnd.ms-outlook`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:OutlookID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `custom:Owner` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:PROP1` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:PROP2` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:Para_digit` | templated,observed | `-` | `-` | `application/msword` |
| `custom:Period` | templated,observed | `-` | `-` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:PeriodLength` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:Periodicity` | templated,observed | `-` | `-` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:PicturePath` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:PresentationFormat` | templated,observed | `-` | `-` | `application/vnd.ms-powerpoint`, `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:Producer` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:ProtectBook` | templated,observed | `-` | `-` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:PublishingContactPicture` | templated,observed | `-` | `-` | `application/msword` |
| `custom:PublishingVariationRelationshipLinkFieldID` | templated,observed | `-` | `-` | `application/msword` |
| `custom:QZyiGwa1Na` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:RESPONSE_SENDER_NAME` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:Region` | templated,observed | `-` | `-` | `application/msword` |
| `custom:ResourceType` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:RootDocFilePath` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:RqUxusf0HsD` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:Rules` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:SPHFHQpY56` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:SRA5lB` | templated,observed | `-` | `-` | `application/msword` |
| `custom:SV_HIDDEN_GRID_QUERY_LIST_4F35BF76-6C0D-4D9B-82B2-816C12CF3733` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:SV_QUERY_LIST_4F35BF76-6C0D-4D9B-82B2-816C12CF3733` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:ScaleCrop` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.oasis.opendocument.text`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:Sensitivity` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:ShareDoc` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.oasis.opendocument.text`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:Skype` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:Slides` | templated,observed | `-` | `-` | `application/vnd.ms-powerpoint`, `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:SmartPDA` | templated,observed | `-` | `-` | `application/msword` |
| `custom:SmartPDA_date` | templated,observed | `-` | `-` | `application/msword` |
| `custom:SpecialProps` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:SpecialProps1` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:SpecialProps2` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:SpecialProps3` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:Status` | templated,observed | `-` | `-` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:Subjectxx` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `custom:T9yWLom5` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:TTQo3zW_W4WV` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:TaxKeyword` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:TaxKeywordTaxHTField` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:Team` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:TeamType` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:Template Type` | templated,observed | `-` | `-` | `application/msword` |
| `custom:TemplateId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:TemplateOperationMode` | templated,observed | `-` | `-` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:TemplateUrl` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:TitleSection1_IsVisible` | templated,observed | `-` | `-` | `application/msword` |
| `custom:TitleSection2_IsVisible` | templated,observed | `-` | `-` | `application/msword` |
| `custom:TitleSection3_IsVisible` | templated,observed | `-` | `-` | `application/msword` |
| `custom:TitleSection4_IsVisible` | templated,observed | `-` | `-` | `application/msword` |
| `custom:TitleSection5_IsVisible` | templated,observed | `-` | `-` | `application/msword` |
| `custom:TitleSection6_IsVisible` | templated,observed | `-` | `-` | `application/msword` |
| `custom:TitleSection7_IsVisible` | templated,observed | `-` | `-` | `application/msword` |
| `custom:TitleSection8_IsVisible` | templated,observed | `-` | `-` | `application/msword` |
| `custom:TitleSection9_IsVisible` | templated,observed | `-` | `-` | `application/msword` |
| `custom:TitusGUID` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:ToRecipients` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `custom:Topic` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:TriggerFlowInfo` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:Ts9FjKo` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:TypePlanning` | templated,observed | `-` | `-` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:UYga2F0odV` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:UserComments` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:VERSION` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:VLXvd0Ge` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:Validate` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:Vbu2wL9e` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:Version` | templated,observed | `-` | `-` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:VersionCheckDate` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:VlnXmN0guA` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:WK_DOCNR` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:WK_SCAN_DOCNR` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:Wegen` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:WorkbookGuid` | templated,observed | `-` | `-` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:XMLTempFilePath` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:XslViewFilePath` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:XsltDocFilePath` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:Y1ejXi7I` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:Ylvv04YDPIcJ` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:ZXL1dWpx` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:ZcAx_B4PhSlE` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:[1qNj1aVD0qR-]0:0` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:[2G-hZUFn1q-b0ap-0bRV1GljYWR-ZA]0:0` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:[2G-hZURj2qtg0qF9ZWQ]0:0` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:[2XBg0qF9ZWRC3Q]0:0` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:[YWN80rVi2GF7_Wld2H9]0:0` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:[YWNo_XZd2H-JRA]0:0` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:[YXRgYXNWZXJn_Wxi]0:0` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:[Yqxp1bN-SUQ]0:0` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:[ZGxr0aljYWR-ZEJtRWp6_Wk]0:0` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:[ZGxr0aljYWR-ZEJtTaFhZQ]0:0` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:[ZGxr0aljYWR-ZEJtVXN-19-E]0:0` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:_2015_ms_pID_725343` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:_2015_ms_pID_7253431` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:_2015_ms_pID_7253432` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:_AdHocReviewCycleID` | templated,observed | `-` | `-` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:_AuthorEmail` | templated,observed | `-` | `-` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:_AuthorEmailDisplayName` | templated,observed | `-` | `-` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:_DocHome` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:_EmailSubject` | templated,observed | `-` | `-` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:_ExtendedDescription` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:_LCID` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:_MarkAsFinal` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-word.template.macroenabled.12` |
| `custom:_NewReviewCycle` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:_PreviousAdHocReviewCycleID` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:_ReviewingToolsShownOnce` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:_TemplateID` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:_Version` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:_dlc_DocId` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:_dlc_DocIdItemGuid` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:_dlc_DocIdUrl` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:aRcAn7h` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:acltywld` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:adwjwHpmj4` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:aeuxaksgyt` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:ahslzjxxpd` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:aoktgdcwhd` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:bTmnSGUkHf` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:bZtl5EtGo` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:befajenekz` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:bjDocumentLabelXML` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:bjDocumentLabelXML-0` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:bjDocumentSecurityLabel` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:bjSaver` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:bpvwfgoprq` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:byrfszjxss` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:cckunotd` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:ce8uzg3R3N` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:d4uQ2bk9K` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:dabxclsirv` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:daxtra.config` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:dkjtobdw` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:dnprjujdxt` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:docIndexRef` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:dpufEuqZ` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:dxzcltnr` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:eDOCS AutoSave` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:efhwgx3j` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:emBueOJG` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:entityid` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:epsotnyxlz` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:eqkcqnyqlj` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:euuotsvvfv` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:facnvlao` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:fnauzsllub` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:gXhEOIO` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:gggfkwukpj` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:graderDownloaded` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:graderName` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:gzoyzbjkom` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:hasChanged` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:htnuyavfyt` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:hwzwlmucsi` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:hydhoitk` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:iJFbkJlmngsO` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:ibemiufpkb` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:iqwovdyz` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:itflkjnsbn` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:jTmN1kaN` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:jcovssgsmo` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:jqw2x9kXv` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:kWZWK373Lvj` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:kaxrpogofh` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:keywords` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:klassifizierung` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:krddsiqwel` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:kwhjqsvsfa` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:l3qDvt3B53wxeXu` | templated,observed | `-` | `-` | `application/msword` |
| `custom:lPWHjGcKsRH` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:lcsF7Ywp8cvKE` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:lrmHIVGaU9Rz` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:lvpklVoK2` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:lynzzyjull` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:mfgwmnwbyr` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:migmsnkneg` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:mioracly` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:mmuizzudln` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:modIZsYpblY` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:moxmzemkcv` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:nsitxxbclo` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:nueycvqalh` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:nvipvuxr` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:nwbDMZfxOqQ` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:nzl0u_W71` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:oNGeXp_xMb` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:ojilpsys` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:orelgusj` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:otacifhj` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:oyAdz7Y2X` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:pabgafdgix` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:pageCount` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:pogykhfy` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:qecybiwgos` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:qmsVyxGtW` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:qqzhrpwb` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:qrUHpwzT` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:qtosbjbdjp` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:qxnjmlrb` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:rdyyhuzwwj` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:reyvmilj` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:rquqtsnzfj` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:rrubvldasu` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:rtrbklvvlh` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:sNLlbz1_LI` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:skrilrvzjp` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:sovhdwsx` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:soydwgtlsg` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:tmpGuid` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:tnrlsujggv` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:tsvmhxkqol` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:ttprwbqemf` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:tykkrrym` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:unqclxbpfl` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:urlktytc` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:vIMKde1z` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:vTusKOVa` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:version` | templated,observed | `-` | `-` | `application/vnd.ms-powerpoint` |
| `custom:vhtfizio` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:vifsnqjx` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:vkO6ICY1B` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:vrHPyPHlo7` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:vzednxfvcv` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:wpsbvlqc` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:xajdhloxgs` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:xd_ProgID` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:xd_Signature` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:xknqcrcogc` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:xvynqqlc` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:yNnVH9taSbv9` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:yqwwgxzy` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:yqxrrkcjej` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:ytLkYCPV` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:yysspixpwc` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:zUTunJgwBO` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:zlukmrubaz` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:zrjbiafine` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:zvmsubdfzh` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:Сайт` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:參照` | templated,observed | `-` | `-` | `application/msword` |
| `custom:审阅者` | templated,observed | `-` | `-` | `application/msword` |
| `data-type` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `database:column_count` | declared,not-observed | `externalInteger` | `Database` | _-_ |
| `database:column_name` | declared,not-observed | `externalTextBag` | `Database` | _-_ |
| `database:row_count` | declared,not-observed | `externalInteger` | `Database` | _-_ |
| `database:table_name` | declared,not-observed | `externalTextBag` | `Database` | _-_ |
| `dc:contributor` | declared,not-observed | `internalTextBag` | `DublinCore` | _-_ |
| `dc:coverage` | declared,not-observed | `internalTextBag` | `DublinCore` | _-_ |
| `dc:creator` | declared,observed | `internalTextBag` | `DublinCore` | `application/msword`, `application/pdf`, `application/rtf` |
| `dc:date` | declared,not-observed | `internalDate` | `DublinCore` | _-_ |
| `dc:description` | declared,observed | `internalTextBag` | `DublinCore` | `application/pdf`, `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `dc:description:x-default` | templated,observed | `-` | `-` | `application/pdf` |
| `dc:format` | declared,observed | `internalText` | `DublinCore` | `application/illustrator`, `application/pdf`, `application/xml` |
| `dc:identifier` | declared,observed | `internalTextBag` | `DublinCore` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/xml`, `message/rfc822` |
| `dc:language` | declared,observed | `internalTextBag` | `DublinCore` | `application/pdf`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12` |
| `dc:publisher` | declared,observed | `internalTextBag` | `DublinCore` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `dc:relation` | declared,observed | `internalTextBag` | `DublinCore` | `message/rfc822` |
| `dc:rights` | declared,not-observed | `internalTextBag` | `DublinCore` | _-_ |
| `dc:source` | declared,not-observed | `internalTextBag` | `DublinCore` | _-_ |
| `dc:subject` | declared,observed | `internalTextBag` | `DublinCore` | `application/msword`, `application/pdf`, `application/vnd.ms-excel` |
| `dc:title` | declared,observed | `internalTextBag` | `DublinCore` | `application/illustrator`, `application/msword`, `application/pdf` |
| `dc:title:x-default` | templated,observed | `-` | `-` | `application/pdf` |
| `dc:type` | declared,not-observed | `internalTextBag` | `DublinCore` | _-_ |
| `dcterms:created` | declared,observed | `internalDate` | `DublinCore` | `application/illustrator`, `application/msword`, `application/pdf` |
| `dcterms:modified` | declared,observed | `internalDate` | `DublinCore` | `application/illustrator`, `application/msword`, `application/octet-stream` |
| `divisionType` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `docx_color_qr:decode_count` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `docx_color_qr:maxcols` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `docx_color_qr:rows` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `dwg:applicationComment` | declared,not-observed | `externalText` | `DWG` | _-_ |
| `dwg:applicationName` | declared,not-observed | `externalText` | `DWG` | _-_ |
| `dwg:applicationVersion` | declared,not-observed | `externalText` | `DWG` | _-_ |
| `dwg:productInfo` | declared,not-observed | `externalText` | `DWG` | _-_ |
| `editing-cycles` | declared,observed | `externalText` | `OpenDocumentMetaParser` | `application/vnd.oasis.opendocument.presentation`, `application/vnd.oasis.opendocument.spreadsheet`, `application/vnd.oasis.opendocument.text` |
| `embeddedResourceType` | declared,observed | `internalClosedChoise` | `TikaCoreProperties` | `application/gzip`, `application/java-archive`, `application/json` |
| `emf:iconOnly` | declared,observed | `internalBoolean` | `EMFParser` | `image/emf` |
| `emf:iconString` | declared,observed | `internalText` | `EMFParser` | `image/emf` |
| `encoding` | undeclared-literal,observed | `-` | `-` | `audio/vnd.wave` |
| `endian` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `envi.lat/lon` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `epub:rendition:layout` | declared,not-observed | `externalClosedChoise` | `Epub` | _-_ |
| `epub:version` | declared,not-observed | `externalText` | `Epub` | _-_ |
| `exif:DateTimeOriginal` | declared,observed | `internalDate` | `TIFF` | `image/jpeg` |
| `exif:ExposureTime` | declared,observed | `internalRational` | `TIFF` | `image/jpeg` |
| `exif:FNumber` | declared,observed | `internalRational` | `TIFF` | `image/jpeg` |
| `exif:Flash` | declared,observed | `internalBoolean` | `TIFF` | `image/jpeg` |
| `exif:FocalLength` | declared,observed | `internalRational` | `TIFF` | `image/jpeg` |
| `exif:IsoSpeedRatings` | declared,observed | `internalIntegerSequence` | `TIFF` | `image/jpeg` |
| `exif:PageCount` | declared,not-observed | `externalInteger` | `TIFF` | _-_ |
| `extended-properties:AppVersion` | declared,observed | `externalText` | `OfficeOpenXMLExtended` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `extended-properties:Application` | declared,observed | `externalText` | `OfficeOpenXMLExtended` | `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-excel.addin.macroenabled.12` |
| `extended-properties:Company` | declared,observed | `externalText` | `OfficeOpenXMLExtended` | `application/msword`, `application/rtf`, `application/vnd.ms-excel` |
| `extended-properties:DocSecurity` | declared,observed | `externalInteger` | `OfficeOpenXMLExtended` | `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `extended-properties:DocSecurityString` | declared,observed | `externalClosedChoise` | `OfficeOpenXMLExtended` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `extended-properties:HiddedSlides` | declared,not-observed | `externalInteger` | `OfficeOpenXMLExtended` | _-_ |
| `extended-properties:Manager` | declared,observed | `externalTextBag` | `OfficeOpenXMLExtended` | `application/msword`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `extended-properties:Notes` | declared,observed | `externalInteger` | `OfficeOpenXMLExtended` | `application/vnd.ms-powerpoint.presentation.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12`, `application/vnd.ms-powerpoint.template.macroenabled.12` |
| `extended-properties:PresentationFormat` | declared,observed | `externalText` | `OfficeOpenXMLExtended` | `application/vnd.ms-powerpoint.presentation.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12`, `application/vnd.ms-powerpoint.template.macroenabled.12` |
| `extended-properties:Template` | declared,observed | `externalText` | `OfficeOpenXMLExtended` | `application/msword`, `application/rtf`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `extended-properties:TotalTime` | declared,observed | `externalInteger` | `OfficeOpenXMLExtended` | `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `external-process:exit-value` | declared,not-observed | `externalInteger` | `ExternalProcess` | _-_ |
| `external-process:stderr` | declared,not-observed | `externalText` | `ExternalProcess` | _-_ |
| `external-process:stderr-length` | declared,not-observed | `externalReal` | `ExternalProcess` | _-_ |
| `external-process:stderr-truncated` | declared,not-observed | `externalBoolean` | `ExternalProcess` | _-_ |
| `external-process:stdout` | declared,not-observed | `externalText` | `ExternalProcess` | _-_ |
| `external-process:stdout-length` | declared,not-observed | `externalReal` | `ExternalProcess` | _-_ |
| `external-process:stdout-truncated` | declared,not-observed | `externalBoolean` | `ExternalProcess` | _-_ |
| `external-process:timeout` | declared,not-observed | `externalBoolean` | `ExternalProcess` | _-_ |
| `file-count` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `file:mime` | declared,not-observed | `externalText` | `FileCommandDetector` | _-_ |
| `fileType` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `font:name` | declared,not-observed | `internalTextBag` | `Font` | _-_ |
| `format` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `fs:accessed` | declared,not-observed | `externalDate` | `FileSystem` | _-_ |
| `fs:created` | declared,not-observed | `externalDate` | `FileSystem` | _-_ |
| `fs:modified` | declared,not-observed | `externalDate` | `FileSystem` | _-_ |
| `fulltext` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `generator` | declared,observed | `externalText` | `OpenDocumentMetaParser` | `application/vnd.oasis.opendocument.presentation`, `application/vnd.oasis.opendocument.spreadsheet`, `application/vnd.oasis.opendocument.text` |
| `geo:alt` | declared,not-observed | `internalReal` | `Geographic` | _-_ |
| `geo:lat` | declared,observed | `internalReal` | `Geographic` | `image/jpeg` |
| `geo:long` | declared,observed | `internalReal` | `Geographic` | `image/jpeg` |
| `geo:timestamp` | declared,observed | `internalDate` | `Geographic` | `image/jpeg` |
| `hasAudio` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `hasSignature` | declared,observed | `internalBoolean` | `TikaCoreProperties` | `application/pdf`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `hasVideo` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `html: bronchium unweeded lugubrious inclosing marble waifish curter numbfish eurythermal skateboarding sylva biogeographer retrials ziggurats ditched epigrapher checkbook pratfall invectives seacrafts nelumbos quadruplets dovishnesses detainers titanite wince chlorophyllous styed mawn terrae mousetrap mosquitoey mislodging dopily widowbirds blisses fermatas dissuaders carotenoids glairs marshalcy pretermitted lavisher cadential loathness inactivate inductances goosefleshes darkroom videotex mudfishes amalgamate` | templated,observed | `-` | `-` | `text/html` |
| `html: coasted lambrequins tombs overorganizes skyboxes bawling bohos gonglike snazziest nongonococcal lipoproteins regardless rebuttons prednisolones auntlier emmetrope conical weatherglass educible outspelling inflows cyprians outorganized pearwood pinky antiglare madam slaughterhouse thistliest jemmies plexal tutees oligophagous reendow sassier hoodier prognosticates landslide pantomimed immaterialisms indoctrinating snickersnees engraves colon omission subdebs homburg cryoprobes dismember extortionist cliffy zoophobes ripple pharisees anisogamy diverted electresses inflater uniforms superstrings` | templated,observed | `-` | `-` | `text/html` |
| `html: equivocating unexcited alliums balefire recoins` | templated,observed | `-` | `-` | `text/html` |
| `html: halftone crepuscles cassises gypsophilas tomcods solved strudels offcuts ultraist etiquette undressed paediatricians arcadings didactical evensongs purveyance yearbooks suboptic oximetries dumpiest aquarium superstimulate bicorne voice` | templated,observed | `-` | `-` | `text/html` |
| `html: hulloes windsurf cyclicalities dislocate strays exceptionably fashionable chappatis neocortex swingeing overdiversities calibrates anvil appendicular plasmatic brings ultrarealist comprador efficacies tody troweler wonderments marsupial supersmart hoof brassing windows embryotic acacias slandered supercilious unsilent guacamoles drillability unprovable ralliform melanosis gladsomenesses spryer influx pinitol tobogganing sergers haecceities chillums salmonella azotic scything imitatively correlational peripheral roaringly pietistic lethargy coypus` | templated,observed | `-` | `-` | `text/html` |
| `html: individuate snubness ailurophobe misconstrued drier ironhearted ain cavetto epitaxic subsatellites doxorubicins campanulate mesmeric alertly calvaries scrollworks mismarriages lamperses monofil penguins sika specifics vagotonia tressures licensures knotgrass recrudescence demonstrably obnoxiousness obtrudes elodeas turnspit haphazardries heliozoan fustier nailhead unblinded iridosmine endogamy zikurat stogies sternpost` | templated,observed | `-` | `-` | `text/html` |
| `html: reliability dissociating ankles sedan completes occipita canter slipup propranolol delegatees injectant handbill overlending expatriates declinists churchman cytoplasm tourings mendicancy decertified horoscopy sleazeballs` | templated,observed | `-` | `-` | `text/html` |
| `html: tarnished shopwindows diastasic reaphook besmirch dapples sapper vitiligo highspots bactericidally graffiting awls unmew lubricant ostensoria rotavirus verists exoskeletal periostitises familiarnesses chatchkas fretsaws immolators photospheres preambles melanitic argalis embarked` | templated,observed | `-` | `-` | `text/html` |
| `html:416c6c20796f7572206261736520` | templated,observed | `-` | `-` | `application/xhtml+xml` |
| `html:6a97888e-site-verification` | templated,observed | `-` | `-` | `text/html` |
| `html:Content-Language` | templated,observed | `-` | `-` | `application/xhtml+xml` |
| `html:Content-Script-Type` | templated,observed | `-` | `-` | `application/xhtml+xml` |
| `html:Content-Style-Type` | templated,observed | `-` | `-` | `application/xhtml+xml` |
| `html:Expires` | templated,observed | `-` | `-` | `text/html` |
| `html:GENERATOR` | templated,observed | `-` | `-` | `application/xhtml+xml`, `text/html` |
| `html:Generator` | templated,observed | `-` | `-` | `text/html` |
| `html:LocLC` | templated,observed | `-` | `-` | `text/html` |
| `html:PageID` | templated,observed | `-` | `-` | `text/html` |
| `html:Pragma` | templated,observed | `-` | `-` | `text/html` |
| `html:ProgId` | templated,observed | `-` | `-` | `text/html` |
| `html:REFRESH` | templated,observed | `-` | `-` | `text/html` |
| `html:Refresh` | templated,observed | `-` | `-` | `text/html` |
| `html:ReqLC` | templated,observed | `-` | `-` | `text/html` |
| `html:X-MS-Activation` | templated,observed | `-` | `-` | `text/html` |
| `html:X-MS-Office365-Version` | templated,observed | `-` | `-` | `text/html` |
| `html:X-MS-Service-Status` | templated,observed | `-` | `-` | `text/html` |
| `html:X-Service-Version` | templated,observed | `-` | `-` | `text/html` |
| `html:X-System` | templated,observed | `-` | `-` | `text/html` |
| `html:X-UA-Compatible` | templated,observed | `-` | `-` | `application/xhtml+xml`, `text/html` |
| `html:al:android:app_name` | templated,observed | `-` | `-` | `text/html` |
| `html:al:android:package` | templated,observed | `-` | `-` | `text/html` |
| `html:al:android:url` | templated,observed | `-` | `-` | `text/html` |
| `html:al:ios:app_name` | templated,observed | `-` | `-` | `text/html` |
| `html:al:ios:app_store_id` | templated,observed | `-` | `-` | `text/html` |
| `html:al:ios:url` | templated,observed | `-` | `-` | `text/html` |
| `html:amp-cookie-scope` | templated,observed | `-` | `-` | `text/html` |
| `html:amp-google-client-id-api` | templated,observed | `-` | `-` | `text/html` |
| `html:amp-usqp` | templated,observed | `-` | `-` | `text/html` |
| `html:amp4ads-id` | templated,observed | `-` | `-` | `text/html` |
| `html:analytics-location` | templated,observed | `-` | `-` | `text/html` |
| `html:appId` | templated,observed | `-` | `-` | `text/html` |
| `html:apple-itunes-app` | templated,observed | `-` | `-` | `text/html` |
| `html:apple-mobile-web-app-capable` | templated,observed | `-` | `-` | `text/html` |
| `html:apple-mobile-web-app-status-bar-style` | templated,observed | `-` | `-` | `text/html` |
| `html:application-title` | templated,observed | `-` | `-` | `text/html` |
| `html:application.version` | templated,observed | `-` | `-` | `text/html` |
| `html:article:modified_time` | templated,observed | `-` | `-` | `text/html` |
| `html:article:published_time` | templated,observed | `-` | `-` | `text/html` |
| `html:bingbot` | templated,observed | `-` | `-` | `text/html` |
| `html:browser-errors-url` | templated,observed | `-` | `-` | `text/html` |
| `html:browser-stats-url` | templated,observed | `-` | `-` | `text/html` |
| `html:chrome` | templated,observed | `-` | `-` | `text/html` |
| `html:color-scheme` | templated,observed | `-` | `-` | `text/html` |
| `html:current-catalog-service-hash` | templated,observed | `-` | `-` | `text/html` |
| `html:dc:title` | templated,observed | `-` | `-` | `text/html` |
| `html:dcterms.issued` | templated,observed | `-` | `-` | `application/xhtml+xml` |
| `html:domain` | templated,observed | `-` | `-` | `text/html` |
| `html:expected-hostname` | templated,observed | `-` | `-` | `text/html` |
| `html:fb:admins` | templated,observed | `-` | `-` | `text/html` |
| `html:fb:app_id` | templated,observed | `-` | `-` | `text/html` |
| `html:format-detection` | templated,observed | `-` | `-` | `text/html` |
| `html:gdpr` | templated,observed | `-` | `-` | `text/html` |
| `html:generator` | templated,observed | `-` | `-` | `text/html` |
| `html:github-keyboard-shortcuts` | templated,observed | `-` | `-` | `text/html` |
| `html:go-import` | templated,observed | `-` | `-` | `text/html` |
| `html:google-adsense-account` | templated,observed | `-` | `-` | `text/html` |
| `html:google-site-verification` | templated,observed | `-` | `-` | `text/html` |
| `html:google-translate-customization` | templated,observed | `-` | `-` | `application/xhtml+xml` |
| `html:googlebot` | templated,observed | `-` | `-` | `text/html` |
| `html:googlebot-news` | templated,observed | `-` | `-` | `text/html` |
| `html:hostname` | templated,observed | `-` | `-` | `text/html` |
| `html:hovercard-subject-tag` | templated,observed | `-` | `-` | `text/html` |
| `html:html-safe-nonce` | templated,observed | `-` | `-` | `text/html` |
| `html:instapp:owner_user_id` | templated,observed | `-` | `-` | `text/html` |
| `html:language` | templated,observed | `-` | `-` | `text/html` |
| `html:medium` | templated,observed | `-` | `-` | `text/html` |
| `html:mobile-web-app-capable` | templated,observed | `-` | `-` | `text/html` |
| `html:msapplication-TileColor` | templated,observed | `-` | `-` | `application/xhtml+xml` |
| `html:msapplication-TileImage` | templated,observed | `-` | `-` | `text/html` |
| `html:msapplication-config` | templated,observed | `-` | `-` | `text/html` |
| `html:msapplication-tap-highlight` | templated,observed | `-` | `-` | `text/html` |
| `html:msnbot` | templated,observed | `-` | `-` | `text/html` |
| `html:next-head-count` | templated,observed | `-` | `-` | `text/html` |
| `html:noarchive` | templated,observed | `-` | `-` | `text/html` |
| `html:noimageindex` | templated,observed | `-` | `-` | `text/html` |
| `html:nosnippet` | templated,observed | `-` | `-` | `text/html` |
| `html:octolytics-dimension-repository_id` | templated,observed | `-` | `-` | `text/html` |
| `html:octolytics-dimension-repository_is_fork` | templated,observed | `-` | `-` | `text/html` |
| `html:octolytics-dimension-repository_network_root_id` | templated,observed | `-` | `-` | `text/html` |
| `html:octolytics-dimension-repository_network_root_nwo` | templated,observed | `-` | `-` | `text/html` |
| `html:octolytics-dimension-repository_nwo` | templated,observed | `-` | `-` | `text/html` |
| `html:octolytics-dimension-repository_public` | templated,observed | `-` | `-` | `text/html` |
| `html:octolytics-dimension-user_id` | templated,observed | `-` | `-` | `text/html` |
| `html:octolytics-dimension-user_login` | templated,observed | `-` | `-` | `text/html` |
| `html:octolytics-url` | templated,observed | `-` | `-` | `text/html` |
| `html:og:description` | templated,observed | `-` | `-` | `text/html` |
| `html:og:image` | templated,observed | `-` | `-` | `application/xhtml+xml`, `text/html` |
| `html:og:image:alt` | templated,observed | `-` | `-` | `text/html` |
| `html:og:image:height` | templated,observed | `-` | `-` | `text/html` |
| `html:og:image:secure_url` | templated,observed | `-` | `-` | `text/html` |
| `html:og:image:type` | templated,observed | `-` | `-` | `text/html` |
| `html:og:image:width` | templated,observed | `-` | `-` | `text/html` |
| `html:og:locale` | templated,observed | `-` | `-` | `text/html` |
| `html:og:site_name` | templated,observed | `-` | `-` | `text/html` |
| `html:og:title` | templated,observed | `-` | `-` | `application/xhtml+xml`, `text/html` |
| `html:og:ttl` | templated,observed | `-` | `-` | `text/html` |
| `html:og:type` | templated,observed | `-` | `-` | `text/html` |
| `html:og:updated_time` | templated,observed | `-` | `-` | `text/html` |
| `html:og:url` | templated,observed | `-` | `-` | `application/xhtml+xml`, `text/html` |
| `html:origin-trial` | templated,observed | `-` | `-` | `application/xhtml+xml`, `text/html` |
| `html:otherbot` | templated,observed | `-` | `-` | `text/html` |
| `html:program` | templated,observed | `-` | `-` | `text/html` |
| `html:referrer` | templated,observed | `-` | `-` | `text/html` |
| `html:refresh` | templated,observed | `-` | `-` | `text/html` |
| `html:request-id` | templated,observed | `-` | `-` | `text/html` |
| `html:robots` | templated,observed | `-` | `-` | `text/html` |
| `html:route-action` | templated,observed | `-` | `-` | `text/html` |
| `html:route-controller` | templated,observed | `-` | `-` | `text/html` |
| `html:route-id` | templated,observed | `-` | `-` | `text/html` |
| `html:route-pattern` | templated,observed | `-` | `-` | `text/html` |
| `html:runtime-type` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-ad-unit-path` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-afs-query` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-app-id` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-author` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-category-id` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-compliant` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-country` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-developer-slug` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-device-platform-id` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-hosted` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-interstitial-navBar` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-interstitial-rapidScroll` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-interstitial-unhideWindow` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-locale` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-main-category-id` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-monetizable` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-page-id` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-platform-id` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-program-logo-url` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-program-name` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-recat` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-region` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-review-vecna` | templated,observed | `-` | `-` | `text/html` |
| `html:rv-tech` | templated,observed | `-` | `-` | `text/html` |
| `html:scriptSrc` | declared,not-observed | `internalText` | `HTML` | _-_ |
| `html:slurp` | templated,observed | `-` | `-` | `text/html` |
| `html:supported-color-schemes` | templated,observed | `-` | `-` | `text/html` |
| `html:td-page` | templated,observed | `-` | `-` | `text/html` |
| `html:teoma` | templated,observed | `-` | `-` | `text/html` |
| `html:theme-color` | templated,observed | `-` | `-` | `application/xhtml+xml`, `text/html` |
| `html:turbo-body-classes` | templated,observed | `-` | `-` | `text/html` |
| `html:turbo-cache-control` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:card` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:data1` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:data2` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:description` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:image` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:label1` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:label2` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:maxage` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:site` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:title` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:url` | templated,observed | `-` | `-` | `text/html` |
| `html:viewport` | templated,observed | `-` | `-` | `application/xhtml+xml`, `text/html` |
| `html:visitor-hmac` | templated,observed | `-` | `-` | `text/html` |
| `html:visitor-payload` | templated,observed | `-` | `-` | `text/html` |
| `html:website` | templated,observed | `-` | `-` | `text/html` |
| `html:x-dns-prefetch-control` | templated,observed | `-` | `-` | `text/html` |
| `html:x-pjax-csp-version` | templated,observed | `-` | `-` | `text/html` |
| `html:x-pjax-css-version` | templated,observed | `-` | `-` | `text/html` |
| `html:x-pjax-js-version` | templated,observed | `-` | `-` | `text/html` |
| `html:x-pjax-version` | templated,observed | `-` | `-` | `text/html` |
| `html:x-ua-compatible` | templated,observed | `-` | `-` | `text/html` |
| `html_unicode_qr:glyph_count` | undeclared-literal,observed | `-` | `-` | `text/html` |
| `http-connection:fetch-truncated` | declared,not-observed | `externalBoolean` | `AtlassianJwtFetcher` | _-_ |
| `http-connection:num-redirects` | declared,not-observed | `externalInteger` | `AtlassianJwtFetcher` | _-_ |
| `http-connection:target-ip-address` | declared,not-observed | `externalText` | `AtlassianJwtFetcher` | _-_ |
| `http-connection:target-url` | declared,not-observed | `externalText` | `AtlassianJwtFetcher` | _-_ |
| `http-header:content-encoding` | declared,not-observed | `externalText` | `AtlassianJwtFetcher` | _-_ |
| `http-header:content-type` | declared,not-observed | `externalText` | `AtlassianJwtFetcher` | _-_ |
| `http-header:status-code` | declared,not-observed | `externalInteger` | `AtlassianJwtFetcher` | _-_ |
| `http://apache.org/xml/properties/security-manager` | declared,not-observed | `String` | `XMLReaderUtils` | _-_ |
| `http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/` | declared,not-observed | `String` | `IPTC` | _-_ |
| `http://iptc.org/std/Iptc4xmpExt/2008-02-29/` | declared,not-observed | `String` | `IPTC` | _-_ |
| `http://localhost:6060` | declared,not-observed | `String` | `RTGTranslator` | _-_ |
| `http://localhost:8000` | declared,not-observed | `String` | `TextLangDetector` | _-_ |
| `http://localhost:8060` | declared,not-observed | `String` | `GrobidNERecogniser` | _-_ |
| `http://localhost:8070` | declared,not-observed | `String` | `GrobidRESTParser` | _-_ |
| `http://localhost:8881` | declared,not-observed | `String` | `NLTKNERecogniser` | _-_ |
| `http://ns.adobe.com/illustrator/1.0/` | declared,not-observed | `String` | `XMPSchemaIllustrator` | _-_ |
| `http://ns.adobe.com/pdfx/1.3/` | declared,not-observed | `String` | `XMPSchemaPDFX` | _-_ |
| `http://ns.adobe.com/photoshop/1.0/` | declared,not-observed | `String` | `Photoshop` | _-_ |
| `http://ns.adobe.com/xap/1.0/` | declared,not-observed | `String` | `XMP` | _-_ |
| `http://ns.adobe.com/xap/1.0/mm/` | declared,not-observed | `String` | `XMPMM` | _-_ |
| `http://ns.adobe.com/xap/1.0/rights/` | declared,not-observed | `String` | `XMPRights` | _-_ |
| `http://ns.adobe.com/xmp/identifier/qual/1.0/` | declared,not-observed | `String` | `XMPIdq` | _-_ |
| `http://ns.useplus.org/ldf/xmp/1.0/` | declared,not-observed | `String` | `IPTC` | _-_ |
| `http://openoffice.org/2000/` | declared,not-observed | `String` | `NSNormalizerContentHandler` | _-_ |
| `http://purl.oclc.org/ooxml/officeDocument/relationships/officeDocument` | declared,not-observed | `String` | `OOXMLExtractorFactory` | _-_ |
| `http://purl.org/dc/elements/1.1` | declared,not-observed | `String` | `CorePropertiesHandler` | _-_ |
| `http://purl.org/dc/elements/1.1/` | declared,not-observed | `String` | `DublinCore` | _-_ |
| `http://purl.org/dc/terms` | declared,not-observed | `String` | `CorePropertiesHandler` | _-_ |
| `http://purl.org/dc/terms/` | declared,not-observed | `String` | `DublinCore` | _-_ |
| `http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel` | declared,not-observed | `String` | `OPCPackageDetector` | _-_ |
| `http://schemas.microsoft.com/office/2006/xmlPackage` | declared,not-observed | `String` | `Word2006MLDocHandler` | _-_ |
| `http://schemas.microsoft.com/office/2007/relationships/media` | declared,not-observed | `String` | `AbstractOOXMLExtractor` | _-_ |
| `http://schemas.microsoft.com/office/2017/10/relationships/person` | declared,not-observed | `String` | `OPCPackageWrapper` | _-_ |
| `http://schemas.microsoft.com/office/2017/10/relationships/threadedComment` | declared,not-observed | `String` | `OPCPackageWrapper` | _-_ |
| `http://schemas.microsoft.com/office/visio/2012/main` | declared,not-observed | `String` | `VSDXExtractorDecorator` | _-_ |
| `http://schemas.microsoft.com/office/word/2003/wordml` | declared,not-observed | `String` | `AbstractXML2003Parser` | _-_ |
| `http://schemas.microsoft.com/visio/2010/relationships/document` | declared,not-observed | `String` | `VSDXExtractorDecorator` | _-_ |
| `http://schemas.microsoft.com/visio/2010/relationships/page` | declared,not-observed | `String` | `VSDXExtractorDecorator` | _-_ |
| `http://schemas.microsoft.com/visio/2010/relationships/pages` | declared,not-observed | `String` | `VSDXExtractorDecorator` | _-_ |
| `http://schemas.microsoft.com/xps/2005/06/fixedrepresentation` | declared,not-observed | `String` | `OPCPackageDetector` | _-_ |
| `http://schemas.openxmlformats.org/drawingml/2006/chart` | declared,not-observed | `String` | `OOXMLWordAndPowerPointTextHandler` | _-_ |
| `http://schemas.openxmlformats.org/drawingml/2006/main` | declared,not-observed | `String` | `OOXMLWordAndPowerPointTextHandler` | _-_ |
| `http://schemas.openxmlformats.org/drawingml/2006/picture` | declared,not-observed | `String` | `OOXMLWordAndPowerPointTextHandler` | _-_ |
| `http://schemas.openxmlformats.org/markup-compatibility/2006` | declared,not-observed | `String` | `OOXMLWordAndPowerPointTextHandler` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes` | declared,not-observed | `String` | `SAXBasedMetadataExtractor` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/extended-properties` | declared,not-observed | `String` | `ExtendedPropertiesHandler` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/extended-properties/` | declared,not-observed | `String` | `OfficeOpenXMLExtended` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships` | declared,not-observed | `String` | `OOXMLWordAndPowerPointTextHandler` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/aFChunk` | declared,not-observed | `String` | `AbstractOOXMLExtractor` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/attachedTemplate` | declared,not-observed | `String` | `SXWPFWordExtractorDecorator` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/audio` | declared,not-observed | `String` | `AbstractOOXMLExtractor` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart` | declared,not-observed | `String` | `XSSFExcelExtractorDecorator` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments` | declared,not-observed | `String` | `XSSFBExcelExtractorDecorator` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/connections` | declared,not-observed | `String` | `XSSFExcelExtractorDecorator` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties` | declared,not-observed | `String` | `SAXBasedMetadataExtractor` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramData` | declared,not-observed | `String` | `AbstractOOXMLExtractor` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing` | declared,not-observed | `String` | `XSSFExcelExtractorDecorator` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties` | declared,not-observed | `String` | `SAXBasedMetadataExtractor` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/externalLink` | declared,not-observed | `String` | `XSSFExcelExtractorDecorator` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/handoutMaster` | declared,not-observed | `String` | `SXSLFPowerPointExtractorDecorator` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink` | declared,not-observed | `String` | `XSSFExcelExtractorDecorator` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument` | declared,not-observed | `String` | `OOXMLExtractorFactory` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject` | declared,not-observed | `String` | `AbstractOOXMLExtractor` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/package` | declared,not-observed | `String` | `AbstractOOXMLExtractor` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/pivotCacheDefinition` | declared,not-observed | `String` | `XSSFExcelExtractorDecorator` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/queryTable` | declared,not-observed | `String` | `XSSFExcelExtractorDecorator` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings` | declared,not-observed | `String` | `SXWPFWordExtractorDecorator` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/subDocument` | declared,not-observed | `String` | `SXWPFWordExtractorDecorator` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/video` | declared,not-observed | `String` | `AbstractOOXMLExtractor` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/vmlDrawing` | declared,not-observed | `String` | `XSSFExcelExtractorDecorator` | _-_ |
| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/webSettings` | declared,not-observed | `String` | `SXWPFWordExtractorDecorator` | _-_ |
| `http://schemas.openxmlformats.org/package/2006/metadata/core-properties` | declared,not-observed | `String` | `CorePropertiesHandler` | _-_ |
| `http://schemas.openxmlformats.org/package/2006/metadata/core-properties/` | declared,not-observed | `String` | `OfficeOpenXMLCore` | _-_ |
| `http://schemas.openxmlformats.org/package/2006/relationships` | declared,not-observed | `String` | `RelationshipsHandler` | _-_ |
| `http://schemas.openxmlformats.org/package/2006/relationships/digital-signature/origin` | declared,not-observed | `String` | `OOXMLParser` | _-_ |
| `http://schemas.openxmlformats.org/spreadsheetml/2006/main` | declared,not-observed | `String` | `TikaSheetXMLHandler` | _-_ |
| `http://schemas.openxmlformats.org/wordprocessingml/2006/main` | declared,not-observed | `String` | `OfficeOpenXMLExtended` | _-_ |
| `http://schemas.openxps.org/oxps/v1.0/fixedrepresentation` | declared,not-observed | `String` | `OPCPackageDetector` | _-_ |
| `http://www.aiim.org/pdfua/ns/id/` | declared,not-observed | `String` | `XMPSchemaPDFUA` | _-_ |
| `http://www.npes.org/pdfvt/ns/id/` | declared,not-observed | `String` | `XMPSchemaPDFVT` | _-_ |
| `http://www.npes.org/pdfx/ns/id/` | declared,not-observed | `String` | `XMPSchemaPDFXId` | _-_ |
| `http://www.w3.org/1999/02/22-rdf-syntax-ns#` | declared,not-observed | `String` | `XMPContentHandler` | _-_ |
| `http://www.w3.org/1999/xhtml` | declared,not-observed | `String` | `XHTMLContentHandler` | _-_ |
| `http://www.w3.org/1999/xlink` | declared,not-observed | `String` | `OpenDocumentBodyHandler` | _-_ |
| `http://www.xfa.org/schema/xfa-data/1.0/` | declared,not-observed | `String` | `XFAExtractor` | _-_ |
| `https://api.lingo24.com/mt/v1/` | declared,not-observed | `String` | `Lingo24LangDetector` | _-_ |
| `https://api.lingo24.com/mt/v1/translate` | declared,not-observed | `String` | `Lingo24Translator` | _-_ |
| `https://translate.yandex.net/api/v1.5/tr.json/translate` | declared,not-observed | `String` | `YandexTranslator` | _-_ |
| `https://wiki.apache.org/tika/TikaJAXRS` | declared,not-observed | `String` | `TikaWelcome` | _-_ |
| `https://www.googleapis.com/language/translate/v2` | declared,not-observed | `String` | `GoogleTranslator` | _-_ |
| `ical:alarm_action` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:alarm_attach` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:alarm_description` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:alarm_trigger` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:attach_html` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:attach_mime` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:attach_sha256` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:attach_url` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:brand_impersonation` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:brand_keyword` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:calendar_description` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:calendar_name` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:conference_host_abused` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:event_attendee` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_attendee_partstat` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_categories` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_class` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_created` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_description` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_description_html` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:event_dtend` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_dtstamp` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_dtstart` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_duration_hours` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_last_modified` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:event_location` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_organizer` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_phone` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_revision` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_rrule` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:event_sequence` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_status` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_summary` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_transp` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_uid` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_urgency_keyword` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_url` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:method` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:prodid` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:source_encoding` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:timezone_id` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:todo_categories` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:todo_description` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:todo_dtstart` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:todo_due` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:todo_last_modified` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:todo_percent_complete` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:todo_priority` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:todo_status` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:todo_summary` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:todo_uid` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:url` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:version` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:warning` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `image:colorhash` | declared,observed | `internalText` | `ImageHash` | `image/bmp`, `image/gif`, `image/jpeg` |
| `image:phash` | declared,observed | `internalText` | `ImageHash` | `image/bmp`, `image/gif`, `image/jpeg` |
| `imagereader:NumImages` | declared,observed | `internalInteger` | `TikaCoreProperties` | `image/bmp`, `image/gif`, `image/png` |
| `img:AE Setting` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:AEB Bracket Value` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:AF Area Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:AF Point Selected` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:AF Points in Focus` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Acceleration Vector` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Action Advised` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Application Record Version` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:ApplicationExtensions ApplicationExtension` | templated,observed | `-` | `-` | `image/gif` |
| `img:Audio` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Auto Exposure Bracketing` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Auto ISO` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Auto Rotate` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Background Color` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Base ISO` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Bulb Duration` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:By-line` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:By-line Title` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Camera Info Array` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Camera Temperature` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Camera Type` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Camera Uptime` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Canon Model ID` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Caption Digest` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Caption Writer/Editor` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Caption/Abstract` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Category` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Chroma BackgroundColor` | templated,observed | `-` | `-` | `image/png` |
| `img:Chroma BackgroundIndex` | templated,observed | `-` | `-` | `image/png` |
| `img:Chroma BlackIsZero` | templated,observed | `-` | `-` | `image/gif`, `image/png` |
| `img:Chroma ColorSpaceType` | templated,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/png` |
| `img:Chroma Gamma` | templated,observed | `-` | `-` | `image/png` |
| `img:Chroma NumChannels` | templated,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/png` |
| `img:Chroma Palette PaletteEntry` | templated,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/png` |
| `img:City` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Clipping Path Name` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Coded Character Set` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Color Effect` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Color Halftoning Information` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Color Tone` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Color Transfer Functions` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Color Transform` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Comment` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:CommentExtensions CommentExtension` | templated,observed | `-` | `-` | `image/gif` |
| `img:Component 1` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Component 2` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Component 3` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Component 4` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Compression CompressionTypeName` | templated,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/png` |
| `img:Compression Lossless` | templated,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/png` |
| `img:Compression NumProgressiveScans` | templated,observed | `-` | `-` | `image/gif`, `image/png` |
| `img:Compression Type` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Contact` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Content Identifier` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Content Location Name` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Continuous Drive Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Contrast` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Control Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Copyright Flag` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Copyright Notice` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Country/Primary Location Code` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Country/Primary Location Name` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Credit` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:DCT Encode Version` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Data BitsPerSample` | templated,observed | `-` | `-` | `image/bmp`, `image/png` |
| `img:Data PlanarConfiguration` | templated,observed | `-` | `-` | `image/png` |
| `img:Data Precision` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Data SampleFormat` | templated,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/png` |
| `img:Data SignificantBitsPerSample` | templated,observed | `-` | `-` | `image/png` |
| `img:Date Created` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Digital Date Created` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Digital Time Created` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Digital Zoom` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Dimension HorizontalPhysicalPixelSpacing` | templated,observed | `-` | `-` | `image/bmp` |
| `img:Dimension HorizontalPixelOffset` | templated,observed | `-` | `-` | `image/gif` |
| `img:Dimension HorizontalPixelSize` | templated,observed | `-` | `-` | `image/bmp`, `image/png`, `image/x-jbig2` |
| `img:Dimension ImageOrientation` | templated,observed | `-` | `-` | `image/gif`, `image/png`, `image/x-jbig2` |
| `img:Dimension PixelAspectRatio` | templated,observed | `-` | `-` | `image/bmp`, `image/png`, `image/x-jbig2` |
| `img:Dimension VerticalPhysicalPixelSpacing` | templated,observed | `-` | `-` | `image/bmp` |
| `img:Dimension VerticalPixelOffset` | templated,observed | `-` | `-` | `image/gif` |
| `img:Dimension VerticalPixelSize` | templated,observed | `-` | `-` | `image/bmp`, `image/png`, `image/x-jbig2` |
| `img:Display Aperture` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Document FormatVersion` | templated,observed | `-` | `-` | `image/bmp` |
| `img:Document ImageModificationTime` | templated,observed | `-` | `-` | `image/png` |
| `img:Easy Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Easy Shooting Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Edit Status` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Envelope Record Version` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Epoch` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Artist` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Bits Per Sample` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Compression` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Copyright` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Date/Time` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Device Setting Description` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Extra Samples` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Host Computer` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Image Description` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Image Height` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Image Width` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Make` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Model` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:New Subfile Type` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Orientation` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Padding` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Photometric Interpretation` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Planar Configuration` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Predictor` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Resolution Unit` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Rows Per Strip` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Samples Per Pixel` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Software` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Strip Byte Counts` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Strip Offsets` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Unknown tag (0x014d)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x0151)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x0220)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x0221)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x0222)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x0223)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x0224)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x0225)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x0301)` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Unknown tag (0x0302)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x0303)` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Unknown tag (0x0320)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x4000)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x4001)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x5090)` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Unknown tag (0x5091)` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Unknown tag (0x5100)` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Unknown tag (0x5101)` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Unknown tag (0x5104)` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Unknown tag (0x5110)` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Unknown tag (0x5111)` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Unknown tag (0x5112)` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Unknown tag (0xc6fe)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Windows XP Author` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Windows XP Comment` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Windows XP Keywords` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Windows XP Title` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:X Resolution` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Y Resolution` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:YCbCr Positioning` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:YCbCr Sub-Sampling` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Aperture Value` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Body Serial Number` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Brightness Value` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:CFA Pattern` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Color Space` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif SubIFD:Components Configuration` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Compressed Bits Per Pixel` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Contrast` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Custom Rendered` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Date/Time Digitized` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Date/Time Original` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Digital Zoom Ratio` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Document Name` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Exif Image Height` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif SubIFD:Exif Image Width` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif SubIFD:Exif Version` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Exposure Bias Value` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Exposure Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Exposure Program` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Exposure Time` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:F-Number` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:File Source` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Flash` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:FlashPix Version` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Focal Length` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Focal Length 35` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Focal Plane Resolution Unit` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Focal Plane X Resolution` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Focal Plane Y Resolution` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Gain Control` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:ISO Speed` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:ISO Speed Ratings` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Interoperability Index` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Interoperability Version` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Lens Make` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Lens Model` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Lens Specification` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Makernote` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Max Aperture Value` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Metering Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Padding` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Recommended Exposure Index` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Saturation` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Scene Capture Type` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Scene Type` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Sensing Method` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Sensitivity Type` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Sharpness` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Shutter Speed Value` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Sub-Sec Time` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Sub-Sec Time Digitized` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Sub-Sec Time Original` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Subject Distance Range` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Subject Location` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Time Zone` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Time Zone Digitized` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Time Zone Original` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Unique Image ID` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Unknown tag (0xa460)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:User Comment` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:White Balance` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:White Balance Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Artist` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Bits Per Sample` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Compression` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Copyright` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Date/Time` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Exif Image Height` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Exif Image Width` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Image Description` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Image Height` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Image Width` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Make` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Model` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:New Subfile Type` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Orientation` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Photometric Interpretation` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Resolution Unit` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Samples Per Pixel` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Software` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Thumbnail Length` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Thumbnail Offset` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:X Resolution` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Y Resolution` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:YCbCr Positioning` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Version` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Expiration Date` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Expiration Time` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exposure Compensation` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exposure Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exposure Time` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:F Number` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:File Modified Date` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff`, `image/webp` |
| `img:File Name` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff`, `image/webp` |
| `img:File Size` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff`, `image/webp` |
| `img:Firmware Version` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Fixture Identifier` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Flags` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Flags 0` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Flags 1` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Flash Activity` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Flash Bias` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Flash Details` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Flash Exposure Compensation` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Flash Guide Number` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Flash Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Focal Units per mm` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Focus Continuous` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Focus Distance Lower` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Focus Distance Upper` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Focus Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Focus Type` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Altitude` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Altitude Ref` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Date Stamp` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Dest Bearing` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Dest Bearing Ref` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Horizontal Positioning Error` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Img Direction` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Img Direction Ref` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Latitude` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Latitude Ref` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Longitude` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Longitude Ref` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Processing Method` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Speed` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Speed Ref` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Time-Stamp` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Version ID` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Global Altitude` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Global Angle` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:GraphicControlExtension` | templated,observed | `-` | `-` | `image/gif` |
| `img:Grayscale and Multichannel Halftoning Information` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Grayscale and Multichannel Transfer Function` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Grid and Guides Information` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Has Alpha` | templated,observed | `-` | `-` | `image/webp` |
| `img:Headline` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:ICC Untagged Profile` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:IHDR` | templated,observed | `-` | `-` | `image/png` |
| `img:Image Height` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `img:Image Number` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Image Orientation` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Image Size` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Image Stabilization` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Image Type` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Image Width` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `img:ImageDescriptor` | templated,observed | `-` | `-` | `image/gif` |
| `img:Internal Serial Number` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Interoperability:Interoperability Index` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Interoperability:Interoperability Version` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Is Animation` | templated,observed | `-` | `-` | `image/webp` |
| `img:Iso` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:JPEG Comment` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:JPEG Quality` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Keywords` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Language Identifier` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Layer Groups Enabled ID` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Layer Selection IDs` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Layer State Information` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Layers Group Information` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Lens Type` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Local Caption` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:LocalColorTable` | templated,observed | `-` | `-` | `image/gif` |
| `img:LocalColorTable ColorTableEntry` | templated,observed | `-` | `-` | `image/gif` |
| `img:Long Focal Length` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Mac Print Info` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Macro Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Manual Flash Output` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Max Aperture` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Measured EV` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Measured EV 2` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Metering Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Min Aperture` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Number of Components` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Number of Tables` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Object Attribute Reference` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Object Cycle` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Object Name` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Object Type Reference` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Optical Zoom Code` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Origin Subpath Info` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Original Transmission Reference` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Originating Program` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Owner Name` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:PLTE PLTEEntry` | templated,observed | `-` | `-` | `image/png` |
| `img:Path Info 1` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Photo Effect` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Photoshop 4.0 Thumbnail` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Pixel Aspect Ratio` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Plug-in 1 Data` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Plug-in 2 Data` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Print Flags` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Print Flags Information` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Print Info` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Print Info 2` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Print Scale` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Print Style` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Program Version` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Province/State` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Quality` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Quality Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Record Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Reference Date` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Reference Number` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Reference Service` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Release Date` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Release Time` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Resolution Info` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Resolution Units` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Saturation` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Scale` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Seed Number` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Self Timer Delay` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Sequence Number` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Sharpness` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Short Focal Length` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Slices` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Slow Shutter` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Source` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Special Instructions` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Spot Metering Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Sub-location` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Supplemental Category(s)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Target Aperture` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Target Exposure Time` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Text TextEntry` | templated,observed | `-` | `-` | `image/gif`, `image/png` |
| `img:Thumbnail Data` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Thumbnail Height Pixels` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Thumbnail Width Pixels` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Time Created` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Transparency Alpha` | templated,observed | `-` | `-` | `image/bmp`, `image/png` |
| `img:Transparency TransparentColor` | templated,observed | `-` | `-` | `image/png` |
| `img:Transparency TransparentIndex` | templated,observed | `-` | `-` | `image/gif` |
| `img:URL` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:URL List` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Unknown Camera Setting 2` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown Camera Setting 3` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown Camera Setting 7` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown Data Dump` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0000)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0001)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0002)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0003)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0004)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0005)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0006)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0007)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x000c)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x000d)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x000e)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0010)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0014)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0016)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0019)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x001a)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x001d)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x001f)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0020)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0021)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0023)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0026)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0027)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0028)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x002b)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x002d)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x002e)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x002f)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0030)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0031)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0032)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0033)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0034)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0035)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0036)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0037)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0038)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0039)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x003a)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x003b)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x003c)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x003d)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x003f)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0040)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0041)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0042)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0043)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0044)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0045)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0046)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0048)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0049)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x004a)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x004d)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x004e)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x004f)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0050)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0051)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0052)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0053)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0054)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0055)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0058)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x005a)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0201)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0238)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x02b7)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x02e7)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x02e8)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x0444)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x080a)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0x4449)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0xc100)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0xc124)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0xc128)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0xc12a)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0xc200)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0xc201)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0xc202)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0xc203)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0xc400)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0xc40b)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Unknown tag (0xc419)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:UnknownChunks UnknownChunk` | templated,observed | `-` | `-` | `image/png` |
| `img:Urgency` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Value` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Version` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Version Info` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:White Balance` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:White Balance Bias` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:X Resolution` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:XML Data` | templated,observed | `-` | `-` | `image/tiff` |
| `img:XMP Value Count` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff`, `image/webp` |
| `img:Y Resolution` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Zoom Source Width` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Zoom Target Width` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:bKGD bKGD_Grayscale` | templated,observed | `-` | `-` | `image/png` |
| `img:bKGD bKGD_Palette` | templated,observed | `-` | `-` | `image/png` |
| `img:bKGD bKGD_RGB` | templated,observed | `-` | `-` | `image/png` |
| `img:cHRM` | templated,observed | `-` | `-` | `image/png` |
| `img:gAMA` | templated,observed | `-` | `-` | `image/png` |
| `img:height` | undeclared-literal,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/png` |
| `img:iCCP` | templated,observed | `-` | `-` | `image/png` |
| `img:iTXt iTXtEntry` | templated,observed | `-` | `-` | `image/png` |
| `img:pHYs` | templated,observed | `-` | `-` | `image/png` |
| `img:sBIT sBIT_Palette` | templated,observed | `-` | `-` | `image/png` |
| `img:sBIT sBIT_RGB` | templated,observed | `-` | `-` | `image/png` |
| `img:sBIT sBIT_RGBAlpha` | templated,observed | `-` | `-` | `image/png` |
| `img:sRGB` | templated,observed | `-` | `-` | `image/png` |
| `img:tEXt tEXtEntry` | templated,observed | `-` | `-` | `image/png` |
| `img:tIME` | templated,observed | `-` | `-` | `image/png` |
| `img:tRNS tRNS_Grayscale` | templated,observed | `-` | `-` | `image/png` |
| `img:tRNS tRNS_Palette tRNS_PaletteEntry` | templated,observed | `-` | `-` | `image/png` |
| `img:width` | undeclared-literal,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/png` |
| `img:zTXt zTXtEntry` | templated,observed | `-` | `-` | `image/png` |
| `iworks:build-version-history` | declared,not-observed | `externalTextBag` | `IWork13PackageParser` | _-_ |
| `iworks:document-id` | declared,not-observed | `externalText` | `IWork13PackageParser` | _-_ |
| `language` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `lnk:AccessTime` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:AltCommand` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:AppendedDataMimeType` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:AppendedDataSHA256` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:AppendedDataSize` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:Arguments` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:Arguments.Hidden` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:BirthDroidFileID` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:BirthDroidVolumeID` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:CommonPathSuffix` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:ConsoleCursorSize` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:ConsoleFaceName` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:ConsoleFillAttributes` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:ConsoleFontSize` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:ConsoleFontWeight` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:ConsoleHistoryBufferSize` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:ConsoleInsertMode` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:ConsoleQuickEdit` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:ConsoleScreenBuffer` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:ConsoleWindowSize` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:CreationTime` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:DriveSerialNumber` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:DriveType` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:DroidFileCreationTime` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:DroidFileID` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:DroidVolumeID` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:EnvironmentVariableTarget` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:ExploitCVE` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:ExploitClass` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:FileAttributes` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:FileSize` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:HotKey` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListAccessTime[Windows]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListCreationTime[Windows]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[00A25E_1.CER]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[?]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[APPLIC_1]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[CHROME_1.EXE]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[Chrome]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[DOWNLO_1]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[FAQ]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[Google]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[INTERN_1]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[PHOTO-_1.VBS]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[PROGRA_2]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[RE_SCAN006YSFVSA.pdf.wsh]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[SysWOW64]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[System32]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[THUNDE_1.EXE]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[WINDOW_1]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[WindowsPowerShell]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[Windows]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[cmd.exe]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[conhost.exe]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[faq]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[fud.vbs]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[ico]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[lmeza]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[mshta.exe]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[new.vbs]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[parcel_photo.vbs]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[powershell.exe]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[receiptcopy.vbs]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[regsvr32.exe]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[rundll32.exe]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[tat.vbs]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[v1.0]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[vdi.wsh]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[windows]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[winrm.cmd]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[wscript.exe]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListPath` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IconEnvironmentTarget` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IconIndex` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IconLocation` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:KnownFolderID` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:LinkFlags` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:LocalBasePath` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:MACAddress` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:MachineID` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:Name` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:NetworkDeviceName` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:NetworkProviderType` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:NetworkShareName` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{0C570607-0396-43DE-9D61-E321D7DF5026}][10]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{0C570607-0396-43DE-9D61-E321D7DF5026}][11]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{0C570607-0396-43DE-9D61-E321D7DF5026}][12]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{0C570607-0396-43DE-9D61-E321D7DF5026}][13]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{0C570607-0396-43DE-9D61-E321D7DF5026}][1]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{0C570607-0396-43DE-9D61-E321D7DF5026}][2]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{0C570607-0396-43DE-9D61-E321D7DF5026}][3]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{0C570607-0396-43DE-9D61-E321D7DF5026}][4]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{0C570607-0396-43DE-9D61-E321D7DF5026}][5]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{0C570607-0396-43DE-9D61-E321D7DF5026}][6]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{0C570607-0396-43DE-9D61-E321D7DF5026}][8]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{0C570607-0396-43DE-9D61-E321D7DF5026}][9]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{28636AA6-953D-11D2-B5D6-00C04FD918D0}][System.Search.QueryString]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{446D16B1-8DAD-4870-A748-402EA43D788C}][System.AppUserModel.ID]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{46588AE2-4CBC-4338-BBFC-139326986DCE}][System.GPS.Latitude]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3}][11]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3}][18]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3}][5]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{B725F130-47EF-101A-A5F1-02608C9EEBAC}][System.DateCreated]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{B725F130-47EF-101A-A5F1-02608C9EEBAC}][System.DateModified]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{B725F130-47EF-101A-A5F1-02608C9EEBAC}][System.FileAttributes]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{B725F130-47EF-101A-A5F1-02608C9EEBAC}][System.ItemType]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{B725F130-47EF-101A-A5F1-02608C9EEBAC}][System.Size]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{DABD30ED-0043-4789-A7F8-D013A4736622}][System.Link.TargetUrl]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:PropertyStore[{E3E0584C-B788-4A5A-BB20-7F5A44C9ACDD}][6]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:RelativePath` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:ResolvedCommand` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:ShowCommand` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:SpecialFolderID` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:VistaIDListPath` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:VolumeLabel` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:WorkingDir` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:WriteTime` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:idlist:target_ansi_only` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:idlist:target_ansi_only_name` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:warning` | undeclared-literal,observed | `-` | `-` | `application/x-ms-shortcut` |
| `location` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `machine:architectureBits` | declared,observed | `internalClosedChoise` | `MachineMetadata` | `application/x-executable`, `application/x-mach-o-executable`, `application/x-msdownload` |
| `machine:endian` | declared,observed | `internalClosedChoise` | `MachineMetadata` | `application/x-executable`, `application/x-mach-o-executable`, `application/x-msdownload` |
| `machine:machineType` | declared,observed | `internalClosedChoise` | `MachineMetadata` | `application/x-executable`, `application/x-mach-o-executable`, `application/x-msdownload` |
| `machine:platform` | declared,observed | `internalClosedChoise` | `MachineMetadata` | `application/x-msdownload` |
| `magika:description` | declared,not-observed | `externalText` | `MagikaDetector` | _-_ |
| `magika:errors` | declared,not-observed | `externalTextBag` | `MagikaDetector` | _-_ |
| `magika:group` | declared,not-observed | `externalText` | `MagikaDetector` | _-_ |
| `magika:is_text` | declared,not-observed | `externalBoolean` | `MagikaDetector` | _-_ |
| `magika:label` | declared,not-observed | `externalText` | `MagikaDetector` | _-_ |
| `magika:mime_type` | declared,not-observed | `externalText` | `MagikaDetector` | _-_ |
| `magika:score` | declared,not-observed | `externalReal` | `MagikaDetector` | _-_ |
| `magika:status` | declared,not-observed | `externalText` | `MagikaDetector` | _-_ |
| `magika:version` | declared,not-observed | `externalText` | `MagikaDetector` | _-_ |
| `mapi:attach:content-id` | declared,observed | `internalText` | `MAPI` | `application/gzip`, `application/illustrator`, `application/msword` |
| `mapi:attach:content-location` | declared,observed | `internalText` | `MAPI` | `image/jpeg`, `image/png` |
| `mapi:attach:display-name` | declared,observed | `internalText` | `MAPI` | `application/gzip`, `application/illustrator`, `application/msword` |
| `mapi:attach:extension` | declared,observed | `internalText` | `MAPI` | `application/gzip`, `application/illustrator`, `application/msword` |
| `mapi:attach:file-name` | declared,observed | `internalText` | `MAPI` | `application/gzip`, `application/illustrator`, `application/msword` |
| `mapi:attach:flags` | declared,observed | `internalInteger` | `MAPI` | `application/pdf`, `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `mapi:attach:hidden` | declared,observed | `internalBoolean` | `MAPI` | `application/pdf`, `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `mapi:attach:language` | declared,observed | `internalText` | `MAPI` | `application/gzip`, `application/illustrator`, `application/msword` |
| `mapi:attach:long-file-name` | declared,observed | `internalText` | `MAPI` | `application/gzip`, `application/illustrator`, `application/msword` |
| `mapi:attach:long-path-name` | declared,not-observed | `internalText` | `MAPI` | _-_ |
| `mapi:attach:mime` | declared,observed | `internalText` | `MAPI` | `application/gzip`, `application/illustrator`, `application/msword` |
| `mapi:body-types-processed` | declared,observed | `internalTextBag` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:client-submit-time` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:conversation-index` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:conversation-topic` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:creation-time` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:from-representing-email` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:from-representing-name` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:importance` | declared,not-observed | `internalInteger` | `MAPI` | _-_ |
| `mapi:in-reply-to-id` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:internet-message-id` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:internet-references` | declared,observed | `internalTextBag` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:is-flagged` | declared,not-observed | `internalBoolean` | `MAPI` | _-_ |
| `mapi:last-modification-time` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:message-class` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:message-class-raw` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:message-delivery-time` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:msg-submission-accepted-at-time` | declared,observed | `internalDate` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:msg-submission-id` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:original-delivery-time` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:original-submit-time` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:priority` | declared,not-observed | `internalInteger` | `MAPI` | _-_ |
| `mapi:property:PidLidAgingDontAgeMe` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentAuxiliaryFlags` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentColor` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentCounterProposal` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentDuration` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentEndWhole` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentLastSequence` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentNotAllowPropose` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentProposalNumber` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentProposedDuration` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentSequence` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentStartWhole` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentStateFlags` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentSubType` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAttendeeCriticalChange` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAutoStartCheck` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidBusyStatus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidChangeHighlight` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidClientIntent` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidClipEnd` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidClipStart` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidCommonEnd` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidCommonStart` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidConferencingType` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidCurrentVersion` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidFInvited` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidFlagString` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidHasPicture` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidIntendedBusyStatus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidIsException` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidIsRecurring` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidMeetingType` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidOwnerCriticalChange` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidPercentComplete` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidPrivate` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidRecurrenceType` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidRecurring` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidReminderDelta` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidReminderOverride` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidReminderPlaySound` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidReminderSet` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidReminderSignalTime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidReminderTime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidResponseStatus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidSideEffects` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidSmartNoAttach` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskAcceptanceState` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskActualEffort` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskComplete` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskDateCompleted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskDueDate` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskEstimatedEffort` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskFFixOffline` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskFRecurring` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskMode` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskNoCompute` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskOrdinal` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskOwnership` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskStartDate` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskState` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskStatus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskVersion` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTeamTask` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidToDoOrdinalDate` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidUseTnef` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidValidFlagStringProof` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:provider-submit-time` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:recipients-string` | declared,not-observed | `internalText` | `MAPI` | _-_ |
| `mapi:reply-time` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:report-time` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:sent-by-server-type` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `meta:author` | declared,not-observed | `internalTextBag` | `Office` | _-_ |
| `meta:character-count` | declared,observed | `internalInteger` | `Office` | `application/msword`, `application/rtf`, `application/vnd.ms-excel` |
| `meta:character-count-with-spaces` | declared,observed | `internalInteger` | `Office` | `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.ms-word.template.macroenabled.12`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `meta:creation-date` | declared,not-observed | `internalDate` | `Office` | _-_ |
| `meta:image-count` | declared,observed | `internalInteger` | `Office` | `application/vnd.oasis.opendocument.text` |
| `meta:initial-author` | declared,not-observed | `internalText` | `Office` | _-_ |
| `meta:keyword` | declared,observed | `internalTextBag` | `Office` | `application/msword`, `application/pdf`, `application/vnd.ms-excel` |
| `meta:last-author` | declared,observed | `internalText` | `Office` | `application/msword`, `application/rtf`, `application/vnd.ms-excel` |
| `meta:line-count` | declared,observed | `internalInteger` | `Office` | `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.ms-word.template.macroenabled.12`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `meta:object-count` | declared,observed | `internalInteger` | `Office` | `application/vnd.oasis.opendocument.presentation`, `application/vnd.oasis.opendocument.spreadsheet`, `application/vnd.oasis.opendocument.text` |
| `meta:page-count` | declared,observed | `internalInteger` | `Office` | `application/msword`, `application/rtf`, `application/vnd.ms-excel` |
| `meta:paragraph-count` | declared,observed | `internalInteger` | `Office` | `application/vnd.ms-powerpoint.presentation.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12`, `application/vnd.ms-powerpoint.template.macroenabled.12` |
| `meta:print-date` | declared,observed | `internalDate` | `Office` | `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-excel.addin.macroenabled.12` |
| `meta:save-date` | declared,not-observed | `internalDate` | `Office` | _-_ |
| `meta:slide-count` | declared,observed | `internalInteger` | `Office` | `application/vnd.ms-powerpoint`, `application/vnd.ms-powerpoint.presentation.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12` |
| `meta:table-count` | declared,observed | `internalInteger` | `Office` | `application/vnd.oasis.opendocument.spreadsheet`, `application/vnd.oasis.opendocument.text` |
| `meta:word-count` | declared,observed | `internalInteger` | `Office` | `application/msword`, `application/rtf`, `application/vnd.ms-excel` |
| `msc:binary_mime` | undeclared-literal,observed | `-` | `-` | `application/x-msc` |
| `msc:binary_sha256` | undeclared-literal,observed | `-` | `-` | `application/x-msc` |
| `msc:binary_type` | undeclared-literal,observed | `-` | `-` | `application/x-msc` |
| `msc:command` | undeclared-literal,observed | `-` | `-` | `application/x-msc` |
| `msc:snap_in_clsid` | undeclared-literal,observed | `-` | `-` | `application/x-msc` |
| `msc:snap_in_name` | undeclared-literal,observed | `-` | `-` | `application/x-msc` |
| `msc:string` | undeclared-literal,observed | `-` | `-` | `application/x-msc` |
| `msc:task_command` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `msc:task_description` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `msc:task_name` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `msc:url` | undeclared-literal,observed | `-` | `-` | `application/x-msc` |
| `msc:warning` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `msoffice:comment-person-display-name` | declared,observed | `internalTextBag` | `Office` | `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-powerpoint.presentation.macroenabled.12` |
| `msoffice:doc:has-attached-template` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `msoffice:doc:has-framesets` | declared,observed | `internalBoolean` | `Office` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `msoffice:doc:has-hidden-text` | declared,observed | `internalBoolean` | `Office` | `application/msword`, `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `msoffice:doc:has-mail-merge` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:doc:has-subdocuments` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:embeddedStorageClassId` | declared,observed | `internalText` | `Office` | `application/msword`, `application/octet-stream`, `application/pdf` |
| `msoffice:excel:has-data-connections` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `msoffice:excel:has-dde-links` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:excel:has-external-links` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `msoffice:excel:has-external-pivot-data` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:excel:has-hidden-cols` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-excel.template.macroenabled.12` |
| `msoffice:excel:has-hidden-rows` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `msoffice:excel:has-hidden-sheets` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `msoffice:excel:has-power-query` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:excel:has-very-hidden-sheets` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `msoffice:excel:has-web-queries` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `msoffice:excel:has-xls4-auto-exec` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel` |
| `msoffice:excel:has-xls4-macros` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel` |
| `msoffice:excel:hidden-sheet-names` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `msoffice:excel:protected-worksheet` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel`, `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `msoffice:excel:very-hidden-sheet-names` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `msoffice:excel:workbook-codename` | declared,observed | `internalText` | `Office` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-excel.template.macroenabled.12` |
| `msoffice:excel:xls4-macro-sheet-names` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel` |
| `msoffice:has-comments` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `msoffice:has-external-chart-data` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:has-external-ole-objects` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.presentationml.slideshow` |
| `msoffice:has-field-hyperlinks` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `msoffice:has-hover-hyperlinks` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-powerpoint.presentation.macroenabled.12` |
| `msoffice:has-linked-ole-objects` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `msoffice:has-track-changes` | declared,observed | `internalBoolean` | `Office` | `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `msoffice:has-vml-hyperlinks` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:link:action-type` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `msoffice:link:context` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `msoffice:link:id` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `msoffice:link:ocr-text` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `msoffice:link:relationship-type` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `msoffice:link:source` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `msoffice:link:text` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `msoffice:link:trigger` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `msoffice:link:type` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `msoffice:link:url` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `msoffice:ocxName` | declared,observed | `internalText` | `Office` | `application/x-tika-msoffice` |
| `msoffice:ooxml:ole-auto-exec` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `msoffice:ooxml:ole-suspicious-progids` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `msoffice:ppt:has-animations` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-powerpoint`, `application/vnd.ms-powerpoint.presentation.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12` |
| `msoffice:ppt:has-hidden-slides` | declared,observed | `internalBoolean` | `Office` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `msoffice:ppt:num-hidden-slides` | declared,observed | `internalInteger` | `Office` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `msoffice:ppt:num-unlisted-slides` | declared,not-observed | `internalInteger` | `Office` | _-_ |
| `msoffice:ppt:unlisted-slide-names` | declared,not-observed | `internalTextBag` | `Office` | _-_ |
| `msoffice:progID` | declared,observed | `internalText` | `Office` | `application/msword`, `application/octet-stream`, `application/pdf` |
| `msoffice:xlsb:has-xlm-macros` | undeclared-literal,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `msoffice:xlsx:has-xlm-macros` | undeclared-literal,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-excel.template.macroenabled.12` |
| `odf:version` | declared,observed | `String` | `OpenDocumentMetaParser` | `application/vnd.oasis.opendocument.presentation`, `application/vnd.oasis.opendocument.spreadsheet`, `application/vnd.oasis.opendocument.text` |
| `onenote:buildNumberCreated` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:buildNumberLastWroteToFile` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:buildNumberNewestWritten` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:buildNumberOldestWritten` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:cTransactionsInLog` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:cbExpectedFileLength` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:cbFreeSpaceInFreeChunkList` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:cbLegacyExpectedFileLength` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:cbLegacyFreeSpaceInFreeChunkList` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:crcName` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:creationTimestamp` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:ffvLastCodeThatWroteToThisFile` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:ffvNewestCodeThatHasWrittenToThisFile` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:ffvOldestCodeThatHasWrittenToThisFile` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:ffvOldestCodeThatMayReadThisFile` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:grfDebugLogFlags` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:lastModifiedTimestamp` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:mostRecentAuthors` | declared,not-observed | `externalTextBag` | `OneNoteParser` | _-_ |
| `onenote:nFileVersionGeneration` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:originalAuthors` | declared,not-observed | `externalTextBag` | `OneNoteParser` | _-_ |
| `onenote:rgbPlaceholder` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `original` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `original-format-type` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `outlinks` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `patches` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `pdf:PDFExtensionVersion` | declared,observed | `internalRational` | `PDF` | `application/pdf` |
| `pdf:PDFVersion` | declared,observed | `internalRational` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:actionTrigger` | declared,observed | `internalText` | `PDF` | `text/javascript` |
| `pdf:actionTriggers` | declared,not-observed | `internalTextBag` | `PDF` | _-_ |
| `pdf:actionTypes` | declared,not-observed | `internalTextBag` | `PDF` | _-_ |
| `pdf:annotationSubtypes` | declared,observed | `internalTextBag` | `PDF` | `application/pdf` |
| `pdf:annotationTypes` | declared,observed | `internalTextBag` | `PDF` | `application/pdf` |
| `pdf:associatedFileRelationship` | declared,not-observed | `internalText` | `PDF` | _-_ |
| `pdf:charsPerPage` | declared,observed | `internalIntegerSequence` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:containsDamagedFont` | declared,observed | `internalBoolean` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:containsNonEmbeddedFont` | declared,observed | `internalBoolean` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:docinfo:created` | declared,observed | `internalDate` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:docinfo:creator` | declared,observed | `internalText` | `PDF` | `application/pdf` |
| `pdf:docinfo:creator_tool` | declared,observed | `internalText` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:docinfo:custom:AIS` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:CA` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:Company` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:Filter` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:GTS_PDFXConformance` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:GTS_PDFXVersion` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:ICNAppName` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:ICNAppPlatform` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:ICNAppVersion` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:ID` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:Index` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:Length` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:Manager` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:Nur_Dienstgebrauch` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:PTEX.Fullbanner` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:S` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:Size` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:SourceModified` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:Type` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:URI` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:W` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:ca` | templated,observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:keywords` | declared,observed | `internalText` | `PDF` | `application/pdf` |
| `pdf:docinfo:modified` | declared,observed | `internalDate` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:docinfo:producer` | declared,observed | `internalText` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:docinfo:subject` | declared,observed | `internalText` | `PDF` | `application/pdf` |
| `pdf:docinfo:title` | declared,observed | `internalText` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:docinfo:trapped` | declared,observed | `internalText` | `PDF` | `application/pdf` |
| `pdf:embeddedFileAnnotationType` | declared,not-observed | `internalText` | `PDF` | _-_ |
| `pdf:embeddedFileDescription` | declared,observed | `externalText` | `PDF` | `application/x-msdownload`, `application/xml` |
| `pdf:embeddedFileSubtype` | declared,observed | `internalText` | `PDF` | `application/x-msdownload`, `image/png` |
| `pdf:encrypted` | declared,observed | `internalBoolean` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:eofOffsets` | declared,observed | `externalRealSeq` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:foundNonAdobeExtensionName` | undeclared-literal,observed | `-` | `-` | `application/pdf` |
| `pdf:has3D` | declared,observed | `internalBoolean` | `PDF` | `application/pdf` |
| `pdf:hasAcroFormFields` | declared,observed | `internalBoolean` | `PDF` | `application/pdf` |
| `pdf:hasCollection` | declared,observed | `internalBoolean` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:hasMarkedContent` | declared,observed | `internalBoolean` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:hasXFA` | declared,observed | `internalBoolean` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:hasXMP` | declared,observed | `internalBoolean` | `PDF` | `application/illustrator`, `application/pdf`, `image/jpeg` |
| `pdf:illustrator:type` | declared,not-observed | `internalText` | `PDF` | _-_ |
| `pdf:incrementalUpdateCount` | declared,observed | `externalInteger` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:incrementalUpdateNumber` | declared,not-observed | `internalInteger` | `PDF` | _-_ |
| `pdf:jsName` | declared,not-observed | `internalText` | `PDF` | _-_ |
| `pdf:num3DAnnotations` | declared,observed | `internalInteger` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:ocrPageCount` | declared,observed | `externalInteger` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:overallPercentageUnmappedUnicodeChars` | declared,observed | `internalReal` | `PDF` | `application/pdf` |
| `pdf:producer` | declared,observed | `internalText` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:totalUnmappedUnicodeChars` | declared,observed | `internalInteger` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:unmappedUnicodeCharsPerPage` | declared,observed | `internalIntegerSequence` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:xmpLocation` | declared,not-observed | `internalText` | `PDF` | _-_ |
| `pdf_color_qr:dark_glyphs` | undeclared-literal,observed | `-` | `-` | `application/pdf` |
| `pdf_color_qr:decode_count` | undeclared-literal,observed | `-` | `-` | `application/pdf` |
| `pdf_color_qr:glyphs` | undeclared-literal,observed | `-` | `-` | `application/illustrator`, `application/pdf` |
| `pdf_color_qr:maxcols` | undeclared-literal,observed | `-` | `-` | `application/pdf` |
| `pdf_color_qr:qualifying` | undeclared-literal,observed | `-` | `-` | `application/pdf` |
| `pdf_color_qr:rows` | undeclared-literal,observed | `-` | `-` | `application/pdf` |
| `pdf_color_qr:stage` | undeclared-literal,observed | `-` | `-` | `application/illustrator`, `application/pdf` |
| `pdfa:PDFVersion` | declared,observed | `internalRational` | `PDF` | `application/pdf` |
| `pdfaid:conformance` | declared,observed | `internalText` | `PDF` | `application/pdf` |
| `pdfaid:part` | declared,observed | `internalInteger` | `PDF` | `application/pdf` |
| `pdfuaid:part` | declared,not-observed | `internalInteger` | `PDF` | _-_ |
| `pdfvt:modified` | declared,not-observed | `internalDate` | `PDF` | _-_ |
| `pdfvt:version` | declared,not-observed | `internalText` | `PDF` | _-_ |
| `pdfx:conformance` | declared,observed | `internalText` | `PDF` | `application/pdf` |
| `pdfx:version` | declared,observed | `internalText` | `PDF` | `application/pdf` |
| `pdfxid:version` | declared,observed | `internalText` | `PDF` | `application/pdf` |
| `phonenumbers` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `photoshop:AuthorsPosition` | declared,not-observed | `internalText` | `Photoshop` | _-_ |
| `photoshop:CaptionWriter` | declared,not-observed | `internalText` | `Photoshop` | _-_ |
| `photoshop:Category` | declared,not-observed | `internalText` | `Photoshop` | _-_ |
| `photoshop:City` | declared,not-observed | `internalText` | `Photoshop` | _-_ |
| `photoshop:ColorMode` | declared,observed | `internalClosedChoise` | `Photoshop` | `image/vnd.adobe.photoshop` |
| `photoshop:Country` | declared,not-observed | `internalText` | `Photoshop` | _-_ |
| `photoshop:Credit` | declared,not-observed | `internalText` | `Photoshop` | _-_ |
| `photoshop:DateCreated` | declared,not-observed | `internalDate` | `Photoshop` | _-_ |
| `photoshop:Headline` | declared,not-observed | `internalText` | `Photoshop` | _-_ |
| `photoshop:Instructions` | declared,not-observed | `internalText` | `Photoshop` | _-_ |
| `photoshop:Source` | declared,not-observed | `internalText` | `Photoshop` | _-_ |
| `photoshop:State` | declared,not-observed | `internalText` | `Photoshop` | _-_ |
| `photoshop:SupplementalCategories` | declared,not-observed | `internalTextBag` | `Photoshop` | _-_ |
| `photoshop:TransmissionReference` | declared,not-observed | `internalText` | `Photoshop` | _-_ |
| `photoshop:Urgency` | declared,not-observed | `internalText` | `Photoshop` | _-_ |
| `platform` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `plus:CopyrightOwner` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:CopyrightOwnerID` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:CopyrightOwnerId` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:CopyrightOwnerName` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:ImageCreator` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:ImageCreatorID` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:ImageCreatorId` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:ImageCreatorName` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:ImageSupplier` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `plus:ImageSupplierID` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `plus:ImageSupplierId` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `plus:ImageSupplierImageID` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `plus:ImageSupplierName` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `plus:Licensor` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorCity` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorCountry` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorEmail` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorExtendedAddress` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorID` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorId` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorName` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorPostalCode` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorRegion` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorStreetAddress` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorTelephone1` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorTelephone2` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorURL` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:MinorModelAgeDisclosure` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `plus:ModelReleaseID` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:ModelReleaseStatus` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `plus:PropertyReleaseID` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:PropertyReleaseStatus` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `plus:Version` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `ppkg:command` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ppkg:data_asset` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ppkg:data_asset_ref` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ppkg:embedded_file_md5` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ppkg:embedded_file_mime` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ppkg:embedded_file_name` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ppkg:embedded_file_sha1` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ppkg:embedded_file_sha256` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ppkg:embedded_file_size` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ppkg:warning` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `pptx_color_qr:decode_count` | templated,observed | `-` | `-` | `application/vnd.ms-powerpoint.slideshow.macroenabled.12` |
| `pptx_color_qr:maxcols` | templated,observed | `-` | `-` | `application/vnd.ms-powerpoint.slideshow.macroenabled.12` |
| `pptx_color_qr:rows` | templated,observed | `-` | `-` | `application/vnd.ms-powerpoint.slideshow.macroenabled.12` |
| `pst:discriptorNodeId` | declared,not-observed | `internalText` | `PST` | _-_ |
| `pst:isValid` | declared,not-observed | `internalBoolean` | `PST` | _-_ |
| `rdp:alternate_full_address` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:audiocapturemode` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:audiomode` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:authentication_level` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:autoreconnection_enabled` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:bandwidthautodetect` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:compression` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:drivestoredirect` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:enablerdsaadauth` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:full_address` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:gatewaycredentialssource` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:gatewayprofileusagemethod` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:gatewayusagemethod` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:keyboardhook` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:networkautodetect` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:pcb_cert_issuer` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `rdp:pcb_cert_san` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `rdp:pcb_cert_self_signed` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `rdp:pcb_cert_subject` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `rdp:pcb_chain_depth` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `rdp:pcb_warning` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `rdp:promptcredentialonce` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:redirectclipboard` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:redirectcomports` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:redirectlocation` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:redirectprinters` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:redirectsmartcards` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:redirectwebauthn` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:remoteapplicationmode` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:screen_mode_id` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:signature_raw` | undeclared-literal,observed | `-` | `-` | `application/x-rdp` |
| `rdp:signature_sha1` | undeclared-literal,observed | `-` | `-` | `application/x-rdp` |
| `rdp:signature_sha256` | undeclared-literal,observed | `-` | `-` | `application/x-rdp` |
| `rdp:signature_warning` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `rdp:signscope` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rdp:signscope_but_missing_sig` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `rdp:videoplaybackmode` | templated,observed | `-` | `-` | `application/x-rdp` |
| `rendering:Rendered-By` | declared,not-observed | `externalTextBag` | `Rendering` | _-_ |
| `rendering:pdfbox-image-writing-ms` | declared,not-observed | `externalReal` | `PDFBoxRenderer` | _-_ |
| `rendering:pdfbox-rendering-ms` | declared,not-observed | `externalReal` | `PDFBoxRenderer` | _-_ |
| `rendering:rendering-time-ms` | declared,not-observed | `externalReal` | `Rendering` | _-_ |
| `rtf:hyperlinkUrl` | declared,observed | `String` | `RtfIocScanner` | `application/rtf` |
| `rtf:nullByteUrl` | declared,not-observed | `String` | `RtfIocScanner` | _-_ |
| `rtf:objdataMixedCase` | declared,observed | `String` | `RtfIocScanner` | `application/rtf` |
| `rtf:protocolHandler` | declared,observed | `String` | `RtfIocScanner` | `application/rtf` |
| `rtf:templateUrl` | declared,not-observed | `String` | `RtfIocScanner` | _-_ |
| `rtf:uncPath` | declared,observed | `String` | `RtfIocScanner` | `application/rtf` |
| `rtf_color_qr:colortbl_size` | undeclared-literal,observed | `-` | `-` | `application/rtf` |
| `rtf_color_qr:enabled` | undeclared-literal,observed | `-` | `-` | `application/rtf` |
| `rtf_color_qr:error` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `rtf_color_qr:rows_captured` | undeclared-literal,observed | `-` | `-` | `application/rtf` |
| `rtf_meta:contains_encapsulated_html` | declared,observed | `internalBoolean` | `RTFMetadata` | `application/rtf`, `application/vnd.ms-outlook` |
| `rtf_meta:emb_app_version` | declared,observed | `internalText` | `RTFMetadata` | `application/octet-stream`, `application/vnd.ms-equation`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `rtf_meta:emb_class` | declared,observed | `internalText` | `RTFMetadata` | `application/octet-stream`, `application/vnd.ms-equation`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `rtf_meta:emb_class_obfuscated` | declared,observed | `internalBoolean` | `RTFMetadata` | `application/octet-stream`, `application/vnd.ms-equation`, `application/vnd.ms-excel.addin.macroenabled.12` |
| `rtf_meta:emb_clsid` | declared,observed | `internalText` | `RTFMetadata` | `application/octet-stream`, `application/vnd.ms-equation`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `rtf_meta:emb_clsid_name` | declared,observed | `internalText` | `RTFMetadata` | `application/octet-stream`, `application/vnd.ms-equation`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `rtf_meta:emb_item` | declared,not-observed | `internalText` | `RTFMetadata` | _-_ |
| `rtf_meta:emb_label` | declared,not-observed | `internalText` | `RTFMetadata` | _-_ |
| `rtf_meta:emb_ole2link_url` | declared,observed | `internalText` | `RTFMetadata` | `application/vnd.ms-equation`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `application/x-tika-msoffice` |
| `rtf_meta:emb_source_path` | declared,observed | `internalText` | `RTFMetadata` | `text/plain`, `text/troff` |
| `rtf_meta:emb_topic` | declared,not-observed | `internalText` | `RTFMetadata` | _-_ |
| `rtf_meta:hex_escape_in_objdata` | declared,not-observed | `internalBoolean` | `RTFMetadata` | _-_ |
| `rtf_meta:malformed_rtf_header` | declared,observed | `internalBoolean` | `RTFMetadata` | `application/rtf` |
| `rtf_meta:objdata_decoy_count` | declared,not-observed | `internalInteger` | `RTFMetadata` | _-_ |
| `rtf_meta:thumbnail` | declared,observed | `internalBoolean` | `RTFMetadata` | `application/octet-stream`, `image/emf`, `image/jpeg` |
| `rtf_meta:unicode_in_objdata` | declared,not-observed | `internalBoolean` | `RTFMetadata` | _-_ |
| `rtf_pict:borderBottomColor` | templated,observed | `-` | `-` | `image/png` |
| `rtf_pict:borderLeftColor` | templated,observed | `-` | `-` | `image/png` |
| `rtf_pict:borderRightColor` | templated,observed | `-` | `-` | `image/png` |
| `rtf_pict:borderTopColor` | templated,observed | `-` | `-` | `image/png` |
| `rtf_pict:dhgt` | templated,observed | `-` | `-` | `image/png` |
| `rtf_pict:fArrowheadsOK` | templated,observed | `-` | `-` | `image/emf` |
| `rtf_pict:fCameFromImgDummy` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/wmf` |
| `rtf_pict:fFakeMaster` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/wmf` |
| `rtf_pict:fFilled` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/png` |
| `rtf_pict:fFlipH` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/jpeg` |
| `rtf_pict:fFlipV` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/jpeg` |
| `rtf_pict:fHidden` | templated,observed | `-` | `-` | `image/png` |
| `rtf_pict:fHitTestFill` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/wmf` |
| `rtf_pict:fHitTestLine` | templated,observed | `-` | `-` | `image/emf` |
| `rtf_pict:fInsetPen` | templated,observed | `-` | `-` | `image/emf` |
| `rtf_pict:fInsetPenOK` | templated,observed | `-` | `-` | `image/emf` |
| `rtf_pict:fIsBullet` | templated,observed | `-` | `-` | `image/png` |
| `rtf_pict:fLayoutInCell` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/jpeg` |
| `rtf_pict:fLine` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/jpeg` |
| `rtf_pict:fLineRecolorFillAsPicture` | templated,observed | `-` | `-` | `image/emf` |
| `rtf_pict:fLineUseShapeAnchor` | templated,observed | `-` | `-` | `image/emf` |
| `rtf_pict:fLockAgainstGrouping` | templated,observed | `-` | `-` | `image/png` |
| `rtf_pict:fLockAgainstSelect` | templated,observed | `-` | `-` | `image/png` |
| `rtf_pict:fLockAspectRatio` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/png` |
| `rtf_pict:fLockCropping` | templated,observed | `-` | `-` | `image/png` |
| `rtf_pict:fLockPosition` | templated,observed | `-` | `-` | `image/png`, `image/wmf` |
| `rtf_pict:fLockRotation` | templated,observed | `-` | `-` | `image/png`, `image/wmf` |
| `rtf_pict:fLockVerticies` | templated,observed | `-` | `-` | `image/png` |
| `rtf_pict:fNoFillHitTest` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/png` |
| `rtf_pict:fNoLineDrawDash` | templated,observed | `-` | `-` | `image/emf` |
| `rtf_pict:fPreferRelativeResize` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/png` |
| `rtf_pict:fPseudoInline` | templated,observed | `-` | `-` | `image/wmf` |
| `rtf_pict:fReallyHidden` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/wmf` |
| `rtf_pict:fRecolorFillAsPicture` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/wmf` |
| `rtf_pict:fScriptAnchor` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/wmf` |
| `rtf_pict:fUseShapeAnchor` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/wmf` |
| `rtf_pict:fillColor` | templated,observed | `-` | `-` | `image/png`, `image/wmf` |
| `rtf_pict:fillOpacity` | templated,observed | `-` | `-` | `image/wmf` |
| `rtf_pict:fillShape` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/wmf` |
| `rtf_pict:fillUseRect` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/wmf` |
| `rtf_pict:lineFillShape` | templated,observed | `-` | `-` | `image/emf` |
| `rtf_pict:pibFlags` | templated,observed | `-` | `-` | `image/jpeg`, `image/wmf` |
| `rtf_pict:pictureActive` | templated,observed | `-` | `-` | `image/emf`, `image/wmf` |
| `rtf_pict:pictureBiLevel` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/png` |
| `rtf_pict:pictureGray` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/png` |
| `rtf_pict:posv` | templated,observed | `-` | `-` | `image/jpeg` |
| `rtf_pict:shapeType` | templated,observed | `-` | `-` | `application/octet-stream`, `image/emf`, `image/jpeg` |
| `rtf_pict:wzDescription` | templated,observed | `-` | `-` | `image/jpeg`, `image/wmf` |
| `rtf_pict:wzName` | templated,observed | `-` | `-` | `image/png` |
| `samplerate` | undeclared-literal,observed | `-` | `-` | `audio/mpeg`, `audio/vnd.wave` |
| `segment-type` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `sf:errors` | declared,not-observed | `externalTextBag` | `SiegfriedDetector` | _-_ |
| `sf:identifiers_details` | declared,not-observed | `externalTextBag` | `SiegfriedDetector` | _-_ |
| `sf:identifiers_name` | declared,not-observed | `externalTextBag` | `SiegfriedDetector` | _-_ |
| `sf:sf_version` | declared,not-observed | `externalText` | `SiegfriedDetector` | _-_ |
| `sf:signature` | declared,not-observed | `externalText` | `SiegfriedDetector` | _-_ |
| `sf:status` | declared,not-observed | `externalText` | `SiegfriedDetector` | _-_ |
| `sheetNames` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `signature:contact-info` | declared,not-observed | `internalTextBag` | `TikaCoreProperties` | _-_ |
| `signature:date` | declared,observed | `internalDateBag` | `TikaCoreProperties` | `application/pdf` |
| `signature:filter` | declared,observed | `internalTextBag` | `TikaCoreProperties` | `application/pdf` |
| `signature:location` | declared,observed | `internalTextBag` | `TikaCoreProperties` | `application/pdf` |
| `signature:name` | declared,not-observed | `internalTextBag` | `TikaCoreProperties` | _-_ |
| `signature:reason` | declared,observed | `internalTextBag` | `TikaCoreProperties` | `application/pdf` |
| `slides-height` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `slides-width` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `source` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `source-language` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `sqlite3:application_id` | declared,not-observed | `internalText` | `SQLite3Parser` | _-_ |
| `sqlite3:user_version` | declared,not-observed | `internalText` | `SQLite3Parser` | _-_ |
| `standard_references` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `streams-total` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `strings:encoding` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `strings:file_output` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `strings:length` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `strings:min-len` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `summary` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `svg:externalScript` | undeclared-literal,observed | `-` | `-` | `image/svg+xml` |
| `svg:externalUseRef` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `svg:hasEventHandlers` | undeclared-literal,observed | `-` | `-` | `image/svg+xml` |
| `svg:hasForeignObject` | undeclared-literal,observed | `-` | `-` | `image/svg+xml` |
| `svg:hasZeroWidthChars` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `svg:link` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `target-language` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `tess:image_magick_processed` | declared,not-observed | `externalBooleanSeq` | `TesseractOCRParser` | _-_ |
| `tess:orientation` | declared,not-observed | `externalInteger` | `TesseractOCRParser` | _-_ |
| `tess:orientation_confidence` | declared,not-observed | `externalReal` | `TesseractOCRParser` | _-_ |
| `tess:page_number` | declared,not-observed | `externalInteger` | `TesseractOCRParser` | _-_ |
| `tess:rotate` | declared,not-observed | `externalInteger` | `TesseractOCRParser` | _-_ |
| `tess:rotation` | declared,not-observed | `externalRealSeq` | `TesseractOCRParser` | _-_ |
| `tess:script` | declared,not-observed | `externalText` | `TesseractOCRParser` | _-_ |
| `tess:script_confidence` | declared,not-observed | `externalReal` | `TesseractOCRParser` | _-_ |
| `tiff:BitsPerSample` | declared,observed | `internalIntegerSequence` | `TIFF` | `image/bmp`, `image/jpeg`, `image/png` |
| `tiff:ImageLength` | declared,observed | `internalInteger` | `TIFF` | `image/bmp`, `image/gif`, `image/jpeg` |
| `tiff:ImageWidth` | declared,observed | `internalInteger` | `TIFF` | `image/bmp`, `image/gif`, `image/jpeg` |
| `tiff:Make` | declared,observed | `internalText` | `TIFF` | `image/jpeg` |
| `tiff:Model` | declared,observed | `internalText` | `TIFF` | `image/jpeg` |
| `tiff:Orientation` | declared,observed | `internalClosedChoise` | `TIFF` | `image/jpeg` |
| `tiff:ResolutionUnit` | declared,observed | `internalClosedChoise` | `TIFF` | `image/jpeg`, `image/tiff` |
| `tiff:SamplesPerPixel` | declared,observed | `internalInteger` | `TIFF` | `image/jpeg`, `image/tiff` |
| `tiff:Software` | declared,observed | `internalText` | `TIFF` | `image/jpeg`, `image/tiff` |
| `tiff:XResolution` | declared,observed | `internalRational` | `TIFF` | `image/jpeg`, `image/tiff` |
| `tiff:YResolution` | declared,observed | `internalRational` | `TIFF` | `image/jpeg`, `image/tiff` |
| `tika-eval:lang` | declared,not-observed | `externalText` | `TikaEvalMetadataFilter` | _-_ |
| `tika-eval:langConfidence` | declared,not-observed | `externalReal` | `TikaEvalMetadataFilter` | _-_ |
| `tika-eval:languageness` | declared,not-observed | `externalReal` | `TikaEvalMetadataFilter` | _-_ |
| `tika-eval:numAlphaTokens` | declared,not-observed | `externalInteger` | `TikaEvalMetadataFilter` | _-_ |
| `tika-eval:numCommonTokens` | declared,not-observed | `externalInteger` | `TikaEvalMetadataFilter` | _-_ |
| `tika-eval:numTokens` | declared,not-observed | `externalInteger` | `TikaEvalMetadataFilter` | _-_ |
| `tika-eval:numUniqueAlphaTokens` | declared,not-observed | `externalInteger` | `TikaEvalMetadataFilter` | _-_ |
| `tika-eval:numUniqueTokens` | declared,not-observed | `externalInteger` | `TikaEvalMetadataFilter` | _-_ |
| `tika-eval:oov` | declared,not-observed | `externalReal` | `TikaEvalMetadataFilter` | _-_ |
| `tika:chunks` | declared,not-observed | `String` | `TikaCoreProperties` | _-_ |
| `tika:link` | declared,not-observed | `String` | `MimeTypesReaderMetKeys` | _-_ |
| `tika:uti` | declared,not-observed | `String` | `MimeTypesReaderMetKeys` | _-_ |
| `tika_pg:page_number` | declared,observed | `internalInteger` | `TikaPagedText` | `image/jpeg`, `image/png`, `image/tiff` |
| `tika_pg:page_rotation` | declared,not-observed | `internalRational` | `TikaPagedText` | _-_ |
| `tracks` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `tu-count` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `tuv-count` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `unicode_qr:glyph_count` | undeclared-literal,observed | `-` | `-` | `application/msword`, `application/pdf`, `application/rtf` |
| `unicode_qr:warning` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `url:hot_key` | undeclared-literal,observed | `-` | `-` | `application/x-mswinurl` |
| `url:icon_file` | undeclared-literal,observed | `-` | `-` | `application/x-mswinurl` |
| `url:icon_index` | undeclared-literal,observed | `-` | `-` | `application/x-mswinurl` |
| `url:idlist_hex_length` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `url:modified` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `url:show_command` | undeclared-literal,observed | `-` | `-` | `application/x-mswinurl` |
| `url:source_encoding` | undeclared-literal,observed | `-` | `-` | `application/x-mswinurl` |
| `url:url` | undeclared-literal,observed | `-` | `-` | `application/x-mswinurl` |
| `url:url_wide` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `url:url_wide_raw` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `url:warning` | undeclared-literal,observed | `-` | `-` | `application/x-mswinurl` |
| `url:working_directory` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `urn:oasis:names:tc:opendocument:xmlns:drawing:1.0` | declared,not-observed | `String` | `OpenDocumentBodyHandler` | _-_ |
| `urn:oasis:names:tc:opendocument:xmlns:meta:1.0` | declared,not-observed | `String` | `Office` | _-_ |
| `urn:oasis:names:tc:opendocument:xmlns:office:1.0` | declared,not-observed | `String` | `OpenDocumentBodyHandler` | _-_ |
| `urn:oasis:names:tc:opendocument:xmlns:presentation:1.0` | declared,not-observed | `String` | `OpenDocumentBodyHandler` | _-_ |
| `urn:oasis:names:tc:opendocument:xmlns:style:1.0` | declared,not-observed | `String` | `OpenDocumentBodyHandler` | _-_ |
| `urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0` | declared,not-observed | `String` | `OpenDocumentBodyHandler` | _-_ |
| `urn:oasis:names:tc:opendocument:xmlns:table:1.0` | declared,not-observed | `String` | `OpenDocumentBodyHandler` | _-_ |
| `urn:oasis:names:tc:opendocument:xmlns:text:1.0` | declared,not-observed | `String` | `OpenDocumentBodyHandler` | _-_ |
| `urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0` | declared,not-observed | `String` | `OpenDocumentBodyHandler` | _-_ |
| `urn:schemas-microsoft-com:office:office` | declared,not-observed | `String` | `OOXMLWordAndPowerPointTextHandler` | _-_ |
| `urn:schemas-microsoft-com:office:spreadsheet` | declared,not-observed | `String` | `AbstractXML2003Parser` | _-_ |
| `urn:schemas-microsoft-com:vml` | declared,not-observed | `String` | `OOXMLWordAndPowerPointTextHandler` | _-_ |
| `vendor` | undeclared-literal,observed | `-` | `-` | `audio/vorbis` |
| `version` | undeclared-literal,observed | `-` | `-` | `audio/mpeg`, `audio/vorbis` |
| `vlm:completion_tokens` | declared,not-observed | `externalInteger` | `AbstractVLMParser` | _-_ |
| `vlm:model` | declared,not-observed | `externalText` | `AbstractVLMParser` | _-_ |
| `vlm:prompt_tokens` | declared,not-observed | `externalInteger` | `AbstractVLMParser` | _-_ |
| `w:Comments` | declared,observed | `externalTextBag` | `OfficeOpenXMLExtended` | `application/msword`, `application/rtf`, `application/vnd.ms-excel` |
| `warc:WARC-Record-ID` | declared,not-observed | `externalText` | `WARC` | _-_ |
| `warc:http:status` | declared,not-observed | `String` | `WARCParser` | _-_ |
| `warc:http:status:reason` | declared,not-observed | `String` | `WARCParser` | _-_ |
| `warc:payload-content-type` | declared,not-observed | `externalText` | `WARC` | _-_ |
| `warc:record-content-type` | declared,not-observed | `externalText` | `WARC` | _-_ |
| `warc:warning` | declared,not-observed | `externalTextBag` | `WARC` | _-_ |
| `wim:descriptor_xml` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `wim:image_count` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `wordperfect:Build` | declared,not-observed | `internalInteger` | `QuattroPro` | _-_ |
| `wordperfect:Encrypted` | declared,not-observed | `internalBoolean` | `WordPerfect` | _-_ |
| `wordperfect:FileId` | declared,not-observed | `internalText` | `WordPerfect` | _-_ |
| `wordperfect:FileSize` | declared,not-observed | `internalText` | `WordPerfect` | _-_ |
| `wordperfect:FileType` | declared,not-observed | `internalInteger` | `WordPerfect` | _-_ |
| `wordperfect:Id` | declared,not-observed | `internalText` | `QuattroPro` | _-_ |
| `wordperfect:LowestVersion` | declared,not-observed | `internalInteger` | `QuattroPro` | _-_ |
| `wordperfect:MajorVersion` | declared,not-observed | `internalInteger` | `WordPerfect` | _-_ |
| `wordperfect:MinorVersion` | declared,not-observed | `internalInteger` | `WordPerfect` | _-_ |
| `wordperfect:ProductType` | declared,not-observed | `internalInteger` | `WordPerfect` | _-_ |
| `wordperfect:Version` | declared,not-observed | `internalInteger` | `QuattroPro` | _-_ |
| `xlsx_color_qr:decode_count` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `xlsx_color_qr:maxcols` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `xlsx_color_qr:rows` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `xmlprofiler:entity_local_names` | declared,not-observed | `internalTextBag` | `XMLProfiler` | _-_ |
| `xmlprofiler:entity_uris` | declared,not-observed | `internalTextBag` | `XMLProfiler` | _-_ |
| `xmlprofiler:root_entity` | declared,not-observed | `internalText` | `XMLProfiler` | _-_ |
| `xmp:About` | declared,observed | `externalTextBag` | `XMP` | `application/pdf` |
| `xmp:Advisory` | declared,not-observed | `externalTextBag` | `XMP` | _-_ |
| `xmp:CreateDate` | declared,observed | `externalDate` | `XMP` | `application/illustrator`, `application/pdf`, `image/jpeg` |
| `xmp:CreatorTool` | declared,observed | `externalText` | `XMP` | `application/illustrator`, `application/pdf`, `audio/vorbis` |
| `xmp:Identifier` | declared,not-observed | `externalTextBag` | `XMP` | _-_ |
| `xmp:Label` | declared,observed | `externalText` | `XMP` | `image/jpeg` |
| `xmp:MetadataDate` | declared,observed | `externalDate` | `XMP` | `application/illustrator`, `application/pdf`, `image/jpeg` |
| `xmp:ModifyDate` | declared,observed | `externalDate` | `XMP` | `application/illustrator`, `application/pdf`, `image/jpeg` |
| `xmp:NickName` | declared,not-observed | `externalText` | `XMP` | _-_ |
| `xmp:Rating` | declared,observed | `externalInteger` | `XMP` | `image/jpeg` |
| `xmp:Title` | declared,not-observed | `externalText` | `XMP` | _-_ |
| `xmp:dc` | declared,not-observed | `String` | `XMPDC` | _-_ |
| `xmp:dc:contributor` | declared,not-observed | `internalTextBag` | `XMPDC` | _-_ |
| `xmp:dc:coverage` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dc:creator` | declared,observed | `internalTextBag` | `XMPDC` | `application/pdf`, `image/jpeg` |
| `xmp:dc:date` | declared,not-observed | `internalDate` | `XMPDC` | _-_ |
| `xmp:dc:description` | declared,observed | `internalText` | `XMPDC` | `application/pdf` |
| `xmp:dc:description:x-default` | templated,observed | `-` | `-` | `application/pdf` |
| `xmp:dc:format` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dc:identifier` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dc:language` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dc:publisher` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dc:relation` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dc:rights` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dc:source` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dc:subject` | declared,observed | `internalTextBag` | `XMPDC` | `application/pdf` |
| `xmp:dc:title` | declared,observed | `internalText` | `XMPDC` | `application/pdf` |
| `xmp:dc:title:x-default` | templated,observed | `-` | `-` | `application/pdf` |
| `xmp:dc:type` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dcterms` | declared,not-observed | `String` | `XMPDC` | _-_ |
| `xmp:dcterms:created` | declared,not-observed | `internalDate` | `XMPDC` | _-_ |
| `xmp:dcterms:modified` | declared,not-observed | `internalDate` | `XMPDC` | _-_ |
| `xmp:pdf:About` | declared,not-observed | `externalTextBag` | `XMPPDF` | _-_ |
| `xmp:pdf:Keywords` | declared,observed | `externalTextBag` | `XMPPDF` | `application/pdf` |
| `xmp:pdf:PDFVersion` | declared,observed | `externalText` | `XMPPDF` | `application/pdf` |
| `xmp:pdf:Producer` | declared,observed | `externalText` | `XMPPDF` | `application/illustrator`, `application/pdf` |
| `xmpDM:absPeakAudioFilePath` | declared,not-observed | `internalURI` | `XMPDM` | _-_ |
| `xmpDM:album` | declared,observed | `externalText` | `XMPDM` | `audio/mpeg` |
| `xmpDM:albumArtist` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:altTapeName` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:artist` | declared,observed | `externalText` | `XMPDM` | `audio/mpeg` |
| `xmpDM:audioChannelType` | declared,observed | `internalClosedChoise` | `XMPDM` | `audio/mpeg`, `audio/vorbis`, `video/mp4` |
| `xmpDM:audioCompressor` | declared,observed | `internalText` | `XMPDM` | `audio/mpeg`, `audio/vorbis` |
| `xmpDM:audioModDate` | declared,not-observed | `internalDate` | `XMPDM` | _-_ |
| `xmpDM:audioSampleRate` | declared,observed | `internalInteger` | `XMPDM` | `audio/mpeg`, `audio/vnd.wave`, `audio/vorbis` |
| `xmpDM:audioSampleType` | declared,observed | `internalClosedChoise` | `XMPDM` | `audio/vnd.wave` |
| `xmpDM:compilation` | declared,not-observed | `externalInteger` | `XMPDM` | _-_ |
| `xmpDM:composer` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:copyright` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:discNumber` | declared,not-observed | `externalInteger` | `XMPDM` | _-_ |
| `xmpDM:duration` | declared,observed | `externalReal` | `XMPDM` | `audio/mpeg`, `audio/vorbis`, `video/mp4` |
| `xmpDM:engineer` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:fileDataRate` | declared,not-observed | `internalRational` | `XMPDM` | _-_ |
| `xmpDM:genre` | declared,observed | `externalText` | `XMPDM` | `audio/mpeg` |
| `xmpDM:instrument` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:key` | declared,not-observed | `internalClosedChoise` | `XMPDM` | _-_ |
| `xmpDM:logComment` | declared,observed | `externalText` | `XMPDM` | `audio/mpeg` |
| `xmpDM:loop` | declared,not-observed | `internalBoolean` | `XMPDM` | _-_ |
| `xmpDM:metadataModDate` | declared,not-observed | `internalDate` | `XMPDM` | _-_ |
| `xmpDM:numberOfBeats` | declared,not-observed | `internalReal` | `XMPDM` | _-_ |
| `xmpDM:pullDown` | declared,not-observed | `internalClosedChoise` | `XMPDM` | _-_ |
| `xmpDM:relativePeakAudioFilePath` | declared,not-observed | `internalURI` | `XMPDM` | _-_ |
| `xmpDM:releaseDate` | declared,observed | `externalDate` | `XMPDM` | `audio/mpeg` |
| `xmpDM:scaleType` | declared,not-observed | `internalClosedChoise` | `XMPDM` | _-_ |
| `xmpDM:scene` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:shotDate` | declared,not-observed | `externalDate` | `XMPDM` | _-_ |
| `xmpDM:shotLocation` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:shotName` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:speakerPlacement` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:stretchMode` | declared,not-observed | `internalClosedChoise` | `XMPDM` | _-_ |
| `xmpDM:tapeName` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:tempo` | declared,not-observed | `internalReal` | `XMPDM` | _-_ |
| `xmpDM:timeSignature` | declared,not-observed | `internalClosedChoise` | `XMPDM` | _-_ |
| `xmpDM:trackNumber` | declared,not-observed | `externalInteger` | `XMPDM` | _-_ |
| `xmpDM:videoAlphaMode` | declared,not-observed | `externalClosedChoise` | `XMPDM` | _-_ |
| `xmpDM:videoAlphaUnityIsTransparent` | declared,not-observed | `internalBoolean` | `XMPDM` | _-_ |
| `xmpDM:videoColorSpace` | declared,not-observed | `internalClosedChoise` | `XMPDM` | _-_ |
| `xmpDM:videoCompressor` | declared,not-observed | `internalText` | `XMPDM` | _-_ |
| `xmpDM:videoFieldOrder` | declared,not-observed | `internalClosedChoise` | `XMPDM` | _-_ |
| `xmpDM:videoFrameRate` | declared,not-observed | `internalOpenChoise` | `XMPDM` | _-_ |
| `xmpDM:videoModDate` | declared,not-observed | `internalDate` | `XMPDM` | _-_ |
| `xmpDM:videoPixelAspectRatio` | declared,not-observed | `internalRational` | `XMPDM` | _-_ |
| `xmpDM:videoPixelDepth` | declared,not-observed | `internalClosedChoise` | `XMPDM` | _-_ |
| `xmpMM:DerivedFrom:DocumentID` | declared,observed | `externalText` | `XMPMM` | `application/pdf`, `image/jpeg` |
| `xmpMM:DerivedFrom:InstanceID` | declared,observed | `externalText` | `XMPMM` | `application/pdf`, `image/jpeg` |
| `xmpMM:DocumentID` | declared,observed | `externalText` | `XMPMM` | `application/illustrator`, `application/pdf`, `image/jpeg` |
| `xmpMM:History:Action` | declared,observed | `externalTextBag` | `XMPMM` | `application/pdf`, `image/jpeg` |
| `xmpMM:History:InstanceID` | declared,observed | `externalTextBag` | `XMPMM` | `application/pdf`, `image/jpeg` |
| `xmpMM:History:SoftwareAgent` | declared,observed | `externalTextBag` | `XMPMM` | `application/pdf`, `image/jpeg` |
| `xmpMM:History:When` | declared,observed | `externalTextBag` | `XMPMM` | `application/pdf`, `image/jpeg` |
| `xmpMM:InstanceID` | declared,observed | `externalText` | `XMPMM` | `application/illustrator`, `application/pdf`, `image/jpeg` |
| `xmpMM:OriginalDocumentID` | declared,not-observed | `externalText` | `XMPMM` | _-_ |
| `xmpMM:RenditionClass` | declared,not-observed | `externalOpenChoise` | `XMPMM` | _-_ |
| `xmpMM:RenditionParams` | declared,not-observed | `externalText` | `XMPMM` | _-_ |
| `xmpRights:Certificate` | declared,not-observed | `internalText` | `XMPRights` | _-_ |
| `xmpRights:Marked` | declared,not-observed | `internalBoolean` | `XMPRights` | _-_ |
| `xmpRights:Owner` | declared,not-observed | `internalTextBag` | `XMPRights` | _-_ |
| `xmpRights:UsageTerms` | declared,not-observed | `internalText` | `XMPRights` | _-_ |
| `xmpRights:WebStatement` | declared,not-observed | `internalText` | `XMPRights` | _-_ |
| `xmpTPg:NPages` | declared,observed | `internalInteger` | `PagedText` | `application/illustrator`, `application/msword`, `application/pdf` |
| `xmpidq:Scheme` | declared,not-observed | `externalText` | `XMPIdq` | _-_ |
| `zip:centralDirectoryOnlyEntries` | declared,observed | `internalTextBag` | `Zip` | `application/vnd.android.package-archive`, `application/zip` |
| `zip:comment` | declared,not-observed | `externalText` | `Zip` | _-_ |
| `zip:compressedSize` | declared,not-observed | `externalText` | `Zip` | _-_ |
| `zip:compressionMethod` | declared,not-observed | `externalInteger` | `Zip` | _-_ |
| `zip:crc32` | declared,not-observed | `externalText` | `Zip` | _-_ |
| `zip:detectorDataDescriptorRequired` | declared,not-observed | `internalBoolean` | `Zip` | _-_ |
| `zip:detectorZipFileOpened` | declared,observed | `internalBoolean` | `Zip` | `application/java-archive`, `application/vnd.android.package-archive`, `application/vnd.ms-excel.addin.macroenabled.12` |
| `zip:duplicateEntryNames` | declared,observed | `internalTextBag` | `Zip` | `application/java-archive`, `application/vnd.android.package-archive` |
| `zip:encrypted` | declared,not-observed | `externalBoolean` | `Zip` | _-_ |
| `zip:integrityCheckResult` | declared,observed | `internalText` | `Zip` | `application/java-archive`, `application/vnd.android.package-archive`, `application/x-tika-java-web-archive` |
| `zip:localHeaderOnlyEntries` | declared,observed | `internalTextBag` | `Zip` | `application/java-archive`, `application/vnd.android.package-archive`, `application/x-tika-ooxml` |
| `zip:platform` | declared,not-observed | `externalInteger` | `Zip` | _-_ |
| `zip:salvaged` | declared,observed | `internalBoolean` | `Zip` | `application/java-archive`, `application/vnd.android.package-archive`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `zip:uncompressedSize` | declared,not-observed | `externalText` | `Zip` | _-_ |
| `zip:unixMode` | declared,not-observed | `externalInteger` | `Zip` | _-_ |
| `zip:versionMadeBy` | declared,not-observed | `externalInteger` | `Zip` | _-_ |
