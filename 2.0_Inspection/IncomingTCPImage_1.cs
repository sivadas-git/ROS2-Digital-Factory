using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;

public class IncomingTCPImage_1 : MonoBehaviour
{
    public string mIP;
    public int mPort;
    private TcpListener mTCPListener; // Server Socket
    private const string IMAGE_SAVE_PATH = "D:/1_PhD/MiniFactory/UC4/Assets/Images";
    private const string LOG_FILE = "D:/1_PhD/MiniFactory/UC4/Assets/Logs/msi_siva_log.txt";
    private List<TcpClient> mClients;
    public bool KeepRunning { get; set; }
    // public float myintensity;
    // public GameObject Led;
    // private Light mylight;

    public IncomingTCPImage_1()
    {
        mClients = new List<TcpClient>();
    }

    void Start()
    {
        StartListeningForIncomingConnection(mIP, mPort);
        // mylight = Led.GetComponent<Light>();
        // mylight.intensity = 0f;

        // Initialize log file
        using (StreamWriter writer = new StreamWriter(LOG_FILE, false))
        {
            writer.WriteLine("Timestamp,Event,Details");
        }
    }

    public async void StartListeningForIncomingConnection(string mIP, int port)
    {
        mPort = port;
        Debug.Log($"IP Address: {mIP} - Port: {mPort}");
        LogEvent("Server Started", $"Listening on {mIP}:{mPort}");
        var myIP = IPAddress.Parse(mIP);
        mTCPListener = new TcpListener(myIP, mPort);

        try
        {
            mTCPListener.Start();
            KeepRunning = true;

            while (KeepRunning)
            {
                var returnedByAccept = await mTCPListener.AcceptTcpClientAsync();
                mClients.Add(returnedByAccept);
                string clientInfo = returnedByAccept.Client.RemoteEndPoint.ToString();
                Debug.Log($"Client connected: {clientInfo}");
                LogEvent("Client Connected", clientInfo);
                TakeCareOfTCPClient(returnedByAccept);
            }
        }
        catch (Exception excp)
        {
            Debug.Log(excp.ToString());
            LogEvent("Error", excp.Message);
        }
    }

    public void StopServer()
    {
        try
        {
            if (mTCPListener != null)
            {
                mTCPListener.Stop();
            }

            foreach (TcpClient c in mClients)
            {
                c.Close();
            }

            mClients.Clear();
            LogEvent("Server Stopped", "All clients disconnected and server stopped.");
        }
        catch (Exception excp)
        {
            Debug.Log(excp.ToString());
            LogEvent("Error", excp.Message);
        }
    }

    private async void TakeCareOfTCPClient(TcpClient returnedByAccept)
    {
        NetworkStream stream = null;
        MemoryStream memoryStream = new MemoryStream();
        byte[] delimiter = Encoding.ASCII.GetBytes("\nEND\n");

        try
        {
            stream = returnedByAccept.GetStream();
            byte[] buff = new byte[8192]; // Buffer for incoming data
            LogEvent("Data Reception Started", "Receiving data from client.");

            while (true)
            {
                int nRet = await stream.ReadAsync(buff, 0, buff.Length);

                if (nRet == 0)
                {
                    LogEvent("Client Disconnected", "Client closed the connection.");
                    Debug.Log("Socket Disconnected");
                    break;
                }

                memoryStream.Write(buff, 0, nRet);

                // Check for delimiter
                if (EndsWithDelimiter(memoryStream, delimiter))
                {
                    LogEvent("Data Reception Completed", $"Total received size: {memoryStream.Length} bytes.");

                    byte[] fullData = RemoveDelimiter(memoryStream, delimiter);

                    // Extract dimensions and image data
                    int separatorIndex = Array.IndexOf(fullData, (byte)'\n');
                    if (separatorIndex == -1)
                    {
                        LogEvent("Error", "Invalid data format: Missing dimensions.");
                        SendReply(returnedByAccept, "Invalid data format: Missing dimensions.");
                        memoryStream.SetLength(0);
                        continue;
                    }

                    string dimensions = Encoding.UTF8.GetString(fullData, 0, separatorIndex).Trim();
                    int imageDataStartIndex = separatorIndex + 1;
                    byte[] imageData = new byte[fullData.Length - imageDataStartIndex];
                    Array.Copy(fullData, imageDataStartIndex, imageData, 0, imageData.Length);

                    // Save the image
                    if (imageData.Length > 0)
                    {
                        string timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                        string imagePath = Path.Combine(IMAGE_SAVE_PATH, $"received_{timestamp}.jpg");
                        File.WriteAllBytes(imagePath, imageData);
                        LogEvent("Image Saved", $"Path: {imagePath}, Dimensions: {dimensions}");
                        Debug.Log($"Image saved to: {imagePath}");
                        Debug.Log($"Dimensions: {dimensions}");

                        // Send confirmation reply
                        SendReply(returnedByAccept, "echo_received");
                        LogEvent("Reply Sent", "echo_received");
                    }
                    else
                    {
                        LogEvent("Error", "No valid image data received.");
                        SendReply(returnedByAccept, "No valid image data received");
                    }

                    memoryStream.SetLength(0); // Reset the memory stream for the next transmission
                }
            }
        }
        catch (Exception excp)
        {
            Debug.Log(excp.ToString());
            LogEvent("Error", excp.Message);
        }
        finally
        {
            RemoveClient(returnedByAccept);
        }
    }

    private void RemoveClient(TcpClient returnedByAccept)
    {
        if (mClients.Contains(returnedByAccept))
        {
            mClients.Remove(returnedByAccept);
            string clientInfo = returnedByAccept.Client.RemoteEndPoint.ToString();
            Debug.Log($"Client removed: {clientInfo}");
            LogEvent("Client Disconnected", clientInfo);
            returnedByAccept.Close();
        }
    }

    private async void SendReply(TcpClient client, string message)
    {
        try
        {
            if (client.Connected)
            {
                byte[] bufferMessage = Encoding.ASCII.GetBytes(message);
                await client.GetStream().WriteAsync(bufferMessage, 0, bufferMessage.Length);
                Debug.Log($"Reply sent to client: {message}");
            }
        }
        catch (Exception excp)
        {
            Debug.Log($"Failed to send reply: {excp}");
            LogEvent("Error", $"Failed to send reply: {excp.Message}");
        }
    }

    private bool EndsWithDelimiter(MemoryStream memoryStream, byte[] delimiter)
    {
        if (memoryStream.Length < delimiter.Length)
            return false;

        byte[] tail = new byte[delimiter.Length];
        memoryStream.Seek(-delimiter.Length, SeekOrigin.End);
        memoryStream.Read(tail, 0, delimiter.Length);

        return Encoding.ASCII.GetString(tail) == Encoding.ASCII.GetString(delimiter);
    }

    private byte[] RemoveDelimiter(MemoryStream memoryStream, byte[] delimiter)
    {
        long dataLength = memoryStream.Length - delimiter.Length;
        byte[] dataWithoutDelimiter = new byte[dataLength];

        memoryStream.Seek(0, SeekOrigin.Begin);
        memoryStream.Read(dataWithoutDelimiter, 0, (int)dataLength);

        return dataWithoutDelimiter;
    }

    private void LogEvent(string eventName, string details)
    {
        string timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
        string logEntry = $"{timestamp},{eventName},{details}";
        Debug.Log(logEntry);

        using (StreamWriter writer = new StreamWriter(LOG_FILE, true))
        {
            writer.WriteLine(logEntry);
        }
    }
}
