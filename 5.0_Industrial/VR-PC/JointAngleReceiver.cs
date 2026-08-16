using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class JointAngleReceiver : MonoBehaviour
{
    [Header("TCP Server Settings")]
    public int listenPort = 30001;

    [Header("Joint Angles (radians)")]
    public float[] jointAnglesRad = new float[6];
    public bool newDataAvailable = false;

    private TcpListener tcpListener;
    private Thread serverThread;
    private bool running = false;

    void Start()
    {
        StartServer();
    }

    void OnApplicationQuit()
    {
        StopServer();
    }

    public void MarkDataConsumed()
    {
        newDataAvailable = false;
    }

    private void StartServer()
    {
        try
        {
            tcpListener = new TcpListener(IPAddress.Any, listenPort);
            tcpListener.Start();
            running = true;

            serverThread = new Thread(ListenForClient);
            serverThread.IsBackground = true;
            serverThread.Start();

            Debug.Log($"TCP Server started on port {listenPort}");
        }
        catch (Exception ex)
        {
            Debug.LogError("Failed to start TCP server: " + ex.Message);
        }
    }

    private void StopServer()
    {
        running = false;

        try
        {
            serverThread?.Abort();
            tcpListener?.Stop();
        }
        catch (Exception ex)
        {
            Debug.LogWarning("Error stopping server: " + ex.Message);
        }
    }

    private void ListenForClient()
    {
        while (running)
        {
            try
            {
                using (TcpClient client = tcpListener.AcceptTcpClient())
                using (NetworkStream stream = client.GetStream())
                {
                    Debug.Log("Client connected to TCP server.");
                    byte[] buffer = new byte[1024];

                    while (running && client.Connected)
                    {
                        if (stream.DataAvailable)
                        {
                            int bytesRead = stream.Read(buffer, 0, buffer.Length);
                            if (bytesRead > 0)
                            {
                                string msg = Encoding.ASCII.GetString(buffer, 0, bytesRead).Trim();
                                ProcessMessage(msg);
                            }
                        }

                        Thread.Sleep(5);
                    }

                    Debug.Log("Client disconnected.");
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning("Client connection error: " + e.Message);
            }

            Thread.Sleep(100);
        }
    }

    private void ProcessMessage(string msg)
    {
        if (!msg.StartsWith("J:")) return;

        string[] parts = msg.Substring(2).Split(',');

        if (parts.Length != 6)
        {
            Debug.LogWarning("Invalid joint data received: " + msg);
            return;
        }

        try
        {
            for (int i = 0; i < 6; i++)
            {
                jointAnglesRad[i] = float.Parse(parts[i], System.Globalization.CultureInfo.InvariantCulture);
            }

            newDataAvailable = true;
        }
        catch (Exception e)
        {
            Debug.LogWarning("Failed to parse joint angles: " + e.Message);
        }
    }
}
