using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.IO;
using UnityEngine;

public class Industrial : MonoBehaviour
{
    private TcpListener listener;
    private Thread serverThread;

    private const int port = 30000;
    private string logPath;

    void Start()
    {
        logPath = Application.dataPath + "/industrial_rtt_log_1.csv";
        WriteCsvHeader();

        serverThread = new Thread(StartServer);
        serverThread.IsBackground = true;
        serverThread.Start();
    }

    void OnApplicationQuit()
    {
        if (listener != null)
            listener.Stop();

        if (serverThread != null)
            serverThread.Abort();
    }

    void WriteCsvHeader()
    {
        if (!File.Exists(logPath))
        {
            File.WriteAllText(logPath, "Timestamp_Sent,RTT_Seconds,Robot_Message\n");
        }
    }

    void AppendToCsv(string timestampSent, string rtt, string message)
    {
        string line = string.Format("{0},{1},\"{2}\"\n", timestampSent, rtt, message);
        File.AppendAllText(logPath, line);
    }

    void StartServer()
    {
        try
        {
            listener = new TcpListener(IPAddress.Any, port);
            listener.Start();
            Debug.Log("✅ Unity TCP server started on port " + port + ".");

            while (true)
            {
                TcpClient client = listener.AcceptTcpClient();
                using (client)
                {
                    Debug.Log("🤖 Robot connected from " + client.Client.RemoteEndPoint);

                    using (NetworkStream stream = client.GetStream())
                    {
                        while (client.Connected)
                        {
                            double t0 = GetUnixTimeNow();
                            string timestampMsg = t0.ToString("F6");
                            byte[] outbound = Encoding.UTF8.GetBytes(timestampMsg);
                            stream.Write(outbound, 0, outbound.Length);
                            Debug.Log("📤 Sent timestamp: " + timestampMsg);

                            byte[] buffer = new byte[1024];
                            int bytesRead = stream.Read(buffer, 0, buffer.Length);
                            if (bytesRead == 0)
                                break;

                            string fullMsg = Encoding.UTF8.GetString(buffer, 0, bytesRead).Trim();
                            Debug.Log("📥 Received from robot: " + fullMsg);

                            if (fullMsg.EndsWith("END"))
                                fullMsg = fullMsg.Substring(0, fullMsg.Length - 3).TrimEnd();

                            string[] parts = fullMsg.Split(',');
                            if (parts.Length > 0 && double.TryParse(parts[0], out double echoedTimestamp))
                            {
                                double tNow = GetUnixTimeNow();
                                double rtt = tNow - echoedTimestamp;
                                Debug.Log("⏱ RTT: " + rtt.ToString("F6") + " seconds");

                                AppendToCsv(timestampMsg, rtt.ToString("F6"), fullMsg);
                            }
                            else
                            {
                                Debug.LogWarning("⚠️ Could not parse timestamp from robot.");
                            }

                            Thread.Sleep(500);
                        }

                        Debug.Log("🔌 Robot disconnected.");
                    }
                }
            }
        }
        catch (Exception ex)
        {
            Debug.LogError("❌ TCP Server Error: " + ex.Message);
        }
    }

    double GetUnixTimeNow()
    {
        return (DateTime.UtcNow - new DateTime(1970, 1, 1)).TotalSeconds;
    }
}
