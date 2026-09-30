using System.Text.Json;
using NexArena.Agent;

var directory = Path.Combine(Path.GetTempPath(), "nexarena-test-" + Guid.NewGuid());
Directory.CreateDirectory(directory);
var count = 0;
void Check(string name, AgentConfig config, object payload, string expected)
{
    using var document = JsonDocument.Parse(JsonSerializer.Serialize(payload));
    var result = Commands.Execute(document.RootElement, config, directory);
    if (result.Success || !result.Message.Contains(expected)) throw new Exception($"{name}: unexpected result {result}");
    Console.WriteLine("PASS " + name);
    count++;
}
object Payload(string command, string? id = null, string gameId = "test", string path = @"C:\Games\test.exe") => new { command_id = id ?? Guid.NewGuid().ToString(), command, game_id = gameId, executable_path = path };
Check("remote commands disabled", new(), Payload("LOCK_SCREEN"), "disabled");
var enabled = new AgentConfig { EnableRemoteCommands = true };
Check("shutdown requires explicit local opt-in", enabled, Payload("SHUTDOWN"), "disabled");
Check("unknown command rejected", enabled, Payload("SHELL"), "Unsupported");
Check("unallowlisted game rejected", enabled, Payload("LAUNCH_GAME"), "allowlist");
enabled.AllowedGames["test"] = @"C:\Games\test.exe";
Check("mismatched path rejected", enabled, Payload("LAUNCH_GAME", path: @"C:\Windows\System32\cmd.exe"), "does not match");
Check("missing executable rejected", enabled, Payload("LAUNCH_GAME"), "not installed");
Check("invalid command ID rejected", enabled, Payload("LOCK_SCREEN", "not-a-guid"), "Invalid");
var replay = Guid.NewGuid().ToString();
Check("first unsupported command recorded", enabled, Payload("UNSUPPORTED", replay), "Unsupported");
Check("replayed command rejected", enabled, Payload("LOCK_SCREEN", replay), "already processed");
Console.WriteLine($"{count} agent safety tests passed; no lock, shutdown, or game process executed.");
