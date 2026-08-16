using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class LidarReceiver : MonoBehaviour
{
    public int port = 31003;
    public bool obstacleDetected = false;

    private TcpListener listener;
    private Thread serverThread;
    private bool isRunning = false;

    void Start()
    {
        serverThread = new Thread(StartServer);
        serverThread.IsBackground = true;
        serverThread.Start();
    }

    void OnApplicationQuit()
    {
        isRunning = false;
        listener?.Stop();
        serverThread?.Abort();
    }

    void StartServer()
    {
        try
        {
            listener = new TcpListener(IPAddress.Any, port);
            listener.Start();
            isRunning = true;
            Debug.Log($"✅ Lidar TCP Server started on port {port}");

            using TcpClient client = listener.AcceptTcpClient();
            Debug.Log($"🌐 Connected to {client.Client.RemoteEndPoint}");

            using NetworkStream stream = client.GetStream();
            byte[] buffer = new byte[64];

            while (isRunning && client.Connected)
            {
                int bytesRead = stream.Read(buffer, 0, buffer.Length);
                if (bytesRead == 0) break;

                string msg = Encoding.UTF8.GetString(buffer, 0, bytesRead).Trim();
                if (msg == "True" || msg == "False")
                {
                    obstacleDetected = (msg == "True");
                    Debug.Log($"📥 LiDAR Status: {obstacleDetected}");
                }
                else
                {
                    Debug.LogWarning($"⚠️ Unexpected LiDAR message: {msg}");
                }
            }

            Debug.Log("🚪 LiDAR connection closed.");
        }
        catch (Exception e)
        {
            Debug.LogError("🚨 LiDAR TCP Server error: " + e.Message);
        }
    }
}
