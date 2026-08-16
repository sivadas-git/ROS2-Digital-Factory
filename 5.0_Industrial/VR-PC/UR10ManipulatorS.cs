using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class UR10ManipulatorS : MonoBehaviour
{
    public UR10Receiver receiver;
    public LidarReceiver lidarReceiver; // 🔴 Add this in Unity Inspector

    public Transform Motor1;
    public Transform Motor2;
    public Transform Motor3;
    public Transform Motor4;
    public Transform Motor5;
    public Transform Motor6;

    public bool invertJoint1 = false;
    public bool invertJoint2 = false;
    public bool invertJoint3 = false;
    public bool invertJoint4 = false;
    public bool invertJoint5 = false;
    public bool invertJoint6 = false;

    public float offsetJ1 = 0f;
    public float offsetJ2 = 0f;
    public float offsetJ3 = 0f;
    public float offsetJ4 = 0f;
    public float offsetJ5 = 0f;
    public float offsetJ6 = 0f;

    void Update()
    {
        // 🔴 Halt movement if LiDAR detects obstacle
        if (lidarReceiver != null && lidarReceiver.obstacleDetected)
            return;

        if (receiver == null || receiver.jointAngles == null || receiver.jointAngles.Length < 6)
            return;

        float sign1 = invertJoint1 ? -1f : 1f;
        float sign2 = invertJoint2 ? -1f : 1f;
        float sign3 = invertJoint3 ? -1f : 1f;
        float sign4 = invertJoint4 ? -1f : 1f;
        float sign5 = invertJoint5 ? -1f : 1f;
        float sign6 = invertJoint6 ? -1f : 1f;

        float j1 = sign1 * receiver.jointAngles[0] * Mathf.Rad2Deg + offsetJ1;
        float j2 = sign2 * receiver.jointAngles[1] * Mathf.Rad2Deg + offsetJ2;
        float j3 = sign3 * receiver.jointAngles[2] * Mathf.Rad2Deg + offsetJ3;
        float j4 = sign4 * receiver.jointAngles[3] * Mathf.Rad2Deg + offsetJ4;
        float j5 = sign5 * receiver.jointAngles[4] * Mathf.Rad2Deg + offsetJ5;
        float j6 = sign6 * receiver.jointAngles[5] * Mathf.Rad2Deg + offsetJ6;

        Motor1.localEulerAngles = new Vector3(0, j1, 0);
        Motor2.localEulerAngles = new Vector3(0, j2, 0);
        Motor3.localEulerAngles = new Vector3(0, j3, 0);
        Motor4.localEulerAngles = new Vector3(0, j4, 0);
        Motor5.localEulerAngles = new Vector3(0, j5, 0);
        Motor6.localEulerAngles = new Vector3(0, j6, 0);
    }
}
