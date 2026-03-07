type Props = {
    title: string
    data: Record<string, any>
    status?: "normal" | "warning" | "critical"
}

export function VehicleOverlay({ title, data, status = "normal" }: Props) {

    const borderColor =
        status === "critical"
            ? "#ff3b3b"
            : status === "warning"
            ? "#ffaa00"
            : "rgba(255,255,255,0.2)"

    const animation =
        status === "critical"
            ? "pulseCritical 1s infinite"
            : status === "warning"
            ? "pulseWarn 2s infinite"
            : "none"

    return (
        <div
            style={{
                background: "rgba(0,0,0,0.85)",
                color: "white",
                padding: "6px 8px",
                borderRadius: 8,
                fontSize: 11,
                minWidth: 120,
                border: `1px solid ${borderColor}`,
                animation
            }}
        >

            <style>
                {`
                @keyframes pulseCritical {
                    0% { box-shadow: 0 0 0px #ff3b3b }
                    50% { box-shadow: 0 0 12px #ff3b3b }
                    100% { box-shadow: 0 0 0px #ff3b3b }
                }

                @keyframes pulseWarn {
                    0% { box-shadow: 0 0 0px #ffaa00 }
                    50% { box-shadow: 0 0 8px #ffaa00 }
                    100% { box-shadow: 0 0 0px #ffaa00 }
                }
                `}
            </style>

            <div
                style={{
                    fontWeight: 600,
                    marginBottom: 4
                }}
            >
                {title}
            </div>

            {Object.entries(data).map(([k, v]) => (
                <div key={k}>
                    <span style={{ opacity: 0.7 }}>{k}:</span> {v}
                </div>
            ))}

        </div>
    )
}