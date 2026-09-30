using System.Net.Http.Json;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Security.Cryptography;
using NexArena.Agent;

var configPath = args.FirstOrDefault() ?? "appsettings.local.json";
if (!File.Exists(configPath))
{
    Console.Error.WriteLine("Copy appsettings.example.json to appsettings.local.json and configure it first.");
    return 1;
}
var config = JsonSerializer.Deserialize<AgentConfig>(File.ReadAllText(configPath)) ?? throw new Exception("Invalid configuration");
if (!Uri.TryCreate(config.BackendUrl, UriKind.Absolute, out var backend) || (backend.Scheme != "http" && backend.Scheme != "https"))
    throw new Exception("BackendUrl must be an HTTP(S) URL");
var stateDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "NexArena", config.MachineId);
Directory.CreateDirectory(stateDir);
var secretFile = Path.Combine(stateDir, "agent.secret");
if (!File.Exists(secretFile)) File.WriteAllText(secretFile, Convert.ToHexString(RandomNumberGenerator.GetBytes(32)));
var secret = File.ReadAllText(secretFile).Trim();
using var http = new HttpClient { BaseAddress = backend, Timeout = TimeSpan.FromSeconds(15) };
http.DefaultRequestHeaders.Add("X-Agent-Key", config.EnrollmentKey);
using var hardware = new HardwareMonitor();
using var cancellation = new CancellationTokenSource();
Console.CancelKeyPress += (_, e) => { e.Cancel = true; cancellation.Cancel(); };
var ct = cancellation.Token;
var retry = 1;
Console.WriteLine("[INFO] NexArena agent started; remote commands " + (config.EnableRemoteCommands ? "enabled" : "disabled"));
while (!ct.IsCancellationRequested)
{
    try
    {
        using var response = await http.PostAsJsonAsync("/api/nodes/register", new
        {
            machine_id = config.MachineId, hostname = Environment.MachineName,
            name = config.DisplayName, branch_id = config.BranchId,
            os = Environment.OSVersion.ToString(), agent_version = "1.0.0", agent_secret = secret
        }, ct);
        response.EnsureSuccessStatusCode();
        using var registration = JsonDocument.Parse(await response.Content.ReadAsStringAsync(ct));
        var nodeId = registration.RootElement.GetProperty("node_id").GetString();
        using var ws = new ClientWebSocket();
        ws.Options.KeepAliveInterval = TimeSpan.FromSeconds(10);
        var wsUri = new UriBuilder(backend) { Scheme = backend.Scheme == "https" ? "wss" : "ws", Path = $"/ws/agent/{nodeId}" }.Uri;
        await ws.ConnectAsync(wsUri, ct);
        using var sendLock = new SemaphoreSlim(1);
        async Task Send(object value, CancellationToken token)
        {
            await sendLock.WaitAsync(token);
            try { await ws.SendAsync(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(value)), WebSocketMessageType.Text, true, token); }
            finally { sendLock.Release(); }
        }
        await Send(new { secret }, ct);
        Console.WriteLine($"[INFO] Connected as node {nodeId}");
        retry = 1;
        using var connection = CancellationTokenSource.CreateLinkedTokenSource(ct);
        var connectionToken = connection.Token;
        var telemetry = Task.Run(async () =>
        {
            while (!connectionToken.IsCancellationRequested)
            {
                await Send(new { type = "telemetry", data = hardware.Read() }, connectionToken);
                await Task.Delay(TimeSpan.FromSeconds(Math.Clamp(config.TelemetrySeconds, 2, 20)), connectionToken);
            }
        }, connectionToken);
        var heartbeat = Task.Run(async () =>
        {
            while (!connectionToken.IsCancellationRequested)
            {
                await Send(new { type = "heartbeat" }, connectionToken);
                await Task.Delay(TimeSpan.FromSeconds(Math.Clamp(config.HeartbeatSeconds, 2, 10)), connectionToken);
            }
        }, connectionToken);
        var receive = Task.Run(async () =>
        {
            var buffer = new byte[8192];
            while (ws.State == WebSocketState.Open && !connectionToken.IsCancellationRequested)
            {
                using var message = new MemoryStream();
                WebSocketReceiveResult part;
                do
                {
                    part = await ws.ReceiveAsync(new ArraySegment<byte>(buffer), connectionToken);
                    if (part.MessageType == WebSocketMessageType.Close) throw new IOException("Backend closed connection");
                    message.Write(buffer, 0, part.Count);
                    if (message.Length > 65536) throw new IOException("Command too large");
                } while (!part.EndOfMessage);
                using var document = JsonDocument.Parse(message.ToArray());
                var data = document.RootElement;
                if (data.GetProperty("type").GetString() != "command") continue;
                var commandId = data.GetProperty("command_id").GetString()!;
                var result = Commands.Execute(data, config, stateDir);
                await Send(new { type = "command_result", command_id = commandId, success = result.Success, message = result.Message }, connectionToken);
                Console.WriteLine($"[INFO] {data.GetProperty("command").GetString()}: {result.Message}");
            }
        }, connectionToken);
        try { await await Task.WhenAny(telemetry, heartbeat, receive); }
        finally
        {
            connection.Cancel();
            ws.Abort();
            try { await Task.WhenAll(telemetry, heartbeat, receive); } catch (Exception) { }
        }
    }
    catch (OperationCanceledException) when (ct.IsCancellationRequested) { break; }
    catch (Exception ex)
    {
        Console.WriteLine($"[WARN] Connection interrupted: {ex.Message}. Retry in {retry}s.");
        try { await Task.Delay(TimeSpan.FromSeconds(retry), ct); } catch (OperationCanceledException) { break; }
        retry = Math.Min(30, retry * 2);
    }
}
return 0;

namespace NexArena.Agent
{
    public sealed class AgentConfig
    {
        public string BackendUrl { get; set; } = "http://localhost:8000";
        public string EnrollmentKey { get; set; } = "";
        public string BranchId { get; set; } = "";
        public string MachineId { get; set; } = Environment.MachineName;
        public string DisplayName { get; set; } = Environment.MachineName;
        public int HeartbeatSeconds { get; set; } = 5;
        public int TelemetrySeconds { get; set; } = 5;
        public bool EnableRemoteCommands { get; set; }
        public bool EnableShutdown { get; set; }
        public Dictionary<string, string> AllowedGames { get; set; } = new();
    }
}
