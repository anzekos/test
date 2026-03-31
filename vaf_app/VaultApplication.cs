// ============================================================
//  VaultApplication.cs  –  AI Legal Assistant VAF
//  Fixes: using direktive, namespace, Configuration razred,
//         SFBoolean, MFVaultAccess, ObjVerEx, JsonConvert,
//         MFEventLog, Exception
// ============================================================

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.Serialization;

using MFiles.VAF;
using MFiles.VAF.Common;
using MFiles.VAF.Configuration;
using MFiles.VAF.Extensions;

using MFilesAPI;

// Eksplicitno kvalificiramo Newtonsoft, ker MFiles.VAF.Extensions
// izvaža lastni JsonConvert in povzroči "ambiguous reference"
using NJson = Newtonsoft.Json.JsonConvert;

namespace AILegalAssistant
{
    // --------------------------------------------------------
    //  Configuration – mora obstajati kot [DataContract] razred.
    //  Prazna zadostuje, dokler nimaš admin UI nastavitev.
    // --------------------------------------------------------
    [DataContract]
    public class Configuration { }

    // --------------------------------------------------------
    //  DTO – prenos podatkov med VAF in UIX
    // --------------------------------------------------------
    [DataContract]
    public class AISodelavecDto
    {
        [DataMember(Name = "id")] public string Id { get; set; }
        [DataMember(Name = "name")] public string Name { get; set; }
        [DataMember(Name = "instruction")] public string Instruction { get; set; }
        [DataMember(Name = "allowed_users")] public List<string> AllowedUsers { get; set; }
        [DataMember(Name = "allowed_groups")] public List<string> AllowedGroups { get; set; }
    }

