using System;
using System.Collections.Generic;
using System.Runtime.Serialization;
using MFiles.VAF;
using MFiles.VAF.Configuration;
using MFiles.VAF.Extensions;

namespace AILegalAssistant
{
    // Uporabljamo razlièico, ki se je prej uspešno zgradila
    public class AILegalApp : ConfigurableVaultApplicationBase<Configuration>
    {
    }

    [DataContract]
    public class Configuration
    {
        [DataMember]
        [JsonConfEditor(Label = "AI Sodelavci")]
        public List<ColleagueConfig> Colleagues { get; set; } = new List<ColleagueConfig>();
    }

    [DataContract]
    public class ColleagueConfig
    {
        [DataMember]
        public string id { get; set; }
        [DataMember]
        public string name { get; set; }
        [DataMember]
        public string instruction { get; set; }
        [DataMember]
        public string allowed_users { get; set; } = "*";
        [DataMember]
        public List<string> allowed_groups { get; set; } = new List<string>();
    }
}
