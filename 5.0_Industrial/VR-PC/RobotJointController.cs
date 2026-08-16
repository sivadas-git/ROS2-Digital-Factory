using UnityEngine;

public class RobotJointController : MonoBehaviour
{
    [Header("UR10 Joint GameObjects")]
    public Transform Motor1;
    public Transform Motor2;
    public Transform Motor3;
    public Transform Motor4;
    public Transform Motor5;
    public Transform Motor6;

    [Header("TCP Joint Angle Input")]
    public JointAngleReceiver jointReceiver;

    [Header("Calibration Offsets (degrees)")]
    public float[] jointOffsets = new float[6];  // can be zero if not calibrated

    private float[] currentAngles = new float[6];

    void Start()
    {
        if (jointReceiver == null)
        {
            Debug.LogError("JointAngleReceiver not assigned.");
        }
    }

    void LateUpdate()
    {
        if (jointReceiver == null || !jointReceiver.newDataAvailable)
            return;

        for (int i = 0; i < 6; i++)
        {
            currentAngles[i] = jointReceiver.jointAnglesRad[i] * Mathf.Rad2Deg + jointOffsets[i];
        }

        ApplyJointAngles(currentAngles);

        jointReceiver.MarkDataConsumed();
    }

    void ApplyJointAngles(float[] angles)
    {
        // Apply angles to each joint's local rotation (adapt axes if needed)
        Motor1.localEulerAngles = new Vector3(0f, angles[0], 0f);
        Motor2.localEulerAngles = new Vector3(0f, angles[1], 0f);
        Motor3.localEulerAngles = new Vector3(0f, angles[2], 0f);
        Motor4.localEulerAngles = new Vector3(0f, angles[3], 0f);
        Motor5.localEulerAngles = new Vector3(0f, angles[4], 0f);
        Motor6.localEulerAngles = new Vector3(0f, angles[5], 0f);
    }
}
