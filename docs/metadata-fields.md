# RedTusk Metadata Field Registry

Combined static + runtime inventory. Generated 2026-05-24T16:24:47.148142+00:00.

- **2034** total fields seen across sources
- **212** declared + observed (the healthy core)
- **337** declared but not observed (rare formats / unwalked code paths)
- **57** observed undeclared string literals (migration targets)
- **63** observed but no source trace (investigation queue)

## Field index

| Field | Status | Type | Declared in | Observed in (top 3 MIMEs) |
|---|---|---|---|---|
| `Abstract` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `AccessContraints ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Address` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Affiliation` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Authors` | undeclared-literal,not-observed | `-` | `-` | _-_ |
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
| `Content-Disposition` | observed | `-` | `-` | `application/gzip`, `application/msword`, `application/pdf` |
| `Content-Encoding` | undeclared-literal,observed | `-` | `-` | `application/mbox`, `application/pdf`, `application/x-bat` |
| `Content-Language` | undeclared-literal,observed | `-` | `-` | `text/html` |
| `Content-Length` | undeclared-literal,observed | `-` | `-` | `application/octet-stream`, `application/vnd.ms-equation`, `application/vnd.ms-excel` |
| `Content-Location` | undeclared-literal,observed | `-` | `-` | `text/html` |
| `Content-Type` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Content-Type-Hint` | declared,observed | `internalText` | `TikaCoreProperties` | `application/xhtml+xml`, `text/html` |
| `Content-Type-Magic-Detected` | declared,observed | `internalText` | `TikaCoreProperties` | `application/gzip`, `application/illustrator`, `application/java-archive` |
| `Content-Type-Override` | declared,not-observed | `internalText` | `TikaCoreProperties` | _-_ |
| `Content-Type-Parser-Override` | declared,observed | `internalText` | `TikaCoreProperties` | `message/rfc822` |
| `Copyright` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `DateInfo ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `DistributionFormatSpecificationAlternativeTitle ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Distributor Contact ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Distributor Organization Name ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Error` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ExploitClass` | undeclared-literal,observed | `-` | `-` | `application/x-msc`, `application/x-mswinurl`, `application/x-rdp` |
| `File-Type-Description` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FileOwner` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FileOwnerGroup` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FilePermissions` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FileSize` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Filename` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `FullAffiliations` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `GeographicIdentifierAuthorityAlternativeTitle ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `GeographicIdentifierAuthorityDate ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `GeographicIdentifierAuthorityTitle ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `GeographicIdentifierCode ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Geographic_LATITUDE` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Geographic_LONGITUDE` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Geographic_NAME` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ICBM` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ICC:Blue Colorant` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Blue TRC` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:CMM Type` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Chromatic Adaptation` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Chromaticity` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Class` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Color space` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `ICC:Device Mfg Description` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Device Model Description` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Device manufacturer` | templated,observed | `-` | `-` | `image/jpeg` |
| `ICC:Device model` | templated,observed | `-` | `-` | `image/jpeg` |
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
| `LoC` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Masked icon count` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Masked icon details` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `MasterPageCount` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `MasterSpreadPageCount` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `MboxParser-accept-language` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-content-language` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-content-transfer-encoding` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-from` | undeclared-literal,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-mime-version` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-received` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-references` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-thread-index` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-thread-topic` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-organization-authas` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-organization-authmechanism` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-organization-authsource` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-organization-avstamp-mailbox` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-ms-exchange-organization-scl` | templated,observed | `-` | `-` | `message/rfc822` |
| `MboxParser-x-originating-ip` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message-Bcc` | undeclared-literal,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message-Cc` | undeclared-literal,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message-From` | undeclared-literal,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message-Recipient-Address` | undeclared-literal,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message-To` | undeclared-literal,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:BCC-Display-Name` | declared,not-observed | `internalTextBag` | `Message` | _-_ |
| `Message:BCC-Email` | declared,not-observed | `internalTextBag` | `Message` | _-_ |
| `Message:BCC-Name` | declared,not-observed | `internalTextBag` | `Message` | _-_ |
| `Message:CC-Display-Name` | declared,observed | `internalTextBag` | `Message` | `application/vnd.ms-outlook` |
| `Message:CC-Email` | declared,observed | `internalTextBag` | `Message` | `application/vnd.ms-outlook` |
| `Message:CC-Name` | declared,observed | `internalTextBag` | `Message` | `application/vnd.ms-outlook` |
| `Message:From-Email` | declared,observed | `internalTextBag` | `Message` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:From-Name` | declared,observed | `internalTextBag` | `Message` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:ARC-Authentication-Results` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:ARC-Message-Signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:ARC-Seal` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Accept-Language` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Authentication-Results` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Authentication-Results-Original` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Author` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Author-email` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Auto-Submitted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:BIMI-Selector` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:CC` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Cc` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Class-Path` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Classifier` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Content-Class` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Content-Description` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Content-Disposition` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Content-ID` | templated,observed | `-` | `-` | `application/pdf`, `application/vnd.ms-excel`, `application/vnd.ms-outlook` |
| `Message:Raw-Header:Content-Language` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Content-Location` | templated,observed | `-` | `-` | `image/webp`, `text/css`, `text/html` |
| `Message:Raw-Header:Content-Transfer-Encoding` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Content-Type` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Created-By` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:DKIM-Filter` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:DKIM-Signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:DKIMCheck` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Date` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Delivered-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Delivery-date` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Disposition-Notification-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Envelope-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Envelope-to` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Errors-To` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:ExtraHeaders00001` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:FMLAT` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:FMLCorePlugin` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:FMLCorePluginContainsFMLMod` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Feedback-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:ForceLoadAsMod` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Forward-Confirmed-ReverseDNS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:From` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Home-page` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Importance` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:In-Reply-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:IronPort-Data` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:IronPort-HdrOrdr` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:IronPort-PHdr` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:IronPort-SDR` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Keywords` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:License-Expression` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:List-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:List-Unsubscribe` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:List-Unsubscribe-Post` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:MIME-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Manifest-Version` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Message-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Message-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Metadata-Version` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Mime-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:MixinConfigs` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Name` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Organization` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Platform` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Project-URL` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Received` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Received-SPF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Received-Spf` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:References` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Reply-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Reply-to` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Require-Recipient-Valid-Since` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Requires-Dist` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Requires-Python` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Return-Path` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Return-path` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:SHA1-Digest-Manifest` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:SPFCheck` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Signature-Version` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Snapshot-Content-Location` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:SpamDiagnosticMetadata` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:SpamDiagnosticOutput` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:SpamTally` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Subject` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:Summary` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:Thread-Index` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Thread-Topic` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:TweakClass` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:User-Agent` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:Version` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-ASG-Debug-ID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-ASG-Orig-Subj` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Amavis-Alert` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Amp-File-Uploaded` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Amp-Result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Android-APK-Signed` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-AntiAbuse` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Antivirus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Antivirus-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Attachment-filename` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-AuditID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Authenticated-Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Authenticated-User` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Authority-Analysis` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Auto-Response-Suppress` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-BANNER-OFF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Barracuda-Apparent-Source-IP` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-BRTS-Status` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Connect` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Effective-Source-IP` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Encrypted` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Envelope-From` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Scan-Msg-Size` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Spam-Flag` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Spam-Report` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Spam-Score` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Spam-Status` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-Start-Time` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Barracuda-URL` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Brightmail-Tracker` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CLOUD-SEC-AV-INT-Relay` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CLOUD-SEC-AV-Info` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CLOUD-SEC-AV-UUID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CLX-Response` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-CLX-Shades` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-CM-HeaderCharset` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-CM-TRANSID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-CMAE-Analysis` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CMAE-Envelope` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CMAE-Score` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CSE-ConnectionGUID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CSE-MsgGUID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Client-Addr` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Client-Proto` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Coremail-Antispam` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Country-Code` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-CrossPremisesHeadersFiltered` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CrossPremisesHeadersFilteredBySendConnector` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-CrossPremisesHeadersPromoted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-DKIM` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-DKIM-Verification` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-DMARC-Verification` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Dedup-Identifier` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Default-Received-SPF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EBS` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-EN-IMPSID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EN-OrigIP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EOPAttributedMessage` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-EOPTenantAttributedMessage` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-ESA-HAT` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ESA-Listener` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ESA-SBRS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ESET-AS` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ESET-Antispam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Encryption` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Entity-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Envelope-From` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Envelope-To` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Envelope-To-Blocked` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Eopattributedmessage` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Eoptenantattributedmessage` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-EsetId` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-EsetResult` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Exchange-Antispam-Report-CFA-Test` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Exchange-Antispam-Report-Test` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-ExclaimerHostedSignatures-MessageProcessed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ExclaimerImprintAction` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ExclaimerImprintLatency` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ExclaimerProxyLatency` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ExtLoop1` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-F-Verdict` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-FACEBOOK-PRIORITY` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FB-Internal-MID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FB-Internal-NotifID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FB-Internal-Notiftype` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-FB-Internal-RecipID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Facebook` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Facebook-Notify` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Filter-ID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Forefront-Antispam-Report` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Forefront-Antispam-Report-Untrusted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Forwarded-Encrypted` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Forwarded-Message-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Get-Message-Sender-Via` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Gm-Features` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Gm-Gg` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Gm-Message-State` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Google-DKIM-Signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Google-Smtp-Source` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Ham-Report` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Helo-Args` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-IP-stats` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IPAS-Result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IncomingHeaderCount` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-IncomingTopHeaderMarker` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Info` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IntLoop1` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IntLoopCount2` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-AV` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-Anti-Spam-Filtered` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-Listener` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-MID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-MailFlowPolicy` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-Outbreak-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-RemoteIP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-Reputation` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IronPort-SenderGroup` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Ironport-Dmarc-Check-Result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-IsFriend` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-LD-Processed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-M2K-DINF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MC-Unique` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ME-Auth` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ME-Date` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ME-Helo` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ME-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MGA-submission` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MIMETrack` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-ATPSafeLinks-BitVector` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-AntiSpam-MessageData-Original-0` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-AntiSpam-MessageData-Original-ChunkCount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-AntiSpam-Relay` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-AtpMessageProperties` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Authentication-Results` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Calendar-Series-Instance-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-AuthAs` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-AuthSource` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-FromEntityHeader` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-MailboxType` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-Network-Message-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-OriginalArrivalTime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-OriginalAttributedTenantConnectingIp` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-RMS-PersistedConsumerOrg` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-UserPrincipalName` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-fromentityheader` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-mailboxtype` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-originalarrivaltime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-rms-persistedconsumerorg` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-CrossTenant-userprincipalname` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-EOPDirect` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-ExternalInOutlookResult` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-ExternalOriginalInternetSender` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Forest-ArrivalHubServer` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Forest-EmailMessageHash` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Forest-IndexAgent` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Forest-IndexAgent-0` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Forest-Language` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Forest-MessageScope` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-ForwardingLoop` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Generated-Message-Source` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-MeetingForward-Message` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-MessageSentRepresentingType` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ACSExecutionContext` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AS-LastExternalIp` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ASDirectionalityType` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AVScanComplete` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AVScannedByV2` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AVStamp-Enterprise` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AVStamp-Mailbox` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AntiPhishPolicy` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antiphish-V2` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antispam-AnalystFeatureFilter-ScanContext` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antispam-AuthResults` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antispam-PreContentFilter-PolicyLoadTime` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antispam-PreContentFilter-ScanContext` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antispam-ProtocolFilterHub-ScanContext` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Antispam-Report` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AttachmentDetailsInfo-0` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AttachmentDetailsInfo-ChunkCount` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Auth-DmarcStatus` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AuthAs` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AuthMechanism` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-AuthSource` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Boomerang-Verdict` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-BypassClutter` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-CommunicationStateSummary` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-CompAuthReason` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-CompAuthRes` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ConnectingEHLO` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ConnectingIP` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Cross-Premises-Headers-Processed` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Cross-Session-Cache` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-EhloAndPtrDomain` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-EmailFingerprintsDetailsInfo-0` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-EmailFingerprintsDetailsInfo-ChunkCount` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExpirationInterval` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExpirationIntervalReason` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExpirationStartTime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExpirationStartTimeReason` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExternalRecipientCount` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ExternalRoutingTopologyAnalysis` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-FFO-ServiceTag` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-FeatureTable` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-FeatureTableV2` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-FirstContactSummary` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-FromEntityHeader` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-HMATPModel-Recipient` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-HMATPModel-Spf` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-HVERecipientsForked` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-HygienePolicy` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-InternalOrgSender` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-IsAnyAttachmentAtpSupported` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-IsAtpTenant` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-IsBipIncludedAtpTenant` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-IsSingleRepresentative` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MessageDirectionality` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MessageFingerprint` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MessageHighPrecisionLatencyInProgress` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MessageLatency` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MessageScope` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-MxPointsToUs` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Network-Message-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OffboxClassificationInfo` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OrderedPrecisionLatencyInProgress` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OrgEopForest` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalArrivalTime` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalAttributedTenantConnectingIp` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalClientIPAddress` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalEnvelopeRecipients` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalServerIPAddress` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalSize` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalTenant-AuthAs` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalTenant-AuthSource` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalTenant-FromEntityHeader` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalTenant-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalTenant-Network-Message-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-OriginalTenant-OriginalArrivalTime` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Originating-Country` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-P2SenderPII` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-PCL` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-PFAHub-Total-Message-Size` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-PRD` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-PassLevelSpfRecord` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-PhishSim-Rules-Execution-History` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-PtrDomains` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Recipient-Limit-Verified` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Recipient-P2-Type` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-RecipientDomainMxInfo` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-RecipientDomainMxRecord-PFAFD` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-RecordReviewCfmType` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-ReplicationInfo` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-RuleName-Execution-Log` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Rules-Execution-History` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-Rules-Execution-Log` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SCL` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SafeAttachmentPolicy` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SafeAttachmentPolicy-Enable` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SafeAttachmentProcessing` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SafeLinksPolicy` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SafeLinksPolicy-EnableSafeLinksForEmail` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SafeLinksPolicy-EnableSafeLinksForInternalSenders` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SenderIdResult` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SenderIntelligence-P2Sender` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SenderIntelligence-P2SenderOrgDomainTenantId` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SenderRecipientCommunicationState` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SenderRep-Data` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SenderRep-Score` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SkipSafeAttachmentProcessing` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-SpoofDetection-Frontdoor-DisplayDomainName` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-TargetResourceForest` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-TenantServiceProvider` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-TopLevelSpfRecord` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-TotalRecipientCount` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-TransportTrafficSubType` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-TransportTrafficType` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-VBR-Class` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Organization-VerifiedDkimDomainsList` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Parent-Message-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-Processed-By-BccFoldering` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-QuarantineResubmitTime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-SenderADCheck` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-SharedMailbox-RoutingAgent-Processed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-MS-Exchange-SkipListedInternetSender` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Transport-CrossTenantHeadersPromoted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Transport-CrossTenantHeadersStamped` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Transport-CrossTenantHeadersStripped` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Exchange-Transport-EndToEndLatency` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Has-Attach` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Office365-Filtering-Correlation-Id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-Office365-Filtering-Correlation-Id-Prvs` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-PublicTrafficType` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-TNEF-Correlator` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MS-TrafficTypeDiagnostic` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-MSMail-Priority` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MSW-Message-Direction` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1761853276621` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1765336011334` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1765336011397` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MTA-INFO-1765336011556` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ma4-Node` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Mail-Args` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MailGates` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Mailer` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Message-Delivery` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Microsoft-Antispam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Microsoft-Antispam-Mailbox-Delivery` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Microsoft-Antispam-Message-Info` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Microsoft-Antispam-Message-Info-Original` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Microsoft-Antispam-Untrusted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Microsoft-Exchange-Diagnostics` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-MimeOLE` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Mimecast-Impersonation-Protect` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Mimecast-MFC-AGG-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Mimecast-MFC-PROC-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Mimecast-Spam-Score` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Ms-Exchange-Crosstenant-Authas` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Crosstenant-Authsource` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Crosstenant-Fromentityheader` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Crosstenant-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Crosstenant-Network-Message-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Crosstenant-Originalarrivaltime` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Authas` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Authmechanism` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Authsource` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Expirationinterval` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Expirationintervalreason` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Expirationstarttime` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Expirationstarttimereason` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Messagedirectionality` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Network-Message-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Network-Message-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Organization-Scl` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Processed-By-Bccfoldering` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Transport-Crosstenantheadersstamped` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Exchange-Transport-Endtoendlatency` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Office365-Filtering-Correlation-Id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Publictraffictype` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Ms-Traffictypediagnostic` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Msg-EID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Msmail-Priority` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Notes-Item` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-OLX-Disclaimer` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-OrganizationHeadersPreserved` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Original-MAILFROM` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Original-RCPTTO` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Original-Recipient` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Original-SENDERCOUNTRY` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Original-SENDERIP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Original-SPF` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Original-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-OriginalArrivalTime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Originating-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-OriginatorOrg` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-PEI-MailScanner` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PEI-MailScanner-From` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PEI-MailScanner-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PEI-MailScanner-Information` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PEI-MailScanner-SpamCheck` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-PHP-Originating-Script` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-POPCON-SPAMCHECK` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-PPP-Message-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-PPP-Vhost` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-PhishAlarm-Format` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Priority` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Proofpoint-GUID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Proofpoint-ID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Proofpoint-ORIG-GUID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Proofpoint-Reinject` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Proofpoint-Spam-Details` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Proofpoint-Spam-Details-Enc` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Proofpoint-Spam-Reason` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Proofpoint-Virus-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-QQ-BUSINESS-ORIGIN` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-Bgrelay` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-FEAT` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-GoodBg` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-MIME` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-Mailer` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-SENDSIZE` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-SSF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-STYLE` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-QQ-mid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Qnum` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Quarantine-ID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-REDF-ATP` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-REDF-SHIELD` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Rcpt-Args` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Rcpt-To` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Received` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Recommended-Action` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Rejection-Reason` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Report-Abuse` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Report-Abuse-To` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Request-ID` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Rules-SCL-Zero` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SASI-Hits` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SASI-RCODE` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SASI-SpamProbability` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SASI-Version` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SES-Outgoing` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SF-HELO-Domain` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SF-Originating-IP` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SF-RX-Return-Path` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SG-EID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SG-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-SID-PRA` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SID-Result` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SPF-Fail` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SPF-Verification` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Scanned-By` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Sender-IP` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Senderauth-Result` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Sophos-OBS` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Source` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Source-Args` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Source-Dir` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Spam-Bar` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Spam-Checker-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Spam-Filter` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Spam-Flag` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Spam-Level` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Spam-Score` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-Spam-Status` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-SpamExperts-Domain` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SpamExperts-Outgoing-Class` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SpamExperts-Outgoing-Evidence` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-SpamExperts-Username` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-System-Trace-ID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-TM-AS-ERS` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-AS-GCONF` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-TM-AS-Product-Ver` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-TM-AS-Result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-TM-AS-URL-Rewrite` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-AS-User-Approved-Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-TM-AS-User-Blocked-Sender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-TM-Addin-Auth` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-Addin-ProductCode` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-Authentication-Results` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-MAIL-RECEIVED-TIME` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-Received-SPF` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TM-SNTS-SMTP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TMASE-MatchedRID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TMASE-Result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TMASE-SNAP-Result` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TMASE-Version` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-TMASE-XGENCLOUD` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-TNEFEvaluated` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-Talos-CUID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Talos-MUID` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-ThreatScanner-Verdict` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Titan-Src-Out` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-UI-Filterresults` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-UIDL` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Vipre-Scanned` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-Virus-Scanned` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:X-WB-RES` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-WB-TRACE-IP` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:X-hMailServer-Reason-1` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-hMailServer-Reason-2` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-hMailServer-Reason-3` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-hMailServer-Reason-4` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-hMailServer-Reason-5` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-hMailServer-Reason-Score` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-hMailServer-Spam` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:X-mailer` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:acceptlanguage` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:arc-authentication-results` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:arc-message-signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:arc-seal` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:authentication-results` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:authentication-results-original` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:dkim-signature` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:feedback-id` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:ironport-hdrordr` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:ironport-sdr` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:list-unsubscribe-post` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:msip_labels` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:received-spf` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-agari-authentication-results` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-amp-file-uploaded` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-amp-result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-c2processedorg` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-eopattributedmessage` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-eoptenantattributedmessage` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-esaext` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-esetid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-esetresult` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-forefront-antispam-report` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-forefront-antispam-report-untrusted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ipas-result` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ironport-anti-spam-filtered` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ironport-av` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ironport-listener` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ironport-mailflowpolicy` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ironport-mid` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ironport-remoteip` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ironport-reputation` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ironport-sendergroup` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ld-processed` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-mga-submission` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-microsoft-antispam` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-microsoft-antispam-message-info` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-microsoft-antispam-message-info-original` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-microsoft-antispam-untrusted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-antispam-messagedata-0` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-antispam-messagedata-chunkcount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-antispam-messagedata-original-0` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-antispam-messagedata-original-chunkcount` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-antispam-relay` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-atpmessageproperties` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-crosstenant-authas` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-crosstenant-authsource` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-crosstenant-fromentityheader` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-crosstenant-id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-crosstenant-network-message-id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-crosstenant-originalarrivaltime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-crosstenant-originalattributedtenantconnectingip` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-organization-authas` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-organization-authsource` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-organization-originalclientipaddress` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-organization-originalserveripaddress` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-processed-by-bccfoldering` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-senderadcheck` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-skiplistedinternetsender` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-slblob-mailprops` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-exchange-transport-crosstenantheaderspromoted` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-transport-crosstenantheadersstamped` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-transport-crosstenantheadersstripped` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-exchange-transport-endtoendlatency` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-has-attach` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-ms-office365-filtering-correlation-id` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-office365-filtering-correlation-id-prvs` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-publictraffictype` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-ms-reactions` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-ms-traffictypediagnostic` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-msw-jemd-lastmta` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-msw-jemd-malware` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-msw-jemd-newsletter` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-msw-jemd-refid` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-msw-jemd-scanning-scores` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-msw-original-dkim-signature` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-originating-ip` | templated,observed | `-` | `-` | `application/vnd.ms-outlook`, `message/rfc822` |
| `Message:Raw-Header:x-pps-dkim-result` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-scoring-category` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-sosafe-report-reference` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `Message:Raw-Header:x-tm-as-product-ver` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-tm-as-result` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-tm-as-user-approved-sender` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:Raw-Header:x-tm-as-user-blocked-sender` | templated,observed | `-` | `-` | `message/rfc822` |
| `Message:To-Display-Name` | declared,observed | `internalTextBag` | `Message` | `application/vnd.ms-outlook` |
| `Message:To-Email` | declared,observed | `internalTextBag` | `Message` | `application/vnd.ms-outlook` |
| `Message:To-Name` | declared,observed | `internalTextBag` | `Message` | `application/vnd.ms-outlook` |
| `MetaDataIdentifierCode` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `MetaDataResourceScope ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `MetaDataStandardEdition ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `MetaDataStandardTitle ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Multipart-Boundary` | undeclared-literal,observed | `-` | `-` | `application/gzip`, `application/msword`, `application/pdf` |
| `Multipart-Subtype` | undeclared-literal,observed | `-` | `-` | `application/gzip`, `application/msword`, `application/pdf` |
| `NumExecutables` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `NumHardLinks` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `OtherConstraints ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `PDF-SLICE-FAILED` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `PDF-SLICED-ERROR` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `PageCount` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ParentMetaDataTitle` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ReferencePageCount` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ResourceFormatSpecificationAlternativeTitle ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `SpreadPageCount` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TEIJSONSource` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TEIXMLSource` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ThesaurusNameDate ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Title` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TotalPageCount` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `Trademark` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TransferOptionsOnlineDescription ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TransferOptionsOnlineFunction ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TransferOptionsOnlineLinkage ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TransferOptionsOnlineName ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TransferOptionsOnlineProfile ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `TransferOptionsOnlineProtocol ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `UserConstraints ` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `X-TIKA:EXCEPTION:container_exception` | declared,not-observed | `internalText` | `TikaCoreProperties` | _-_ |
| `X-TIKA:EXCEPTION:embedded_bytes_exception` | declared,not-observed | `internalTextBag` | `TikaCoreProperties` | _-_ |
| `X-TIKA:EXCEPTION:embedded_depth_limit_reached` | declared,not-observed | `internalBoolean` | `TikaCoreProperties` | _-_ |
| `X-TIKA:EXCEPTION:embedded_exception` | declared,not-observed | `internalTextBag` | `TikaCoreProperties` | _-_ |
| `X-TIKA:EXCEPTION:embedded_resource_limit_reached` | declared,not-observed | `internalBoolean` | `TikaCoreProperties` | _-_ |
| `X-TIKA:EXCEPTION:embedded_stream_exception` | declared,not-observed | `internalTextBag` | `TikaCoreProperties` | _-_ |
| `X-TIKA:EXCEPTION:embedded_warning` | declared,not-observed | `internalTextBag` | `TikaCoreProperties` | _-_ |
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
| `X-Tika-OCR-Duration-Ms` | undeclared-literal,observed | `-` | `-` | `image/gif`, `image/jpeg`, `image/png` |
| `X-Tika-OCR-Skipped-Reason` | undeclared-literal,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/jpeg` |
| `access_permission:assemble_document` | declared,observed | `externalText` | `AccessPermissions` | `application/illustrator`, `application/pdf` |
| `access_permission:can_modify` | declared,observed | `externalTextBag` | `AccessPermissions` | `application/illustrator`, `application/pdf` |
| `access_permission:can_print` | declared,observed | `externalText` | `AccessPermissions` | `application/illustrator`, `application/pdf` |
| `access_permission:can_print_faithful` | declared,observed | `externalText` | `AccessPermissions` | `application/illustrator`, `application/pdf` |
| `access_permission:extract_content` | declared,observed | `externalText` | `AccessPermissions` | `application/illustrator`, `application/pdf` |
| `access_permission:extract_for_accessibility` | declared,observed | `externalText` | `AccessPermissions` | `application/illustrator`, `application/pdf` |
| `access_permission:fill_in_form` | declared,observed | `externalText` | `AccessPermissions` | `application/illustrator`, `application/pdf` |
| `access_permission:modify_annotations` | declared,observed | `externalText` | `AccessPermissions` | `application/illustrator`, `application/pdf` |
| `admin-language` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `barcode:error-correction-level` | declared,observed | `internalTextBag` | `Barcode` | `image/gif`, `image/jpeg`, `image/png` |
| `barcode:format` | declared,observed | `internalTextBag` | `Barcode` | `image/gif`, `image/jpeg`, `image/png` |
| `barcode:is-mirrored` | declared,observed | `internalTextBag` | `Barcode` | `image/gif`, `image/jpeg`, `image/png` |
| `barcode:position` | declared,observed | `internalTextBag` | `Barcode` | `image/gif`, `image/jpeg`, `image/png` |
| `barcode:raw-bytes` | declared,observed | `internalTextBag` | `Barcode` | `image/gif`, `image/jpeg`, `image/png` |
| `barcode:value` | declared,observed | `internalTextBag` | `Barcode` | `image/gif`, `image/jpeg`, `image/png` |
| `bits` | undeclared-literal,observed | `-` | `-` | `audio/vnd.wave` |
| `channels` | undeclared-literal,observed | `-` | `-` | `audio/vnd.wave` |
| `cp:category` | declared,observed | `externalText` | `OfficeOpenXMLCore` | `application/vnd.ms-word.document.macroenabled.12` |
| `cp:contentStatus` | declared,observed | `externalText` | `OfficeOpenXMLCore` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-word.template.macroenabled.12` |
| `cp:lastModifiedBy` | declared,not-observed | `externalText` | `OfficeOpenXMLCore` | _-_ |
| `cp:lastPrinted` | declared,not-observed | `externalDate` | `OfficeOpenXMLCore` | _-_ |
| `cp:revision` | declared,observed | `externalText` | `OfficeOpenXMLCore` | `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-powerpoint` |
| `cp:version` | declared,not-observed | `externalText` | `OfficeOpenXMLCore` | _-_ |
| `createdOn` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `creation-tool` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `creation-tool-version` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ctakes:schema` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `custom:AVIWkjEfj` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:AsjGx0` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:Business Objects Context Information` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:Business Objects Context Information1` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:Business Objects Context Information2` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:Business Objects Context Information3` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:Business Objects Context Information4` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:Business Objects Context Information5` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:Business Objects Context Information6` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:BzR5V1sq45` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:Client` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:ContentTypeId` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12` |
| `custom:Created` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:Creator` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:DocumentID` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:FHGvorlage` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:GrammarlyDocumentId` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:ICV` | templated,observed | `-` | `-` | `application/msword`, `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:KSOProductBuildVer` | templated,observed | `-` | `-` | `application/msword`, `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:LastSaved` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:MP_InheritedTags` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:MSIP_Label_340ed6a7-0f03-43d9-901d-02d4a7e408aa_ActionId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_340ed6a7-0f03-43d9-901d-02d4a7e408aa_ContentBits` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_340ed6a7-0f03-43d9-901d-02d4a7e408aa_Enabled` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_340ed6a7-0f03-43d9-901d-02d4a7e408aa_Method` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_340ed6a7-0f03-43d9-901d-02d4a7e408aa_Name` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_340ed6a7-0f03-43d9-901d-02d4a7e408aa_SetDate` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_340ed6a7-0f03-43d9-901d-02d4a7e408aa_SiteId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `custom:MSIP_Label_fe213162-8742-4817-ab6f-53da7c79e427_ActionId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_fe213162-8742-4817-ab6f-53da7c79e427_ContentBits` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_fe213162-8742-4817-ab6f-53da7c79e427_Enabled` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_fe213162-8742-4817-ab6f-53da7c79e427_Method` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_fe213162-8742-4817-ab6f-53da7c79e427_Name` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_fe213162-8742-4817-ab6f-53da7c79e427_SetDate` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MSIP_Label_fe213162-8742-4817-ab6f-53da7c79e427_SiteId` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:MediaServiceImageTags` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12` |
| `custom:Notes` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:Owner` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:PresentationFormat` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:Producer` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:Slides` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:SpecialProps` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:SpecialProps1` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:SpecialProps2` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:SpecialProps3` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:Ts9FjKo` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:Version` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:VersionCheckDate` | templated,observed | `-` | `-` | `application/vnd.ms-excel` |
| `custom:WorkbookGuid` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:Y1ejXi7I` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:_DocHome` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `custom:_MarkAsFinal` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-word.template.macroenabled.12` |
| `custom:_NewReviewCycle` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:_TemplateID` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:_dlc_DocId` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:_dlc_DocIdItemGuid` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:_dlc_DocIdUrl` | templated,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `custom:aRcAn7h` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:bTmnSGUkHf` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:bjDocumentLabelXML` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:bjDocumentLabelXML-0` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:bjDocumentSecurityLabel` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:bjSaver` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:docIndexRef` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:dpufEuqZ` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:hasChanged` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:klassifizierung` | templated,observed | `-` | `-` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `custom:l3qDvt3B53wxeXu` | templated,observed | `-` | `-` | `application/msword` |
| `custom:lPWHjGcKsRH` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:lcsF7Ywp8cvKE` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:lrmHIVGaU9Rz` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:modIZsYpblY` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:qmsVyxGtW` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `custom:zUTunJgwBO` | templated,observed | `-` | `-` | `application/vnd.ms-word.document.macroenabled.12` |
| `data-type` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `database:column_count` | declared,not-observed | `externalInteger` | `Database` | _-_ |
| `database:column_name` | declared,not-observed | `externalTextBag` | `Database` | _-_ |
| `database:row_count` | declared,not-observed | `externalInteger` | `Database` | _-_ |
| `database:table_name` | declared,not-observed | `externalTextBag` | `Database` | _-_ |
| `dc:contributor` | declared,not-observed | `internalTextBag` | `DublinCore` | _-_ |
| `dc:coverage` | declared,not-observed | `internalTextBag` | `DublinCore` | _-_ |
| `dc:creator` | declared,observed | `internalTextBag` | `DublinCore` | `application/msword`, `application/pdf`, `application/rtf` |
| `dc:date` | declared,not-observed | `internalDate` | `DublinCore` | _-_ |
| `dc:description` | declared,observed | `internalTextBag` | `DublinCore` | `application/pdf`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-outlook` |
| `dc:description:x-default` | observed | `-` | `-` | `application/pdf` |
| `dc:format` | declared,observed | `internalText` | `DublinCore` | `application/illustrator`, `application/pdf`, `message/rfc822` |
| `dc:identifier` | declared,observed | `internalTextBag` | `DublinCore` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `message/rfc822` |
| `dc:language` | declared,observed | `internalTextBag` | `DublinCore` | `application/pdf`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `dc:publisher` | declared,observed | `internalTextBag` | `DublinCore` | `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12` |
| `dc:relation` | declared,observed | `internalTextBag` | `DublinCore` | `message/rfc822` |
| `dc:rights` | declared,not-observed | `internalTextBag` | `DublinCore` | _-_ |
| `dc:source` | declared,not-observed | `internalTextBag` | `DublinCore` | _-_ |
| `dc:subject` | declared,observed | `internalTextBag` | `DublinCore` | `application/msword`, `application/pdf`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `dc:title` | declared,observed | `internalTextBag` | `DublinCore` | `application/msword`, `application/pdf`, `application/vnd.ms-excel` |
| `dc:title:x-default` | observed | `-` | `-` | `application/pdf` |
| `dc:type` | declared,not-observed | `internalTextBag` | `DublinCore` | _-_ |
| `dcterms:created` | declared,observed | `internalDate` | `DublinCore` | `application/illustrator`, `application/msword`, `application/pdf` |
| `dcterms:modified` | declared,observed | `internalDate` | `DublinCore` | `application/illustrator`, `application/msword`, `application/pdf` |
| `divisionType` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `dwg:applicationComment` | declared,not-observed | `externalText` | `DWG` | _-_ |
| `dwg:applicationName` | declared,not-observed | `externalText` | `DWG` | _-_ |
| `dwg:applicationVersion` | declared,not-observed | `externalText` | `DWG` | _-_ |
| `dwg:productInfo` | declared,not-observed | `externalText` | `DWG` | _-_ |
| `embeddedResourceType` | declared,observed | `internalClosedChoise` | `TikaCoreProperties` | `application/gzip`, `application/java-archive`, `application/msword` |
| `emf:iconOnly` | observed | `-` | `-` | `image/emf` |
| `emf:iconString` | observed | `-` | `-` | `image/emf` |
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
| `extended-properties:Company` | declared,observed | `externalText` | `OfficeOpenXMLExtended` | `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `extended-properties:DocSecurity` | declared,observed | `externalInteger` | `OfficeOpenXMLExtended` | `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-word.document.macroenabled.12` |
| `extended-properties:DocSecurityString` | declared,observed | `externalClosedChoise` | `OfficeOpenXMLExtended` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `extended-properties:HiddedSlides` | declared,not-observed | `externalInteger` | `OfficeOpenXMLExtended` | _-_ |
| `extended-properties:Manager` | declared,observed | `externalTextBag` | `OfficeOpenXMLExtended` | `application/vnd.ms-powerpoint`, `application/vnd.ms-word.document.macroenabled.12` |
| `extended-properties:Notes` | declared,observed | `externalInteger` | `OfficeOpenXMLExtended` | `application/vnd.ms-powerpoint.presentation.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12`, `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `extended-properties:PresentationFormat` | declared,observed | `externalText` | `OfficeOpenXMLExtended` | `application/vnd.ms-powerpoint.presentation.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12`, `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `extended-properties:Template` | declared,observed | `externalText` | `OfficeOpenXMLExtended` | `application/msword`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-powerpoint` |
| `extended-properties:TotalTime` | declared,observed | `externalInteger` | `OfficeOpenXMLExtended` | `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-powerpoint` |
| `external-process:exit-value` | declared,not-observed | `externalInteger` | `ExternalProcess` | _-_ |
| `external-process:stderr` | declared,not-observed | `externalText` | `ExternalProcess` | _-_ |
| `external-process:stderr-length` | declared,not-observed | `externalReal` | `ExternalProcess` | _-_ |
| `external-process:stderr-truncated` | declared,not-observed | `externalBoolean` | `ExternalProcess` | _-_ |
| `external-process:stdout` | declared,not-observed | `externalText` | `ExternalProcess` | _-_ |
| `external-process:stdout-length` | declared,not-observed | `externalReal` | `ExternalProcess` | _-_ |
| `external-process:stdout-truncated` | declared,not-observed | `externalBoolean` | `ExternalProcess` | _-_ |
| `external-process:timeout` | declared,not-observed | `externalBoolean` | `ExternalProcess` | _-_ |
| `file-count` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `fileType` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `font:name` | declared,not-observed | `internalTextBag` | `Font` | _-_ |
| `fs:accessed` | declared,not-observed | `externalDate` | `FileSystem` | _-_ |
| `fs:created` | declared,not-observed | `externalDate` | `FileSystem` | _-_ |
| `fs:modified` | declared,not-observed | `externalDate` | `FileSystem` | _-_ |
| `fulltext` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `geo:alt` | declared,not-observed | `internalReal` | `Geographic` | _-_ |
| `geo:lat` | declared,not-observed | `internalReal` | `Geographic` | _-_ |
| `geo:long` | declared,not-observed | `internalReal` | `Geographic` | _-_ |
| `geo:timestamp` | declared,observed | `internalDate` | `Geographic` | `image/jpeg` |
| `hasAudio` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `hasSignature` | declared,observed | `internalBoolean` | `TikaCoreProperties` | `application/pdf` |
| `hasVideo` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `html:GENERATOR` | templated,observed | `-` | `-` | `text/html` |
| `html:Generator` | templated,observed | `-` | `-` | `text/html` |
| `html:REFRESH` | templated,observed | `-` | `-` | `text/html` |
| `html:X-Service-Version` | templated,observed | `-` | `-` | `text/html` |
| `html:X-System` | templated,observed | `-` | `-` | `text/html` |
| `html:X-UA-Compatible` | templated,observed | `-` | `-` | `application/xhtml+xml`, `text/html` |
| `html:article:modified_time` | templated,observed | `-` | `-` | `text/html` |
| `html:article:published_time` | templated,observed | `-` | `-` | `text/html` |
| `html:generator` | templated,observed | `-` | `-` | `text/html` |
| `html:google-site-verification` | templated,observed | `-` | `-` | `text/html` |
| `html:googlebot` | templated,observed | `-` | `-` | `text/html` |
| `html:googlebot-news` | templated,observed | `-` | `-` | `text/html` |
| `html:msapplication-TileImage` | templated,observed | `-` | `-` | `text/html` |
| `html:noarchive` | templated,observed | `-` | `-` | `text/html` |
| `html:noimageindex` | templated,observed | `-` | `-` | `text/html` |
| `html:nosnippet` | templated,observed | `-` | `-` | `text/html` |
| `html:og:description` | templated,observed | `-` | `-` | `text/html` |
| `html:og:image` | templated,observed | `-` | `-` | `text/html` |
| `html:og:image:alt` | templated,observed | `-` | `-` | `text/html` |
| `html:og:image:height` | templated,observed | `-` | `-` | `text/html` |
| `html:og:image:secure_url` | templated,observed | `-` | `-` | `text/html` |
| `html:og:image:type` | templated,observed | `-` | `-` | `text/html` |
| `html:og:image:width` | templated,observed | `-` | `-` | `text/html` |
| `html:og:locale` | templated,observed | `-` | `-` | `text/html` |
| `html:og:site_name` | templated,observed | `-` | `-` | `text/html` |
| `html:og:title` | templated,observed | `-` | `-` | `text/html` |
| `html:og:type` | templated,observed | `-` | `-` | `text/html` |
| `html:og:updated_time` | templated,observed | `-` | `-` | `text/html` |
| `html:og:url` | templated,observed | `-` | `-` | `text/html` |
| `html:otherbot` | templated,observed | `-` | `-` | `text/html` |
| `html:robots` | templated,observed | `-` | `-` | `text/html` |
| `html:scriptSrc` | declared,not-observed | `internalText` | `HTML` | _-_ |
| `html:twitter:card` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:data1` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:data2` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:description` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:image` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:label1` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:label2` | templated,observed | `-` | `-` | `text/html` |
| `html:twitter:title` | templated,observed | `-` | `-` | `text/html` |
| `html:viewport` | templated,observed | `-` | `-` | `application/xhtml+xml`, `text/html` |
| `html:x-ua-compatible` | templated,observed | `-` | `-` | `text/html` |
| `html_unicode_qr:glyph_count` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:alarm_action` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:alarm_attach` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:attach_html` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:attach_mime` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:attach_sha256` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:attach_url` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:brand_impersonation` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:brand_keyword` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:calendar_description` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:calendar_name` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:conference_host_abused` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:event_attendee` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_attendee_partstat` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_class` | observed | `-` | `-` | `text/calendar` |
| `ical:event_dtend` | observed | `-` | `-` | `text/calendar` |
| `ical:event_dtstamp` | observed | `-` | `-` | `text/calendar` |
| `ical:event_dtstart` | observed | `-` | `-` | `text/calendar` |
| `ical:event_duration_hours` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_location` | observed | `-` | `-` | `text/calendar` |
| `ical:event_organizer` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:event_phone` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:event_revision` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:event_status` | observed | `-` | `-` | `text/calendar` |
| `ical:event_summary` | observed | `-` | `-` | `text/calendar` |
| `ical:event_transp` | observed | `-` | `-` | `text/calendar` |
| `ical:event_uid` | observed | `-` | `-` | `text/calendar` |
| `ical:event_urgency_keyword` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:method` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:prodid` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:source_encoding` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:timezone_id` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:url` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ical:version` | undeclared-literal,observed | `-` | `-` | `text/calendar` |
| `ical:warning` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `image:colorhash` | declared,observed | `internalText` | `ImageHash` | `image/bmp`, `image/gif`, `image/jpeg` |
| `image:phash` | declared,observed | `internalText` | `ImageHash` | `image/bmp`, `image/gif`, `image/jpeg` |
| `imagereader:NumImages` | declared,observed | `internalInteger` | `TikaCoreProperties` | `image/bmp`, `image/gif`, `image/png` |
| `img:Application Record Version` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:ApplicationExtensions ApplicationExtension` | templated,observed | `-` | `-` | `image/gif` |
| `img:Background Color` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Caption Digest` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Chroma BackgroundColor` | templated,observed | `-` | `-` | `image/png` |
| `img:Chroma BackgroundIndex` | templated,observed | `-` | `-` | `image/png` |
| `img:Chroma BlackIsZero` | templated,observed | `-` | `-` | `image/gif`, `image/png` |
| `img:Chroma ColorSpaceType` | templated,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/png` |
| `img:Chroma Gamma` | templated,observed | `-` | `-` | `image/png` |
| `img:Chroma NumChannels` | templated,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/png` |
| `img:Chroma Palette PaletteEntry` | templated,observed | `-` | `-` | `image/gif`, `image/png` |
| `img:Coded Character Set` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Color Halftoning Information` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Color Transfer Functions` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Color Transform` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:CommentExtensions CommentExtension` | templated,observed | `-` | `-` | `image/gif` |
| `img:Component 1` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Component 2` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Component 3` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Compression CompressionTypeName` | templated,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/png` |
| `img:Compression Lossless` | templated,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/png` |
| `img:Compression NumProgressiveScans` | templated,observed | `-` | `-` | `image/gif`, `image/png` |
| `img:Compression Type` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Copyright Flag` | templated,observed | `-` | `-` | `image/tiff` |
| `img:DCT Encode Version` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Data BitsPerSample` | templated,observed | `-` | `-` | `image/bmp`, `image/png` |
| `img:Data PlanarConfiguration` | templated,observed | `-` | `-` | `image/png` |
| `img:Data Precision` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Data SampleFormat` | templated,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/png` |
| `img:Data SignificantBitsPerSample` | templated,observed | `-` | `-` | `image/png` |
| `img:Date Created` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Dimension HorizontalPixelOffset` | templated,observed | `-` | `-` | `image/gif` |
| `img:Dimension HorizontalPixelSize` | templated,observed | `-` | `-` | `image/png` |
| `img:Dimension ImageOrientation` | templated,observed | `-` | `-` | `image/gif`, `image/png` |
| `img:Dimension PixelAspectRatio` | templated,observed | `-` | `-` | `image/png` |
| `img:Dimension VerticalPixelOffset` | templated,observed | `-` | `-` | `image/gif` |
| `img:Dimension VerticalPixelSize` | templated,observed | `-` | `-` | `image/png` |
| `img:Document FormatVersion` | templated,observed | `-` | `-` | `image/bmp` |
| `img:Document ImageModificationTime` | templated,observed | `-` | `-` | `image/png` |
| `img:Envelope Record Version` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Artist` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Bits Per Sample` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Compression` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Copyright` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Date/Time` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Image Height` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Image Width` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Make` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Model` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:New Subfile Type` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Orientation` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Padding` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Photometric Interpretation` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Planar Configuration` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Resolution Unit` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Rows Per Strip` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Samples Per Pixel` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Software` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Strip Byte Counts` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Strip Offsets` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Exif IFD0:Unknown tag (0x0301)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x0303)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x4000)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x4001)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x5110)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x5111)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Unknown tag (0x5112)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:Windows XP Author` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif IFD0:X Resolution` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:Y Resolution` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif IFD0:YCbCr Positioning` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Aperture Value` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Brightness Value` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Color Space` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Exif SubIFD:Components Configuration` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Compressed Bits Per Pixel` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Contrast` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Custom Rendered` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Date/Time Digitized` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Date/Time Original` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Digital Zoom Ratio` | templated,observed | `-` | `-` | `image/jpeg` |
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
| `img:Exif SubIFD:Gain Control` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:ISO Speed Ratings` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Makernote` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Max Aperture Value` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Metering Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Padding` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Saturation` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Scene Capture Type` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Scene Type` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Sensing Method` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Sharpness` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Shutter Speed Value` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Sub-Sec Time` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Sub-Sec Time Digitized` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Sub-Sec Time Original` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Subject Distance Range` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:Subject Location` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:White Balance` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif SubIFD:White Balance Mode` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Compression` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Image Height` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Image Width` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Orientation` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Resolution Unit` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Thumbnail Length` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Thumbnail Offset` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:X Resolution` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Exif Thumbnail:Y Resolution` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:File Modified Date` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff`, `image/webp` |
| `img:File Name` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff`, `image/webp` |
| `img:File Size` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff`, `image/webp` |
| `img:Flags 0` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Flags 1` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Altitude` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Altitude Ref` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Date Stamp` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Processing Method` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Time-Stamp` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:GPS:GPS Version ID` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Global Altitude` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Global Angle` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:GraphicControlExtension` | templated,observed | `-` | `-` | `image/gif` |
| `img:Grayscale and Multichannel Halftoning Information` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Grayscale and Multichannel Transfer Function` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Grid and Guides Information` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Has Alpha` | templated,observed | `-` | `-` | `image/webp` |
| `img:ICC Untagged Profile` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:IHDR` | templated,observed | `-` | `-` | `image/png` |
| `img:Image Height` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `img:Image Width` | templated,observed | `-` | `-` | `image/jpeg`, `image/webp` |
| `img:ImageDescriptor` | templated,observed | `-` | `-` | `image/gif` |
| `img:Interoperability:Interoperability Index` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Is Animation` | templated,observed | `-` | `-` | `image/webp` |
| `img:JPEG Comment` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:JPEG Quality` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Layer Groups Enabled ID` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Layer Selection IDs` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Layer State Information` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Layers Group Information` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:LocalColorTable` | templated,observed | `-` | `-` | `image/gif` |
| `img:LocalColorTable ColorTableEntry` | templated,observed | `-` | `-` | `image/gif` |
| `img:Mac Print Info` | templated,observed | `-` | `-` | `image/tiff` |
| `img:Number of Components` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Number of Tables` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Object Name` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:PLTE PLTEEntry` | templated,observed | `-` | `-` | `image/png` |
| `img:Pixel Aspect Ratio` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Plug-in 1 Data` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Plug-in 2 Data` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Print Flags` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Print Flags Information` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Print Info 2` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Print Scale` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Print Style` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Quality` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Resolution Info` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Resolution Units` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Seed Number` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Slices` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Text TextEntry` | templated,observed | `-` | `-` | `image/gif`, `image/png` |
| `img:Thumbnail Data` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Thumbnail Height Pixels` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Thumbnail Width Pixels` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Time Created` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Transparency Alpha` | templated,observed | `-` | `-` | `image/bmp`, `image/png` |
| `img:Transparency TransparentColor` | templated,observed | `-` | `-` | `image/png` |
| `img:Transparency TransparentIndex` | templated,observed | `-` | `-` | `image/gif` |
| `img:URL List` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:Unknown tag (0x0238)` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:UnknownChunks UnknownChunk` | templated,observed | `-` | `-` | `image/png` |
| `img:Version` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:Version Info` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff` |
| `img:X Resolution` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:XML Data` | templated,observed | `-` | `-` | `image/tiff` |
| `img:XMP Value Count` | templated,observed | `-` | `-` | `image/jpeg`, `image/tiff`, `image/webp` |
| `img:Y Resolution` | templated,observed | `-` | `-` | `image/jpeg` |
| `img:bKGD bKGD_Grayscale` | templated,observed | `-` | `-` | `image/png` |
| `img:bKGD bKGD_Palette` | templated,observed | `-` | `-` | `image/png` |
| `img:bKGD bKGD_RGB` | templated,observed | `-` | `-` | `image/png` |
| `img:cHRM` | templated,observed | `-` | `-` | `image/png` |
| `img:gAMA` | templated,observed | `-` | `-` | `image/png` |
| `img:height` | templated,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/png` |
| `img:iCCP` | templated,observed | `-` | `-` | `image/png` |
| `img:iTXt iTXtEntry` | templated,observed | `-` | `-` | `image/png` |
| `img:pHYs` | templated,observed | `-` | `-` | `image/png` |
| `img:sBIT sBIT_RGB` | templated,observed | `-` | `-` | `image/png` |
| `img:sBIT sBIT_RGBAlpha` | templated,observed | `-` | `-` | `image/png` |
| `img:sRGB` | templated,observed | `-` | `-` | `image/png` |
| `img:tEXt tEXtEntry` | templated,observed | `-` | `-` | `image/png` |
| `img:tIME` | templated,observed | `-` | `-` | `image/png` |
| `img:tRNS tRNS_Grayscale` | templated,observed | `-` | `-` | `image/png` |
| `img:tRNS tRNS_Palette tRNS_PaletteEntry` | templated,observed | `-` | `-` | `image/png` |
| `img:width` | templated,observed | `-` | `-` | `image/bmp`, `image/gif`, `image/png` |
| `img:zTXt zTXtEntry` | templated,observed | `-` | `-` | `image/png` |
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
| `lnk:ExploitClass` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:FileAttributes` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:FileSize` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:HotKey` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[RE_SCAN006YSFVSA.pdf.wsh]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[System32]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[WindowsPowerShell]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[Windows]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[cmd.exe]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[faq]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[powershell.exe]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[receiptcopy.vbs]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[v1.0]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
| `lnk:IDListModTime[vdi.wsh]` | templated,observed | `-` | `-` | `application/x-ms-shortcut` |
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
| `machine:architectureBits` | declared,observed | `internalClosedChoise` | `MachineMetadata` | `application/x-msdownload` |
| `machine:endian` | declared,observed | `internalClosedChoise` | `MachineMetadata` | `application/x-msdownload` |
| `machine:machineType` | declared,observed | `internalClosedChoise` | `MachineMetadata` | `application/x-msdownload` |
| `machine:platform` | declared,observed | `internalClosedChoise` | `MachineMetadata` | `application/x-msdownload` |
| `mapi:attach:content-id` | declared,observed | `internalText` | `MAPI` | `application/msword`, `application/pdf`, `application/vnd.ms-excel` |
| `mapi:attach:content-location` | declared,not-observed | `internalText` | `MAPI` | _-_ |
| `mapi:attach:display-name` | declared,observed | `internalText` | `MAPI` | `application/msword`, `application/pdf`, `application/vnd.ms-excel` |
| `mapi:attach:extension` | declared,observed | `internalText` | `MAPI` | `application/msword`, `application/pdf`, `application/vnd.ms-excel` |
| `mapi:attach:file-name` | declared,observed | `internalText` | `MAPI` | `application/msword`, `application/pdf`, `application/vnd.ms-excel` |
| `mapi:attach:flags` | declared,observed | `internalInteger` | `MAPI` | `application/pdf`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-outlook` |
| `mapi:attach:hidden` | declared,observed | `internalBoolean` | `MAPI` | `application/pdf`, `application/vnd.ms-outlook`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `mapi:attach:language` | declared,observed | `internalText` | `MAPI` | `application/msword`, `application/pdf`, `application/vnd.ms-excel` |
| `mapi:attach:long-file-name` | declared,observed | `internalText` | `MAPI` | `application/msword`, `application/pdf`, `application/vnd.ms-excel` |
| `mapi:attach:long-path-name` | declared,not-observed | `internalText` | `MAPI` | _-_ |
| `mapi:attach:mime` | declared,observed | `internalText` | `MAPI` | `application/msword`, `application/pdf`, `application/vnd.ms-excel` |
| `mapi:body-types-processed` | declared,observed | `internalTextBag` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:client-submit-time` | observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:conversation-index` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:conversation-topic` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:creation-time` | observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:from-representing-email` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:from-representing-name` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:importance` | declared,not-observed | `internalInteger` | `MAPI` | _-_ |
| `mapi:in-reply-to-id` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:internet-message-id` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:internet-references` | declared,observed | `internalTextBag` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:is-flagged` | declared,not-observed | `internalBoolean` | `MAPI` | _-_ |
| `mapi:last-modification-time` | observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:message-class` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:message-class-raw` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:message-delivery-time` | observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:msg-submission-accepted-at-time` | declared,observed | `internalDate` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:msg-submission-id` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `mapi:priority` | declared,not-observed | `internalInteger` | `MAPI` | _-_ |
| `mapi:property:PidLidAgingDontAgeMe` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentAuxiliaryFlags` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentColor` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentCounterProposal` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentDuration` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidAppointmentEndWhole` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
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
| `mapi:property:PidLidClipEnd` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidClipStart` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidCommonEnd` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidCommonStart` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidConferencingType` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidCurrentVersion` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidFInvited` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
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
| `mapi:property:PidLidReminderSet` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidReminderSignalTime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidReminderTime` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidResponseStatus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidSideEffects` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidSmartNoAttach` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskComplete` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskDueDate` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskMode` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskStartDate` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidTaskStatus` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidToDoOrdinalDate` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidUseTnef` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:property:PidLidValidFlagStringProof` | templated,observed | `-` | `-` | `application/vnd.ms-outlook` |
| `mapi:recipients-string` | declared,not-observed | `internalText` | `MAPI` | _-_ |
| `mapi:sent-by-server-type` | declared,observed | `internalText` | `MAPI` | `application/vnd.ms-outlook` |
| `meta:author` | declared,not-observed | `internalTextBag` | `Office` | _-_ |
| `meta:character-count` | declared,observed | `internalInteger` | `Office` | `application/msword`, `application/rtf`, `application/vnd.ms-word.document.macroenabled.12` |
| `meta:character-count-with-spaces` | declared,observed | `internalInteger` | `Office` | `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.ms-word.template.macroenabled.12`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `meta:creation-date` | declared,not-observed | `internalDate` | `Office` | _-_ |
| `meta:image-count` | declared,not-observed | `internalInteger` | `Office` | _-_ |
| `meta:initial-author` | declared,not-observed | `internalText` | `Office` | _-_ |
| `meta:keyword` | observed | `-` | `-` | `application/pdf`, `application/vnd.ms-powerpoint`, `application/vnd.ms-word.document.macroenabled.12` |
| `meta:last-author` | declared,observed | `internalText` | `Office` | `application/msword`, `application/rtf`, `application/vnd.ms-excel` |
| `meta:line-count` | declared,observed | `internalInteger` | `Office` | `application/vnd.ms-word.document.macroenabled.12`, `application/vnd.ms-word.template.macroenabled.12`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `meta:object-count` | declared,not-observed | `internalInteger` | `Office` | _-_ |
| `meta:page-count` | declared,observed | `internalInteger` | `Office` | `application/msword`, `application/rtf`, `application/vnd.ms-word.document.macroenabled.12` |
| `meta:paragraph-count` | declared,observed | `internalInteger` | `Office` | `application/vnd.ms-powerpoint.presentation.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12` |
| `meta:print-date` | declared,observed | `internalDate` | `Office` | `application/msword`, `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `meta:save-date` | declared,not-observed | `internalDate` | `Office` | _-_ |
| `meta:slide-count` | declared,observed | `internalInteger` | `Office` | `application/vnd.ms-powerpoint`, `application/vnd.ms-powerpoint.presentation.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12` |
| `meta:table-count` | declared,not-observed | `internalInteger` | `Office` | _-_ |
| `meta:word-count` | declared,observed | `internalInteger` | `Office` | `application/msword`, `application/rtf`, `application/vnd.ms-powerpoint` |
| `msc:binary_mime` | observed | `-` | `-` | `application/x-msc` |
| `msc:binary_sha256` | observed | `-` | `-` | `application/x-msc` |
| `msc:binary_type` | observed | `-` | `-` | `application/x-msc` |
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
| `msoffice:doc:has-hidden-text` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-word.document.macroenabled.12` |
| `msoffice:doc:has-mail-merge` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:doc:has-subdocuments` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:embeddedStorageClassId` | declared,observed | `internalText` | `Office` | `application/vnd.ms-equation`, `application/vnd.ms-excel`, `application/vnd.ms-outlook` |
| `msoffice:excel:has-data-connections` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:excel:has-dde-links` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:excel:has-external-links` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `msoffice:excel:has-external-pivot-data` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:excel:has-hidden-cols` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-excel.template.macroenabled.12` |
| `msoffice:excel:has-hidden-rows` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `msoffice:excel:has-hidden-sheets` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `msoffice:excel:has-power-query` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:excel:has-very-hidden-sheets` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `msoffice:excel:has-web-queries` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:excel:has-xls4-auto-exec` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:excel:has-xls4-macros` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel` |
| `msoffice:excel:hidden-sheet-names` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `msoffice:excel:protected-worksheet` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel`, `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `msoffice:excel:very-hidden-sheet-names` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.macroenabled.12` |
| `msoffice:excel:workbook-codename` | declared,observed | `internalText` | `Office` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-excel.template.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `msoffice:excel:xls4-macro-sheet-names` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel` |
| `msoffice:has-comments` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel`, `application/vnd.ms-excel.sheet.binary.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `msoffice:has-external-chart-data` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:has-external-ole-objects` | declared,observed | `internalBoolean` | `Office` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `msoffice:has-field-hyperlinks` | declared,observed | `internalBoolean` | `Office` | `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `msoffice:has-hover-hyperlinks` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:has-linked-ole-objects` | declared,observed | `internalBoolean` | `Office` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `msoffice:has-track-changes` | declared,observed | `internalBoolean` | `Office` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `msoffice:has-vml-hyperlinks` | declared,not-observed | `internalBoolean` | `Office` | _-_ |
| `msoffice:link:action-type` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12` |
| `msoffice:link:context` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12` |
| `msoffice:link:id` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12` |
| `msoffice:link:ocr-text` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12` |
| `msoffice:link:relationship-type` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12` |
| `msoffice:link:source` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12` |
| `msoffice:link:text` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12` |
| `msoffice:link:trigger` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12` |
| `msoffice:link:type` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12` |
| `msoffice:link:url` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-powerpoint.slideshow.macroenabled.12`, `application/vnd.ms-word.document.macroenabled.12` |
| `msoffice:ocxName` | declared,observed | `internalText` | `Office` | `application/x-tika-msoffice` |
| `msoffice:ooxml:ole-auto-exec` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `msoffice:ooxml:ole-suspicious-progids` | declared,observed | `internalTextBag` | `Office` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `msoffice:ppt:has-animations` | declared,observed | `internalBoolean` | `Office` | `application/vnd.ms-powerpoint`, `application/vnd.ms-powerpoint.presentation.macroenabled.12`, `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `msoffice:ppt:has-hidden-slides` | declared,observed | `internalBoolean` | `Office` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `msoffice:ppt:num-hidden-slides` | declared,observed | `internalInteger` | `Office` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `msoffice:ppt:num-unlisted-slides` | declared,not-observed | `internalInteger` | `Office` | _-_ |
| `msoffice:ppt:unlisted-slide-names` | declared,not-observed | `internalTextBag` | `Office` | _-_ |
| `msoffice:progID` | declared,observed | `internalText` | `Office` | `application/msword`, `application/octet-stream`, `application/pdf` |
| `msoffice:xlsb:has-xlm-macros` | undeclared-literal,observed | `-` | `-` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `msoffice:xlsx:has-xlm-macros` | undeclared-literal,observed | `-` | `-` | `application/vnd.ms-excel.sheet.macroenabled.12`, `application/vnd.ms-excel.template.macroenabled.12` |
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
| `onenote:nFileVersionGeneration` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `onenote:rgbPlaceholder` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `original` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `original-format-type` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `outlinks` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `patches` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `pdf:PDFExtensionVersion` | declared,observed | `internalRational` | `PDF` | `application/pdf` |
| `pdf:PDFVersion` | declared,observed | `internalRational` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:actionTrigger` | declared,not-observed | `internalText` | `PDF` | _-_ |
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
| `pdf:docinfo:custom:Company` | observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:Nur_Dienstgebrauch` | observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:custom:SourceModified` | observed | `-` | `-` | `application/pdf` |
| `pdf:docinfo:keywords` | declared,observed | `internalText` | `PDF` | `application/pdf` |
| `pdf:docinfo:modified` | declared,observed | `internalDate` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:docinfo:producer` | declared,observed | `internalText` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:docinfo:subject` | declared,observed | `internalText` | `PDF` | `application/pdf` |
| `pdf:docinfo:title` | declared,observed | `internalText` | `PDF` | `application/pdf` |
| `pdf:docinfo:trapped` | declared,observed | `internalText` | `PDF` | `application/pdf` |
| `pdf:embeddedFileAnnotationType` | declared,not-observed | `internalText` | `PDF` | _-_ |
| `pdf:embeddedFileDescription` | declared,observed | `externalText` | `PDF` | `application/xml` |
| `pdf:embeddedFileSubtype` | declared,not-observed | `internalText` | `PDF` | _-_ |
| `pdf:encrypted` | declared,observed | `internalBoolean` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:eofOffsets` | declared,observed | `externalRealSeq` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:foundNonAdobeExtensionName` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `pdf:has3D` | declared,not-observed | `internalBoolean` | `PDF` | _-_ |
| `pdf:hasAcroFormFields` | declared,observed | `internalBoolean` | `PDF` | `application/pdf` |
| `pdf:hasCollection` | declared,observed | `internalBoolean` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:hasMarkedContent` | declared,observed | `internalBoolean` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:hasXFA` | declared,observed | `internalBoolean` | `PDF` | `application/illustrator`, `application/pdf` |
| `pdf:hasXMP` | declared,observed | `internalBoolean` | `PDF` | `application/illustrator`, `application/pdf`, `image/jpeg` |
| `pdf:illustrator:type` | declared,not-observed | `internalText` | `PDF` | _-_ |
| `pdf:incrementalUpdateCount` | observed | `-` | `-` | `application/illustrator`, `application/pdf` |
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
| `pdfa:PDFVersion` | declared,not-observed | `internalRational` | `PDF` | _-_ |
| `pdfaid:conformance` | declared,not-observed | `internalText` | `PDF` | _-_ |
| `pdfaid:part` | declared,not-observed | `internalInteger` | `PDF` | _-_ |
| `pdfuaid:part` | declared,not-observed | `internalInteger` | `PDF` | _-_ |
| `pdfvt:modified` | declared,not-observed | `internalDate` | `PDF` | _-_ |
| `pdfvt:version` | declared,not-observed | `internalText` | `PDF` | _-_ |
| `pdfx:conformance` | declared,not-observed | `internalText` | `PDF` | _-_ |
| `pdfx:version` | declared,not-observed | `internalText` | `PDF` | _-_ |
| `pdfxid:version` | declared,not-observed | `internalText` | `PDF` | _-_ |
| `phonenumbers` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `photoshop:AuthorsPosition` | declared,not-observed | `internalText` | `Photoshop` | _-_ |
| `photoshop:CaptionWriter` | declared,not-observed | `internalText` | `Photoshop` | _-_ |
| `photoshop:Category` | declared,not-observed | `internalText` | `Photoshop` | _-_ |
| `photoshop:City` | declared,not-observed | `internalText` | `Photoshop` | _-_ |
| `photoshop:ColorMode` | declared,not-observed | `internalClosedChoise` | `Photoshop` | _-_ |
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
| `plus:CopyrightOwnerName` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:ImageCreator` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:ImageCreatorName` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:ImageSupplier` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `plus:ImageSupplierImageID` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `plus:ImageSupplierName` | declared,not-observed | `internalText` | `IPTC` | _-_ |
| `plus:Licensor` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorCity` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorCountry` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorEmail` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
| `plus:LicensorExtendedAddress` | declared,not-observed | `internalTextBag` | `IPTC` | _-_ |
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
| `ppkg:data_asset_ref` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `ppkg:warning` | undeclared-literal,not-observed | `-` | `-` | _-_ |
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
| `rendering:rendering-time-ms` | declared,not-observed | `externalReal` | `Rendering` | _-_ |
| `rtf:objdataMixedCase` | observed | `-` | `-` | `application/rtf` |
| `rtf:protocolHandler` | observed | `-` | `-` | `application/rtf` |
| `rtf:uncPath` | observed | `-` | `-` | `application/rtf` |
| `rtf_color_qr:colortbl_size` | undeclared-literal,observed | `-` | `-` | `application/rtf` |
| `rtf_color_qr:enabled` | undeclared-literal,observed | `-` | `-` | `application/rtf` |
| `rtf_color_qr:error` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `rtf_color_qr:rows_captured` | undeclared-literal,observed | `-` | `-` | `application/rtf` |
| `rtf_meta:contains_encapsulated_html` | declared,observed | `internalBoolean` | `RTFMetadata` | `application/rtf`, `application/vnd.ms-outlook` |
| `rtf_meta:emb_app_version` | declared,observed | `internalText` | `RTFMetadata` | `application/vnd.ms-equation`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/x-tika-msoffice` |
| `rtf_meta:emb_class` | declared,observed | `internalText` | `RTFMetadata` | `application/vnd.ms-equation`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/x-tika-msoffice` |
| `rtf_meta:emb_class_obfuscated` | declared,observed | `internalBoolean` | `RTFMetadata` | `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `application/x-tika-msoffice` |
| `rtf_meta:emb_clsid` | declared,observed | `internalText` | `RTFMetadata` | `application/vnd.ms-equation`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/x-tika-msoffice` |
| `rtf_meta:emb_clsid_name` | declared,observed | `internalText` | `RTFMetadata` | `application/vnd.ms-equation`, `application/vnd.ms-excel.sheet.macroenabled.12`, `application/x-tika-msoffice` |
| `rtf_meta:emb_item` | declared,not-observed | `internalText` | `RTFMetadata` | _-_ |
| `rtf_meta:emb_label` | declared,not-observed | `internalText` | `RTFMetadata` | _-_ |
| `rtf_meta:emb_ole2link_url` | declared,observed | `internalText` | `RTFMetadata` | `application/vnd.ms-equation`, `application/x-tika-msoffice` |
| `rtf_meta:emb_source_path` | declared,observed | `internalText` | `RTFMetadata` | `text/plain` |
| `rtf_meta:emb_topic` | declared,not-observed | `internalText` | `RTFMetadata` | _-_ |
| `rtf_meta:hex_escape_in_objdata` | declared,not-observed | `internalBoolean` | `RTFMetadata` | _-_ |
| `rtf_meta:malformed_rtf_header` | declared,observed | `internalBoolean` | `RTFMetadata` | `application/rtf` |
| `rtf_meta:objdata_decoy_count` | declared,not-observed | `internalInteger` | `RTFMetadata` | _-_ |
| `rtf_meta:thumbnail` | declared,observed | `internalBoolean` | `RTFMetadata` | `application/octet-stream`, `image/emf`, `image/jpeg` |
| `rtf_meta:unicode_in_objdata` | declared,not-observed | `internalBoolean` | `RTFMetadata` | _-_ |
| `rtf_pict:fArrowheadsOK` | observed | `-` | `-` | `image/emf` |
| `rtf_pict:fCameFromImgDummy` | observed | `-` | `-` | `image/emf`, `image/wmf` |
| `rtf_pict:fFakeMaster` | observed | `-` | `-` | `image/emf`, `image/wmf` |
| `rtf_pict:fFilled` | observed | `-` | `-` | `image/emf`, `image/wmf` |
| `rtf_pict:fFlipH` | observed | `-` | `-` | `image/emf`, `image/jpeg`, `image/wmf` |
| `rtf_pict:fFlipV` | observed | `-` | `-` | `image/emf`, `image/jpeg`, `image/wmf` |
| `rtf_pict:fHitTestFill` | observed | `-` | `-` | `image/emf`, `image/wmf` |
| `rtf_pict:fHitTestLine` | observed | `-` | `-` | `image/emf` |
| `rtf_pict:fInsetPen` | observed | `-` | `-` | `image/emf` |
| `rtf_pict:fInsetPenOK` | observed | `-` | `-` | `image/emf` |
| `rtf_pict:fLayoutInCell` | observed | `-` | `-` | `image/emf`, `image/jpeg`, `image/wmf` |
| `rtf_pict:fLine` | observed | `-` | `-` | `image/emf`, `image/jpeg`, `image/wmf` |
| `rtf_pict:fLineRecolorFillAsPicture` | observed | `-` | `-` | `image/emf` |
| `rtf_pict:fLineUseShapeAnchor` | observed | `-` | `-` | `image/emf` |
| `rtf_pict:fLockAspectRatio` | observed | `-` | `-` | `image/emf`, `image/wmf` |
| `rtf_pict:fNoFillHitTest` | observed | `-` | `-` | `image/emf`, `image/wmf` |
| `rtf_pict:fNoLineDrawDash` | observed | `-` | `-` | `image/emf` |
| `rtf_pict:fPreferRelativeResize` | observed | `-` | `-` | `image/emf`, `image/wmf` |
| `rtf_pict:fReallyHidden` | observed | `-` | `-` | `image/emf`, `image/wmf` |
| `rtf_pict:fRecolorFillAsPicture` | observed | `-` | `-` | `image/emf`, `image/wmf` |
| `rtf_pict:fScriptAnchor` | observed | `-` | `-` | `image/emf`, `image/wmf` |
| `rtf_pict:fUseShapeAnchor` | observed | `-` | `-` | `image/emf`, `image/wmf` |
| `rtf_pict:fillColor` | observed | `-` | `-` | `image/wmf` |
| `rtf_pict:fillOpacity` | observed | `-` | `-` | `image/wmf` |
| `rtf_pict:fillShape` | observed | `-` | `-` | `image/emf`, `image/wmf` |
| `rtf_pict:fillUseRect` | observed | `-` | `-` | `image/emf`, `image/wmf` |
| `rtf_pict:lineFillShape` | observed | `-` | `-` | `image/emf` |
| `rtf_pict:pictureActive` | observed | `-` | `-` | `image/emf` |
| `rtf_pict:pictureBiLevel` | observed | `-` | `-` | `image/emf`, `image/wmf` |
| `rtf_pict:pictureGray` | observed | `-` | `-` | `image/emf`, `image/wmf` |
| `rtf_pict:shapeType` | observed | `-` | `-` | `image/emf`, `image/jpeg`, `image/wmf` |
| `rtf_pict:wzDescription` | observed | `-` | `-` | `image/wmf` |
| `samplerate` | undeclared-literal,observed | `-` | `-` | `audio/vnd.wave` |
| `segment-type` | undeclared-literal,not-observed | `-` | `-` | _-_ |
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
| `standard_references` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `streams-total` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `strings:encoding` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `strings:file_output` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `strings:length` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `strings:min-len` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `summary` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `svg:externalScript` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `svg:externalUseRef` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `svg:hasEventHandlers` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `svg:hasForeignObject` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `svg:hasZeroWidthChars` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `svg:link` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `target-language` | undeclared-literal,not-observed | `-` | `-` | _-_ |
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
| `tika:chunks` | undeclared-literal,not-observed | `-` | `-` | _-_ |
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
| `vendor` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `version` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `w:Comments` | declared,observed | `externalTextBag` | `OfficeOpenXMLExtended` | `image/gif`, `image/jpeg` |
| `warc:WARC-Record-ID` | declared,not-observed | `externalText` | `WARC` | _-_ |
| `warc:http:status` | undeclared-literal,not-observed | `-` | `-` | _-_ |
| `warc:http:status:reason` | undeclared-literal,not-observed | `-` | `-` | _-_ |
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
| `xmp:About` | declared,observed | `externalTextBag` | `XMP` | `application/pdf` |
| `xmp:Advisory` | declared,not-observed | `externalTextBag` | `XMP` | _-_ |
| `xmp:CreateDate` | declared,observed | `externalDate` | `XMP` | `application/illustrator`, `application/pdf` |
| `xmp:CreatorTool` | declared,observed | `externalText` | `XMP` | `application/illustrator`, `application/pdf`, `video/mp4` |
| `xmp:Identifier` | declared,not-observed | `externalTextBag` | `XMP` | _-_ |
| `xmp:Label` | declared,not-observed | `externalText` | `XMP` | _-_ |
| `xmp:MetadataDate` | declared,observed | `externalDate` | `XMP` | `application/illustrator`, `application/pdf` |
| `xmp:ModifyDate` | declared,observed | `externalDate` | `XMP` | `application/illustrator`, `application/pdf` |
| `xmp:NickName` | declared,not-observed | `externalText` | `XMP` | _-_ |
| `xmp:Rating` | declared,not-observed | `externalInteger` | `XMP` | _-_ |
| `xmp:Title` | declared,not-observed | `externalText` | `XMP` | _-_ |
| `xmp:dc:contributor` | declared,not-observed | `internalTextBag` | `XMPDC` | _-_ |
| `xmp:dc:coverage` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dc:creator` | declared,observed | `internalTextBag` | `XMPDC` | `application/pdf` |
| `xmp:dc:date` | declared,not-observed | `internalDate` | `XMPDC` | _-_ |
| `xmp:dc:description` | declared,observed | `internalText` | `XMPDC` | `application/pdf` |
| `xmp:dc:description:x-default` | observed | `-` | `-` | `application/pdf` |
| `xmp:dc:format` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dc:identifier` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dc:language` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dc:publisher` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dc:relation` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dc:rights` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dc:source` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dc:subject` | declared,observed | `internalTextBag` | `XMPDC` | `application/pdf` |
| `xmp:dc:title` | declared,observed | `internalText` | `XMPDC` | `application/pdf` |
| `xmp:dc:title:x-default` | observed | `-` | `-` | `application/pdf` |
| `xmp:dc:type` | declared,not-observed | `internalText` | `XMPDC` | _-_ |
| `xmp:dcterms:created` | declared,not-observed | `internalDate` | `XMPDC` | _-_ |
| `xmp:dcterms:modified` | declared,not-observed | `internalDate` | `XMPDC` | _-_ |
| `xmp:pdf:About` | declared,not-observed | `externalTextBag` | `XMPPDF` | _-_ |
| `xmp:pdf:Keywords` | declared,observed | `externalTextBag` | `XMPPDF` | `application/pdf` |
| `xmp:pdf:PDFVersion` | declared,not-observed | `externalText` | `XMPPDF` | _-_ |
| `xmp:pdf:Producer` | declared,observed | `externalText` | `XMPPDF` | `application/illustrator`, `application/pdf` |
| `xmpDM:absPeakAudioFilePath` | declared,not-observed | `internalURI` | `XMPDM` | _-_ |
| `xmpDM:album` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:albumArtist` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:altTapeName` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:artist` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:audioChannelType` | declared,observed | `internalClosedChoise` | `XMPDM` | `video/mp4` |
| `xmpDM:audioCompressor` | declared,not-observed | `internalText` | `XMPDM` | _-_ |
| `xmpDM:audioModDate` | declared,not-observed | `internalDate` | `XMPDM` | _-_ |
| `xmpDM:audioSampleRate` | declared,observed | `internalInteger` | `XMPDM` | `audio/vnd.wave`, `video/mp4` |
| `xmpDM:audioSampleType` | declared,observed | `internalClosedChoise` | `XMPDM` | `audio/vnd.wave` |
| `xmpDM:compilation` | declared,not-observed | `externalInteger` | `XMPDM` | _-_ |
| `xmpDM:composer` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:copyright` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:discNumber` | declared,not-observed | `externalInteger` | `XMPDM` | _-_ |
| `xmpDM:duration` | declared,observed | `externalReal` | `XMPDM` | `video/mp4` |
| `xmpDM:engineer` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:fileDataRate` | declared,not-observed | `internalRational` | `XMPDM` | _-_ |
| `xmpDM:genre` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:instrument` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:key` | declared,not-observed | `internalClosedChoise` | `XMPDM` | _-_ |
| `xmpDM:logComment` | declared,not-observed | `externalText` | `XMPDM` | _-_ |
| `xmpDM:loop` | declared,not-observed | `internalBoolean` | `XMPDM` | _-_ |
| `xmpDM:metadataModDate` | declared,not-observed | `internalDate` | `XMPDM` | _-_ |
| `xmpDM:numberOfBeats` | declared,not-observed | `internalReal` | `XMPDM` | _-_ |
| `xmpDM:pullDown` | declared,not-observed | `internalClosedChoise` | `XMPDM` | _-_ |
| `xmpDM:relativePeakAudioFilePath` | declared,not-observed | `internalURI` | `XMPDM` | _-_ |
| `xmpDM:releaseDate` | declared,not-observed | `externalDate` | `XMPDM` | _-_ |
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
| `xmpMM:DerivedFrom:DocumentID` | declared,not-observed | `externalText` | `XMPMM` | _-_ |
| `xmpMM:DerivedFrom:InstanceID` | declared,not-observed | `externalText` | `XMPMM` | _-_ |
| `xmpMM:DocumentID` | declared,observed | `externalText` | `XMPMM` | `application/illustrator`, `application/pdf`, `image/jpeg` |
| `xmpMM:History:Action` | declared,not-observed | `externalTextBag` | `XMPMM` | _-_ |
| `xmpMM:History:InstanceID` | declared,not-observed | `externalTextBag` | `XMPMM` | _-_ |
| `xmpMM:History:SoftwareAgent` | declared,not-observed | `externalTextBag` | `XMPMM` | _-_ |
| `xmpMM:History:When` | declared,not-observed | `externalTextBag` | `XMPMM` | _-_ |
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
| `zip:centralDirectoryOnlyEntries` | declared,not-observed | `internalTextBag` | `Zip` | _-_ |
| `zip:comment` | declared,not-observed | `externalText` | `Zip` | _-_ |
| `zip:compressedSize` | declared,not-observed | `externalText` | `Zip` | _-_ |
| `zip:compressionMethod` | declared,not-observed | `externalInteger` | `Zip` | _-_ |
| `zip:crc32` | declared,not-observed | `externalText` | `Zip` | _-_ |
| `zip:detectorDataDescriptorRequired` | declared,not-observed | `internalBoolean` | `Zip` | _-_ |
| `zip:detectorZipFileOpened` | declared,observed | `internalBoolean` | `Zip` | `application/java-archive`, `application/vnd.ms-excel.addin.macroenabled.12`, `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `zip:duplicateEntryNames` | declared,not-observed | `internalTextBag` | `Zip` | _-_ |
| `zip:encrypted` | declared,not-observed | `externalBoolean` | `Zip` | _-_ |
| `zip:integrityCheckResult` | declared,observed | `internalText` | `Zip` | `application/java-archive`, `application/zip` |
| `zip:localHeaderOnlyEntries` | declared,not-observed | `internalTextBag` | `Zip` | _-_ |
| `zip:platform` | declared,not-observed | `externalInteger` | `Zip` | _-_ |
| `zip:salvaged` | declared,observed | `internalBoolean` | `Zip` | `application/vnd.ms-excel.sheet.binary.macroenabled.12` |
| `zip:uncompressedSize` | declared,not-observed | `externalText` | `Zip` | _-_ |
| `zip:unixMode` | declared,not-observed | `externalInteger` | `Zip` | _-_ |
| `zip:versionMadeBy` | declared,not-observed | `externalInteger` | `Zip` | _-_ |
