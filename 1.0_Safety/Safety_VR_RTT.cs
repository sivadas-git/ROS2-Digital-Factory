using UnityEngine;
using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

public class Safety_VR_RTT : MonoBehaviour
{
    private const int Port = 23002;
    private TcpListener server;
    private Thread acceptThread;

    // Keep original public variables for your scene/UI
    public string x;
    public string y;

    // Optional debug
    public string lastUuid;
    public string lastRawMessage;

    void Start()
    {
        StartServer();
    }

    void OnApplicationQuit()
    {
        StopServer();
    }

    private void StartServer()
    {
        try
        {
            server = new TcpListener(IPAddress.Any, Port);
            server.Start();
            Debug.Log($"[VR] TCP server listening on port {Port}.");

            acceptThread = new Thread(() =>
            {
                try
                {
                    while (true)
                    {
                        TcpClient client = server.AcceptTcpClient();
                        ThreadPool.QueueUserWorkItem(HandleClient, client);
                    }
                }
                catch (SocketException)
                {
                    // Expected when server.Stop() is called on quit
                }
                catch (Exception e)
                {
                    Debug.LogError($"[VR] Accept loop exception: {e.Message}");
                }
            });

            acceptThread.IsBackground = true;
            acceptThread.Start();
        }
        catch (Exception e)
        {
            Debug.LogError($"[VR] Exception starting server: {e.Message}");
        }
    }

    private void HandleClient(object obj)
    {
        TcpClient client = (TcpClient)obj;

        try
        {
            using (var stream = client.GetStream())
            using (var reader = new StreamReader(stream, Encoding.UTF8))
            using (var writer = new StreamWriter(stream, Encoding.UTF8) { AutoFlush = true })
            {
                // Keep connection open; echo each line
                while (client.Connected)
                {
                    string message = reader.ReadLine();
                    if (message == null) break;

                    // 1) Echo immediately (RTT should not include processing)
                    writer.WriteLine(message);

                    // 2) Then process for visualization/debug
                    ProcessMessage(message);
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"[VR] HandleClient exception: {e.Message}");
        }
        finally
        {
            try { client.Close(); } catch { }
        }
    }

    private void ProcessMessage(string message)
    {
        // Expected:
        //   "uuid;light,sound"
        // Legacy:
        //   "light,sound"
        if (string.IsNullOrEmpty(message))
            return;

        lastRawMessage = message;

        string uuidPart = "";
        string payload = message;

        int semi = message.IndexOf(';');
        if (semi >= 0)
        {
            uuidPart = message.Substring(0, semi);
            payload = message.Substring(semi + 1);
        }

        // Parse payload for VR UI/state (does not affect RTT since echo already sent)
        string[] parts = payload.Split(',');
        if (parts.Length == 2)
        {
            lastUuid = uuidPart;
            x = parts[0];
            y = parts[1];
        }
        else
        {
            // Keep this lightweight; heavy logging can add noise on VR side
            // but RTT path is already completed due to immediate echo.
            Debug.Log("[VR] Invalid payload format. Expected 'light,sound' (optionally prefixed by uuid;).");
        }
    }

    private void StopServer()
    {
        try
        {
            server?.Stop();
        }
        catch (Exception e)
        {
            Debug.LogError($"[VR] Exception stopping server: {e.Message}");
        }
    }
}
