using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class UR10Receiver : MonoBehaviour
{
    public int port = 31002;
    public float[] jointAngles = new float[6]; // Angles in radians (public for inspector)
    
    private TcpListener listener;
    private Thread serverThread;
    private bool isRunning = false;
    private StringBuilder buffer = new StringBuilder();

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
            Debug.Log($"UR10 TCP Server started on port {port}");

            TcpClient client = listener.AcceptTcpClient();
            Debug.Log($"UR10 connected from {client.Client.RemoteEndPoint}");

            NetworkStream stream = client.GetStream();
            byte[] byteBuffer = new byte[256];

            while (isRunning && client.Connected)
            {
                int bytesRead = stream.Read(byteBuffer, 0, byteBuffer.Length);
                if (bytesRead == 0) break;

                string incoming = Encoding.UTF8.GetString(byteBuffer, 0, bytesRead);
                buffer.Append(incoming);

                ProcessBuffer();
            }

            Debug.Log("UR10 connection closed.");
        }
        catch (Exception e)
        {
            Debug.LogError("UR10 TCP Server error: " + e.Message);
        }
    }

    void ProcessBuffer()
    {
        string buf = buffer.ToString();
        int start = buf.IndexOf('[');
        int end = buf.IndexOf(']');

        if (start >= 0 && end > start)
        {
            string cleanData = buf.Substring(start + 1, end - start - 1); // get content inside [ ]
            string[] parts = cleanData.Split(',');

            if (parts.Length == 6)
            {
                for (int i = 0; i < 6; i++)
                {
                    if (float.TryParse(parts[i].Trim(), out float val))
                    {
                        jointAngles[i] = val;
                    }
                    else
                    {
                        Debug.LogWarning($"Parse error on joint {i}: '{parts[i]}'");
                    }
                }

                Debug.Log($"✅ Received UR10 joint angles: [{string.Join(", ", jointAngles)}]");
            }
            else
            {
                Debug.LogWarning($"⚠️ Unexpected joint count: {parts.Length}, data: {cleanData}");
            }

            buffer.Clear(); // ready for next
        }
        else if (buf.Length > 500) // prevent runaway memory
        {
            Debug.LogWarning("⚠️ Discarding overflow buffer");
            buffer.Clear();
        }
    }
}
