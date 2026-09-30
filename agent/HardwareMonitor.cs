using System.Diagnostics;
using System.Management;
using LibreHardwareMonitor.Hardware;

namespace NexArena.Agent;

public sealed class HardwareMonitor : IDisposable
{
    private readonly Computer computer = new() { IsCpuEnabled = true, IsGpuEnabled = true, IsMemoryEnabled = true, IsMotherboardEnabled = true, IsControllerEnabled = true };
    private PerformanceCounter? cpu;
    private DateTime lastPeripherals = DateTime.MinValue;
    private bool? keyboard, mouse;

    public HardwareMonitor()
    {
        try { computer.Open(); } catch (Exception ex) { Console.WriteLine("[WARN] Hardware sensors: " + ex.Message); }
        try { cpu = new PerformanceCounter("Processor", "% Processor Time", "_Total"); cpu.NextValue(); } catch (Exception) { }
    }

    private static IEnumerable<IHardware> All(IHardware hardware)
    {
        hardware.Update();
        yield return hardware;
        foreach (var child in hardware.SubHardware)
            foreach (var item in All(child)) yield return item;
    }

    private static bool? Peripheral(string type)
    {
        try
        {
            using var query = new ManagementObjectSearcher($"SELECT DeviceID FROM {type} WHERE ConfigManagerErrorCode = 0");
            using var results = query.Get();
            return results.Count > 0;
        }
        catch (Exception) { return null; }
    }

    public object Read()
    {
        float? cpuLoad = null, ram = null, cpuTemp = null, gpuTemp = null, fan = null;
        try
        {
            foreach (var h in computer.Hardware.SelectMany(All))
                foreach (var s in h.Sensors)
                {
                    if (!s.Value.HasValue || !float.IsFinite(s.Value.Value)) continue;
                    if (h.HardwareType == HardwareType.Cpu && s.SensorType == SensorType.Load && s.Name.Contains("Total")) cpuLoad = s.Value;
                    if (h.HardwareType == HardwareType.Memory && s.SensorType == SensorType.Load) ram = s.Value;
                    if (h.HardwareType == HardwareType.Cpu && s.SensorType == SensorType.Temperature) cpuTemp = Math.Max(cpuTemp ?? -50, s.Value.Value);
                    if (h.HardwareType.ToString().StartsWith("Gpu") && s.SensorType == SensorType.Temperature) gpuTemp = Math.Max(gpuTemp ?? -50, s.Value.Value);
                    if (s.SensorType == SensorType.Fan) fan = Math.Max(fan ?? 0, s.Value.Value);
                }
        }
        catch (Exception) { }
        if (cpuLoad is null && cpu is not null) { try { cpuLoad = Math.Clamp(cpu.NextValue(), 0, 100); } catch (Exception) { } }
        if (ram is null)
        {
            try
            {
                using var query = new ManagementObjectSearcher("SELECT TotalVisibleMemorySize, FreePhysicalMemory FROM Win32_OperatingSystem");
                using var values = query.Get();
                foreach (ManagementObject value in values)
                    ram = (float)(100 * (1 - Convert.ToDouble(value["FreePhysicalMemory"]) / Convert.ToDouble(value["TotalVisibleMemorySize"])));
            }
            catch (Exception) { }
        }
        if ((DateTime.UtcNow - lastPeripherals).TotalSeconds > 5)
        {
            keyboard = Peripheral("Win32_Keyboard");
            mouse = Peripheral("Win32_PointingDevice");
            lastPeripherals = DateTime.UtcNow;
        }
        return new { cpu = cpuLoad, ram, cpu_temperature = cpuTemp, gpu_temperature = gpuTemp, fan_rpm = fan, keyboard, mouse };
    }

    public void Dispose() { cpu?.Dispose(); computer.Close(); }
}
