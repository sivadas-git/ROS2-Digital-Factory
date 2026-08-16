// This script will link the PLCReceiver values to SensorStatus3D behavior
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class SensorStatus3DROS : MonoBehaviour
{
    public GameObject sensor;
    public float mySensorValue;

    public float minSensorValue;
    public float nomSensorValue;
    public float maxSensorValue;
    public string sensorTopic; // e.g., "sensor/s204"
    public PLCReceiver plcReceiver; // Assign via Inspector or FindObjectOfType

    private TextMesh sensor_value;

    public void setMin(float val) => minSensorValue = val;
    public void setNom(float val) => nomSensorValue = val;
    public void setMax(float val) => maxSensorValue = val;

    void Start()
    {
        if (plcReceiver == null)
        {
            plcReceiver = FindObjectOfType<PLCReceiver>();
        }

        sensor_value = transform.Find("New Text")?.GetComponent<TextMesh>();
    }

    void Update()
    {
        if (plcReceiver != null && plcReceiver.sensorValues.TryGetValue(sensorTopic, out float value))
        {
            mySensorValue = value;
            if (sensor_value != null)
                sensor_value.text = value.ToString("F2");
        }
        else
        {
            mySensorValue = 327.64f;
            if (sensor_value != null)
                sensor_value.text = "out";
        }

        // Visual color feedback
        Color statusColor = Color.green;
        Vector3 directionOffset = new Vector3(0, -0.25f, 0);

        if (mySensorValue < minSensorValue)
        {
            statusColor = Color.red;
            directionOffset = new Vector3(-1.25f, -0.25f, 0);
        }
        else if (mySensorValue > maxSensorValue)
        {
            statusColor = Color.red;
            directionOffset = new Vector3(1.25f, -0.25f, 0);
        }

        SetColorAndDirection(statusColor, directionOffset);
    }

    private void SetColorAndDirection(Color color, Vector3 directionPosition)
    {
        Transform bar = transform.Find("bar");
        Transform dir = transform.Find("direction");
        Transform plane1 = transform.Find("Plane (1)");
        Transform plane2 = transform.Find("Plane");

        if (bar) bar.GetComponent<Renderer>().material.color = color;
        if (dir)
        {
            dir.GetComponent<Renderer>().material.color = color;
            dir.localPosition = directionPosition;
        }
        if (plane1) plane1.GetComponent<Renderer>().material.color = color;
        if (plane2) plane2.GetComponent<Renderer>().material.color = color;
    }
}