    // --------------------------------------------------------
    //  VaultApplication
    //  Ime razreda se mora ujemati z appdef.xml:
    //  <class>AILegalAssistant.VaultApplication</class>
    // --------------------------------------------------------
    public class VaultApplication
        : ConfigurableVaultApplicationBase<Configuration>
    {
        // ----------------------------------------------------
        //  MFIdentifier aliasi
        //  Samodejno se povežejo z vault ID-ji ob zagonu VAF.
        //  Aliasi morajo biti enaki tistim nastavljenim v
        //  M-Files Admin → Object Types / Property Defs / Classes
        // ----------------------------------------------------

        [MFObjType(Required = true)]
        public MFIdentifier AISodelavecObjType =
            "MFiles.ObjectType.AISodelavec";

        [MFPropertyDef(Required = true)]
        public MFIdentifier NavodiloPropertyDef =
            "MFiles.Prop.AISodelavec.Navodilo";

        [MFPropertyDef(Required = true)]
        public MFIdentifier DovoljeniUporabnikiPropDef =
            "MFiles.Prop.AISodelavec.DovoljeniUporabniki";

        [MFPropertyDef(Required = true)]
        public MFIdentifier DovoljeneSkupinePropDef =
            "MFiles.Prop.AISodelavec.DovoljeneSkupine";

        [MFClass(Required = true)]
        public MFIdentifier AISodelavecClass =
            "MFiles.Class.AISodelavec";

        // ----------------------------------------------------
        //  GetAISodelavci – Vault Extension Method
        //  UIX klic:
        //    vault.ExtensionMethodOperations
        //         .ExecuteVaultExtensionMethod("GetAISodelavci","")
        // ----------------------------------------------------
        [VaultExtensionMethod("GetAISodelavci",
            RequiredVaultAccess = MFVaultAccess.MFVaultAccessNone)]
        public string GetAISodelavci(EventHandlerEnvironment env)
        {
            var result = new List<AISodelavecDto>();

            try
            {
                var searchBuilder = new MFSearchBuilder(env.Vault);
                searchBuilder.ObjType(AISodelavecObjType.ID);
                var found = searchBuilder.FindEx();

                foreach (var item in found)
                {
                    result.Add(new AISodelavecDto
                    {
                        Id            = item.ObjVer.ObjID.ID.ToString(),
                        Name          = item.Title,
                        Instruction   = GetTextProperty(item, NavodiloPropertyDef.ID),
                        AllowedUsers  = GetLookupValues(item, DovoljeniUporabnikiPropDef.ID),
                        AllowedGroups = GetLookupValues(item, DovoljeneSkupinePropDef.ID),
                    });
                }
            }
            catch (Exception ex)
            {
                // System.Diagnostics.EventLog – neviden če nimas admin pravic,
                // ampak ne sesuje aplikacije
                try
                {
                    EventLog.WriteEntry(
                        "AILegalAssistant",
                        "GetAISodelavci napaka: " + ex.Message,
                        EventLogEntryType.Error);
                }
                catch { /* EventLog ni dostopen – ignoriraj */ }
            }

            return NJson.SerializeObject(result);
        }

        // ----------------------------------------------------
        //  CreateAISodelavec – Vault Extension Method (opcijsko)
        //  Ustvari novega AI Sodelavca direktno iz UIX-a.
        //  Dejanske pravice urejanja ureja M-Files ACL na
        //  Object Type – ne parametar RequiredVaultAccess.
        // ----------------------------------------------------
        [VaultExtensionMethod("CreateAISodelavec",
            RequiredVaultAccess = MFVaultAccess.MFVaultAccessNone)]
        private string CreateAISodelavec(EventHandlerEnvironment env)
        {
            try
            {
                var dto = NJson.DeserializeObject<AISodelavecDto>(env.Input);

                if (dto == null || string.IsNullOrWhiteSpace(dto.Name))
                    return NJson.SerializeObject(
                        new { success = false, error = "Manjka ime." });

                var props = new PropertyValues();

                // Name / Title
                var titlePv = new PropertyValue();
                titlePv.PropertyDef =
                    (int)MFBuiltInPropertyDef.MFBuiltInPropertyDefNameOrTitle;
                titlePv.TypedValue.SetValue(
                    MFDataType.MFDatatypeText, dto.Name);
                props.Add(-1, titlePv);

                // Class
                var classPv = new PropertyValue();
                classPv.PropertyDef =
                    (int)MFBuiltInPropertyDef.MFBuiltInPropertyDefClass;
                classPv.TypedValue.SetValue(
                    MFDataType.MFDatatypeLookup, AISodelavecClass.ID);
                props.Add(-1, classPv);

                // AI Navodilo
                if (!string.IsNullOrWhiteSpace(dto.Instruction))
                {
                    var instrPv = new PropertyValue();
                    instrPv.PropertyDef = NavodiloPropertyDef.ID;
                    instrPv.TypedValue.SetValue(
                        MFDataType.MFDatatypeMultiLineText, dto.Instruction);
                    props.Add(-1, instrPv);
                }

                // CreateNewObjectEx – booleans so navadni bool, ne SFBoolean
                env.Vault.ObjectOperations.CreateNewObjectEx(
                    AISodelavecObjType.ID,
                    props,
                    new SourceObjectFiles(),
                    true,   // CheckInImmediately
                    true,   // AutoSelectPermissionsFromClass
                    null);  // AccessControlList – vzame iz class nastavitev

                return NJson.SerializeObject(new { success = true });
            }
            catch (Exception ex)
            {
                return NJson.SerializeObject(
                    new { success = false, error = ex.Message });
            }
        }

        // ----------------------------------------------------
        //  Pomožne metode
        //  ObjVerEx je iz MFiles.VAF.Common (ne MFilesAPI)
        // ----------------------------------------------------
        private string GetTextProperty(ObjVerEx item, int propDefId)
        {
            try
            {
                var pv = item.GetProperty(propDefId);
                return pv?.TypedValue?.DisplayValue ?? string.Empty;
            }
            catch { return string.Empty; }
        }

        private List<string> GetLookupValues(ObjVerEx item, int propDefId)
        {
            var names = new List<string>();
            try
            {
                var pv = item.GetProperty(propDefId);
                if (pv == null) return names;

                var lookups = pv.TypedValue.GetValueAsLookups();
                for (int i = 1; i <= lookups.Count; i++)
                    names.Add(lookups[i].DisplayValue);
            }
            catch { }
            return names;
        }
    }
}