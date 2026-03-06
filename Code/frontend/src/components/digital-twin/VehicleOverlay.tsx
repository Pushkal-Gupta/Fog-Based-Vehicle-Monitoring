type Props = {
    title: string
    data: Record<string, any>
}

export function VehicleOverlay({ title, data }: Props) {

    return (
        <div
            style={{
                background: "rgba(0,0,0,0.75)",
                padding: "8px 10px",
                borderRadius: "8px",
                color: "white",
                fontSize: "12px",
                minWidth: "120px"
            }}
        >
            <div style={{ fontWeight: "bold", marginBottom: "4px" }}>
                {title}
            </div>

            {Object.entries(data).map(([k, v]) => (
                <div key={k}>
                    {k}: {v}
                </div>
            ))}
        </div>
    )
}