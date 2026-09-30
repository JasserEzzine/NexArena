using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.Json;

namespace NexArena.Agent;

public record CommandResult(bool Success, string Message);

public static class Commands
{
    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool LockWorkStation();

    public static CommandResult Execute(JsonElement data, AgentConfig config, string stateDir)
    {
        if (!config.EnableRemoteCommands) return new(false, "Remote commands are disabled in this agent's local configuration.");
        try
        {
            var id = data.GetProperty("command_id").GetString();
            if (!Guid.TryParse(id, out _)) return new(false, "Invalid command identifier");
            var marker = Path.Combine(stateDir, "command-" + id);
            if (File.Exists(marker)) return new(false, "Command already processed; refusing replay");
            File.WriteAllText(marker, DateTime.UtcNow.ToString("O"));
            switch (data.GetProperty("command").GetString())
            {
                case "LOCK_SCREEN":
                    return LockWorkStation() ? new(true, "Windows workstation locked") : new(false, "Windows refused lock; run the agent in the interactive user session");
                case "SHUTDOWN":
                    if (!config.EnableShutdown) return new(false, "Shutdown is disabled in local agent configuration");
                    using (var p = Process.Start(new ProcessStartInfo(Path.Combine(Environment.SystemDirectory, "shutdown.exe")) { UseShellExecute = false, CreateNoWindow = true, ArgumentList = { "/s", "/t", "30", "/c", "NexArena administrator requested shutdown" } }))
                    {
                        if (p is null) return new(false, "Unable to start Windows shutdown");
                        p.WaitForExit(5000);
                        return p.HasExited && p.ExitCode == 0 ? new(true, "Windows shutdown scheduled in 30 seconds") : new(false, "Windows rejected shutdown request");
                    }
                case "LAUNCH_GAME":
                    var gameId = data.GetProperty("game_id").GetString() ?? "";
                    if (!config.AllowedGames.TryGetValue(gameId, out var allowed)) return new(false, "Game is not in the local allowlist");
                    var requested = data.GetProperty("executable_path").GetString() ?? "";
                    if (!Path.IsPathFullyQualified(allowed) || !Path.IsPathFullyQualified(requested) || allowed.StartsWith(@"\\") || !string.Equals(Path.GetFullPath(allowed), Path.GetFullPath(requested), StringComparison.OrdinalIgnoreCase))
                        return new(false, "Executable does not match the local allowlist");
                    if (!File.Exists(allowed) || !string.Equals(Path.GetExtension(allowed), ".exe", StringComparison.OrdinalIgnoreCase)) return new(false, "Configured executable is not installed");
                    using (var p = Process.Start(new ProcessStartInfo(allowed) { UseShellExecute = false, WorkingDirectory = Path.GetDirectoryName(allowed) }))
                        return p is null ? new(false, "Windows could not start game") : new(true, "Game process started");
                default:
                    return new(false, "Unsupported command");
            }
        }
        catch (Exception ex) { return new(false, ex.Message); }
    }
}
