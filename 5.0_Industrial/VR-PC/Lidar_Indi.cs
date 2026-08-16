using UnityEngine;

public class Lidar_Indi : MonoBehaviour
{
    public LidarReceiver lidarReceiver; // ✅ Renamed to avoid naming conflict
    private TextMesh sensorText;
    private Renderer[] renderers;

    void Start()
    {
        sensorText = transform.Find("New Text")?.GetComponent<TextMesh>();
        renderers = GetComponentsInChildren<Renderer>();
    }

    void Update()
    {
        if (lidarReceiver == null || sensorText == null) return;

        if (lidarReceiver.obstacleDetected)
        {
            sensorText.text = "ERR";
            sensorText.color = Color.red;
            SetColor(Color.red);
        }
        else
        {
            sensorText.text = "SAFE";
            sensorText.color = Color.black;
            SetColor(Color.green);
        }
    }

    void SetColor(Color c)
    {
        foreach (Renderer rend in renderers)
        {
            if (rend != null) rend.material.color = c;
        }
    }
}
