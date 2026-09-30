// ==============================================================================
// NetIntel Power Query (M) Scripts for Power BI Desktop
// Paste into Power Query Advanced Editor for instant schema ingestion
// ==============================================================================

// ------------------------------------------------------------------------------
// Query 1: FactNetworkMetrics
// ------------------------------------------------------------------------------
let
    // Update path to your local project directory if needed
    Source = Csv.Document(File.Contents("C:\PROJECTS\CN-PROJECT\data\exports\network_metrics.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromoteHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangeTypes = Table.TransformColumnTypes(PromoteHeaders,{
        {"timestamp", type datetimezone},
        {"epoch_time", type number},
        {"interface", type text},
        {"upload_mbps", type number},
        {"download_mbps", type number},
        {"bytes_sent", Int64.Type},
        {"bytes_recv", Int64.Type},
        {"packets_sent", Int64.Type},
        {"packets_recv", Int64.Type},
        {"packets_sent_per_sec", type number},
        {"packets_recv_per_sec", type number},
        {"latency_ms", type number},
        {"jitter_ms", type number},
        {"packet_loss_percent", type number},
        {"estimated_utilization_percent", type number},
        {"health_score", type number},
        {"stability_score", type number},
        {"monitoring_mode", type text},
        {"is_simulation", Int64.Type}
    }),
    AddDateKey = Table.AddColumn(ChangeTypes, "DateKey", each Date.Year(DateTimeZone.Date([timestamp])) * 10000 + Date.Month(DateTimeZone.Date([timestamp])) * 100 + Date.Day(DateTimeZone.Date([timestamp])), Int64.Type),
    AddTimeKey = Table.AddColumn(AddDateKey, "TimeKey", each Time.ToText(DateTimeZone.Time([timestamp]), "hh:mm:ss"), type text)
in
    AddTimeKey


// ------------------------------------------------------------------------------
// Query 2: FactLatencyProbes
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents("C:\PROJECTS\CN-PROJECT\data\exports\latency_metrics.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromoteHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangeTypes = Table.TransformColumnTypes(PromoteHeaders,{
        {"timestamp", type datetimezone},
        {"target_name", type text},
        {"target_host", type text},
        {"probes_sent", Int64.Type},
        {"probes_received", Int64.Type},
        {"packet_loss_percent", type number},
        {"latency_min_ms", type number},
        {"latency_avg_ms", type number},
        {"latency_max_ms", type number},
        {"jitter_ms", type number},
        {"status", type text}
    }),
    AddDateKey = Table.AddColumn(ChangeTypes, "DateKey", each Date.Year(DateTimeZone.Date([timestamp])) * 10000 + Date.Month(DateTimeZone.Date([timestamp])) * 100 + Date.Day(DateTimeZone.Date([timestamp])), Int64.Type),
    AddTimeKey = Table.AddColumn(AddDateKey, "TimeKey", each Time.ToText(DateTimeZone.Time([timestamp]), "hh:mm:ss"), type text)
in
    AddTimeKey


// ------------------------------------------------------------------------------
// Query 3: FactIncidents
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents("C:\PROJECTS\CN-PROJECT\data\exports\incidents.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromoteHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangeTypes = Table.TransformColumnTypes(PromoteHeaders,{
        {"incident_id", type text},
        {"start_timestamp", type datetimezone},
        {"duration_seconds", type number},
        {"status", type text},
        {"severity", type text},
        {"trigger_reason", type text},
        {"peak_latency_ms", type number},
        {"peak_jitter_ms", type number},
        {"peak_packet_loss_percent", type number},
        {"min_health_score", type number},
        {"min_stability_score", type number},
        {"diagnosis_summary", type text}
    })
in
    ChangeTypes
