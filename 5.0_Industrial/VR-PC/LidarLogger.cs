// ===================== Unity Side: LidarLogger.cs =====================

using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;

public class LidarLogger : MonoBehaviour
{
    public int port = 31005;
    private TcpListener listener;
    private Thread serverThread;
    private bool isRunning = false;

    private Dictionary<string, DateTime> requestTimestamps = new Dictionary<string, DateTime>();
    private ConcurrentQueue<string> logQueue = new ConcurrentQueue<string>();
    private ConcurrentQueue<string> csvQueue = new ConcurrentQueue<string>();

    private TcpClient client;
    private NetworkStream stream;
    private float timer = 0f;
    private float interval = 1f / 60f;

    private int requestCounter = 1;
    private string logPath;

    void Start()
    {
        logPath = Path.Combine(Application.dataPath, "lidar_rtt_log.csv");

        if (!File.Exists(logPath))
        {
            File.WriteAllText(logPath, "Timestamp,RequestID,RTT_ms,Obstacle\n");
        }

        serverThread = new Thread(StartServer);
        serverThread.IsBackground = true;
        serverThread.Start();
    }

    void Update()
    {
        // Send request at ~60 FPS
        timer += Time.deltaTime;
        if (timer >= interval && stream != null && stream.CanWrite)
        {
            timer = 0f;
            string requestId = "REQ" + requestCounter++;
            requestTimestamps[requestId] = DateTime.Now;
            byte[] msg = Encoding.ASCII.GetBytes(requestId + "\n");
            stream.Write(msg, 0, msg.Length);
        }

        // Console logs
        while (logQueue.TryDequeue(out string logMsg))
        {
            Debug.Log(logMsg);
        }

        // Write to CSV
        while (csvQueue.TryDequeue(out string csvLine))
        {
            File.AppendAllText(logPath, csvLine + "\n");
        }
    }

    void OnApplicationQuit()
    {
        isRunning = false;
        listener?.Stop();
        stream?.Close();
        client?.Close();
        serverThread?.Abort();
    }

    void StartServer()
    {
        try
        {
            listener = new TcpListener(IPAddress.Any, port);
            listener.Start();
            isRunning = true;
            logQueue.Enqueue("✅ Lidar RTT Server started on port " + port);

            client = listener.AcceptTcpClient();
            stream = client.GetStream();
            byte[] buffer = new byte[128];

            while (isRunning && client.Connected)
            {
                int bytesRead = stream.Read(buffer, 0, buffer.Length);
                if (bytesRead == 0) break;

                string reply = Encoding.ASCII.GetString(buffer, 0, bytesRead).Trim();
                if (reply.StartsWith("REQ"))
                {
                    string[] parts = reply.Split('|');
                    if (parts.Length == 2 && requestTimestamps.TryGetValue(parts[0], out DateTime sentTime))
                    {
                        DateTime receivedTime = DateTime.Now;
                        TimeSpan rtt = receivedTime - sentTime;
                        double rttMs = Math.Round(rtt.TotalMilliseconds, 4);

                        string timestamp = receivedTime.ToString("yyyy-MM-dd HH:mm:ss.ffff");
                        string csvLine = $"{timestamp},{parts[0]},{rttMs},{parts[1]}";

                        logQueue.Enqueue($"📡 RTT ({parts[0]}): {rttMs} ms | Obstacle: {parts[1]}");
                        csvQueue.Enqueue(csvLine);

                        requestTimestamps.Remove(parts[0]);
                    }
                }
            }

            logQueue.Enqueue("🚪 Lidar RTT connection closed.");
        }
        catch (Exception e)
        {
            logQueue.Enqueue("❌ Lidar RTT server error: " + e.Message);
        }
    }
}
