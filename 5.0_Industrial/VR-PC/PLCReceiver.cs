using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class PLCReceiver : MonoBehaviour
{
    public int port = 31004;

    // Inspector-exposed variables for sensor topics
    [Header("Live Sensor Values")]
    public float sensor_s203;
    public float sensor_s204;
    public float sensor_s205;
    public float sensor_s207;
    public float sensor_s212;
    public float sensor_s213;
    public float sensor_s215;
    public float sensor_s216;

    public Dictionary<string, float> sensorValues = new Dictionary<string, float>();

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
            Debug.Log($"PLC TCP Server started on port {port}");

            TcpClient client = listener.AcceptTcpClient();
            Debug.Log($"PLC connected from {client.Client.RemoteEndPoint}");

            NetworkStream stream = client.GetStream();
            byte[] buffer = new byte[128];

            while (isRunning && client.Connected)
            {
                int bytesRead = stream.Read(buffer, 0, buffer.Length);
                if (bytesRead == 0) break;

                string msg = Encoding.UTF8.GetString(buffer, 0, bytesRead).Trim();
                string[] lines = msg.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);

                foreach (string line in lines)
                {
                    string[] parts = line.Trim().Split(',');

                    if (parts.Length == 2 && float.TryParse(parts[1], out float value))
                    {
                        string topic = parts[0].Trim();
                        sensorValues[topic] = value;
                        AssignToInspectorVariable(topic, value);
                        Debug.Log($"📥 Sensor: {topic}, Value: {value:F2}");
                    }
                    else
                    {
                        Debug.LogWarning($"⚠️ Unexpected PLC message line: {line}");
                    }
                }
            }

            Debug.Log("PLC connection closed.");
            stream.Close();
            client.Close();
        }
        catch (Exception e)
        {
            Debug.LogError("PLC TCP Server error: " + e.Message);
        }
    }

    void AssignToInspectorVariable(string topic, float value)
    {
        switch (topic)
        {
            case "sensor/s203": sensor_s203 = value; break;
            case "sensor/s204": sensor_s204 = value; break;
            case "sensor/s205": sensor_s205 = value; break;
            case "sensor/s207": sensor_s207 = value; break;
            case "sensor/s212": sensor_s212 = value; break;
            case "sensor/s213": sensor_s213 = value; break;
            case "sensor/s215": sensor_s215 = value; break;
            case "sensor/s216": sensor_s216 = value; break;
        }
    }

    public float GetSensorValue(string topic)
    {
        if (sensorValues.TryGetValue(topic, out float value))
            return value;
        return float.NaN;
    }
}
